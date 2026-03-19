from typing import TypeVar, Generic, Type, Optional, List, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi.encoders import jsonable_encoder

from ..database import Base

# O Tipo Genérico que representará nossas Entidades SQLAlchemy
ModelType = TypeVar("ModelType", bound=Base)


class IRepository(Generic[ModelType]):
    """
    Interface (Contrato Base) para Repositórios.
    O 'I' representa as regras que qualquer classe de banco de dados deve seguir.
    (SOLID: Dependency Inversion Principle - Serviços dependerão disto, não do SQLAlchemy).
    """
    
    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        raise NotImplementedError
        
    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        raise NotImplementedError
        
    async def create(self, db: AsyncSession, obj_in: Any) -> ModelType:
        raise NotImplementedError
        
    async def update(self, db: AsyncSession, db_obj: ModelType, obj_in: Any) -> ModelType:
        raise NotImplementedError
        
    async def remove(self, db: AsyncSession, id: Any) -> ModelType:
        raise NotImplementedError


class SQLAlchemyRepository(IRepository[ModelType]):
    """
    Implementação concreta do Repositório usando SQLAlchemy para acesso ao DB.
    """
    
    def __init__(self, model: Type[ModelType]):
        """
        Recebe a classe do modelo (ex: User, Order) 
        para que as operações genéricas saibam a quem acessar.
        """
        self.model = model

    async def get(self, db: AsyncSession, id: Any) -> Optional[ModelType]:
        result = await db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_multi(self, db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ModelType]:
        result = await db.execute(select(self.model).offset(skip).limit(limit))
        return list(result.scalars().all())

    async def create(self, db: AsyncSession, obj_in: Any) -> ModelType:
        if isinstance(obj_in, dict):
            obj_in_data = obj_in
        else:
            # Pydantic v2/v1 compat
            obj_in_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in.dict(exclude_unset=True)
            
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, db_obj: ModelType, obj_in: Any) -> ModelType:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True) if hasattr(obj_in, "model_dump") else obj_in.dict(exclude_unset=True)
            
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
                
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def remove(self, db: AsyncSession, id: Any) -> ModelType:
        obj = await self.get(db, id)
        if obj:
            await db.delete(obj)
            await db.commit()
        return obj

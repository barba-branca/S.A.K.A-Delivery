from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from .base import SQLAlchemyRepository
from ..models import Order


class OrderRepository(SQLAlchemyRepository[Order]):
    """Repositório Específico para a entidade Order (Pedidos KDS)."""
    
    def __init__(self):
        super().__init__(Order)
        
    async def get_with_items(self, db: AsyncSession, order_id: str) -> Optional[Order]:
        """Busca um pedido trazendo (Eager Loading) seus itens atrelados."""
        result = await db.execute(
            select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()
        
    async def get_all_with_items(self, db: AsyncSession, tenant_id: Optional[int] = None) -> List[Order]:
        """Traz todos os pedidos de um Tenant específico com seus itens."""
        query = select(Order).options(selectinload(Order.items)).order_by(Order.created_at.desc())
        
        if tenant_id is not None:
            query = query.where(Order.tenant_id == tenant_id)
            
        result = await db.execute(query)
        return list(result.scalars().all())

    async def get_by_ifood_id(self, db: AsyncSession, ifood_id: str) -> Optional[Order]:
        result = await db.execute(
            select(Order).options(selectinload(Order.items)).where(Order.ifood_id == ifood_id)
        )
        return result.scalar_one_or_none()


# Singleton
order_repository = OrderRepository()

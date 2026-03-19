from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base import SQLAlchemyRepository
from ..models import User

class UserRepository(SQLAlchemyRepository[User]):
    """Repositório Específico para a entidade User."""
    
    def __init__(self):
        super().__init__(User)
        
    async def get_by_username(self, db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()
        
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

# Instância Singleton do repositório para injeção (padrão de Factories também é bem-vindo)
user_repository = UserRepository()

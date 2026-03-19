from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base import SQLAlchemyRepository
from ..models import Pacote


class PacoteRepository(SQLAlchemyRepository[Pacote]):
    """Repositório Específico para Pacotes Pré-Pagos."""
    
    def __init__(self):
        super().__init__(Pacote)
        
    async def get_by_user(self, db: AsyncSession, user_id: int) -> List[Pacote]:
        result = await db.execute(select(Pacote).where(Pacote.user_id == user_id))
        return list(result.scalars().all())

# Singleton
pacote_repository = PacoteRepository()

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .base import SQLAlchemyRepository
from ..models import Tenant


class TenantRepository(SQLAlchemyRepository[Tenant]):
    """Repositório Específico para a entidade Tenant (Locatários SaaS)."""
    
    def __init__(self):
        super().__init__(Tenant)
        
    async def get_by_slug(self, db: AsyncSession, slug: str) -> Optional[Tenant]:
        result = await db.execute(select(Tenant).where(Tenant.slug == slug))
        return result.scalar_one_or_none()

# Singleton
tenant_repository = TenantRepository()

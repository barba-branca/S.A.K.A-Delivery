"""
Configuração do banco de dados PostgreSQL com SQLAlchemy Async.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import get_settings

settings = get_settings()

# Engine async para PostgreSQL
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base declarativa para todos os modelos."""
    pass


async def get_db():
    """
    Dependency que fornece uma sessão async do banco de dados.
    Garante que a sessão seja fechada após o uso.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Inicializa o banco de dados criando todas as tabelas (fallback se Alembic não rodar)."""
    from . import models  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

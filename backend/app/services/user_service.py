"""
Serviço para gerenciamento de usuários (async).
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User, UserRole as DBUserRole
from ..security import hash_password, verify_password

logger = logging.getLogger(__name__)


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_all_users(db: AsyncSession) -> List[User]:
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().all())


async def create_user(
    db: AsyncSession,
    username: str,
    full_name: str,
    password: str,
    role: str = DBUserRole.KITCHEN.value,
    email: Optional[str] = None,
) -> Optional[User]:
    """Cria um novo usuário com hash bcrypt."""
    existing = await get_user_by_username(db, username)
    if existing:
        return None
    
    if email:
        existing_email = await get_user_by_email(db, email)
        if existing_email:
            return None
    
    user = User(
        username=username,
        email=email,
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
        saldo_credito=Decimal("0.00"),
        is_active=True,
        created_at=datetime.utcnow(),
    )
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    logger.info(f"Usuário criado: {username} ({role})")
    return user


async def authenticate_user(db: AsyncSession, username: str, password: str) -> Optional[User]:
    """Autentica um usuário com bcrypt."""
    # Credenciais padrão do sistema (auto-cria na primeira vez)
    default_users = {
        "admin": ("Admin User", "admin123", DBUserRole.ADMIN.value),
        "cozinha": ("Equipe Cozinha", "123", DBUserRole.KITCHEN.value),
    }
    
    if username in default_users and password == default_users[username][1]:
        user = await get_user_by_username(db, username)
        if not user:
            full_name, pwd, role = default_users[username]
            user = await create_user(db, username, full_name, pwd, role)
        else:
            user.last_login = datetime.utcnow()
            await db.commit()
        return user
    
    # Busca normal
    user = await get_user_by_username(db, username)
    if not user or not user.is_active:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    user.last_login = datetime.utcnow()
    await db.commit()
    
    logger.info(f"Login bem-sucedido: {username}")
    return user


async def delete_user(db: AsyncSession, user_id: int) -> bool:
    user = await get_user_by_id(db, user_id)
    if not user:
        return False
    
    await db.delete(user)
    await db.commit()
    
    logger.info(f"Usuário excluído: {user.username}")
    return True

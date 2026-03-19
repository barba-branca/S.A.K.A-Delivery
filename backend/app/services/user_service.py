"""
Serviço para gerenciamento de usuários (async) seguindo SOLID (Clean Architecture).
As rotinas de banco de dados foram movidas para os Repositórios.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import User, UserRole as DBUserRole
from ..security import hash_password, verify_password
from ..repositories.user import UserRepository, user_repository as default_user_repo

logger = logging.getLogger(__name__)


async def get_user_by_username(
    db: AsyncSession, 
    username: str, 
    user_repo: UserRepository = default_user_repo
) -> Optional[User]:
    return await user_repo.get_by_username(db, username)


async def get_user_by_id(
    db: AsyncSession, 
    user_id: int, 
    user_repo: UserRepository = default_user_repo
) -> Optional[User]:
    return await user_repo.get(db, user_id)


async def get_user_by_email(
    db: AsyncSession, 
    email: str, 
    user_repo: UserRepository = default_user_repo
) -> Optional[User]:
    return await user_repo.get_by_email(db, email)


async def get_all_users(
    db: AsyncSession, 
    user_repo: UserRepository = default_user_repo
) -> List[User]:
    return await user_repo.get_multi(db)


async def create_user(
    db: AsyncSession,
    username: str,
    full_name: str,
    password: str,
    role: str = DBUserRole.KITCHEN.value,
    email: Optional[str] = None,
    tenant_id: Optional[int] = None,
    user_repo: UserRepository = default_user_repo
) -> Optional[User]:
    """Cria um novo usuário com hash bcrypt."""
    existing = await user_repo.get_by_username(db, username)
    if existing:
        return None
    
    if email:
        existing_email = await user_repo.get_by_email(db, email)
        if existing_email:
            return None
    
    user_in = {
        "username": username,
        "email": email,
        "full_name": full_name,
        "password_hash": hash_password(password),
        "role": role,
        "saldo_credito": Decimal("0.00"),
        "is_active": True,
        "tenant_id": tenant_id,
        "created_at": datetime.utcnow()
    }
    
    user = await user_repo.create(db, obj_in=user_in)
    logger.info(f"Usuário criado: {username} ({role}) - Tenant: {tenant_id}")
    return user


async def authenticate_user(
    db: AsyncSession, 
    username: str, 
    password: str,
    user_repo: UserRepository = default_user_repo
) -> Optional[User]:
    """Autentica um usuário via repositório."""
    # Credenciais padrão (Criação automática)
    default_users = {
        "admin": ("Admin User", "admin123", DBUserRole.ADMIN.value),
        "cozinha": ("Equipe Cozinha", "123", DBUserRole.KITCHEN.value),
    }
    
    if username in default_users and password == default_users[username][1]:
        user = await user_repo.get_by_username(db, username)
        if not user:
            full_name, pwd, role = default_users[username]
            user = await create_user(db, username, full_name, pwd, role, user_repo=user_repo)
        else:
            await user_repo.update(db, db_obj=user, obj_in={"last_login": datetime.utcnow()})
        return user
    
    # Busca normal
    user = await user_repo.get_by_username(db, username)
    if not user or not user.is_active:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    await user_repo.update(db, db_obj=user, obj_in={"last_login": datetime.utcnow()})
    logger.info(f"Login bem-sucedido: {username}")
    return user


async def delete_user(
    db: AsyncSession, 
    user_id: int, 
    user_repo: UserRepository = default_user_repo
) -> bool:
    user = await user_repo.remove(db, user_id)
    if user:
        logger.info(f"Usuário excluído ID: {user_id}")
        return True
    return False


async def update_user_credits(
    db: AsyncSession, 
    user_id: int, 
    novo_saldo: float,
    user_repo: UserRepository = default_user_repo
) -> Optional[User]:
    """Atualiza o saldo de créditos de um usuário (admin only)."""
    user = await user_repo.get(db, user_id)
    if not user:
        return None
    
    old_saldo = float(user.saldo_credito or 0)
    user = await user_repo.update(db, db_obj=user, obj_in={"saldo_credito": Decimal(str(novo_saldo))})
    
    logger.info(f"Créditos atualizados ID {user_id}: R${old_saldo:.2f} → R${novo_saldo:.2f}")
    return user


async def update_user_role(
    db: AsyncSession, 
    user_id: int, 
    new_role: str,
    user_repo: UserRepository = default_user_repo
) -> Optional[User]:
    """Atualiza o role de um usuário (admin only)."""
    user = await user_repo.get(db, user_id)
    if not user:
        return None
    
    old_role = user.role
    user = await user_repo.update(db, db_obj=user, obj_in={"role": new_role})
    
    logger.info(f"Role atualizado ID {user_id}: {old_role} → {new_role}")
    return user

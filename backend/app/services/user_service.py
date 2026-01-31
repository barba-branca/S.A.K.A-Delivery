"""
Serviço para gerenciamento de usuários.
Contém a lógica de negócio para autenticação e registro.
"""
import logging
import hashlib
from datetime import datetime
from typing import Optional, List
from sqlalchemy.orm import Session

from ..models import User, UserRole as DBUserRole

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """
    Cria um hash simples da senha.
    
    NOTA: Em produção, use bcrypt ou argon2.
    """
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verifica se a senha corresponde ao hash."""
    return hash_password(password) == password_hash


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Busca usuário pelo username."""
    return db.query(User).filter(User.username == username).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Busca usuário pelo ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_all_users(db: Session) -> List[User]:
    """Retorna todos os usuários."""
    return db.query(User).order_by(User.created_at.desc()).all()


def create_user(
    db: Session,
    username: str,
    full_name: str,
    password: str,
    role: str = DBUserRole.KITCHEN.value
) -> Optional[User]:
    """
    Cria um novo usuário.
    
    Args:
        db: Sessão do banco de dados
        username: Nome de usuário único
        full_name: Nome completo
        password: Senha (será hasheada)
        role: Papel do usuário (ADMIN ou KITCHEN)
    
    Returns:
        Usuário criado ou None se username já existe
    """
    # Verifica se username já existe
    existing = get_user_by_username(db, username)
    if existing:
        return None
    
    user = User(
        username=username,
        full_name=full_name,
        password_hash=hash_password(password),
        role=role,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    logger.info(f"Usuário criado: {username} ({role})")
    return user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    """
    Autentica um usuário.
    
    Args:
        db: Sessão do banco de dados
        username: Nome de usuário
        password: Senha
    
    Returns:
        Usuário se autenticado, None caso contrário
    """
    # Credenciais padrão do sistema
    if username == "admin" and password == "admin123":
        # Retorna ou cria usuário admin padrão
        admin = get_user_by_username(db, "admin")
        if not admin:
            admin = create_user(db, "admin", "Admin User", "admin123", DBUserRole.ADMIN.value)
        else:
            admin.last_login = datetime.utcnow()
            db.commit()
        return admin
    
    if username == "cozinha" and password == "123":
        # Retorna ou cria usuário cozinha padrão
        kitchen = get_user_by_username(db, "cozinha")
        if not kitchen:
            kitchen = create_user(db, "cozinha", "Equipe Cozinha", "123", DBUserRole.KITCHEN.value)
        else:
            kitchen.last_login = datetime.utcnow()
            db.commit()
        return kitchen
    
    # Busca usuário no banco
    user = get_user_by_username(db, username)
    if not user:
        return None
    
    if not user.is_active:
        return None
    
    if not verify_password(password, user.password_hash):
        return None
    
    # Atualiza último login
    user.last_login = datetime.utcnow()
    db.commit()
    
    logger.info(f"Login bem-sucedido: {username}")
    return user


def delete_user(db: Session, user_id: int) -> bool:
    """
    Exclui um usuário.
    
    Args:
        db: Sessão do banco de dados
        user_id: ID do usuário
    
    Returns:
        True se excluído, False se não encontrado
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    db.delete(user)
    db.commit()
    
    logger.info(f"Usuário excluído: {user.username}")
    return True

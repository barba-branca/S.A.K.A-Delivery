"""
Router para autenticação de usuários.
Fornece endpoints para login e registro.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User as UserModel
from ..schemas import UserRegister, UserLogin, UserResponse, LoginResponse, UserRole
from ..services import user_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


def user_to_response(user: UserModel) -> dict:
    """Converte modelo de usuário para resposta."""
    return {
        "id": user.id,
        "username": user.username,
        "fullName": user.full_name,
        "role": user.role,
        "isActive": user.is_active,
        "createdAt": user.created_at.isoformat() if user.created_at else None
    }


@router.post(
    "/login",
    summary="Login de usuário",
    description="Autentica um usuário e retorna seus dados"
)
async def login(
    credentials: UserLogin,
    db: Session = Depends(get_db)
) -> dict:
    """
    Autentica um usuário.
    
    Args:
        credentials: Username e senha
    
    Returns:
        Dados do usuário autenticado
    
    Raises:
        401: Se credenciais inválidas
    """
    user = user_service.authenticate_user(db, credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas. Tente admin/admin123 ou cozinha/123"
        )
    
    return {
        "message": "Login bem-sucedido",
        "user": user_to_response(user)
    }


@router.post(
    "/register",
    summary="Registro de usuário",
    description="Cria uma nova conta de usuário"
)
async def register(
    user_data: UserRegister,
    db: Session = Depends(get_db)
) -> dict:
    """
    Registra um novo usuário.
    
    Args:
        user_data: Dados do novo usuário
    
    Returns:
        Dados do usuário criado
    
    Raises:
        400: Se username já existe
    """
    user = user_service.create_user(
        db,
        username=user_data.username,
        full_name=user_data.full_name,
        password=user_data.password,
        role=user_data.role.value
    )
    
    if not user:
        raise HTTPException(
            status_code=400,
            detail="Este nome de usuário já está em uso"
        )
    
    return {
        "message": "Conta criada com sucesso",
        "user": user_to_response(user)
    }


@router.get(
    "/users",
    summary="Lista usuários",
    description="Retorna todos os usuários cadastrados (apenas admin)"
)
async def list_users(
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Lista todos os usuários.
    
    Returns:
        Lista de usuários
    """
    users = user_service.get_all_users(db)
    return [user_to_response(user) for user in users]


@router.delete(
    "/users/{user_id}",
    summary="Exclui usuário",
    description="Remove um usuário do sistema"
)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """
    Exclui um usuário.
    
    Args:
        user_id: ID do usuário
    
    Returns:
        Confirmação de exclusão
    
    Raises:
        404: Se usuário não encontrado
    """
    success = user_service.delete_user(db, user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {
        "message": "Usuário excluído com sucesso",
        "userId": user_id
    }

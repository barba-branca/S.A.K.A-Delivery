"""
Router para autenticação de usuários com JWT.
"""
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User as UserModel
from ..schemas import UserRegister, UserLogin, UserResponse, LoginResponse, UserRole
from ..services import user_service
from ..security import create_access_token, get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Authentication"])


def user_to_response(user: UserModel) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "fullName": user.full_name,
        "full_name": user.full_name,
        "role": user.role,
        "saldoCredito": float(user.saldo_credito or 0),
        "saldo_credito": float(user.saldo_credito or 0),
        "isActive": user.is_active,
        "is_active": user.is_active,
        "createdAt": user.created_at.isoformat() if user.created_at else None,
        "created_at": user.created_at if user.created_at else None,
    }


@router.post("/login", summary="Login de usuário", response_model=LoginResponse)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    """Autentica usuário e retorna JWT token."""
    user = await user_service.authenticate_user(db, credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Credenciais inválidas. Tente admin/admin123 ou cozinha/123",
        )
    
    token = create_access_token(data={"sub": user.username, "role": user.role})
    
    return {
        "message": "Login bem-sucedido",
        "user": user_to_response(user),
        "access_token": token,
        "token_type": "bearer",
    }


@router.post("/register", summary="Registro de usuário")
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Registra um novo usuário e retorna JWT token."""
    user = await user_service.create_user(
        db,
        username=user_data.username,
        full_name=user_data.full_name,
        password=user_data.password,
        role=user_data.role.value,
        email=user_data.email,
    )
    
    if not user:
        raise HTTPException(status_code=400, detail="Este nome de usuário ou email já está em uso")
    
    token = create_access_token(data={"sub": user.username, "role": user.role})
    
    return {
        "message": "Conta criada com sucesso",
        "user": user_to_response(user),
        "access_token": token,
        "token_type": "bearer",
    }


@router.get("/me", summary="Dados do usuário logado")
async def get_me(current_user: UserModel = Depends(get_current_user)):
    """Retorna dados do usuário autenticado."""
    return user_to_response(current_user)


@router.get("/users", summary="Lista usuários")
async def list_users(db: AsyncSession = Depends(get_db)):
    users = await user_service.get_all_users(db)
    return [user_to_response(user) for user in users]


@router.delete("/users/{user_id}", summary="Exclui usuário")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    success = await user_service.delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return {"message": "Usuário excluído com sucesso", "userId": user_id}


@router.patch("/users/{user_id}/creditos", summary="Atualiza créditos do usuário (Admin)")
async def update_user_credits(
    user_id: int,
    body: dict,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza o saldo de créditos de um usuário. Requer ADMIN ou SUPER_ADMIN."""
    if current_user.role not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    
    novo_saldo = body.get("saldo_credito")
    if novo_saldo is None or not isinstance(novo_saldo, (int, float)):
        raise HTTPException(status_code=400, detail="Campo 'saldo_credito' (número) é obrigatório")
    
    if novo_saldo < 0:
        raise HTTPException(status_code=400, detail="Saldo não pode ser negativo")
    
    user = await user_service.update_user_credits(db, user_id, float(novo_saldo))
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {
        "message": f"Créditos atualizados para R${novo_saldo:.2f}",
        "user": user_to_response(user),
    }


@router.patch("/users/{user_id}/role", summary="Atualiza role do usuário (Admin)")
async def update_user_role(
    user_id: int,
    body: dict,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Atualiza o role de um usuário. Requer ADMIN ou SUPER_ADMIN."""
    if current_user.role not in ("ADMIN", "SUPER_ADMIN"):
        raise HTTPException(status_code=403, detail="Acesso negado. Apenas administradores.")
    
    new_role = body.get("role")
    valid_roles = ["SUPER_ADMIN", "ADMIN", "CLIENTE", "KITCHEN"]
    if not new_role or new_role not in valid_roles:
        raise HTTPException(status_code=400, detail=f"Role inválido. Opções: {valid_roles}")
    
    user = await user_service.update_user_role(db, user_id, new_role)
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return {
        "message": f"Role atualizado para {new_role}",
        "user": user_to_response(user),
    }

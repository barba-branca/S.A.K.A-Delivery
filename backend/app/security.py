"""
Módulo de segurança: JWT, hashing de senhas e validação iFood.
"""
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import get_settings
from .database import get_db

logger = logging.getLogger(__name__)
settings = get_settings()

# Password hashing with bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token scheme
bearer_scheme = HTTPBearer(auto_error=False)


# ============== Password Hashing ==============

def hash_password(password: str) -> str:
    """Cria hash bcrypt da senha."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha contra hash bcrypt."""
    return pwd_context.verify(plain_password, hashed_password)


# ============== JWT Tokens ==============

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Cria um JWT access token.
    
    Args:
        data: Dados a codificar no token (ex: {"sub": "username"})
        expires_delta: Tempo de expiração customizado
    
    Returns:
        Token JWT codificado
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.jwt_expire_minutes))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> Optional[dict]:
    """
    Decodifica um JWT access token.
    
    Returns:
        Payload decodificado ou None se inválido
    """
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        return payload
    except JWTError:
        return None


# ============== FastAPI Dependencies ==============

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
):
    """
    Dependency que extrai e valida o usuário do token JWT.
    
    Raises:
        401: Se token ausente ou inválido
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de autenticação não fornecido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    username: str = payload.get("sub")
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido: campo 'sub' ausente",
        )
    
    # Import here to avoid circular imports
    from .models import User
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta desativada",
        )
    
    return user


# ============== iFood Webhook Security ==============

def validate_ifood_signature(
    payload: bytes,
    signature: Optional[str],
    client_secret: Optional[str] = None
) -> bool:
    """
    Valida a assinatura X-iFood-Signature do webhook.
    """
    if not signature:
        logger.warning("Webhook recebido sem assinatura X-iFood-Signature")
        return False
    
    secret = client_secret or settings.ifood_client_secret
    
    if not secret:
        logger.error("IFOOD_CLIENT_SECRET não configurado!")
        return False
    
    try:
        expected_signature = hmac.new(
            key=secret.encode('utf-8'),
            msg=payload,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(signature.lower(), expected_signature.lower())
        
        if not is_valid:
            logger.warning(
                f"Assinatura inválida. Recebida: {signature[:20]}..., "
                f"Esperada: {expected_signature[:20]}..."
            )
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Erro ao validar assinatura: {e}")
        return False


def generate_signature(payload: bytes, client_secret: str) -> str:
    """Gera uma assinatura HMAC SHA256 para um payload."""
    return hmac.new(
        key=client_secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

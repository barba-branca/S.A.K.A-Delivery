"""
Módulo de segurança para validação de assinatura do webhook iFood.
Implementa validação HMAC SHA256 conforme documentação iFood.
"""
import hmac
import hashlib
import logging
from typing import Optional

from .config import get_settings

logger = logging.getLogger(__name__)


def validate_ifood_signature(
    payload: bytes,
    signature: Optional[str],
    client_secret: Optional[str] = None
) -> bool:
    """
    Valida a assinatura X-iFood-Signature do webhook.
    
    O iFood envia um header X-iFood-Signature que é um HMAC SHA256
    do body da requisição usando o client_secret como chave.
    
    Args:
        payload: Corpo da requisição em bytes
        signature: Valor do header X-iFood-Signature
        client_secret: Client secret do iFood (opcional, usa config se não fornecido)
    
    Returns:
        True se a assinatura for válida, False caso contrário
    """
    if not signature:
        logger.warning("Webhook recebido sem assinatura X-iFood-Signature")
        return False
    
    settings = get_settings()
    secret = client_secret or settings.ifood_client_secret
    
    if not secret:
        logger.error("IFOOD_CLIENT_SECRET não configurado!")
        return False
    
    try:
        # Calcula o HMAC SHA256 do payload usando o client_secret
        expected_signature = hmac.new(
            key=secret.encode('utf-8'),
            msg=payload,
            digestmod=hashlib.sha256
        ).hexdigest()
        
        # Compara as assinaturas de forma segura (timing-safe)
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
    """
    Gera uma assinatura HMAC SHA256 para um payload.
    Útil para testes e simulação de webhooks.
    
    Args:
        payload: Corpo da requisição em bytes
        client_secret: Client secret do iFood
    
    Returns:
        Assinatura HMAC SHA256 em hexadecimal
    """
    return hmac.new(
        key=client_secret.encode('utf-8'),
        msg=payload,
        digestmod=hashlib.sha256
    ).hexdigest()

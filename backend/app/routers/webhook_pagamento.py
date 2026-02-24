"""
Router para webhook de pagamento (futuro OpenPix).
"""
import logging
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas import WebhookPagamentoPayload

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["Webhook Pagamento"])


@router.post("/pagamento", summary="Webhook de pagamento (futuro OpenPix)")
async def webhook_pagamento(
    payload: WebhookPagamentoPayload,
    db: AsyncSession = Depends(get_db),
):
    """
    Recebe notificação de pagamento e adiciona crédito ao usuário.
    STUB: Preparado para integração futura com OpenPix.
    
    Payload esperado:
    - txid: ID da transação
    - valor: Valor pago
    - user_id: ID do usuário
    """
    logger.info(f"Webhook pagamento recebido: txid={payload.txid}, valor={payload.valor}")
    
    result = await db.execute(select(User).where(User.id == payload.user_id))
    user = result.scalar_one_or_none()
    
    if not user:
        return {"status": "error", "message": "Usuário não encontrado"}
    
    # Adiciona crédito ao saldo
    user.saldo_credito = Decimal(str(user.saldo_credito or 0)) + Decimal(str(payload.valor))
    await db.commit()
    
    logger.info(f"Crédito adicionado via webhook: user={user.id}, valor={payload.valor}")
    
    return {
        "status": "success",
        "message": "Crédito adicionado com sucesso",
        "txid": payload.txid,
        "novo_saldo": float(user.saldo_credito),
    }

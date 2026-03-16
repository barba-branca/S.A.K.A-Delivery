"""
Router para pagamentos PIX via Mercado Pago.

Endpoints:
- POST /api/v1/payments/create  — Gera pagamento PIX e retorna QR Code
- GET  /api/v1/payments/{id}/status — Polling de status da transação
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas import (
    PaymentCreateRequest,
    PaymentCreateResponse,
    TransactionStatusResponse,
)
from ..security import get_current_user
from ..services.payment_service import PaymentService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@router.post(
    "/create",
    response_model=PaymentCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar pagamento PIX",
)
async def create_payment(
    request: PaymentCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Gera um pagamento PIX no Mercado Pago, registra a transação como 'pending'
    no banco e retorna os dados do QR Code para o frontend.
    """
    logger.info(
        f"Criando pagamento PIX: user_id={current_user.id}, valor={request.valor}"
    )

    try:
        result = await PaymentService.create_pix_payment(
            db=db,
            user=current_user,
            valor=request.valor,
        )
        return result

    except ValueError as e:
        logger.error(f"Erro ao criar pagamento: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Erro na API do Mercado Pago: {str(e)}",
        )
    except ImportError:
        logger.error("SDK mercadopago não instalado")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Serviço de pagamento não disponível (SDK não instalado)",
        )
    except Exception as e:
        logger.error(f"Erro inesperado ao criar pagamento: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro interno ao processar pagamento",
        )


@router.get(
    "/{transaction_id}/status",
    response_model=TransactionStatusResponse,
    summary="Consultar status do pagamento",
)
async def get_payment_status(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retorna o status atual de uma transação.
    Usado pelo frontend para polling enquanto aguarda a confirmação do webhook.
    """
    transaction = await PaymentService.get_transaction_status(
        db=db,
        transaction_id=transaction_id,
    )

    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transação não encontrada",
        )

    # Verifica se a transação pertence ao usuário autenticado
    if transaction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso negado",
        )

    return transaction

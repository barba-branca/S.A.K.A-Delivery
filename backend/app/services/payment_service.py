"""
PaymentService — Serviço assíncrono para integração com Mercado Pago PIX.

Utiliza asyncio.to_thread() para executar chamadas síncronas do SDK
do Mercado Pago sem bloquear o event loop do FastAPI.
"""
import asyncio
import logging
from decimal import Decimal
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..models import Transaction, TransactionStatus, User

logger = logging.getLogger(__name__)
settings = get_settings()


class PaymentService:
    """Serviço de pagamentos PIX via Mercado Pago."""

    @staticmethod
    def _create_mp_payment(valor: float, email: str, nome: str, user_id: int) -> dict:
        """
        Cria pagamento PIX no Mercado Pago (chamada síncrona do SDK).
        Deve ser executada via asyncio.to_thread().
        """
        import mercadopago

        sdk = mercadopago.SDK(settings.mercadopago_access_token)

        payment_data = {
            "transaction_amount": float(valor),
            "description": "Recarga de Créditos SAKA Delivery",
            "payment_method_id": "pix",
            "external_reference": str(user_id),
            "payer": {
                "email": email or "cliente@sakdelivery.com",
                "first_name": nome or "Cliente",
                "last_name": "SAKA",
                "identification": {
                    "type": "CPF",
                    "number": "19119119100",
                },
            },
        }

        response = sdk.payment().create(payment_data)
        logger.info(
            f"Mercado Pago response: status={response['status']}, "
            f"payment_id={response['response'].get('id')}"
        )

        if response["status"] != 201:
            raise ValueError(
                f"Mercado Pago retornou status {response['status']}: "
                f"{response['response']}"
            )

        return response["response"]

    @staticmethod
    async def create_pix_payment(
        db: AsyncSession,
        user: User,
        valor: float,
    ) -> dict:
        """
        Cria um pagamento PIX e registra a Transaction no banco.

        Returns:
            dict com transaction_id, external_id, qr_code, qr_code_base64, copia_cola
        """
        email = getattr(user, "email", None)
        nome = getattr(user, "full_name", None)

        # Executa a chamada síncrona do SDK em thread separada
        payment = await asyncio.to_thread(
            PaymentService._create_mp_payment,
            valor,
            email,
            nome,
            user.id,
        )

        external_id = str(payment["id"])
        poi = payment["point_of_interaction"]["transaction_data"]
        qr_code = poi["qr_code"]
        qr_code_base64 = poi["qr_code_base64"]

        # Registra a transação como pending
        transaction = Transaction(
            external_id=external_id,
            user_id=user.id,
            amount=Decimal(str(valor)),
            status=TransactionStatus.PENDING.value,
        )
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)

        logger.info(
            f"Transaction criada: id={transaction.id}, external_id={external_id}, "
            f"user_id={user.id}, valor={valor}"
        )

        return {
            "transaction_id": transaction.id,
            "external_id": external_id,
            "qr_code": qr_code,
            "qr_code_base64": qr_code_base64,
            "copia_cola": qr_code,
        }

    @staticmethod
    async def get_transaction_status(
        db: AsyncSession,
        transaction_id: int,
    ) -> Optional[Transaction]:
        """Busca o status de uma transação pelo ID."""
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def update_transaction_status(
        db: AsyncSession,
        external_id: str,
        new_status: str,
    ) -> Optional[Transaction]:
        """
        Atualiza o status de uma transação pelo external_id (payment_id do MP).

        Returns:
            Transaction atualizada ou None se não encontrada.
        """
        result = await db.execute(
            select(Transaction).where(Transaction.external_id == external_id)
        )
        transaction = result.scalar_one_or_none()

        if not transaction:
            logger.warning(f"Transaction não encontrada para external_id={external_id}")
            return None

        old_status = transaction.status
        transaction.status = new_status
        await db.commit()
        await db.refresh(transaction)

        logger.info(
            f"Transaction atualizada: id={transaction.id}, "
            f"external_id={external_id}, {old_status} -> {new_status}"
        )

        return transaction

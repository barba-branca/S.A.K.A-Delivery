"""
Serviço para pedidos SaaS (consumo de crédito).
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import PedidoSaas, Repasse, User, PedidoStatus, RepasseStatus

logger = logging.getLogger(__name__)

VALOR_POR_PEDIDO = Decimal("5.00")
PERCENTUAL_ARNALDO = Decimal("0.30")  # 30%


async def criar_pedido(db: AsyncSession, user_id: int, via_arnaldo: bool = False) -> PedidoSaas:
    """
    Cria um pedido SaaS, deduzindo crédito do saldo do usuário.
    
    Regras:
    - Verifica saldo_credito >= 5.00
    - Deduz R$5.00 do saldo
    - Se via_arnaldo=True: cria Repasse com valor_para_arnaldo = 1.50 (30%)
    
    Raises:
        ValueError: Se saldo insuficiente ou usuário não encontrado
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise ValueError("Usuário não encontrado")
    
    saldo_atual = Decimal(str(user.saldo_credito or 0))
    if saldo_atual < VALOR_POR_PEDIDO:
        raise ValueError(
            f"Saldo insuficiente. Saldo atual: R${saldo_atual:.2f}, necessário: R${VALOR_POR_PEDIDO:.2f}"
        )
    
    # Deduz crédito
    user.saldo_credito = saldo_atual - VALOR_POR_PEDIDO
    
    # Cria pedido
    pedido = PedidoSaas(
        user_id=user_id,
        valor_consumido=VALOR_POR_PEDIDO,
        via_arnaldo=via_arnaldo,
        data=datetime.utcnow(),
        status=PedidoStatus.ATIVO.value,
    )
    db.add(pedido)
    await db.flush()  # Para obter o ID do pedido antes do commit
    
    # Se via_arnaldo, cria repasse
    if via_arnaldo:
        valor_repasse = VALOR_POR_PEDIDO * PERCENTUAL_ARNALDO  # R$1.50
        repasse = Repasse(
            pedido_id=pedido.id,
            valor_para_arnaldo=valor_repasse,
            status=RepasseStatus.PENDENTE.value,
            created_at=datetime.utcnow(),
        )
        db.add(repasse)
    
    await db.commit()
    await db.refresh(pedido)
    await db.refresh(user)
    
    logger.info(
        f"Pedido SaaS criado: pedido_id={pedido.id}, user={user_id}, "
        f"via_arnaldo={via_arnaldo}, novo_saldo={user.saldo_credito}"
    )
    return pedido


async def listar_pedidos(
    db: AsyncSession, user_id: int, limit: int = 50
) -> List[PedidoSaas]:
    """Lista pedidos SaaS do usuário."""
    result = await db.execute(
        select(PedidoSaas)
        .where(PedidoSaas.user_id == user_id)
        .order_by(PedidoSaas.data.desc())
        .limit(limit)
    )
    return list(result.scalars().all())


async def get_pedido_by_id(db: AsyncSession, pedido_id: int) -> Optional[PedidoSaas]:
    result = await db.execute(select(PedidoSaas).where(PedidoSaas.id == pedido_id))
    return result.scalar_one_or_none()

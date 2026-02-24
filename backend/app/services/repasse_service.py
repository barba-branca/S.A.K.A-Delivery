"""
Serviço para repasses financeiros.
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import List
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Repasse, RepasseStatus

logger = logging.getLogger(__name__)


async def get_repasse_mensal(db: AsyncSession, ano: int = None, mes: int = None) -> dict:
    """
    Calcula resumo mensal de repasses.
    Se ano/mes não fornecidos, usa mês atual.
    """
    now = datetime.utcnow()
    ano = ano or now.year
    mes = mes or now.month
    
    # Repasses pendentes do mês
    pendente_query = select(
        func.coalesce(func.sum(Repasse.valor_para_arnaldo), 0),
        func.count(Repasse.id),
    ).where(
        and_(
            Repasse.status == RepasseStatus.PENDENTE.value,
            func.extract("year", Repasse.created_at) == ano,
            func.extract("month", Repasse.created_at) == mes,
        )
    )
    
    pago_query = select(
        func.coalesce(func.sum(Repasse.valor_para_arnaldo), 0),
        func.count(Repasse.id),
    ).where(
        and_(
            Repasse.status == RepasseStatus.PAGO.value,
            func.extract("year", Repasse.created_at) == ano,
            func.extract("month", Repasse.created_at) == mes,
        )
    )
    
    pendente_result = await db.execute(pendente_query)
    pago_result = await db.execute(pago_query)
    
    total_pendente, qtd_pendente = pendente_result.one()
    total_pago, qtd_pago = pago_result.one()
    
    # Lista repasses do mês
    repasses_query = (
        select(Repasse)
        .where(
            func.extract("year", Repasse.created_at) == ano,
            func.extract("month", Repasse.created_at) == mes,
        )
        .order_by(Repasse.created_at.desc())
    )
    repasses_result = await db.execute(repasses_query)
    repasses = list(repasses_result.scalars().all())
    
    return {
        "total_pendente": float(total_pendente),
        "total_pago": float(total_pago),
        "quantidade_pendente": qtd_pendente,
        "quantidade_pago": qtd_pago,
        "repasses": repasses,
    }


async def marcar_como_pago(db: AsyncSession, ano: int = None, mes: int = None) -> int:
    """Marca todos os repasses pendentes do mês como pagos."""
    now = datetime.utcnow()
    ano = ano or now.year
    mes = mes or now.month
    
    query = select(Repasse).where(
        and_(
            Repasse.status == RepasseStatus.PENDENTE.value,
            func.extract("year", Repasse.created_at) == ano,
            func.extract("month", Repasse.created_at) == mes,
        )
    )
    result = await db.execute(query)
    repasses = list(result.scalars().all())
    
    for repasse in repasses:
        repasse.status = RepasseStatus.PAGO.value
        repasse.data_repasse = datetime.utcnow()
    
    await db.commit()
    
    logger.info(f"Marcados {len(repasses)} repasses como pagos ({ano}-{mes:02d})")
    return len(repasses)

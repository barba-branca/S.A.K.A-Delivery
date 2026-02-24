"""
Router para relatórios de repasse financeiro.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..services import repasse_service
from ..security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/repasse", tags=["Repasse Financeiro"])


@router.get("/mensal", summary="Relatório mensal de repasses")
async def get_repasse_mensal(
    ano: int = None,
    mes: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Calcula SUM(valor_para_arnaldo) pendente do mês.
    Retorna total pendente, total pago, e lista de repasses.
    """
    result = await repasse_service.get_repasse_mensal(db, ano, mes)
    
    return {
        "total_pendente": result["total_pendente"],
        "total_pago": result["total_pago"],
        "quantidade_pendente": result["quantidade_pendente"],
        "quantidade_pago": result["quantidade_pago"],
        "repasses": [
            {
                "id": r.id,
                "pedido_id": r.pedido_id,
                "valor_para_arnaldo": float(r.valor_para_arnaldo),
                "status": r.status,
                "data_repasse": r.data_repasse.isoformat() if r.data_repasse else None,
                "created_at": r.created_at.isoformat(),
            }
            for r in result["repasses"]
        ],
    }


@router.post("/pagar", summary="Marcar repasses como pagos")
async def pagar_repasses(
    ano: int = None,
    mes: int = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Marca todos os repasses pendentes do mês como pagos."""
    count = await repasse_service.marcar_como_pago(db, ano, mes)
    return {"message": f"{count} repasses marcados como pagos", "quantidade": count}

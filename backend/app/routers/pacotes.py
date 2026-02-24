"""
Router para pacotes pré-pagos.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User
from ..schemas import PacoteComprar, PacoteResponse
from ..services import pacote_service
from ..security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pacotes", tags=["Pacotes (SaaS)"])


@router.post("/comprar", summary="Comprar pacote pré-pago")
async def comprar_pacote(
    dados: PacoteComprar,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Simula compra de pacote e adiciona crédito ao saldo.
    Pacote padrão: R$5.000 / 1.000 pedidos.
    """
    try:
        pacote = await pacote_service.comprar_pacote(db, current_user.id, dados.tipo)
        return {
            "message": "Pacote comprado com sucesso!",
            "pacote": {
                "id": pacote.id,
                "valor_pago": float(pacote.valor_pago),
                "qtd_pedidos": pacote.qtd_pedidos,
                "data_compra": pacote.data_compra.isoformat(),
            },
            "novo_saldo": float(current_user.saldo_credito),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", summary="Lista pacotes do usuário")
async def listar_pacotes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pacotes = await pacote_service.listar_pacotes(db, current_user.id)
    return [
        {
            "id": p.id,
            "valor_pago": float(p.valor_pago),
            "qtd_pedidos": p.qtd_pedidos,
            "data_compra": p.data_compra.isoformat(),
        }
        for p in pacotes
    ]

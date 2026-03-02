"""
Router para pedidos SaaS (consumo de crédito).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import User, UserRole
from ..schemas import PedidoSaasCreate, PedidoSaasResponse
from ..services import pedido_saas_service
from ..security import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pedidos", tags=["Pedidos (SaaS)"])


@router.post("", summary="Criar pedido SaaS")
async def criar_pedido(
    dados: PedidoSaasCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Cria um pedido SaaS. Deduz R$5.00 do saldo_credito.
    Se via_arnaldo=True, acumula R$1.50 (30%) em repasse pendente.
    """
    try:
        pedido = await pedido_saas_service.criar_pedido(
            db, current_user.id, dados.via_arnaldo
        )
        response_pedido = {
            "id": pedido.id,
            "valor_consumido": float(pedido.valor_consumido),
            "data": pedido.data.isoformat(),
            "status": pedido.status,
        }
        
        if current_user.role in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
            response_pedido["via_arnaldo"] = pedido.via_arnaldo

        return {
            "message": "Pedido criado com sucesso!",
            "pedido": response_pedido,
            "novo_saldo": float(current_user.saldo_credito),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", summary="Lista pedidos SaaS do usuário")
async def listar_pedidos(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    pedidos = await pedido_saas_service.listar_pedidos(db, current_user.id, limit)
    results = []
    for p in pedidos:
        p_dict = {
            "id": p.id,
            "user_id": p.user_id,
            "valor_consumido": float(p.valor_consumido),
            "data": p.data.isoformat(),
            "status": p.status,
        }
        if current_user.role in [UserRole.SUPER_ADMIN.value, UserRole.ADMIN.value]:
            p_dict["via_arnaldo"] = p.via_arnaldo
        results.append(p_dict)
    
    return results

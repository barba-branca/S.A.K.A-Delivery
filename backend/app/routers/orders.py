"""
Router para API de pedidos.
Fornece endpoints para o frontend KDS consumir os dados.
"""
import logging
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Order as OrderModel
from ..schemas import OrderResponse, OrderUpdate, OrderStatus, OrderItemResponse
from ..services import order_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["Orders"])


def order_to_response(order: OrderModel) -> dict:
    """
    Converte modelo do banco para formato de resposta do frontend.
    
    O frontend espera timestamps em milissegundos e campos em camelCase.
    """
    def to_timestamp_ms(dt: Optional[datetime]) -> Optional[int]:
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)
    
    items = []
    for item in order.items:
        items.append({
            "name": item.name,
            "quantity": item.quantity,
            "notes": item.notes
        })
    
    return {
        "id": order.id,
        "displayId": order.display_id,
        "customerName": order.customer_name,
        "source": order.source,
        "status": order.status,
        "items": items,
        "createdAt": to_timestamp_ms(order.created_at),
        "preparingAt": to_timestamp_ms(order.preparing_at),
        "readyAt": to_timestamp_ms(order.ready_at),
        "deliveryAt": to_timestamp_ms(order.delivery_at),
        "deliveryFee": order.delivery_fee,
        "driverName": order.driver_name,
        "isDriverPaid": order.is_driver_paid
    }


@router.get(
    "",
    summary="Lista todos os pedidos",
    description="Retorna lista de pedidos com filtros opcionais"
)
async def list_orders(
    status: Optional[str] = Query(None, description="Filtrar por status"),
    source: Optional[str] = Query(None, description="Filtrar por origem"),
    active_only: bool = Query(False, description="Apenas pedidos ativos"),
    limit: int = Query(100, description="Limite de resultados"),
    db: Session = Depends(get_db)
) -> List[dict]:
    """
    Lista pedidos com filtros opcionais.
    
    Returns:
        Lista de pedidos no formato esperado pelo frontend
    """
    if active_only:
        orders = order_service.get_active_orders(db)
    else:
        orders = order_service.get_all_orders(db, status=status, source=source, limit=limit)
    
    return [order_to_response(order) for order in orders]


@router.get(
    "/{order_id}",
    summary="Busca pedido por ID",
    description="Retorna detalhes de um pedido específico"
)
async def get_order(
    order_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Busca um pedido específico pelo ID.
    
    Args:
        order_id: ID do pedido
    
    Returns:
        Pedido no formato esperado pelo frontend
    
    Raises:
        404: Se pedido não encontrado
    """
    order = order_service.get_order_by_id(db, order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    return order_to_response(order)


@router.patch(
    "/{order_id}/status",
    summary="Atualiza status do pedido",
    description="Atualiza o status de um pedido existente"
)
async def update_order_status(
    order_id: str,
    update_data: OrderUpdate,
    db: Session = Depends(get_db)
) -> dict:
    """
    Atualiza o status de um pedido.
    
    Args:
        order_id: ID do pedido
        update_data: Dados de atualização
    
    Returns:
        Pedido atualizado
    
    Raises:
        404: Se pedido não encontrado
    """
    if update_data.status:
        order = order_service.update_order_status(
            db, order_id, update_data.status, update_data.driver_name
        )
    else:
        order = order_service.get_order_by_id(db, order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    # Atualiza pagamento do motorista se necessário
    if update_data.is_driver_paid is not None and order.driver_name:
        order.is_driver_paid = update_data.is_driver_paid
        db.commit()
        db.refresh(order)
    
    return order_to_response(order)


@router.post(
    "/drivers/{driver_name}/pay",
    summary="Marca motorista como pago",
    description="Marca todos os pedidos de um motorista como pagos"
)
async def pay_driver(
    driver_name: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Marca todos os pedidos de um motorista como pagos.
    
    Args:
        driver_name: Nome do motorista
    
    Returns:
        Quantidade de pedidos atualizados
    """
    orders = order_service.mark_driver_as_paid(db, driver_name)
    
    return {
        "message": f"Motorista {driver_name} marcado como pago",
        "ordersUpdated": len(orders)
    }


@router.delete(
    "/{order_id}",
    summary="Exclui um pedido",
    description="Remove um pedido específico do sistema"
)
async def delete_order(
    order_id: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    Exclui um pedido pelo ID.
    
    Args:
        order_id: ID do pedido
    
    Returns:
        Confirmação de exclusão
    
    Raises:
        404: Se pedido não encontrado
    """
    success = order_service.delete_order(db, order_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    return {
        "message": "Pedido excluído com sucesso",
        "orderId": order_id
    }


@router.delete(
    "",
    summary="Limpa todos os pedidos",
    description="Remove todos os pedidos do sistema (reset diário)"
)
async def reset_orders(
    db: Session = Depends(get_db)
) -> dict:
    """
    Remove todos os pedidos (reset).
    
    Returns:
        Quantidade de pedidos removidos
    """
    count = order_service.reset_all_orders(db)
    
    return {
        "message": "Todos os pedidos foram removidos",
        "ordersRemoved": count
    }


@router.get(
    "/stats",
    summary="Estatísticas dos pedidos",
    description="Retorna contagem de pedidos por status"
)
async def get_stats(
    db: Session = Depends(get_db)
) -> dict:
    """
    Retorna estatísticas dos pedidos.
    
    Returns:
        Contagem total e por status
    """
    return order_service.get_orders_count(db)


@router.post(
    "/daily-reset",
    summary="Verificação de reset diário",
    description="Verifica e realiza reset diário se necessário"
)
async def check_daily_reset(
    last_reset_date: Optional[str] = None,
    db: Session = Depends(get_db)
) -> dict:
    """
    Verifica se deve realizar o reset diário.
    
    Args:
        last_reset_date: Data do último reset (formato YYYY-MM-DD)
    
    Returns:
        Se o reset foi realizado e a data atual
    """
    reset_performed, current_date = order_service.check_and_perform_daily_reset(db, last_reset_date)
    
    return {
        "resetPerformed": reset_performed,
        "currentDate": current_date
    }

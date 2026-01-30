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

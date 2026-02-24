"""
Router para API de pedidos KDS (async).
"""
import logging
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ..database import get_db
from ..models import Order as OrderModel
from ..schemas import OrderCreate, OrderUpdate, OrderStatus
from ..services import order_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/orders", tags=["Orders (KDS)"])


def order_to_response(order: OrderModel) -> dict:
    def to_timestamp_ms(dt: Optional[datetime]) -> Optional[int]:
        if dt is None:
            return None
        return int(dt.timestamp() * 1000)
    
    items = [{"name": item.name, "quantity": item.quantity, "notes": item.notes} for item in order.items]
    
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
        "isDriverPaid": order.is_driver_paid,
    }


@router.get("", summary="Lista todos os pedidos KDS")
async def list_orders(
    status: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    active_only: bool = Query(False),
    limit: int = Query(100),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    if active_only:
        orders = await order_service.get_active_orders(db)
    else:
        orders = await order_service.get_all_orders(db, status=status, source=source, limit=limit)
    return [order_to_response(order) for order in orders]


@router.post("/create", summary="Cria novo pedido KDS")
async def create_order(order_data: OrderCreate, db: AsyncSession = Depends(get_db)) -> dict:
    """Cria um pedido KDS diretamente (para testes e uso manual)."""
    order_id = str(uuid.uuid4())
    order = await order_service.create_order(db, order_data, order_id)
    return order_to_response(order)


@router.get("/stats", summary="Estatísticas dos pedidos")
async def get_stats(db: AsyncSession = Depends(get_db)) -> dict:
    return await order_service.get_orders_count(db)


@router.get("/{order_id}", summary="Busca pedido por ID")
async def get_order(order_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    order = await order_service.get_order_by_id(db, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return order_to_response(order)


@router.patch("/{order_id}/status", summary="Atualiza status do pedido")
async def update_order_status(
    order_id: str, update_data: OrderUpdate, db: AsyncSession = Depends(get_db)
) -> dict:
    if update_data.status:
        order = await order_service.update_order_status(
            db, order_id, update_data.status, update_data.driver_name
        )
    else:
        order = await order_service.get_order_by_id(db, order_id)
    
    if not order:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    
    if update_data.is_driver_paid is not None and order.driver_name:
        order.is_driver_paid = update_data.is_driver_paid
        await db.commit()
        await db.refresh(order)
    
    return order_to_response(order)


@router.post("/drivers/{driver_name}/pay", summary="Marca motorista como pago")
async def pay_driver(driver_name: str, db: AsyncSession = Depends(get_db)) -> dict:
    orders = await order_service.mark_driver_as_paid(db, driver_name)
    return {"message": f"Motorista {driver_name} marcado como pago", "ordersUpdated": len(orders)}


@router.delete("/{order_id}", summary="Exclui um pedido")
async def delete_order(order_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    success = await order_service.delete_order(db, order_id)
    if not success:
        raise HTTPException(status_code=404, detail="Pedido não encontrado")
    return {"message": "Pedido excluído com sucesso", "orderId": order_id}


@router.delete("", summary="Limpa todos os pedidos")
async def reset_orders(db: AsyncSession = Depends(get_db)) -> dict:
    count = await order_service.reset_all_orders(db)
    return {"message": "Todos os pedidos foram removidos", "ordersRemoved": count}


@router.post("/daily-reset", summary="Reset diário")
async def check_daily_reset(
    last_reset_date: Optional[str] = None, db: AsyncSession = Depends(get_db)
) -> dict:
    reset_performed, current_date = await order_service.check_and_perform_daily_reset(db, last_reset_date)
    return {"resetPerformed": reset_performed, "currentDate": current_date}

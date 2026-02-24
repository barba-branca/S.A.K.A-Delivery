"""
Serviço para processamento de webhooks do iFood (async).
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import WebhookEvent, Order, OrderStatus as DBOrderStatus
from .order_service import create_order_from_ifood, get_order_by_ifood_id
from ..schemas import OrderStatus

logger = logging.getLogger(__name__)


class IFoodEventCodes:
    ORDER_PLACED = "PLC"
    ORDER_CONFIRMED = "CFM"
    ORDER_READY_TO_PICKUP = "RTP"
    ORDER_DISPATCHED = "DSP"
    ORDER_CONCLUDED = "CON"
    ORDER_CANCELLED = "CAN"
    INTEGRATION_TEST = "TEST"


async def save_webhook_event(db: AsyncSession, event_data: Dict[str, Any]) -> WebhookEvent:
    event = WebhookEvent(
        event_id=event_data.get("id", ""),
        event_code=event_data.get("code", ""),
        order_id=event_data.get("orderId"),
        merchant_id=event_data.get("merchantId"),
        payload=json.dumps(event_data, ensure_ascii=False),
        created_at=datetime.utcnow(),
    )
    db.add(event)
    await db.commit()
    await db.refresh(event)
    logger.info(f"Evento webhook salvo: {event.event_id} (Código: {event.event_code})")
    return event


async def process_webhook_event(db: AsyncSession, event_data: Dict[str, Any]) -> bool:
    event_code = event_data.get("code", "")
    order_id = event_data.get("orderId")
    
    logger.info(f"Processando evento: {event_code} para pedido: {order_id}")
    
    try:
        if event_code == IFoodEventCodes.ORDER_PLACED:
            await _handle_order_placed(db, event_data)
        elif event_code == IFoodEventCodes.ORDER_CONFIRMED:
            await _handle_order_status_change(db, order_id, OrderStatus.PREPARING)
        elif event_code == IFoodEventCodes.ORDER_READY_TO_PICKUP:
            await _handle_order_status_change(db, order_id, OrderStatus.READY)
        elif event_code == IFoodEventCodes.ORDER_DISPATCHED:
            await _handle_order_status_change(db, order_id, OrderStatus.DELIVERY)
        elif event_code == IFoodEventCodes.ORDER_CANCELLED:
            await _handle_order_status_change(db, order_id, OrderStatus.CANCELLED)
        elif event_code == IFoodEventCodes.INTEGRATION_TEST:
            logger.info("Evento de teste recebido com sucesso!")
        else:
            logger.warning(f"Código de evento não tratado: {event_code}")
        return True
    except Exception as e:
        logger.error(f"Erro ao processar evento: {e}")
        return False


async def _handle_order_placed(db: AsyncSession, event_data: Dict[str, Any]) -> Optional[Order]:
    order_id = event_data.get("orderId")
    existing = await get_order_by_ifood_id(db, order_id)
    if existing:
        logger.info(f"Pedido {order_id} já existe, ignorando duplicado")
        return existing
    
    metadata = event_data.get("metadata", {})
    ifood_order = {
        "id": order_id,
        "displayId": metadata.get("displayId", ""),
        "shortReference": metadata.get("shortReference", order_id[:8] if order_id else ""),
        "customer": {"name": metadata.get("customerName", "Cliente iFood"), "phone": {"number": ""}},
        "total": {
            "subTotal": metadata.get("subTotal", 0),
            "deliveryFee": metadata.get("deliveryFee", 0),
            "orderAmount": metadata.get("orderAmount", 0),
        },
        "items": metadata.get("items", [{"name": "Pedido iFood", "quantity": 1, "unitPrice": 0, "totalPrice": 0}]),
        "delivery": {"deliveryAddress": metadata.get("deliveryAddress", {})},
    }
    return await create_order_from_ifood(db, ifood_order)


async def _handle_order_status_change(
    db: AsyncSession, ifood_order_id: str, new_status: OrderStatus
) -> Optional[Order]:
    order = await get_order_by_ifood_id(db, ifood_order_id)
    if not order:
        logger.warning(f"Pedido não encontrado: {ifood_order_id}")
        return None
    
    order.status = new_status.value
    now = datetime.utcnow()
    if new_status == OrderStatus.PREPARING:
        order.preparing_at = now
    elif new_status == OrderStatus.READY:
        order.ready_at = now
    elif new_status == OrderStatus.DELIVERY:
        order.delivery_at = now
    
    await db.commit()
    await db.refresh(order)
    logger.info(f"Pedido {order.id} atualizado para: {new_status.value}")
    return order


async def mark_event_as_processed(
    db: AsyncSession, event_id: str, success: bool, error_message: Optional[str] = None
) -> None:
    result = await db.execute(select(WebhookEvent).where(WebhookEvent.event_id == event_id))
    event = result.scalar_one_or_none()
    if event:
        event.processed = success
        event.processed_at = datetime.utcnow()
        if error_message:
            event.error_message = error_message
        await db.commit()

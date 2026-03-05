"""
Serviço para gerenciamento de pedidos KDS (async).
"""
import json
import logging
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..models import Order, OrderItem, OrderStatus as DBOrderStatus, OrderSource as DBOrderSource
from ..schemas import OrderCreate, OrderStatus

logger = logging.getLogger(__name__)


async def get_next_display_id(db: AsyncSession) -> int:
    result = await db.execute(select(func.max(Order.display_id)))
    max_id = result.scalar()
    return (max_id or 100) + 1


async def get_all_orders(
    db: AsyncSession,
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100,
) -> List[Order]:
    query = select(Order).options(selectinload(Order.items))
    if status:
        query = query.where(Order.status == status)
    if source:
        query = query.where(Order.source == source)
    query = query.order_by(Order.created_at.desc()).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_active_orders(db: AsyncSession) -> List[Order]:
    active_statuses = [s.value for s in DBOrderStatus if s != DBOrderStatus.CANCELLED]
    query = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.status.in_(active_statuses))
        .order_by(Order.created_at.desc())
    )
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_order_by_id(db: AsyncSession, order_id: str) -> Optional[Order]:
    query = select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_order_by_ifood_id(db: AsyncSession, ifood_id: str) -> Optional[Order]:
    query = select(Order).options(selectinload(Order.items)).where(Order.ifood_id == ifood_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def create_order(db: AsyncSession, order_data: OrderCreate, order_id: str) -> Order:
    display_id = await get_next_display_id(db)
    
    order = Order(
        id=order_id,
        display_id=display_id,
        customer_name=order_data.customer_name,
        customer_phone=order_data.customer_phone,
        source=order_data.source.value,
        status=DBOrderStatus.RECEIVED.value,
        subtotal=order_data.subtotal,
        delivery_fee=order_data.delivery_fee,
        total=order_data.total,
        delivery_address=order_data.delivery_address,
        created_at=datetime.utcnow(),
    )
    
    for item_data in order_data.items:
        item = OrderItem(
            name=item_data.name,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            total_price=item_data.total_price,
            notes=item_data.notes,
            options=item_data.options,
        )
        order.items.append(item)
    
    db.add(order)
    await db.commit()
    
    # Re-fetch with eagerly loaded items to avoid lazy-loading in async context
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one()
    
    logger.info(f"Pedido criado: {order.id} (Display: #{order.display_id})")
    return order


async def create_order_from_ifood(db: AsyncSession, ifood_order: dict) -> Order:
    display_id = await get_next_display_id(db)
    
    customer = ifood_order.get("customer", {})
    customer_name = customer.get("name", "Cliente iFood")
    customer_phone = customer.get("phone", {}).get("number", "")
    
    delivery_address = ""
    delivery = ifood_order.get("delivery", {})
    if delivery:
        address = delivery.get("deliveryAddress", {})
        delivery_address = (
            f"{address.get('streetName', '')}, {address.get('streetNumber', '')} - "
            f"{address.get('neighborhood', '')} - {address.get('city', '')}"
        )
    
    total_info = ifood_order.get("total", {})
    subtotal = total_info.get("subTotal", 0) / 100
    delivery_fee = total_info.get("deliveryFee", 0) / 100
    total = total_info.get("orderAmount", 0) / 100
    
    order = Order(
        id=ifood_order.get("id", f"ifood_{datetime.now().timestamp()}"),
        display_id=display_id,
        ifood_id=ifood_order.get("id"),
        ifood_display_id=ifood_order.get("displayId"),
        ifood_short_reference=ifood_order.get("shortReference"),
        customer_name=customer_name,
        customer_phone=customer_phone,
        source=DBOrderSource.IFOOD.value,
        status=DBOrderStatus.RECEIVED.value,
        subtotal=subtotal,
        delivery_fee=delivery_fee,
        total=total,
        delivery_address=delivery_address,
        raw_data=json.dumps(ifood_order, ensure_ascii=False),
        created_at=datetime.utcnow(),
    )
    
    for item_data in ifood_order.get("items", []):
        notes = item_data.get("observations", "")
        options = []
        for option in item_data.get("options", []):
            options.append(f"{option.get('name', '')}: {option.get('quantity', 1)}x")
        
        item = OrderItem(
            name=item_data.get("name", "Item sem nome"),
            quantity=item_data.get("quantity", 1),
            unit_price=item_data.get("unitPrice", 0) / 100,
            total_price=item_data.get("totalPrice", 0) / 100,
            notes=notes if notes else None,
            options=json.dumps(options, ensure_ascii=False) if options else None,
        )
        order.items.append(item)
    
    db.add(order)
    await db.commit()
    
    # Re-fetch with eagerly loaded items
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order.id)
    )
    order = result.scalar_one()
    
    logger.info(f"Pedido iFood criado: {order.id} (Display: #{order.display_id})")
    return order


async def update_order_status(
    db: AsyncSession, order_id: str, new_status: OrderStatus, driver_name: Optional[str] = None
) -> Optional[Order]:
    order = await get_order_by_id(db, order_id)
    if not order:
        return None
    
    order.status = new_status.value
    
    now = datetime.utcnow()
    if new_status == OrderStatus.PREPARING and not order.preparing_at:
        order.preparing_at = now
    elif new_status == OrderStatus.READY and not order.ready_at:
        order.ready_at = now
    elif new_status == OrderStatus.DELIVERY and not order.delivery_at:
        order.delivery_at = now
        if driver_name and not order.driver_name:
            order.driver_name = driver_name
    
    await db.commit()
    
    # Re-fetch with eagerly loaded items
    result = await db.execute(
        select(Order).options(selectinload(Order.items)).where(Order.id == order_id)
    )
    order = result.scalar_one()
    
    logger.info(f"Pedido {order_id} atualizado para status: {new_status.value}")
    return order


async def mark_driver_as_paid(db: AsyncSession, driver_name: str) -> List[Order]:
    query = (
        select(Order)
        .where(
            Order.driver_name == driver_name,
            Order.status == DBOrderStatus.DELIVERY.value,
            Order.is_driver_paid == False,
        )
    )
    result = await db.execute(query)
    orders = list(result.scalars().all())
    
    for order in orders:
        order.is_driver_paid = True
    
    await db.commit()
    logger.info(f"Marcados {len(orders)} pedidos como pagos para: {driver_name}")
    return orders


async def delete_order(db: AsyncSession, order_id: str) -> bool:
    order = await get_order_by_id(db, order_id)
    if not order:
        return False
    await db.delete(order)
    await db.commit()
    logger.info(f"Pedido {order_id} excluído")
    return True


async def reset_all_orders(db: AsyncSession) -> int:
    count_result = await db.execute(select(func.count(Order.id)))
    count = count_result.scalar() or 0
    await db.execute(delete(OrderItem))
    await db.execute(delete(Order))
    await db.commit()
    logger.info(f"Reset executado: {count} pedidos removidos")
    return count


async def check_and_perform_daily_reset(
    db: AsyncSession, last_reset_date: Optional[str] = None
) -> tuple:
    today = date.today().isoformat()
    if last_reset_date != today:
        await reset_all_orders(db)
        logger.info(f"Reset diário realizado: {today}")
        return True, today
    return False, today


async def get_orders_count(db: AsyncSession) -> dict:
    count_result = await db.execute(select(func.count(Order.id)))
    total = count_result.scalar() or 0
    by_status = {}
    for status in DBOrderStatus:
        result = await db.execute(
            select(func.count(Order.id)).where(Order.status == status.value)
        )
        by_status[status.value] = result.scalar() or 0
    return {"total": total, "byStatus": by_status}

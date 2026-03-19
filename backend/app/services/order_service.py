"""
Serviço para gerenciamento de pedidos KDS (async) usando padrão de Repositórios.
"""
import json
import logging
from datetime import datetime, date
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ..models import Order, OrderItem, OrderStatus as DBOrderStatus, OrderSource as DBOrderSource
from ..schemas import OrderCreate, OrderStatus
from ..repositories.order import OrderRepository, order_repository as default_order_repo
from ..core.ws_manager import manager

logger = logging.getLogger(__name__)


# Obs: algumas lógicas muito específicas do KDS (como reset diário e count manual) 
# poderiam migrar para o repositório se aumetarem muito de complexidade.

async def get_all_orders(
    db: AsyncSession,
    tenant_id: Optional[int] = None,
    status: Optional[str] = None,
    source: Optional[str] = None,
    order_repo: OrderRepository = default_order_repo
) -> List[Order]:
    orders = await order_repo.get_all_with_items(db, tenant_id=tenant_id)
    
    # Filtros em memória ou via repository custom method. Para MVP, memória:
    if status:
        orders = [o for o in orders if o.status == status]
    if source:
        orders = [o for o in orders if o.source == source]
        
    return orders


async def get_active_orders(
    db: AsyncSession,
    tenant_id: Optional[int] = None,
    order_repo: OrderRepository = default_order_repo
) -> List[Order]:
    orders = await order_repo.get_all_with_items(db, tenant_id=tenant_id)
    return [o for o in orders if o.status != DBOrderStatus.CANCELLED.value]


async def get_order_by_id(
    db: AsyncSession, 
    order_id: str,
    order_repo: OrderRepository = default_order_repo
) -> Optional[Order]:
    return await order_repo.get_with_items(db, order_id)


async def get_order_by_ifood_id(
    db: AsyncSession, 
    ifood_id: str,
    order_repo: OrderRepository = default_order_repo
) -> Optional[Order]:
    return await order_repo.get_by_ifood_id(db, ifood_id)


async def create_order(
    db: AsyncSession, 
    order_data: OrderCreate, 
    order_id: str,
    tenant_id: Optional[int] = None,
    order_repo: OrderRepository = default_order_repo
) -> Order:
    # Gerar display_id local seria melhor num Repo estrito, mas por MVP,
    # contornaremos contando o tamanho para o dia.
    # Na evolução SOLID ideal, as entidades geram seus próprios aggregates.
    
    order_in = {
        "id": order_id,
        "display_id": int(datetime.utcnow().timestamp()) % 10000, # Simplified display id
        "tenant_id": tenant_id,
        "customer_name": order_data.customer_name,
        "customer_phone": order_data.customer_phone,
        "source": order_data.source.value,
        "status": DBOrderStatus.RECEIVED.value,
        "subtotal": order_data.subtotal,
        "delivery_fee": order_data.delivery_fee,
        "total": order_data.total,
        "delivery_address": order_data.delivery_address,
        "created_at": datetime.utcnow()
    }
    
    order = await order_repo.create(db, obj_in=order_in)
    
    # Adicionando itens. Para respeitar SOLID perfeitamente, o Repository faria a 
    # inserção atômica "Aggregate Root" de Order + Items.
    for item_data in order_data.items:
        item = OrderItem(
            order_id=order.id,
            name=item_data.name,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            total_price=item_data.total_price,
            notes=item_data.notes,
            options=item_data.options,
        )
        db.add(item)
    await db.commit()
    
    order = await order_repo.get_with_items(db, order_id)
    
    # Notifica os WebSockets do Tenant
    await manager.broadcast_to_tenant(
        tenant_id or 0, 
        {"action": "ORDER_CREATED", "order_id": order_id}
    )
    
    logger.info(f"Pedido criado: {order.id} (Tenant: {tenant_id})")
    return order


async def create_order_from_ifood(
    db: AsyncSession, 
    ifood_order: dict,
    tenant_id: Optional[int] = None,
    order_repo: OrderRepository = default_order_repo
) -> Order:
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
    
    order_in = {
        "id": ifood_order.get("id", f"ifood_{datetime.now().timestamp()}"),
        "display_id": ifood_order.get("displayId", int(datetime.utcnow().timestamp()) % 10000),
        "ifood_id": ifood_order.get("id"),
        "tenant_id": tenant_id,
        "customer_name": customer_name,
        "customer_phone": customer_phone,
        "source": DBOrderSource.IFOOD.value,
        "status": DBOrderStatus.RECEIVED.value,
        "subtotal": subtotal,
        "delivery_fee": delivery_fee,
        "total": total,
        "delivery_address": delivery_address,
        "raw_data": json.dumps(ifood_order, ensure_ascii=False),
        "created_at": datetime.utcnow()
    }
    
    order = await order_repo.create(db, obj_in=order_in)
    
    for item_data in ifood_order.get("items", []):
        notes = item_data.get("observations", "")
        options = []
        for option in item_data.get("options", []):
            options.append(f"{option.get('name', '')}: {option.get('quantity', 1)}x")
            
        item = OrderItem(
            order_id=order.id,
            name=item_data.get("name", "Item sem nome"),
            quantity=item_data.get("quantity", 1),
            unit_price=item_data.get("unitPrice", 0) / 100,
            total_price=item_data.get("totalPrice", 0) / 100,
            notes=notes if notes else None,
            options=json.dumps(options, ensure_ascii=False) if options else None,
        )
        db.add(item)
    await db.commit()
    
    return await order_repo.get_with_items(db, order.id)


async def update_order_status(
    db: AsyncSession, 
    order_id: str, 
    new_status: OrderStatus, 
    driver_name: Optional[str] = None,
    order_repo: OrderRepository = default_order_repo
) -> Optional[Order]:
    order = await order_repo.get(db, order_id)
    if not order:
        return None
        
    update_data = {"status": new_status.value}
    now = datetime.utcnow()
    
    if new_status == OrderStatus.PREPARING and not order.preparing_at:
        update_data["preparing_at"] = now
    elif new_status == OrderStatus.READY and not order.ready_at:
        update_data["ready_at"] = now
    elif new_status == OrderStatus.DELIVERY and not order.delivery_at:
        update_data["delivery_at"] = now
        if driver_name and not order.driver_name:
            update_data["driver_name"] = driver_name
            
    
    await order_repo.update(db, db_obj=order, obj_in=update_data)
    
    # Notifica WS
    await manager.broadcast_to_tenant(
        order.tenant_id or 0, 
        {"action": "ORDER_UPDATED", "order_id": order_id, "status": new_status.value}
    )
    
    logger.info(f"Pedido {order_id} atualizado para status: {new_status.value}")
    
    return await order_repo.get_with_items(db, order_id)


async def update_order_payment_status(
    db: AsyncSession,
    order_id: str,
    is_driver_paid: bool,
    order_repo: OrderRepository = default_order_repo
) -> Optional[Order]:
    order = await order_repo.get(db, order_id)
    if not order:
        return None
        
    await order_repo.update(db, db_obj=order, obj_in={"is_driver_paid": is_driver_paid})
    
    # Notifica WS
    await manager.broadcast_to_tenant(
        order.tenant_id or 0, 
        {"action": "DRIVER_PAID", "order_id": order_id, "is_driver_paid": is_driver_paid}
    )
    
    return await order_repo.get_with_items(db, order_id)


async def delete_order(
    db: AsyncSession, 
    order_id: str,
    order_repo: OrderRepository = default_order_repo
) -> bool:
    order = await order_repo.remove(db, order_id)
    return order is not None

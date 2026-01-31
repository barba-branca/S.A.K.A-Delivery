"""
Serviço para gerenciamento de pedidos.
Contém a lógica de negócio para criação e atualização de pedidos.
"""
import json
import logging
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models import Order, OrderItem, OrderStatus as DBOrderStatus, OrderSource as DBOrderSource
from ..schemas import OrderCreate, OrderUpdate, OrderStatus, OrderSource

logger = logging.getLogger(__name__)


def get_next_display_id(db: Session) -> int:
    """Gera o próximo display_id sequencial."""
    max_id = db.query(func.max(Order.display_id)).scalar()
    return (max_id or 100) + 1


def get_all_orders(
    db: Session,
    status: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 100
) -> List[Order]:
    """
    Retorna todos os pedidos, com filtros opcionais.
    
    Args:
        db: Sessão do banco de dados
        status: Filtrar por status
        source: Filtrar por origem
        limit: Limite de resultados
    
    Returns:
        Lista de pedidos
    """
    query = db.query(Order)
    
    if status:
        query = query.filter(Order.status == status)
    if source:
        query = query.filter(Order.source == source)
    
    return query.order_by(Order.created_at.desc()).limit(limit).all()


def get_active_orders(db: Session) -> List[Order]:
    """
    Retorna pedidos ativos (não finalizados).
    Exclui pedidos cancelados e já entregues há mais de 24h.
    """
    active_statuses = [
        DBOrderStatus.RECEIVED.value,
        DBOrderStatus.PREPARING.value,
        DBOrderStatus.READY.value,
        DBOrderStatus.DELIVERY.value
    ]
    
    return db.query(Order).filter(
        Order.status.in_(active_statuses)
    ).order_by(Order.created_at.desc()).all()


def get_order_by_id(db: Session, order_id: str) -> Optional[Order]:
    """Busca um pedido pelo ID."""
    return db.query(Order).filter(Order.id == order_id).first()


def get_order_by_ifood_id(db: Session, ifood_id: str) -> Optional[Order]:
    """Busca um pedido pelo ID do iFood."""
    return db.query(Order).filter(Order.ifood_id == ifood_id).first()


def create_order(db: Session, order_data: OrderCreate, order_id: str) -> Order:
    """
    Cria um novo pedido no banco de dados.
    
    Args:
        db: Sessão do banco de dados
        order_data: Dados do pedido
        order_id: ID único do pedido
    
    Returns:
        Pedido criado
    """
    display_id = get_next_display_id(db)
    
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
        created_at=datetime.utcnow()
    )
    
    # Adiciona os itens
    for item_data in order_data.items:
        item = OrderItem(
            name=item_data.name,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
            total_price=item_data.total_price,
            notes=item_data.notes,
            options=item_data.options
        )
        order.items.append(item)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    logger.info(f"Pedido criado: {order.id} (Display: #{order.display_id})")
    return order


def create_order_from_ifood(db: Session, ifood_order: dict) -> Order:
    """
    Cria um pedido a partir dos dados do webhook iFood.
    
    Args:
        db: Sessão do banco de dados
        ifood_order: Dados completos do pedido do iFood
    
    Returns:
        Pedido criado
    """
    display_id = get_next_display_id(db)
    
    # Extrai dados do cliente
    customer = ifood_order.get("customer", {})
    customer_name = customer.get("name", "Cliente iFood")
    customer_phone = customer.get("phone", {}).get("number", "")
    
    # Extrai endereço de entrega
    delivery_address = ""
    delivery = ifood_order.get("delivery", {})
    if delivery:
        address = delivery.get("deliveryAddress", {})
        delivery_address = (
            f"{address.get('streetName', '')}, {address.get('streetNumber', '')} - "
            f"{address.get('neighborhood', '')} - {address.get('city', '')}"
        )
    
    # Extrai valores
    total_info = ifood_order.get("total", {})
    subtotal = total_info.get("subTotal", 0) / 100  # iFood envia em centavos
    delivery_fee = total_info.get("deliveryFee", 0) / 100
    total = total_info.get("orderAmount", 0) / 100
    
    # Cria o pedido
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
        created_at=datetime.utcnow()
    )
    
    # Extrai e adiciona os itens
    items = ifood_order.get("items", [])
    for item_data in items:
        # Extrai observações e opções
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
            options=json.dumps(options, ensure_ascii=False) if options else None
        )
        order.items.append(item)
    
    db.add(order)
    db.commit()
    db.refresh(order)
    
    logger.info(
        f"Pedido iFood criado: {order.id} "
        f"(Display: #{order.display_id}, iFood Ref: {order.ifood_short_reference})"
    )
    return order


def update_order_status(
    db: Session,
    order_id: str,
    new_status: OrderStatus,
    driver_name: Optional[str] = None
) -> Optional[Order]:
    """
    Atualiza o status de um pedido.
    
    Args:
        db: Sessão do banco de dados
        order_id: ID do pedido
        new_status: Novo status
        driver_name: Nome do motorista (opcional, para status DELIVERY)
    
    Returns:
        Pedido atualizado ou None se não encontrado
    """
    order = get_order_by_id(db, order_id)
    if not order:
        return None
    
    order.status = new_status.value
    
    # Atualiza timestamps conforme o status
    now = datetime.utcnow()
    if new_status == OrderStatus.PREPARING and not order.preparing_at:
        order.preparing_at = now
    elif new_status == OrderStatus.READY and not order.ready_at:
        order.ready_at = now
    elif new_status == OrderStatus.DELIVERY and not order.delivery_at:
        order.delivery_at = now
        if driver_name and not order.driver_name:
            order.driver_name = driver_name
    
    db.commit()
    db.refresh(order)
    
    logger.info(f"Pedido {order_id} atualizado para status: {new_status.value}")
    return order


def mark_driver_as_paid(db: Session, driver_name: str) -> List[Order]:
    """
    Marca todos os pedidos de um motorista como pagos.
    
    Args:
        db: Sessão do banco de dados
        driver_name: Nome do motorista
    
    Returns:
        Lista de pedidos atualizados
    """
    orders = db.query(Order).filter(
        Order.driver_name == driver_name,
        Order.status == DBOrderStatus.DELIVERY.value,
        Order.is_driver_paid == False
    ).all()
    
    for order in orders:
        order.is_driver_paid = True
    
    db.commit()
    
    logger.info(f"Marcados {len(orders)} pedidos como pagos para o motorista: {driver_name}")
    return orders


def delete_order(db: Session, order_id: str) -> bool:
    """
    Exclui um pedido do banco de dados.
    
    Args:
        db: Sessão do banco de dados
        order_id: ID do pedido a ser excluído
    
    Returns:
        True se excluído com sucesso, False se não encontrado
    """
    order = get_order_by_id(db, order_id)
    if not order:
        return False
    
    db.delete(order)
    db.commit()
    
    logger.info(f"Pedido {order_id} excluído com sucesso")
    return True


def reset_all_orders(db: Session) -> int:
    """
    Remove todos os pedidos do banco de dados (reset diário).
    
    Args:
        db: Sessão do banco de dados
    
    Returns:
        Quantidade de pedidos removidos
    """
    count = db.query(Order).count()
    db.query(OrderItem).delete()
    db.query(Order).delete()
    db.commit()
    
    logger.info(f"Reset executado: {count} pedidos removidos")
    return count


def check_and_perform_daily_reset(db: Session, last_reset_date: Optional[str] = None) -> tuple[bool, str]:
    """
    Verifica se deve realizar o reset diário e executa se necessário.
    
    Args:
        db: Sessão do banco de dados
        last_reset_date: Data do último reset (formato YYYY-MM-DD)
    
    Returns:
        Tupla (reset_realizado, nova_data)
    """
    from datetime import date
    today = date.today().isoformat()
    
    if last_reset_date != today:
        reset_all_orders(db)
        logger.info(f"Reset diário realizado: {today}")
        return True, today
    
    return False, today


def get_orders_count(db: Session) -> dict:
    """
    Retorna estatísticas dos pedidos.
    
    Args:
        db: Sessão do banco de dados
    
    Returns:
        Dicionário com contagens por status
    """
    total = db.query(Order).count()
    by_status = {}
    
    for status in DBOrderStatus:
        count = db.query(Order).filter(Order.status == status.value).count()
        by_status[status.value] = count
    
    return {
        "total": total,
        "byStatus": by_status
    }

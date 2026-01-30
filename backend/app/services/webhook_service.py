"""
Serviço para processamento de webhooks do iFood.
Processa eventos de forma assíncrona para responder rapidamente.
"""
import json
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from ..models import WebhookEvent, Order, OrderStatus as DBOrderStatus
from .order_service import create_order_from_ifood, get_order_by_ifood_id, update_order_status
from ..schemas import OrderStatus

logger = logging.getLogger(__name__)


# Códigos de eventos do iFood
class IFoodEventCodes:
    """Códigos de eventos do webhook iFood."""
    # Eventos de pedido
    ORDER_PLACED = "PLC"  # Pedido colocado
    ORDER_CONFIRMED = "CFM"  # Pedido confirmado
    ORDER_READY_TO_PICKUP = "RTP"  # Pronto para retirada
    ORDER_DISPATCHED = "DSP"  # Despachado para entrega
    ORDER_CONCLUDED = "CON"  # Pedido concluído
    ORDER_CANCELLED = "CAN"  # Pedido cancelado
    
    # Eventos de integração
    INTEGRATION_TEST = "TEST"  # Evento de teste


def save_webhook_event(db: Session, event_data: Dict[str, Any]) -> WebhookEvent:
    """
    Salva o evento do webhook no banco de dados.
    
    Args:
        db: Sessão do banco de dados
        event_data: Dados do evento recebido
    
    Returns:
        Evento salvo
    """
    event = WebhookEvent(
        event_id=event_data.get("id", ""),
        event_code=event_data.get("code", ""),
        order_id=event_data.get("orderId"),
        merchant_id=event_data.get("merchantId"),
        payload=json.dumps(event_data, ensure_ascii=False),
        created_at=datetime.utcnow()
    )
    
    db.add(event)
    db.commit()
    db.refresh(event)
    
    logger.info(f"Evento webhook salvo: {event.event_id} (Código: {event.event_code})")
    return event


def process_webhook_event(db: Session, event_data: Dict[str, Any]) -> bool:
    """
    Processa um evento de webhook do iFood.
    
    Esta função deve ser executada de forma rápida para garantir
    resposta em menos de 5 segundos conforme requisito do iFood.
    
    Args:
        db: Sessão do banco de dados
        event_data: Dados do evento
    
    Returns:
        True se processado com sucesso, False caso contrário
    """
    event_code = event_data.get("code", "")
    order_id = event_data.get("orderId")
    
    logger.info(f"Processando evento: {event_code} para pedido: {order_id}")
    
    try:
        if event_code == IFoodEventCodes.ORDER_PLACED:
            # Novo pedido - buscar detalhes completos via API seria ideal
            # Por enquanto, cria com dados básicos do evento
            # Em produção, usar a API para buscar os detalhes completos
            _handle_order_placed(db, event_data)
            
        elif event_code == IFoodEventCodes.ORDER_CONFIRMED:
            _handle_order_status_change(db, order_id, OrderStatus.PREPARING)
            
        elif event_code == IFoodEventCodes.ORDER_READY_TO_PICKUP:
            _handle_order_status_change(db, order_id, OrderStatus.READY)
            
        elif event_code == IFoodEventCodes.ORDER_DISPATCHED:
            _handle_order_status_change(db, order_id, OrderStatus.DELIVERY)
            
        elif event_code == IFoodEventCodes.ORDER_CANCELLED:
            _handle_order_status_change(db, order_id, OrderStatus.CANCELLED)
            
        elif event_code == IFoodEventCodes.INTEGRATION_TEST:
            logger.info("Evento de teste recebido com sucesso!")
            
        else:
            logger.warning(f"Código de evento não tratado: {event_code}")
        
        return True
        
    except Exception as e:
        logger.error(f"Erro ao processar evento: {e}")
        return False


def _handle_order_placed(db: Session, event_data: Dict[str, Any]) -> Optional[Order]:
    """
    Processa evento de novo pedido colocado.
    
    Em produção, o evento PLC contém apenas informações básicas.
    Os detalhes completos do pedido devem ser buscados via API /orders/{orderId}
    
    Para esta implementação, vamos simular a criação com os dados disponíveis.
    """
    order_id = event_data.get("orderId")
    
    # Verifica se o pedido já existe
    existing = get_order_by_ifood_id(db, order_id)
    if existing:
        logger.info(f"Pedido {order_id} já existe, ignorando duplicado")
        return existing
    
    # Dados do evento - em produção, buscar via API
    # Aqui simulamos com dados básicos do metadata
    metadata = event_data.get("metadata", {})
    
    # Cria estrutura básica do pedido
    # Em produção: chamar API iFood GET /orders/{orderId}
    ifood_order = {
        "id": order_id,
        "displayId": metadata.get("displayId", ""),
        "shortReference": metadata.get("shortReference", order_id[:8] if order_id else ""),
        "customer": {
            "name": metadata.get("customerName", "Cliente iFood"),
            "phone": {"number": ""}
        },
        "total": {
            "subTotal": metadata.get("subTotal", 0),
            "deliveryFee": metadata.get("deliveryFee", 0),
            "orderAmount": metadata.get("orderAmount", 0)
        },
        "items": metadata.get("items", [
            {"name": "Pedido iFood", "quantity": 1, "unitPrice": 0, "totalPrice": 0}
        ]),
        "delivery": {
            "deliveryAddress": metadata.get("deliveryAddress", {})
        }
    }
    
    order = create_order_from_ifood(db, ifood_order)
    return order


def _handle_order_status_change(
    db: Session,
    ifood_order_id: str,
    new_status: OrderStatus
) -> Optional[Order]:
    """
    Processa mudança de status do pedido.
    
    Args:
        db: Sessão do banco de dados
        ifood_order_id: ID do pedido no iFood
        new_status: Novo status
    
    Returns:
        Pedido atualizado ou None
    """
    order = get_order_by_ifood_id(db, ifood_order_id)
    
    if not order:
        logger.warning(f"Pedido não encontrado para atualização: {ifood_order_id}")
        return None
    
    order.status = new_status.value
    
    now = datetime.utcnow()
    if new_status == OrderStatus.PREPARING:
        order.preparing_at = now
    elif new_status == OrderStatus.READY:
        order.ready_at = now
    elif new_status == OrderStatus.DELIVERY:
        order.delivery_at = now
    
    db.commit()
    db.refresh(order)
    
    logger.info(f"Pedido {order.id} atualizado para: {new_status.value}")
    return order


def mark_event_as_processed(
    db: Session,
    event_id: str,
    success: bool,
    error_message: Optional[str] = None
) -> None:
    """
    Marca um evento como processado.
    
    Args:
        db: Sessão do banco de dados
        event_id: ID do evento
        success: Se foi processado com sucesso
        error_message: Mensagem de erro (se houver)
    """
    event = db.query(WebhookEvent).filter(WebhookEvent.event_id == event_id).first()
    if event:
        event.processed = success
        event.processed_at = datetime.utcnow()
        if error_message:
            event.error_message = error_message
        db.commit()

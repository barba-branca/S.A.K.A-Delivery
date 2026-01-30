"""
Modelos do banco de dados SQLAlchemy.
Define as tabelas para armazenar pedidos do iFood.
"""
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, Text, Enum, ForeignKey
from sqlalchemy.orm import relationship
import enum

from .database import Base


class OrderStatus(str, enum.Enum):
    """Status do pedido no KDS."""
    RECEIVED = "RECEIVED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERY = "DELIVERY"
    CANCELLED = "CANCELLED"


class OrderSource(str, enum.Enum):
    """Origem do pedido."""
    IFOOD = "IFOOD"
    WHATSAPP = "WHATSAPP"
    UBER = "UBER"
    FOOD99 = "FOOD99"


class Order(Base):
    """Modelo de pedido."""
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True, index=True)
    display_id = Column(Integer, unique=True, index=True)
    
    # Dados do iFood
    ifood_id = Column(String, unique=True, nullable=True, index=True)
    ifood_display_id = Column(String, nullable=True)
    ifood_short_reference = Column(String, nullable=True)
    
    # Dados do cliente
    customer_name = Column(String, nullable=False)
    customer_phone = Column(String, nullable=True)
    
    # Dados do pedido
    source = Column(String, default=OrderSource.IFOOD.value)
    status = Column(String, default=OrderStatus.RECEIVED.value)
    
    # Valores
    subtotal = Column(Float, default=0.0)
    delivery_fee = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    
    # Entrega
    driver_name = Column(String, nullable=True)
    is_driver_paid = Column(Boolean, default=False)
    
    # Endereço
    delivery_address = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    preparing_at = Column(DateTime, nullable=True)
    ready_at = Column(DateTime, nullable=True)
    delivery_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Dados brutos do iFood (JSON)
    raw_data = Column(Text, nullable=True)
    
    # Relacionamento com itens
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    """Modelo de item do pedido."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    
    name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    options = Column(Text, nullable=True)  # JSON string com opções/complementos
    
    order = relationship("Order", back_populates="items")


class WebhookEvent(Base):
    """Modelo para armazenar eventos recebidos do webhook."""
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, unique=True, index=True)
    event_code = Column(String, nullable=False)
    order_id = Column(String, nullable=True, index=True)
    merchant_id = Column(String, nullable=True)
    
    payload = Column(Text, nullable=False)  # JSON completo do evento
    
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

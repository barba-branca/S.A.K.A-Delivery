"""
Modelos do banco de dados SQLAlchemy.
Define tabelas para o KDS (pedidos iFood) e o sistema SaaS (pacotes, créditos, repasse).
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, Numeric
)
from sqlalchemy.orm import relationship
import enum

from .database import Base


# ============== Enums ==============

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


class UserRole(str, enum.Enum):
    """Papel do usuário no sistema."""
    SUPER_ADMIN = "SUPER_ADMIN"
    CLIENTE = "CLIENTE"
    ADMIN = "ADMIN"      # Legacy
    KITCHEN = "KITCHEN"  # Legacy


class PedidoStatus(str, enum.Enum):
    """Status do pedido SaaS."""
    ATIVO = "ATIVO"
    CANCELADO = "CANCELADO"
    FINALIZADO = "FINALIZADO"


class RepasseStatus(str, enum.Enum):
    """Status do repasse."""
    PENDENTE = "PENDENTE"
    PAGO = "PAGO"


class TransactionStatus(str, enum.Enum):
    """Status de uma transação de pagamento."""
    PENDING = "pending"
    APPROVED = "approved"
    CANCELLED = "cancelled"


# ============== SaaS Models (New) ==============

class Tenant(Base):
    """Modelo de Estabelecimento (Multitenancy)."""
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    users = relationship("User", back_populates="tenant")
    orders = relationship("Order", back_populates="tenant")
    pacotes = relationship("Pacote", back_populates="tenant")


# ============== KDS Models (Existing) ==============

class Order(Base):
    """Modelo de pedido KDS (iFood/WhatsApp)."""
    __tablename__ = "orders"
    
    id = Column(String, primary_key=True, index=True)
    display_id = Column(Integer, unique=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    
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
    tenant = relationship("Tenant", back_populates="orders")


class OrderItem(Base):
    """Modelo de item do pedido KDS."""
    __tablename__ = "order_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String, ForeignKey("orders.id"), nullable=False)
    
    name = Column(String, nullable=False)
    quantity = Column(Integer, default=1)
    unit_price = Column(Float, default=0.0)
    total_price = Column(Float, default=0.0)
    notes = Column(Text, nullable=True)
    options = Column(Text, nullable=True)
    
    order = relationship("Order", back_populates="items")


class WebhookEvent(Base):
    """Modelo para armazenar eventos recebidos do webhook."""
    __tablename__ = "webhook_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    event_id = Column(String, unique=True, index=True)
    event_code = Column(String, nullable=False)
    order_id = Column(String, nullable=True, index=True)
    merchant_id = Column(String, nullable=True)
    
    payload = Column(Text, nullable=False)
    
    processed = Column(Boolean, default=False)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)


# ============== Users & Billing Models ==============

class User(Base):
    """Modelo de usuário do sistema."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    username = Column(String, unique=True, nullable=False, index=True)
    email = Column(String, unique=True, nullable=True, index=True)
    full_name = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default=UserRole.KITCHEN.value)
    
    # Saldo de crédito pré-pago (em reais)
    saldo_credito = Column(Numeric(10, 2), default=Decimal("0.00"))
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relacionamentos
    tenant = relationship("Tenant", back_populates="users")
    pacotes = relationship("Pacote", back_populates="user", cascade="all, delete-orphan")
    pedidos_saas = relationship("PedidoSaas", back_populates="user", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")


class Pacote(Base):
    """Pacote pré-pago comprado pelo usuário."""
    __tablename__ = "pacotes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    valor_pago = Column(Numeric(10, 2), nullable=False)
    qtd_pedidos = Column(Integer, nullable=False)  # quantidade de pedidos que o pacote permite
    data_compra = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="pacotes")
    tenant = relationship("Tenant", back_populates="pacotes")


class PedidoSaas(Base):
    """Pedido consumido no sistema SaaS (consome crédito)."""
    __tablename__ = "pedidos_saas"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    valor_consumido = Column(Numeric(10, 2), nullable=False, default=Decimal("5.00"))
    via_arnaldo = Column(Boolean, default=False)
    data = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default=PedidoStatus.ATIVO.value)
    
    user = relationship("User", back_populates="pedidos_saas")
    repasse = relationship("Repasse", back_populates="pedido", uselist=False, cascade="all, delete-orphan")


class Repasse(Base):
    """Repasse financeiro para o Arnaldo (30% do pedido via_arnaldo)."""
    __tablename__ = "repasses"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    pedido_id = Column(Integer, ForeignKey("pedidos_saas.id"), nullable=False)
    
    valor_para_arnaldo = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default=RepasseStatus.PENDENTE.value)
    data_repasse = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    pedido = relationship("PedidoSaas", back_populates="repasse")


class WebhookMercadoPagoLog(Base):
    """Log de auditoria para webhooks do Mercado Pago."""
    __tablename__ = "webhook_mercadopago_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Dados do webhook recebido
    webhook_id = Column(String, nullable=True, index=True)  # ID da notificação do MP
    payment_id = Column(Integer, nullable=True, index=True)  # ID do pagamento
    user_id = Column(Integer, nullable=True, index=True)  # ID do usuário no sistema
    
    # Dados da transação
    transaction_amount = Column(Numeric(10, 2), nullable=True)
    payment_status = Column(String, nullable=True)
    
    # Ações tomadas
    action = Column(String, nullable=False)  # created, updated, approved, rejected, etc.
    status = Column(String, nullable=False)  # success, error, ignored, retry
    
    # Dados originais (JSON)
    request_payload = Column(Text, nullable=True)
    payment_data = Column(Text, nullable=True)  # Dados retornados da API do MP
    
    # Informações de erro
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    
    #Resultado
    credit_added = Column(Numeric(10, 2), nullable=True)
    new_balance = Column(Numeric(10, 2), nullable=True)


class Transaction(Base):
    """Transação de pagamento via Mercado Pago (PIX)."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    external_id = Column(String, unique=True, nullable=False, index=True)  # ID do pagamento no MP
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    amount = Column(Numeric(10, 2), nullable=False)
    status = Column(String, default=TransactionStatus.PENDING.value, index=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relacionamento
    user = relationship("User", back_populates="transactions")

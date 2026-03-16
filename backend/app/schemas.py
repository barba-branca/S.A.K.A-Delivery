"""
Schemas Pydantic para validação e serialização de dados.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


# ============== Enums ==============

class OrderStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERY = "DELIVERY"
    CANCELLED = "CANCELLED"


class OrderSource(str, Enum):
    IFOOD = "IFOOD"
    WHATSAPP = "WHATSAPP"
    UBER = "UBER"
    FOOD99 = "FOOD99"


class UserRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    CLIENTE = "CLIENTE"
    ADMIN = "ADMIN"      # Legacy
    KITCHEN = "KITCHEN"  # Legacy


class PedidoStatusEnum(str, Enum):
    ATIVO = "ATIVO"
    CANCELADO = "CANCELADO"
    FINALIZADO = "FINALIZADO"


class RepasseStatusEnum(str, Enum):
    PENDENTE = "PENDENTE"
    PAGO = "PAGO"


# ============== Order Item Schemas (KDS) ==============

class OrderItemBase(BaseModel):
    name: str
    quantity: int = 1
    notes: Optional[str] = None


class OrderItemCreate(OrderItemBase):
    unit_price: float = 0.0
    total_price: float = 0.0
    options: Optional[str] = None


class OrderItemResponse(OrderItemBase):
    id: int
    unit_price: float
    total_price: float
    options: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============== Order Schemas (KDS) ==============

class OrderBase(BaseModel):
    customer_name: str
    source: OrderSource = OrderSource.IFOOD
    delivery_fee: float = 0.0


class OrderCreate(OrderBase):
    items: List[OrderItemCreate]
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    subtotal: float = 0.0
    total: float = 0.0


class OrderUpdate(BaseModel):
    status: Optional[OrderStatus] = None
    driver_name: Optional[str] = None
    is_driver_paid: Optional[bool] = None


class OrderResponse(BaseModel):
    id: str
    displayId: int = Field(alias="display_id")
    customerName: str = Field(alias="customer_name")
    source: str
    status: str
    items: List[OrderItemResponse]
    createdAt: int
    preparingAt: Optional[int] = None
    readyAt: Optional[int] = None
    deliveryAt: Optional[int] = None
    deliveryFee: float = Field(alias="delivery_fee")
    driverName: Optional[str] = Field(default=None, alias="driver_name")
    isDriverPaid: bool = Field(alias="is_driver_paid")
    
    class Config:
        from_attributes = True
        populate_by_name = True


# ============== iFood Webhook Schemas ==============

class IFoodWebhookEvent(BaseModel):
    id: str = Field(..., description="ID único do evento")
    code: str = Field(..., description="Código do tipo de evento")
    orderId: Optional[str] = Field(None, description="ID do pedido no iFood")
    merchantId: Optional[str] = Field(None, description="ID do merchant")
    createdAt: Optional[str] = Field(None, description="Data de criação do evento")
    metadata: Optional[dict] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"


class WebhookEventResponse(BaseModel):
    id: int
    event_id: str
    event_code: str
    order_id: Optional[str]
    processed: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# ============== API Response Schemas ==============

class HealthCheckResponse(BaseModel):
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int


# ============== User Schemas ==============

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=3)
    role: UserRole = UserRole.KITCHEN


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    fullName: str = Field(alias="full_name")
    role: str
    saldoCredito: float = Field(default=0.0, alias="saldo_credito")
    isActive: bool = Field(alias="is_active")
    createdAt: datetime = Field(alias="created_at")
    
    class Config:
        from_attributes = True
        populate_by_name = True


class LoginResponse(BaseModel):
    message: str
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


# ============== Pacote Schemas (SaaS) ==============

class PacoteComprar(BaseModel):
    """Schema para compra de pacote."""
    tipo: str = Field(default="padrao", description="Tipo do pacote: 'padrao' (R$5000/1000 pedidos)")


class PacoteResponse(BaseModel):
    id: int
    valor_pago: float
    qtd_pedidos: int
    data_compra: datetime
    
    class Config:
        from_attributes = True


# ============== Pedido SaaS Schemas ==============

class PedidoSaasCreate(BaseModel):
    """Schema para criação de pedido SaaS."""
    via_arnaldo: bool = Field(default=False, description="Se o pedido passa pelo Arnaldo (30% repasse)")


class PedidoSaasResponse(BaseModel):
    id: int
    user_id: int
    valor_consumido: float
    via_arnaldo: bool
    data: datetime
    status: str
    
    class Config:
        from_attributes = True


class PedidoSaasResponseCliente(BaseModel):
    """Resposta filtrada para o cliente final (sem repasse interno)."""
    id: int
    user_id: int
    valor_consumido: float
    data: datetime
    status: str
    
    class Config:
        from_attributes = True


# ============== Repasse Schemas ==============

class RepasseResponse(BaseModel):
    id: int
    pedido_id: int
    valor_para_arnaldo: float
    status: str
    data_repasse: Optional[datetime] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class RepasseMensalResponse(BaseModel):
    """Resumo mensal de repasses."""
    total_pendente: float
    total_pago: float
    quantidade_pendente: int
    quantidade_pago: int
    repasses: List[RepasseResponse]


# ============== Webhook Pagamento (OpenPix) ==============

class WebhookPagamentoPayload(BaseModel):
    """Payload esperado do webhook de pagamento (futuro OpenPix)."""
    txid: str
    valor: float
    user_id: int


# ============== Faturamento ==============

class FaturamentoCriarRequest(BaseModel):
    """Requisição para criar uma cobrança PIX."""
    user_id: int
    valor: float = Field(..., gt=0, le=10000)
    descricao: Optional[str] = None


class FaturamentoCobrancaResponse(BaseModel):
    """Resposta com os dados da cobrança PIX."""
    id: str
    user_id: int
    valor: float
    status: str
    txid: str
    codigo_pix: str
    chave_pix: str
    descricao: str
    qr_code_url: Optional[str] = None
    data_criacao: str
    data_expiracao: str


# ============== Payment (Mercado Pago PIX) ==============

class PaymentCreateRequest(BaseModel):
    """Requisição para criar pagamento PIX."""
    valor: float = Field(..., gt=0, le=10000, description="Valor em reais da recarga")


class PaymentCreateResponse(BaseModel):
    """Resposta com dados do pagamento PIX gerado."""
    transaction_id: int
    external_id: str
    qr_code: str
    qr_code_base64: str
    copia_cola: str


class TransactionStatusResponse(BaseModel):
    """Status de uma transação."""
    id: int
    external_id: str
    amount: float
    status: str
    created_at: datetime

    class Config:
        from_attributes = True

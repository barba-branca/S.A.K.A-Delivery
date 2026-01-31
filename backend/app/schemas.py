"""
Schemas Pydantic para validação e serialização de dados.
"""
from datetime import datetime
from typing import Optional, List, Any
from pydantic import BaseModel, Field
from enum import Enum


class OrderStatus(str, Enum):
    """Status do pedido no KDS."""
    RECEIVED = "RECEIVED"
    PREPARING = "PREPARING"
    READY = "READY"
    DELIVERY = "DELIVERY"
    CANCELLED = "CANCELLED"


class OrderSource(str, Enum):
    """Origem do pedido."""
    IFOOD = "IFOOD"
    WHATSAPP = "WHATSAPP"
    UBER = "UBER"
    FOOD99 = "FOOD99"


# ============== Order Item Schemas ==============

class OrderItemBase(BaseModel):
    """Schema base para item de pedido."""
    name: str
    quantity: int = 1
    notes: Optional[str] = None


class OrderItemCreate(OrderItemBase):
    """Schema para criação de item."""
    unit_price: float = 0.0
    total_price: float = 0.0
    options: Optional[str] = None


class OrderItemResponse(OrderItemBase):
    """Schema de resposta para item de pedido."""
    id: int
    unit_price: float
    total_price: float
    options: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============== Order Schemas ==============

class OrderBase(BaseModel):
    """Schema base para pedido."""
    customer_name: str
    source: OrderSource = OrderSource.IFOOD
    delivery_fee: float = 0.0


class OrderCreate(OrderBase):
    """Schema para criação de pedido."""
    items: List[OrderItemCreate]
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    subtotal: float = 0.0
    total: float = 0.0


class OrderUpdate(BaseModel):
    """Schema para atualização de pedido."""
    status: Optional[OrderStatus] = None
    driver_name: Optional[str] = None
    is_driver_paid: Optional[bool] = None


class OrderResponse(BaseModel):
    """
    Schema de resposta para pedido.
    Compatível com o formato esperado pelo frontend KDS.
    """
    id: str
    displayId: int = Field(alias="display_id")
    customerName: str = Field(alias="customer_name")
    source: str
    status: str
    items: List[OrderItemResponse]
    createdAt: int  # Timestamp em milissegundos
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
    """
    Schema para eventos do webhook do iFood.
    Baseado na documentação oficial da API iFood.
    """
    id: str = Field(..., description="ID único do evento")
    code: str = Field(..., description="Código do tipo de evento")
    orderId: Optional[str] = Field(None, description="ID do pedido no iFood")
    merchantId: Optional[str] = Field(None, description="ID do merchant")
    createdAt: Optional[str] = Field(None, description="Data de criação do evento")
    metadata: Optional[dict] = Field(default_factory=dict)
    
    class Config:
        extra = "allow"


class WebhookEventResponse(BaseModel):
    """Schema de resposta para evento de webhook."""
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
    """Schema para health check."""
    status: str = "healthy"
    timestamp: datetime
    version: str = "1.0.0"


class ErrorResponse(BaseModel):
    """Schema para respostas de erro."""
    error: str
    detail: Optional[str] = None
    status_code: int


# ============== User Schemas ==============

class UserRole(str, Enum):
    """Papel do usuário no sistema."""
    ADMIN = "ADMIN"
    KITCHEN = "KITCHEN"


class UserRegister(BaseModel):
    """Schema para registro de usuário."""
    username: str = Field(..., min_length=3, max_length=50)
    full_name: str = Field(..., min_length=2, max_length=100)
    password: str = Field(..., min_length=3)
    role: UserRole = UserRole.KITCHEN


class UserLogin(BaseModel):
    """Schema para login de usuário."""
    username: str
    password: str


class UserResponse(BaseModel):
    """Schema de resposta para usuário."""
    id: int
    username: str
    fullName: str = Field(alias="full_name")
    role: str
    isActive: bool = Field(alias="is_active")
    createdAt: datetime = Field(alias="created_at")
    
    class Config:
        from_attributes = True
        populate_by_name = True


class LoginResponse(BaseModel):
    """Schema de resposta para login."""
    message: str
    user: UserResponse
    token: Optional[str] = None

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.order import OrderStatus, PaymentStatus


class OrderItemResponse(BaseModel):
    id: int
    product_id: Optional[int] = None
    seller_id: Optional[int] = None
    quantity: int
    price_at_time: float
    subtotal: float

    model_config = {"from_attributes": True}


class OrderResponse(BaseModel):
    id: int
    buyer_id: Optional[int] = None
    status: OrderStatus
    total_price: float
    stripe_payment_intent_id: Optional[str] = None
    items: list[OrderItemResponse]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaymentResponse(BaseModel):
    id: int
    order_id: int
    stripe_id: Optional[str] = None
    amount: float
    currency: str
    status: PaymentStatus
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Stripe checkout ───────────────────────────────────────────────────────────
class CheckoutResponse(BaseModel):
    order_id: int
    client_secret: str          # Stripe PaymentIntent client_secret
    publishable_key: str
    amount: float
    currency: str


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.schemas.product import ProductResponse


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=100)


class CartItemUpdate(BaseModel):
    quantity: int = Field(..., ge=0, le=100)   # 0 = remove


class CartItemResponse(BaseModel):
    id: int
    product_id: int
    quantity: int
    price_at_time: float
    subtotal: float
    product: Optional[ProductResponse] = None

    model_config = {"from_attributes": True}

    @property
    def subtotal(self) -> float:  # type: ignore[override]
        return round(self.price_at_time * self.quantity, 2)


class CartResponse(BaseModel):
    id: int
    user_id: int
    items: list[CartItemResponse]
    total: float
    item_count: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from app.models.refund import RefundStatus


class RefundCreate(BaseModel):
    amount: Optional[float] = Field(
        default=None,
        gt=0,
        description="Montant à rembourser. Si absent, remboursement total.",
    )
    reason: Optional[str] = Field(
        default="requested_by_customer",
        description="duplicate | fraudulent | requested_by_customer",
    )
    note: Optional[str] = None


class RefundResponse(BaseModel):
    id: int
    order_id: int
    stripe_refund_id: Optional[str] = None
    amount: float
    reason: Optional[str] = None
    note: Optional[str] = None
    status: RefundStatus
    created_at: datetime

    model_config = {"from_attributes": True}
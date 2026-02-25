from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime, Enum, Text
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum
from app.core.database import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class RefundStatus(str, enum.Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Refund(Base):
    __tablename__ = "refunds"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="SET NULL"), nullable=True)
    stripe_refund_id = Column(String(255), nullable=True, unique=True)
    amount = Column(Float, nullable=False)          # montant remboursé
    reason = Column(String(255), nullable=True)     # ex: "duplicate", "fraudulent", "requested_by_customer"
    note = Column(Text, nullable=True)              # note interne admin
    status = Column(Enum(RefundStatus), default=RefundStatus.PENDING, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=_now, onupdate=_now, nullable=False)

    # Relationships
    order = relationship("Order", backref="refunds")
    payment = relationship("Payment", backref="refunds")
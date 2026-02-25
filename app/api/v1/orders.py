from fastapi import APIRouter, Depends, Request, Header, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import get_current_user, require_admin
from app.models.user import User
from app.schemas.order import OrderResponse, CheckoutResponse, OrderStatusUpdate, PaymentResponse
from app.services.order_service import OrderService
from app.schemas.refund import RefundCreate, RefundResponse
from app.services.refund_service import RefundService

router = APIRouter(tags=["Orders & Payments"])


@router.post("/checkout", response_model=CheckoutResponse, status_code=status.HTTP_201_CREATED)
def checkout(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return OrderService.checkout(db, current_user)


@router.post("/webhooks/stripe", tags=["Webhooks"])
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: Session = Depends(get_db),
):
    payload = await request.body()
    return OrderService.handle_stripe_webhook(db, payload, stripe_signature or "")


@router.get("/orders", response_model=list[OrderResponse])
def my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return OrderService.get_user_orders(db, current_user)


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return OrderService.get_order(db, order_id, current_user)


@router.patch("/admin/orders/{order_id}/status", response_model=OrderResponse)
def update_order_status(
    order_id: int,
    data: OrderStatusUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return OrderService.update_order_status(db, order_id, data, admin)


@router.post("/admin/orders/{order_id}/refund", response_model=RefundResponse)
def refund_order(
    order_id: int,
    data: RefundCreate,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    """**Admin only** — rembourser une commande (total ou partiel) via Stripe."""
    return RefundService.create_refund(db, order_id, data, admin)
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.cart import Cart, CartItem
from app.models.order import Order, OrderItem, Payment, OrderStatus, PaymentStatus
from app.models.user import User
from app.schemas.order import CheckoutResponse, OrderStatusUpdate
from app.core.stripe_client import stripe  

if settings.STRIPE_SECRET_KEY:
    stripe.api_key = settings.STRIPE_SECRET_KEY


class OrderService:
    @staticmethod
    def checkout(db: Session, user: User) -> CheckoutResponse:
        """Convert cart → Order + Stripe PaymentIntent."""
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart or not cart.items:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cart is empty")

        # ── Build order ───────────────────────────────────────────────────────
        total = 0.0
        order_items: list[OrderItem] = []
        for ci in cart.items:
            if not ci.product or not ci.product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {ci.product_id} is no longer available",
                )
            if ci.product.stock < ci.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Insufficient stock for {ci.product.name}",
                )
            subtotal = round(ci.price_at_time * ci.quantity, 2)
            total += subtotal
            order_items.append(
                OrderItem(
                    product_id=ci.product_id,
                    seller_id=ci.product.seller_id,
                    quantity=ci.quantity,
                    price_at_time=ci.price_at_time,
                    subtotal=subtotal,
                )
            )

        order = Order(buyer_id=user.id, total_price=round(total, 2), items=order_items)
        db.add(order)
        db.flush()  # get order.id before Stripe call

        # ── Create Stripe PaymentIntent ───────────────────────────────────────
        if not settings.STRIPE_SECRET_KEY:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Payment service not configured",
            )

        try:
            intent = stripe.PaymentIntent.create(
                amount=int(total * 100),   # Stripe uses cents
                currency="usd",
                metadata={"order_id": order.id, "user_id": user.id},
                automatic_payment_methods={"enabled": True},
            )
        except stripe.StripeError as e:
            db.rollback()
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

        order.stripe_payment_intent_id = intent.id
        payment = Payment(
            order_id=order.id,
            stripe_id=intent.id,
            amount=total,
            currency="usd",
            status=PaymentStatus.PENDING,
        )
        db.add(payment)

        # Reserve stock
        for ci in cart.items:
            ci.product.stock -= ci.quantity

        # Clear cart
        db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
        db.commit()
        db.refresh(order)

        return CheckoutResponse(
            order_id=order.id,
            client_secret=intent.client_secret,
            publishable_key=settings.STRIPE_PUBLISHABLE_KEY or "",
            amount=total,
            currency="usd",
        )

    @staticmethod
    def handle_stripe_webhook(db: Session, payload: bytes, sig_header: str) -> dict:
        """Process Stripe webhook events."""
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except (ValueError, stripe.SignatureVerificationError):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook signature")

        if event["type"] == "payment_intent.succeeded":
            pi = event["data"]["object"]
            order = db.query(Order).filter(Order.stripe_payment_intent_id == pi["id"]).first()
            if order:
                order.status = OrderStatus.PAID
                if order.payment:
                    order.payment.status = PaymentStatus.SUCCEEDED
                db.commit()

        elif event["type"] == "payment_intent.payment_failed":
            pi = event["data"]["object"]
            order = db.query(Order).filter(Order.stripe_payment_intent_id == pi["id"]).first()
            if order:
                order.status = OrderStatus.CANCELLED
                if order.payment:
                    order.payment.status = PaymentStatus.FAILED

                # ✅ Restauration du stock
                for item in order.items:
                    if item.product:
                        item.product.stock += item.quantity

                db.commit()

        return {"received": True}

    @staticmethod
    def get_user_orders(db: Session, user: User) -> list[Order]:
        return db.query(Order).filter(Order.buyer_id == user.id).order_by(Order.created_at.desc()).all()

    @staticmethod
    def get_order(db: Session, order_id: int, user: User) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        # Buyers can only see their own orders; admins see all
        from app.models.user import UserRole
        if user.role != UserRole.ADMIN and order.buyer_id != user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        return order

    @staticmethod
    def update_order_status(db: Session, order_id: int, data: OrderStatusUpdate, admin: User) -> Order:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
        order.status = data.status
        db.commit()
        db.refresh(order)
        return order
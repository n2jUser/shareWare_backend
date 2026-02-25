import stripe
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.order import Order, OrderStatus, PaymentStatus
from app.models.refund import Refund, RefundStatus
from app.models.user import User
from app.schemas.refund import RefundCreate
from app.core.stripe_client import stripe  


class RefundService:
    @staticmethod
    def create_refund(db: Session, order_id: int, data: RefundCreate, admin: User) -> Refund:
        order = db.query(Order).filter(Order.id == order_id).first()
        if not order:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Commande introuvable")

        if not order.stripe_payment_intent_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Aucun PaymentIntent Stripe associé à cette commande",
            )

        if order.status not in (OrderStatus.PAID, OrderStatus.SHIPPED, OrderStatus.DELIVERED):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Impossible de rembourser une commande avec le statut '{order.status}'",
            )

        # Montant en centimes pour Stripe
        refund_amount = data.amount if data.amount else order.total_price
        amount_cents = int(round(refund_amount * 100))

        try:
            stripe_refund = stripe.Refund.create(
                payment_intent=order.stripe_payment_intent_id,
                amount=amount_cents,
                reason=data.reason or "requested_by_customer",
            )
        except stripe.StripeError as e:
            raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(e))

        # Enregistrement en base
        refund = Refund(
            order_id=order.id,
            payment_id=order.payment.id if order.payment else None,
            stripe_refund_id=stripe_refund.id,
            amount=refund_amount,
            reason=data.reason,
            note=data.note,
            status=RefundStatus.SUCCEEDED if stripe_refund.status == "succeeded" else RefundStatus.PENDING,
        )
        db.add(refund)

        # Mise à jour statut commande & paiement
        order.status = OrderStatus.REFUNDED
        if order.payment:
            order.payment.status = PaymentStatus.REFUNDED

        db.commit()
        db.refresh(refund)
        return refund
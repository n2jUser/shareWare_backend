# Ajouter l'import
from app.models.refund import Refund, RefundStatus

# Ajouter dans __all__
__all__ = [
    "User", "UserRole",
    "Product",
    "Cart", "CartItem",
    "Order", "OrderItem", "Payment", "OrderStatus", "PaymentStatus",
    "Refund", "RefundStatus",   # <-- nouveau
]
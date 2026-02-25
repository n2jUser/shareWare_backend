from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.models.cart import Cart, CartItem
from app.schemas.cart import CartItemAdd, CartItemUpdate, CartResponse, CartItemResponse
from app.services.cart_service import CartService

router = APIRouter(prefix="/cart", tags=["Cart"])


def _build_cart_response(cart: Cart) -> CartResponse:
    items = []
    total = 0.0
    for ci in cart.items:
        subtotal = round(ci.price_at_time * ci.quantity, 2)
        total += subtotal
        items.append(CartItemResponse(
            id=ci.id,
            product_id=ci.product_id,
            quantity=ci.quantity,
            price_at_time=ci.price_at_time,
            subtotal=subtotal,
        ))
    return CartResponse(
        id=cart.id,
        user_id=cart.user_id,
        items=items,
        total=round(total, 2),
        item_count=sum(i.quantity for i in cart.items),
        created_at=cart.created_at,
        updated_at=cart.updated_at,
    )


@router.get("", response_model=CartResponse)
def get_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # 🔒 authenticated
):
    """**Authenticated** — get the current user's cart."""
    cart = CartService.get_cart(db, current_user)
    return _build_cart_response(cart)


@router.post("/items", response_model=CartResponse, status_code=status.HTTP_201_CREATED)
def add_item(
    data: CartItemAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # 🔒 authenticated
):
    """**Authenticated** — add a product to cart (or increase quantity if already present)."""
    cart = CartService.add_item(db, current_user, data)
    return _build_cart_response(cart)


@router.patch("/items/{item_id}", response_model=CartResponse)
def update_item(
    item_id: int,
    data: CartItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # 🔒 authenticated
):
    """**Authenticated** — update quantity (set 0 to remove)."""
    cart = CartService.update_item(db, current_user, item_id, data)
    return _build_cart_response(cart)


@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),   # 🔒 authenticated
):
    """**Authenticated** — remove all items from cart."""
    CartService.clear(db, current_user)
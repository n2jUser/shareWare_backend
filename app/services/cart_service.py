from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from app.models.cart import Cart, CartItem
from app.models.product import Product
from app.models.user import User
from app.schemas.cart import CartItemAdd, CartItemUpdate


class CartService:
    @staticmethod
    def _get_or_create_cart(db: Session, user: User) -> Cart:
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if not cart:
            cart = Cart(user_id=user.id)
            db.add(cart)
            db.commit()
            db.refresh(cart)
        return cart

    @staticmethod
    def get_cart(db: Session, user: User) -> Cart:
        return CartService._get_or_create_cart(db, user)

    @staticmethod
    def add_item(db: Session, user: User, data: CartItemAdd) -> Cart:
        product = db.query(Product).filter(Product.id == data.product_id, Product.is_active == True).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if product.stock < data.quantity:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")

        cart = CartService._get_or_create_cart(db, user)

        # Check if item already in cart
        item = db.query(CartItem).filter(CartItem.cart_id == cart.id, CartItem.product_id == data.product_id).first()
        if item:
            new_qty = item.quantity + data.quantity
            if product.stock < new_qty:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
            item.quantity = new_qty
        else:
            item = CartItem(
                cart_id=cart.id,
                product_id=data.product_id,
                quantity=data.quantity,
                price_at_time=product.price,
            )
            db.add(item)

        db.commit()
        db.refresh(cart)
        return cart

    @staticmethod
    def update_item(db: Session, user: User, item_id: int, data: CartItemUpdate) -> Cart:
        cart = CartService._get_or_create_cart(db, user)
        item = db.query(CartItem).filter(CartItem.id == item_id, CartItem.cart_id == cart.id).first()
        if not item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")

        if data.quantity == 0:
            db.delete(item)
        else:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product and product.stock < data.quantity:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Insufficient stock")
            item.quantity = data.quantity

        db.commit()
        db.refresh(cart)
        return cart

    @staticmethod
    def clear(db: Session, user: User) -> None:
        cart = db.query(Cart).filter(Cart.user_id == user.id).first()
        if cart:
            db.query(CartItem).filter(CartItem.cart_id == cart.id).delete()
            db.commit()
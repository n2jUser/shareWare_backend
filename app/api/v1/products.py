from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.core.permissions import get_current_user, require_seller, require_admin
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse, ProductListResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("", response_model=ProductListResponse)
def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    category: Optional[str] = None,
    search: Optional[str] = None,
    seller_id: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """
    Public — list all active products.
    Supports pagination, category filter, keyword search, and seller filter.
    """
    return ProductService.list_products(db, page, page_size, category, search, seller_id)


@router.get("/{product_id}", response_model=ProductResponse)
def get_product(product_id: int, db: Session = Depends(get_db)):
    """Public — get a single product by ID."""
    return ProductService.get_by_id(db, product_id)


@router.post("", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
def create_product(
    data: ProductCreate,
    db: Session = Depends(get_db),
    current_seller: User = Depends(require_seller),   # 🔒 sellers only
):
    """
    **Sellers only** — create a new product.
    """
    return ProductService.create(db, data, current_seller)


@router.patch("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    data: ProductUpdate,
    db: Session = Depends(get_db),
    current_seller: User = Depends(require_seller),   # 🔒 sellers only
):
    """
    **Sellers only** — update one of your products.
    Sellers can only update their own products.
    """
    return ProductService.update(db, product_id, data, current_seller)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_seller: User = Depends(require_seller),   # 🔒 sellers only
):
    """
    **Sellers only** — soft-delete one of your products.
    """
    ProductService.delete(db, product_id, current_seller)


# ── Seller's own products ──────────────────────────────────────────────────────
@router.get("/me/products", response_model=ProductListResponse)
def my_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_seller: User = Depends(require_seller),   # 🔒 sellers only
):
    """**Sellers only** — list all your products (including inactive ones)."""
    return ProductService.list_products(db, page, page_size, seller_id=current_seller.id)
import math
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.product import Product
from app.models.user import User
from app.schemas.product import ProductCreate, ProductUpdate, ProductListResponse, ProductResponse


class ProductService:
    @staticmethod
    def create(db: Session, data: ProductCreate, seller: User) -> Product:
        product = Product(**data.model_dump(), seller_id=seller.id)
        db.add(product)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def get_by_id(db: Session, product_id: int) -> Product:
        product = db.query(Product).filter(Product.id == product_id, Product.is_active == True).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        return product

    @staticmethod
    def list_products(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        category: str | None = None,
        search: str | None = None,
        seller_id: int | None = None,
    ) -> ProductListResponse:
        query = db.query(Product).filter(Product.is_active == True)

        if category:
            query = query.filter(Product.category == category)
        if seller_id:
            query = query.filter(Product.seller_id == seller_id)
        if search:
            query = query.filter(
                or_(
                    Product.name.ilike(f"%{search}%"),
                    Product.description.ilike(f"%{search}%"),
                )
            )

        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()

        return ProductListResponse(
            items=[ProductResponse.model_validate(p) for p in items],
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total else 0,
        )

    @staticmethod
    def update(db: Session, product_id: int, data: ProductUpdate, seller: User) -> Product:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if product.seller_id != seller.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your product")

        for field, value in data.model_dump(exclude_none=True).items():
            setattr(product, field, value)
        db.commit()
        db.refresh(product)
        return product

    @staticmethod
    def delete(db: Session, product_id: int, seller: User) -> None:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
        if product.seller_id != seller.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your product")
        product.is_active = False  # soft delete
        db.commit()
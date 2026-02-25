from fastapi import APIRouter, Depends, UploadFile, File, Request
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import require_seller
from app.core.storage import save_product_image, delete_product_image
from app.models.user import User
from app.schemas.product import ProductResponse
from app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


@router.post("/{product_id}/image", response_model=ProductResponse)
async def upload_product_image(
    product_id: int,
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_seller: User = Depends(require_seller),
):
    """
    **Sellers only** — upload ou remplace l'image principale d'un produit.
    Formats acceptés : JPEG, PNG, WEBP. Taille max : 5MB.
    """
    # base_url ex: "http://localhost:8000"
    base_url = str(request.base_url).rstrip("/")

    product = ProductService.get_by_id(db, product_id)

    # Vérifier que c'est bien son produit
    if product.seller_id != current_seller.id:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your product")

    # Supprimer l'ancienne image si elle existe
    if product.image_url:
        delete_product_image(product.image_url, base_url)

    # Sauvegarder la nouvelle
    image_url = save_product_image(file, base_url)

    # Mettre à jour le produit
    product.image_url = image_url
    db.commit()
    db.refresh(product)
    return product
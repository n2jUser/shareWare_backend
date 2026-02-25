import os
import uuid
from pathlib import Path
from fastapi import UploadFile, HTTPException, status

# Dossier où les images seront stockées
MEDIA_DIR = Path("media/products")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_SIZE_MB = 5


def save_product_image(file: UploadFile, base_url: str) -> str:
    """
    Sauvegarde l'image sur le serveur et retourne son URL publique.
    base_url : ex. 'https://monapi.com'
    """
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Type de fichier non supporté. Acceptés : {ALLOWED_TYPES}",
        )

    # Lire le contenu
    content = file.file.read()

    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Image trop lourde (max {MAX_SIZE_MB}MB)",
        )

    # Générer un nom unique
    ext = file.filename.rsplit(".", 1)[-1] if "." in file.filename else "jpg"
    filename = f"{uuid.uuid4().hex}.{ext}"
    file_path = MEDIA_DIR / filename

    with open(file_path, "wb") as f:
        f.write(content)

    # Retourner l'URL publique
    return f"{base_url}/media/products/{filename}"


def delete_product_image(image_url: str, base_url: str) -> None:
    """Supprime l'ancienne image du serveur si elle existe."""
    if not image_url or not image_url.startswith(base_url):
        return  # image externe ou nulle, on ignore
    relative = image_url.replace(f"{base_url}/", "")
    file_path = Path(relative)
    if file_path.exists():
        file_path.unlink()
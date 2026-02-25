"""
Role-based access control (RBAC).

Usage in endpoints:
    @router.get("/...", dependencies=[Depends(require_seller)])
    # or
    current_user: User = Depends(require_seller)
"""
from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import get_token_payload
from app.models.user import User, UserRole


# ── Base user dependency ──────────────────────────────────────────────────────
def get_current_user(
    payload: dict = Depends(get_token_payload),
    db: Session = Depends(get_db),
) -> User:
    user = db.query(User).filter(User.id == payload["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive account")
    return user


def get_current_verified_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please verify your account first.",
        )
    return current_user


# ── Role-specific dependencies ────────────────────────────────────────────────
def require_seller(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.SELLER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Seller account required",
        )
    return current_user


def require_buyer(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role not in (UserRole.BUYER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Buyer account required",
        )
    return current_user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required",
        )
    return current_user
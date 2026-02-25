from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.permissions import get_current_user
from app.models.user import User
from app.schemas.user import (
    UserCreate, UserLogin, UserUpdate, PasswordChange,
    TokenResponse, UserResponse, RefreshRequest,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/signup", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def signup(data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user. Returns access + refresh tokens.
    
    - Roles: **buyer** (default) or **seller**
    - Password must be ≥ 8 chars, 1 uppercase, 1 digit
    """
    user, access_token, refresh_token = AuthService.signup(db, data)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/signin", response_model=TokenResponse)
def signin(data: UserLogin, db: Session = Depends(get_db)):
    """Authenticate with email + password. Returns access + refresh tokens."""
    user, access_token, refresh_token = AuthService.signin(db, data.email, data.password)
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.post("/refresh", response_model=TokenResponse)
def refresh_tokens(data: RefreshRequest, db: Session = Depends(get_db)):
    """Obtain new access + refresh tokens using a valid refresh token."""
    access_token, refresh_token = AuthService.refresh(db, data.refresh_token)
    # Re-fetch user for response
    from app.core.security import decode_token
    payload = decode_token(refresh_token)
    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: User = Depends(get_current_user)):
    """Get the currently authenticated user's profile."""
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
def update_profile(
    data: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update the current user's profile (name, avatar)."""
    user = AuthService.update_profile(db, current_user, data)
    return UserResponse.model_validate(user)


@router.post("/me/change-password", status_code=status.HTTP_204_NO_CONTENT)
def change_password(
    data: PasswordChange,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Change the current user's password."""
    AuthService.change_password(db, current_user, data)


@router.post("/logout", status_code=status.HTTP_200_OK)
def logout(current_user: User = Depends(get_current_user)):
    """
    Logout (stateless — token invalidation handled on the client).
    For true server-side invalidation, implement a token blocklist (e.g. Redis).
    """
    return {"message": "Logged out successfully"}
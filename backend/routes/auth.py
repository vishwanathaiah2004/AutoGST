import logging
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from config.database import get_db
from models.schemas import UserCreate, UserLogin, TokenResponse, UserResponse, SuccessResponse
from services.auth_service import register_user, login_user, get_current_user
from models.models import User

logger = logging.getLogger("autogst.routes.auth")
router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=SuccessResponse, status_code=201)
def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user account."""
    logger.info("Registration request for email: %s", user_data.email)
    user = register_user(db, user_data)
    return SuccessResponse(
        message="Registration successful",
        data=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate and receive JWT token."""
    logger.info("Login request for email: %s", credentials.email)
    return login_user(db, credentials)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    """Get current authenticated user's profile."""
    return current_user


@router.post("/logout", response_model=SuccessResponse)
def logout(current_user: User = Depends(get_current_user)):
    """Logout (client should discard token)."""
    logger.info("User logged out: %s", current_user.email)
    return SuccessResponse(message="Logged out successfully")

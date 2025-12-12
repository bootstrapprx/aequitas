from datetime import datetime, timedelta
from typing import Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.orm import Session

from jose import jwt
from passlib.context import CryptContext

from app.core.config import settings

# qbo_token_storage removed - using QboToken model in DB

# Hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def check_superuser(current_user) -> None:
    """
    Dependency to check if current user is a superuser.
    Raises 403 Forbidden if not a superuser.

    Usage:
        @router.get("/admin/endpoint")
        def admin_endpoint(
            current_user: User = Depends(get_current_user),
            _: None = Depends(check_superuser)
        ):
            ...
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required"
        )
    return None

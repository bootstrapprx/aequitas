"""
Authentication routes for user registration, login, and database setup.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import Optional
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.schemas.user import (
    UserCreate,
    UserResponse,
    Token,
    LoginRequest
)
from app.schemas.user_company import UserCompanyUpdate
from app.core.security import create_access_token, verify_password
from app.services.user_service import UserService
from app.core.config import settings

router = APIRouter()

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

# Token expiration
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        token: JWT access token
        db: Database session
    
    Returns:
        User object
    
    Raises:
        HTTPException: If token is invalid or user not found
    """
    from jose import jwt, JWTError
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(UUID(user_id))
    if user is None:
        raise credentials_exception
    
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """
    Register a new user.

    For initial sign-up: provide is_initial_signup=True and company_name
    For joining existing company: provide company_ids list

    Args:
        user_data: User registration data (email, password, and company info)
        db: Database session

    Returns:
        Created user information
    """
    from app.services.company_service import CompanyService
    from app.schemas.company import CompanyCreate
    from app.services.permission_service import PermissionService

    user_service = UserService(db)

    try:
        # Handle initial sign-up (create company + user)
        if user_data.is_initial_signup:
            if not user_data.company_name:
                raise ValueError("Company name is required for initial sign-up")

            # Create company
            company_service = CompanyService()
            company_data = CompanyCreate(name=user_data.company_name)
            company = company_service.create_company(db, company_data)

            # Create user with company association
            user = user_service.create_user(user_data, company_ids=[company.id])

            # Make user admin of their company
            permission_service = PermissionService(db)
            user_company = permission_service.get_user_company(user.id, company.id)
            if user_company:
                permission_service.update_user_company_permissions(
                    user.id,
                    company.id,
                    UserCompanyUpdate(is_admin=True)
                )

            db.refresh(user)
            return user
        else:
            # Join existing company
            user = user_service.create_user(user_data)
            return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    Login and get access token with company information.

    Args:
        form_data: OAuth2 form data (username=email, password)
        db: Database session

    Returns:
        Access token with company_ids and preferred_company_id
    """
    user_service = UserService(db)
    user = user_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user's company IDs
    company_ids = user.get_company_ids()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "company_ids": [str(cid) for cid in company_ids],
            "preferred_company_id": str(user.preferred_company_id) if user.preferred_company_id else None,
            "is_superuser": user.is_superuser
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "company_ids": company_ids,
        "preferred_company_id": user.preferred_company_id
    }

@router.post("/login-json", response_model=Token)
def login_json(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login using JSON body (alternative to OAuth2 form).

    Args:
        login_data: Login request with email and password
        db: Database session

    Returns:
        Access token with company information
    """
    user_service = UserService(db)
    user = user_service.authenticate_user(login_data.email, login_data.password)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user's company IDs
    company_ids = user.get_company_ids()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "company_ids": [str(cid) for cid in company_ids],
            "preferred_company_id": str(user.preferred_company_id) if user.preferred_company_id else None,
            "is_superuser": user.is_superuser
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "company_ids": company_ids,
        "preferred_company_id": user.preferred_company_id
    }

@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information.
    
    Args:
        current_user: Current authenticated user
    
    Returns:
        User information
    """
    return current_user



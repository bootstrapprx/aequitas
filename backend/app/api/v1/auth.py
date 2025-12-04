"""
Authentication routes for user registration, login, and database setup.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Union
from uuid import UUID
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.company import Company
from app.db.models.user_company import UserCompany
from app.db.models.pending_registration import PendingRegistration
from app.schemas.user import (
    UserCreate,
    UserResponse,
    Token,
    LoginRequest,
    RegistrationRequest,
    RegistrationConfirmRequest,
    CheckoutSessionResponse,
)
from app.schemas.user_company import UserCompanyUpdate
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.ucid import generate_ucid
from app.services.user_service import UserService
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

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


@router.post("/register", response_model=Union[Token, CheckoutSessionResponse])
def register(
    request: RegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register a new user with company.
    
    Supports two registration types:
    - **free**: Creates user immediately (requires ALLOW_PUBLIC_SIGNUP=true)
    - **paid**: Creates Stripe checkout session or uses mock mode
    
    Returns:
        Token for free registration, CheckoutSessionResponse for paid
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check for existing pending registration
    existing_pending = db.query(PendingRegistration).filter(
        PendingRegistration.email == request.email,
        PendingRegistration.expires_at > datetime.utcnow()
    ).first()
    if existing_pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration already pending for this email"
        )
    
    if request.register_type == "free":
        # Free registration - check if allowed
        if not settings.ALLOW_PUBLIC_SIGNUP:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Public registration is disabled. Please use Pay & Register or contact an administrator."
            )
        
        # Create user and company immediately
        return _create_user_with_company(db, request)
    
    elif request.register_type == "paid":
        # Paid registration - create pending registration and checkout session
        return _create_checkout_session(db, request)
    
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid register_type. Must be 'free' or 'paid'"
        )


@router.post("/register/confirm", response_model=Token)
def confirm_registration(
    request: RegistrationConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    Confirm pending registration after payment.
    
    Called after successful Stripe payment or in mock mode.
    Finalizes user and company creation.
    """
    # Find pending registration
    pending = db.query(PendingRegistration).filter(
        PendingRegistration.token == request.token,
        PendingRegistration.expires_at > datetime.utcnow()
    ).first()
    
    if not pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired registration token"
        )
    
    # Check if email was taken while pending
    existing_user = db.query(User).filter(User.email == pending.email).first()
    if existing_user:
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email was registered while payment was pending"
        )
    
    # Finalize registration
    token = _finalize_registration(db, pending)
    
    # Clean up pending registration
    db.delete(pending)
    db.commit()
    
    return token


def _create_user_with_company(db: Session, request: RegistrationRequest) -> Token:
    """
    Create a new user and company atomically.
    
    Args:
        db: Database session
        request: Registration request data
    
    Returns:
        Token with access credentials
    """
    try:
        # Generate UCID for company
        ucid = generate_ucid(request.company_name)
        
        # Check if UCID already exists (rare collision)
        existing_company = db.query(Company).filter(Company.ucid == ucid).first()
        if existing_company:
            # Append random suffix
            import secrets
            ucid = f"{ucid}{secrets.token_hex(2).upper()}"
        
        # Create company
        company = Company(
            name=request.company_name,
            ucid=ucid,
            is_active=True
        )
        db.add(company)
        db.flush()  # Get company ID
        
        # Create user
        user = User(
            email=request.email,
            hashed_password=get_password_hash(request.password),
            is_active=True,
            is_superuser=False,
            preferred_company_id=company.id
        )
        db.add(user)
        db.flush()  # Get user ID
        
        # Create user-company association (as admin)
        user_company = UserCompany(
            user_id=user.id,
            company_id=company.id,
            is_admin=True,
            can_edit=True,
            can_view=True
        )
        db.add(user_company)
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"✓ New user registered: {request.email} with company: {request.company_name} (UCID: {ucid})")
        
        # Generate token
        return _generate_user_token(user)
        
    except Exception as e:
        db.rollback()
        logger.error(f"Registration failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


def _create_checkout_session(db: Session, request: RegistrationRequest) -> CheckoutSessionResponse:
    """
    Create a pending registration and Stripe checkout session.
    
    Args:
        db: Database session
        request: Registration request data
    
    Returns:
        CheckoutSessionResponse with checkout URL
    """
    # Create pending registration
    pending = PendingRegistration(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        company_name=request.company_name,
        plan=request.plan,
        token=PendingRegistration.generate_token(),
        expires_at=PendingRegistration.default_expiry()
    )
    
    if settings.STRIPE_ENABLED:
        # Use real Stripe
        try:
            import stripe
            stripe.api_key = settings.STRIPE_API_KEY
            
            # Create Stripe checkout session
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": "usd",
                        "product_data": {
                            "name": f"Aequitas {request.plan.title()} Plan",
                            "description": f"Account registration for {request.company_name}"
                        },
                        "unit_amount": 4999 if request.plan == "starter" else 9999,  # $49.99 or $99.99
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=f"{_get_frontend_url()}/auth/payment-success?token={pending.token}",
                cancel_url=f"{_get_frontend_url()}/register?canceled=true",
                customer_email=request.email,
                metadata={
                    "pending_token": pending.token
                }
            )
            
            pending.stripe_session_id = checkout_session.id
            db.add(pending)
            db.commit()
            
            return CheckoutSessionResponse(
                checkout_url=checkout_session.url,
                session_id=checkout_session.id,
                pending_token=pending.token
            )
            
        except Exception as e:
            logger.error(f"Stripe checkout creation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Payment setup failed. Please try again."
            )
    else:
        # Mock mode - simulate payment
        logger.info(f"Mock payment mode: Creating pending registration for {request.email}")
        pending.stripe_session_id = f"mock_session_{pending.token[:8]}"
        db.add(pending)
        db.commit()
        
        # In mock mode, return a URL that will auto-confirm
        return CheckoutSessionResponse(
            checkout_url=f"{_get_frontend_url()}/auth/payment-success?token={pending.token}&mock=true",
            session_id=pending.stripe_session_id,
            pending_token=pending.token
        )


def _finalize_registration(db: Session, pending: PendingRegistration) -> Token:
    """
    Finalize registration from pending data.
    
    Args:
        db: Database session
        pending: Pending registration record
    
    Returns:
        Token with access credentials
    """
    # Generate UCID
    ucid = generate_ucid(pending.company_name)
    existing_company = db.query(Company).filter(Company.ucid == ucid).first()
    if existing_company:
        import secrets
        ucid = f"{ucid}{secrets.token_hex(2).upper()}"
    
    # Create company
    company = Company(
        name=pending.company_name,
        ucid=ucid,
        is_active=True
    )
    db.add(company)
    db.flush()
    
    # Create user with pre-hashed password
    user = User(
        email=pending.email,
        hashed_password=pending.hashed_password,
        is_active=True,
        is_superuser=False,
        preferred_company_id=company.id
    )
    db.add(user)
    db.flush()
    
    # Create user-company association
    user_company = UserCompany(
        user_id=user.id,
        company_id=company.id,
        is_admin=True,
        can_edit=True,
        can_view=True
    )
    db.add(user_company)
    
    db.commit()
    db.refresh(user)
    
    logger.info(f"✓ Registration finalized: {pending.email} with company: {pending.company_name}")
    
    return _generate_user_token(user)


def _generate_user_token(user: User) -> Token:
    """Generate JWT token for user."""
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
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        company_ids=company_ids,
        preferred_company_id=user.preferred_company_id
    )


def _get_frontend_url() -> str:
    """Get the frontend URL for redirects."""
    # Could be configured via env var in production
    return "http://localhost:5173"


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
    
    # Debug: Log login attempt (no password!)
    logger.info(f"Login attempt for email: {form_data.username}")
    
    user = user_service.authenticate_user(form_data.username, form_data.password)

    if not user:
        # Debug: Log failed login
        existing_user = db.query(User).filter(User.email == form_data.username).first()
        if existing_user:
            logger.warning(f"Failed login for {form_data.username}: password mismatch")
        else:
            logger.warning(f"Failed login for {form_data.username}: user not found")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Successful login for: {user.email}")
    return _generate_user_token(user)

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
    
    # Debug: Log login attempt (no password!)
    logger.info(f"Login-JSON attempt for email: {login_data.email}")
    
    user = user_service.authenticate_user(login_data.email, login_data.password)

    if not user:
        # Debug: Log failed login
        existing_user = db.query(User).filter(User.email == login_data.email).first()
        if existing_user:
            logger.warning(f"Failed login-json for {login_data.email}: password mismatch")
        else:
            logger.warning(f"Failed login-json for {login_data.email}: user not found")
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    logger.info(f"Successful login-json for: {user.email}")
    return _generate_user_token(user)

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


@router.get("/config")
def get_auth_config():
    """
    Get public authentication configuration.
    
    Returns:
        Configuration for frontend (signup enabled, Stripe key, etc.)
    
    Always returns valid JSON with defaults even on error.
    """
    try:
        stripe_configured = settings.STRIPE_ENABLED
        mock_payments_allowed = not stripe_configured and settings.ALLOW_MOCK_PAYMENTS
        
        return {
            "allow_public_signup": settings.ALLOW_PUBLIC_SIGNUP,
            "stripe_configured": stripe_configured,
            "stripe_enabled": stripe_configured,  # Legacy compatibility
            "mock_payments_allowed": mock_payments_allowed,
            "stripe_mock_mode": mock_payments_allowed,  # Legacy compatibility
        }
    except Exception as e:
        logger.error(f"Error fetching auth config: {e}")
        # Return safe defaults on error
        return {
            "allow_public_signup": False,
            "stripe_configured": False,
            "stripe_enabled": False,
            "mock_payments_allowed": False,
            "stripe_mock_mode": False,
            "warning": "Configuration unavailable"
        }


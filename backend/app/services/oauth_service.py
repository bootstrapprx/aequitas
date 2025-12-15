"""
OAuth Service for handling external identity provider authentication.

Supports Google OAuth with architecture for Microsoft/Apple expansion.

SECURITY:
- Never grants superuser via OAuth
- Requires email_verified=true from provider
- CSRF protection via signed state tokens
- Short-lived link tokens for account collision resolution
- All operations audited
"""
import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict, Any
from uuid import UUID
from sqlalchemy.orm import Session
from jose import jwt, JWTError
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from fastapi import HTTPException, status

from app.db.models.user import User
from app.db.models.oauth_account import OAuthAccount
from app.core.config import settings
from app.core.security import create_access_token
from app.schemas.oauth import GoogleIDTokenClaims

logger = logging.getLogger(__name__)


class OAuthService:
    """
    Service for managing OAuth authentication flows.

    Handles:
    - OAuth flow initiation (authorization URL generation)
    - Callback processing (token exchange, ID token validation)
    - Account linking (collision resolution)
    - User creation for new OAuth users
    """

    def __init__(self, db: Session):
        self.db = db

    # ==================== Google OAuth ====================

    def create_google_authorization_url(self) -> Tuple[str, str]:
        """
        Create Google OAuth authorization URL with CSRF state.

        Returns:
            Tuple of (authorization_url, signed_state)

        Raises:
            HTTPException: If Google OAuth not configured
        """
        if not settings.GOOGLE_OAUTH_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Google OAuth is not configured"
            )

        # Generate and sign state for CSRF protection
        state = self._generate_signed_state()

        # Build Google OAuth URL
        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "access_type": "offline",  # Request refresh token
            "prompt": "select_account",  # Force account selection
        }

        # Construct URL
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        authorization_url = f"{base_url}?{param_str}"

        logger.info("Generated Google OAuth authorization URL")
        return authorization_url, state

    async def handle_google_callback(
        self,
        code: str,
        state: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Handle Google OAuth callback.

        Process:
        1. Validate CSRF state
        2. Exchange code for tokens
        3. Validate ID token
        4. Check for existing OAuth account
        5. Handle account linking if email collision
        6. Create user if new
        7. Return status and token/link_token

        Args:
            code: Authorization code from Google
            state: CSRF state token

        Returns:
            Tuple of (status, response_data)
            - status: "success", "link_required", "setup_required"
            - response_data: Dict with access_token or link_token

        Raises:
            HTTPException: On validation errors or OAuth failures
        """
        # 1. Validate state
        if not self._verify_signed_state(state):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid state parameter (CSRF check failed)"
            )

        # 2. Exchange code for tokens
        token_response = await self._exchange_google_code(code)
        id_token_str = token_response.get("id_token")
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)

        if not id_token_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ID token received from Google"
            )

        # 3. Validate and decode ID token
        claims = self._validate_google_id_token(id_token_str)

        # 4. Security: Reject unverified emails
        if not claims.email_verified:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Email not verified by Google. Please verify your email first."
            )

        # 5. Check for existing OAuth account
        oauth_account = self.db.query(OAuthAccount).filter(
            OAuthAccount.provider == "google",
            OAuthAccount.provider_account_id == claims.sub
        ).first()

        if oauth_account:
            # Existing OAuth user - update tokens and login
            oauth_account.access_token = access_token
            oauth_account.refresh_token = refresh_token
            oauth_account.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            oauth_account.last_login_at = datetime.utcnow()
            self.db.commit()

            user = oauth_account.user
            logger.info(f"OAuth login: {user.email} via Google")

            # Check if user needs setup (no companies)
            requires_setup = len(user.user_companies) == 0

            return "success" if not requires_setup else "setup_required", {
                "access_token": self._create_user_jwt(user),
                "token_type": "bearer",
                "company_ids": user.get_company_ids(),
                "preferred_company_id": user.preferred_company_id,
                "requires_setup": requires_setup
            }

        # 6. New OAuth user - check email collision
        existing_user = self.db.query(User).filter(User.email == claims.email).first()

        if existing_user:
            # Email collision - require explicit linking
            logger.info(f"OAuth email collision: {claims.email}")
            link_token = self._create_link_token(claims.sub, claims.email, "google")

            return "link_required", {
                "link_token": link_token,
                "link_token_expires_at": datetime.utcnow() + timedelta(minutes=15),
                "provider_email": claims.email,
                "existing_user_email": existing_user.email,
            }

        # 7. Create new user (OAuth-only, no password)
        new_user = User(
            email=claims.email,
            hashed_password=None,  # OAuth-only user
            is_active=True,
            is_superuser=False,  # NEVER grant superuser via OAuth
        )
        self.db.add(new_user)
        self.db.flush()  # Get user ID

        # Create OAuth account record
        new_oauth_account = OAuthAccount(
            user_id=new_user.id,
            provider="google",
            provider_account_id=claims.sub,
            email_at_provider=claims.email,
            email_verified=claims.email_verified,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.utcnow() + timedelta(seconds=expires_in),
            profile_picture_url=claims.picture,
            raw_claims={
                "sub": claims.sub,
                "email": claims.email,
                "name": claims.name,
                "picture": claims.picture,
            },
            last_login_at=datetime.utcnow()
        )
        self.db.add(new_oauth_account)
        self.db.commit()
        self.db.refresh(new_user)

        logger.info(f"Created new OAuth user: {new_user.email} via Google")

        # New users always need setup
        return "setup_required", {
            "access_token": self._create_user_jwt(new_user),
            "token_type": "bearer",
            "company_ids": [],
            "preferred_company_id": None,
            "requires_setup": True
        }

    def confirm_account_link(self, link_token: str, confirm: bool) -> Dict[str, Any]:
        """
        Confirm linking OAuth account to existing user.

        Args:
            link_token: Short-lived link token from callback
            confirm: User confirmation

        Returns:
            Dict with access_token if successful

        Raises:
            HTTPException: On validation errors or link failures
        """
        if not confirm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account linking was not confirmed"
            )

        # Decode and validate link token
        try:
            payload = jwt.decode(
                link_token,
                settings.OAUTH_STATE_SECRET_KEY,
                algorithms=["HS256"]
            )
            provider_account_id = payload.get("sub")
            email = payload.get("email")
            provider = payload.get("provider")

            if not all([provider_account_id, email, provider]):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid link token"
                )

        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired link token"
            )

        # Find existing user
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )

        # Check if OAuth account already exists
        existing_oauth = self.db.query(OAuthAccount).filter(
            OAuthAccount.provider == provider,
            OAuthAccount.provider_account_id == provider_account_id
        ).first()

        if existing_oauth:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth account already linked"
            )

        # Create OAuth account link
        oauth_account = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_account_id=provider_account_id,
            email_at_provider=email,
            email_verified=True,  # Already verified by provider
            last_login_at=datetime.utcnow()
        )
        self.db.add(oauth_account)
        self.db.commit()

        logger.info(f"Linked {provider} account to user: {user.email}")

        return {
            "status": "success",
            "access_token": self._create_user_jwt(user),
            "token_type": "bearer",
            "message": f"{provider.title()} account linked successfully",
            "company_ids": user.get_company_ids(),
            "preferred_company_id": user.preferred_company_id
        }

    # ==================== Helper Methods ====================

    def _generate_signed_state(self) -> str:
        """Generate and sign a CSRF state token."""
        random_state = secrets.token_urlsafe(32)
        payload = {
            "state": random_state,
            "exp": datetime.utcnow() + timedelta(minutes=10)
        }
        signed = jwt.encode(payload, settings.OAUTH_STATE_SECRET_KEY, algorithm="HS256")
        return signed

    def _verify_signed_state(self, state: str) -> bool:
        """Verify a signed CSRF state token."""
        try:
            jwt.decode(state, settings.OAUTH_STATE_SECRET_KEY, algorithms=["HS256"])
            return True
        except JWTError:
            return False

    async def _exchange_google_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens.

        Args:
            code: Authorization code from Google

        Returns:
            Token response with id_token, access_token, refresh_token

        Raises:
            HTTPException: On token exchange failure
        """
        import httpx

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

        if response.status_code != 200:
            logger.error(f"Google token exchange failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )

        return response.json()

    def _validate_google_id_token(self, id_token_str: str) -> GoogleIDTokenClaims:
        """
        Validate Google ID token and extract claims.

        Args:
            id_token_str: JWT ID token from Google

        Returns:
            GoogleIDTokenClaims with validated user data

        Raises:
            HTTPException: On validation failure
        """
        try:
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                id_token_str,
                google_requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            # Validate issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                raise ValueError('Invalid issuer')

            # Parse into schema
            claims = GoogleIDTokenClaims(**idinfo)
            return claims

        except ValueError as e:
            logger.error(f"Google ID token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID token"
            )

    def _create_link_token(self, provider_account_id: str, email: str, provider: str) -> str:
        """Create a short-lived token for account linking."""
        payload = {
            "sub": provider_account_id,
            "email": email,
            "provider": provider,
            "purpose": "link",
            "exp": datetime.utcnow() + timedelta(minutes=15)
        }
        return jwt.encode(payload, settings.OAUTH_STATE_SECRET_KEY, algorithm="HS256")

    def _create_user_jwt(self, user: User) -> str:
        """Create Aequitas JWT for authenticated user."""
        company_ids = user.get_company_ids()
        access_token_expires = timedelta(hours=24)

        access_token = create_access_token(
            data={
                "sub": str(user.id),
                "email": user.email,
                "company_ids": [str(cid) for cid in company_ids],
                "preferred_company_id": str(user.preferred_company_id) if user.preferred_company_id else None,
                "is_superuser": user.is_superuser,
                "force_password_reset": user.force_password_reset
            },
            expires_delta=access_token_expires
        )
        return access_token

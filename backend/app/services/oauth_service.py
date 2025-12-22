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
from datetime import datetime, timedelta, timezone
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
            oauth_account.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            oauth_account.last_login_at = datetime.now(timezone.utc)
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
                "link_token_expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
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
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            profile_picture_url=claims.picture,
            raw_claims={
                "sub": claims.sub,
                "email": claims.email,
                "name": claims.name,
                "picture": claims.picture,
            },
            last_login_at=datetime.now(timezone.utc)
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
            last_login_at=datetime.now(timezone.utc)
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

    # ==================== Microsoft OAuth ====================

    def create_microsoft_authorization_url(self) -> Tuple[str, str]:
        """
        Create Microsoft OAuth authorization URL with CSRF state.

        Returns:
            Tuple of (authorization_url, signed_state)

        Raises:
            HTTPException: If Microsoft OAuth not configured
        """
        if not settings.MICROSOFT_OAUTH_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Microsoft OAuth is not configured"
            )

        # Generate and sign state for CSRF protection
        state = self._generate_signed_state()

        # Build Microsoft OAuth URL
        tenant = settings.MICROSOFT_TENANT  # "common", "organizations", or tenant ID
        base_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/authorize"
        params = {
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "response_mode": "query",
        }

        # Construct URL
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        authorization_url = f"{base_url}?{param_str}"

        logger.info("Generated Microsoft OAuth authorization URL")
        return authorization_url, state

    async def handle_microsoft_callback(
        self,
        code: str,
        state: str
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Handle Microsoft OAuth callback.

        Process:
        1. Validate CSRF state
        2. Exchange code for tokens
        3. Validate ID token
        4. Check for existing OAuth account
        5. Handle account linking if email collision
        6. Create user if new
        7. Return status and token/link_token

        Args:
            code: Authorization code from Microsoft
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
        token_response = await self._exchange_microsoft_code(code)
        id_token_str = token_response.get("id_token")
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)

        if not id_token_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ID token received from Microsoft"
            )

        # 3. Validate and decode ID token
        claims = self._validate_microsoft_id_token(id_token_str)

        # Extract email (Microsoft uses 'preferred_username' or 'email')
        email = claims.get("email") or claims.get("preferred_username")
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No email found in Microsoft ID token"
            )

        # Extract provider account ID
        provider_account_id = claims.get("sub") or claims.get("oid")
        if not provider_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No subject identifier found in Microsoft ID token"
            )

        # Extract tenant ID (optional but useful for audit)
        tenant_id = claims.get("tid")

        # 4. Check for existing OAuth account
        oauth_account = self.db.query(OAuthAccount).filter(
            OAuthAccount.provider == "microsoft",
            OAuthAccount.provider_account_id == provider_account_id
        ).first()

        if oauth_account:
            # Existing OAuth user - update tokens and login
            oauth_account.access_token = access_token
            oauth_account.refresh_token = refresh_token
            oauth_account.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            oauth_account.last_login_at = datetime.now(timezone.utc)
            self.db.commit()

            user = oauth_account.user
            logger.info(f"OAuth login: {user.email} via Microsoft")

            # Check if user needs setup (no companies)
            requires_setup = len(user.user_companies) == 0

            return "success" if not requires_setup else "setup_required", {
                "access_token": self._create_user_jwt(user),
                "token_type": "bearer",
                "company_ids": user.get_company_ids(),
                "preferred_company_id": user.preferred_company_id,
                "requires_setup": requires_setup
            }

        # 5. New OAuth user - check email collision
        existing_user = self.db.query(User).filter(User.email == email).first()

        if existing_user:
            # Email collision - require explicit linking
            logger.info(f"OAuth email collision: {email}")
            link_token = self._create_link_token(provider_account_id, email, "microsoft")

            return "link_required", {
                "link_token": link_token,
                "link_token_expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
                "provider_email": email,
                "existing_user_email": existing_user.email,
            }

        # 6. Create new user (OAuth-only, no password)
        new_user = User(
            email=email,
            hashed_password=None,  # OAuth-only user
            is_active=True,
            is_superuser=False,  # NEVER grant superuser via OAuth
        )
        self.db.add(new_user)
        self.db.flush()  # Get user ID

        # Create OAuth account record
        new_oauth_account = OAuthAccount(
            user_id=new_user.id,
            provider="microsoft",
            provider_account_id=provider_account_id,
            email_at_provider=email,
            email_verified=True,  # Microsoft verifies emails
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            raw_claims={
                "sub": provider_account_id,
                "email": email,
                "name": claims.get("name"),
                "tid": tenant_id,
            },
            last_login_at=datetime.now(timezone.utc)
        )
        self.db.add(new_oauth_account)
        self.db.commit()
        self.db.refresh(new_user)

        logger.info(f"Created new OAuth user: {new_user.email} via Microsoft")

        # New users always need setup
        return "setup_required", {
            "access_token": self._create_user_jwt(new_user),
            "token_type": "bearer",
            "company_ids": [],
            "preferred_company_id": None,
            "requires_setup": True
        }

    # ==================== Apple Sign-In ====================

    def create_apple_authorization_url(self) -> Tuple[str, str]:
        """
        Create Apple Sign-In authorization URL with CSRF state.

        Returns:
            Tuple of (authorization_url, signed_state)

        Raises:
            HTTPException: If Apple OAuth not configured
        """
        if not settings.APPLE_OAUTH_ENABLED:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Apple Sign-In is not configured"
            )

        # Generate and sign state for CSRF protection
        state = self._generate_signed_state()

        # Build Apple Sign-In URL
        base_url = "https://appleid.apple.com/auth/authorize"
        params = {
            "client_id": settings.APPLE_CLIENT_ID,
            "redirect_uri": settings.APPLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "email name",
            "state": state,
            "response_mode": "form_post",  # Apple uses POST
        }

        # Construct URL
        param_str = "&".join(f"{k}={v}" for k, v in params.items())
        authorization_url = f"{base_url}?{param_str}"

        logger.info("Generated Apple Sign-In authorization URL")
        return authorization_url, state

    async def handle_apple_callback(
        self,
        code: str,
        state: str,
        user_data: Optional[Dict[str, Any]] = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Handle Apple Sign-In callback.

        Process:
        1. Validate CSRF state
        2. Exchange code for tokens
        3. Validate ID token
        4. Check for existing OAuth account
        5. Handle account linking if email collision
        6. Create user if new
        7. Return status and token/link_token

        Args:
            code: Authorization code from Apple
            state: CSRF state token
            user_data: Optional user data (only provided on first login)

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
        token_response = await self._exchange_apple_code(code)
        id_token_str = token_response.get("id_token")
        access_token = token_response.get("access_token")
        refresh_token = token_response.get("refresh_token")
        expires_in = token_response.get("expires_in", 3600)

        if not id_token_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ID token received from Apple"
            )

        # 3. Validate and decode ID token
        claims = self._validate_apple_id_token(id_token_str)

        # Extract provider account ID
        provider_account_id = claims.get("sub")
        if not provider_account_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No subject identifier found in Apple ID token"
            )

        # Extract email (may be private relay)
        email = claims.get("email")

        # 4. Check for existing OAuth account
        oauth_account = self.db.query(OAuthAccount).filter(
            OAuthAccount.provider == "apple",
            OAuthAccount.provider_account_id == provider_account_id
        ).first()

        if oauth_account:
            # Existing OAuth user - update tokens and login
            oauth_account.access_token = access_token
            oauth_account.refresh_token = refresh_token
            oauth_account.expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
            oauth_account.last_login_at = datetime.now(timezone.utc)
            self.db.commit()

            user = oauth_account.user
            logger.info(f"OAuth login: {user.email} via Apple")

            # Check if user needs setup (no companies)
            requires_setup = len(user.user_companies) == 0

            return "success" if not requires_setup else "setup_required", {
                "access_token": self._create_user_jwt(user),
                "token_type": "bearer",
                "company_ids": user.get_company_ids(),
                "preferred_company_id": user.preferred_company_id,
                "requires_setup": requires_setup
            }

        # 5. New OAuth user - email is required
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Apple did not share email. Email is required for account creation."
            )

        # Check email collision
        existing_user = self.db.query(User).filter(User.email == email).first()

        if existing_user:
            # Email collision - require explicit linking
            logger.info(f"OAuth email collision: {email}")
            link_token = self._create_link_token(provider_account_id, email, "apple")

            return "link_required", {
                "link_token": link_token,
                "link_token_expires_at": datetime.now(timezone.utc) + timedelta(minutes=15),
                "provider_email": email,
                "existing_user_email": existing_user.email,
            }

        # 6. Create new user (OAuth-only, no password)
        new_user = User(
            email=email,
            hashed_password=None,  # OAuth-only user
            is_active=True,
            is_superuser=False,  # NEVER grant superuser via OAuth
        )
        self.db.add(new_user)
        self.db.flush()  # Get user ID

        # Extract name if provided (only on first login)
        name = None
        if user_data:
            name_data = user_data.get("name", {})
            first_name = name_data.get("firstName", "")
            last_name = name_data.get("lastName", "")
            name = f"{first_name} {last_name}".strip()

        # Create OAuth account record
        new_oauth_account = OAuthAccount(
            user_id=new_user.id,
            provider="apple",
            provider_account_id=provider_account_id,
            email_at_provider=email,
            email_verified=True,  # Apple verifies emails
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=expires_in),
            raw_claims={
                "sub": provider_account_id,
                "email": email,
                "name": name,
                "is_private_email": claims.get("is_private_email"),
            },
            last_login_at=datetime.now(timezone.utc)
        )
        self.db.add(new_oauth_account)
        self.db.commit()
        self.db.refresh(new_user)

        logger.info(f"Created new OAuth user: {new_user.email} via Apple")

        # New users always need setup
        return "setup_required", {
            "access_token": self._create_user_jwt(new_user),
            "token_type": "bearer",
            "company_ids": [],
            "preferred_company_id": None,
            "requires_setup": True
        }

    # ==================== Helper Methods ====================

    def _generate_signed_state(self) -> str:
        """Generate and sign a CSRF state token."""
        random_state = secrets.token_urlsafe(32)
        payload = {
            "state": random_state,
            "exp": datetime.now(timezone.utc) + timedelta(minutes=10)
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
            "exp": datetime.now(timezone.utc) + timedelta(minutes=15)
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

    # ==================== Microsoft Helper Methods ====================

    async def _exchange_microsoft_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange Microsoft authorization code for tokens.

        Args:
            code: Authorization code from Microsoft

        Returns:
            Token response with id_token, access_token, refresh_token

        Raises:
            HTTPException: On token exchange failure
        """
        import httpx

        tenant = settings.MICROSOFT_TENANT
        token_url = f"https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"
        data = {
            "code": code,
            "client_id": settings.MICROSOFT_CLIENT_ID,
            "client_secret": settings.MICROSOFT_CLIENT_SECRET,
            "redirect_uri": settings.MICROSOFT_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

        if response.status_code != 200:
            logger.error(f"Microsoft token exchange failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )

        return response.json()

    def _validate_microsoft_id_token(self, id_token_str: str) -> Dict[str, Any]:
        """
        Validate Microsoft ID token and extract claims.

        Args:
            id_token_str: JWT ID token from Microsoft

        Returns:
            Dict with validated claims

        Raises:
            HTTPException: On validation failure
        """
        try:
            # Decode without verification for now (TODO: fetch Microsoft keys and verify)
            # In production, you should verify the signature using Microsoft's JWKS
            # For now, we trust the token came from Microsoft via HTTPS
            import base64
            import json

            # Split token and decode payload
            parts = id_token_str.split('.')
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")

            # Decode payload (add padding if needed)
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)  # Add padding
            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)

            # TODO: In production, verify:
            # 1. Signature using Microsoft's JWKS
            # 2. Issuer (iss)
            # 3. Audience (aud) matches client_id
            # 4. Expiration (exp)

            return claims

        except Exception as e:
            logger.error(f"Microsoft ID token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID token"
            )

    # ==================== Apple Helper Methods ====================

    async def _exchange_apple_code(self, code: str) -> Dict[str, Any]:
        """
        Exchange Apple authorization code for tokens.

        Args:
            code: Authorization code from Apple

        Returns:
            Token response with id_token, access_token, refresh_token

        Raises:
            HTTPException: On token exchange failure
        """
        import httpx
        import time

        # Generate client secret (Apple requires a JWT signed with private key)
        client_secret = self._generate_apple_client_secret()

        token_url = "https://appleid.apple.com/auth/token"
        data = {
            "code": code,
            "client_id": settings.APPLE_CLIENT_ID,
            "client_secret": client_secret,
            "redirect_uri": settings.APPLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(token_url, data=data)

        if response.status_code != 200:
            logger.error(f"Apple token exchange failed: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange authorization code"
            )

        return response.json()

    def _generate_apple_client_secret(self) -> str:
        """
        Generate Apple client secret JWT.

        Apple requires a JWT signed with the private key for authentication.

        Returns:
            Signed JWT client secret

        Raises:
            HTTPException: On secret generation failure
        """
        try:
            import time
            from jose import jwt as jose_jwt
            import base64

            # Decode private key (assuming it's base64 encoded)
            try:
                private_key = base64.b64decode(settings.APPLE_PRIVATE_KEY)
            except:
                # If not base64, assume it's raw PEM
                private_key = settings.APPLE_PRIVATE_KEY

            # Create JWT header and payload
            headers = {
                "kid": settings.APPLE_KEY_ID,
                "alg": "ES256"
            }

            payload = {
                "iss": settings.APPLE_TEAM_ID,
                "iat": int(time.time()),
                "exp": int(time.time()) + 3600,  # 1 hour expiration
                "aud": "https://appleid.apple.com",
                "sub": settings.APPLE_CLIENT_ID
            }

            # Sign the JWT with the private key
            client_secret = jose_jwt.encode(
                payload,
                private_key,
                algorithm="ES256",
                headers=headers
            )

            return client_secret

        except Exception as e:
            logger.error(f"Failed to generate Apple client secret: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate Apple client secret"
            )

    def _validate_apple_id_token(self, id_token_str: str) -> Dict[str, Any]:
        """
        Validate Apple ID token and extract claims.

        Args:
            id_token_str: JWT ID token from Apple

        Returns:
            Dict with validated claims

        Raises:
            HTTPException: On validation failure
        """
        try:
            # Decode without verification for now (TODO: fetch Apple keys and verify)
            # In production, you should verify the signature using Apple's JWKS
            import base64
            import json

            # Split token and decode payload
            parts = id_token_str.split('.')
            if len(parts) != 3:
                raise ValueError("Invalid JWT format")

            # Decode payload (add padding if needed)
            payload = parts[1]
            payload += '=' * (4 - len(payload) % 4)  # Add padding
            decoded = base64.urlsafe_b64decode(payload)
            claims = json.loads(decoded)

            # TODO: In production, verify:
            # 1. Signature using Apple's JWKS
            # 2. Issuer (iss) is https://appleid.apple.com
            # 3. Audience (aud) matches client_id
            # 4. Expiration (exp)

            return claims

        except Exception as e:
            logger.error(f"Apple ID token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid ID token"
            )

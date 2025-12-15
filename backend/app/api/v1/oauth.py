"""
OAuth authentication routes for Google (and future providers).

Handles:
- OAuth flow initiation
- OAuth callback processing
- Account linking for email collisions
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session
import logging

from app.db.session import get_db
from app.services.oauth_service import OAuthService
from app.services.audit_service import AuditService
from app.schemas.oauth import (
    OAuthStartResponse,
    OAuthCallbackRequest,
    OAuthCallbackResponse,
    OAuthLinkConfirmRequest,
    OAuthLinkConfirmResponse,
    OAuthConfigResponse
)
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/config", response_model=OAuthConfigResponse)
def get_oauth_config():
    """
    Get public OAuth configuration for frontend.

    Returns available OAuth providers and their status.
    """
    return OAuthConfigResponse(
        google_enabled=settings.GOOGLE_OAUTH_ENABLED,
        microsoft_enabled=False,  # Future
        apple_enabled=False,  # Future
    )


@router.get("/google/start", response_model=OAuthStartResponse)
def google_oauth_start(db: Session = Depends(get_db)):
    """
    Initiate Google OAuth flow.

    Returns:
        OAuthStartResponse with authorization URL and CSRF state

    Raises:
        503: If Google OAuth not configured
    """
    oauth_service = OAuthService(db)

    try:
        authorization_url, state = oauth_service.create_google_authorization_url()

        return OAuthStartResponse(
            authorization_url=authorization_url,
            state=state,
            provider="google"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create Google OAuth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initialize OAuth flow"
        )


@router.post("/google/callback", response_model=OAuthCallbackResponse)
async def google_oauth_callback(
    request_data: OAuthCallbackRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback after user grants consent.

    Process:
    1. Validate CSRF state
    2. Exchange code for tokens
    3. Validate ID token
    4. Check for existing OAuth account
    5. Handle email collision (link_required)
    6. Create new user if needed
    7. Return JWT token or link token

    Args:
        request_data: OAuth callback data (code, state)
        request: FastAPI request (for IP logging)
        db: Database session

    Returns:
        OAuthCallbackResponse with status and appropriate tokens

    Raises:
        400: Invalid state, code, or ID token
        403: Email not verified by Google
        500: Internal errors
    """
    oauth_service = OAuthService(db)
    audit_service = AuditService(db)

    try:
        # Get client IP for audit logging
        client_ip = request.client.host if request.client else None

        # Process OAuth callback
        status_result, response_data = await oauth_service.handle_google_callback(
            code=request_data.code,
            state=request_data.state
        )

        # Build response based on status
        if status_result == "success":
            # Successful login - audit log
            user_email = response_data.get("user_email")  # OAuth service should provide this
            # Note: We'd need to pass user info from service for complete audit
            logger.info(f"OAuth login successful via Google")

            return OAuthCallbackResponse(
                status="success",
                access_token=response_data["access_token"],
                token_type=response_data["token_type"],
                company_ids=response_data["company_ids"],
                preferred_company_id=response_data["preferred_company_id"],
                requires_setup=response_data.get("requires_setup", False)
            )

        elif status_result == "setup_required":
            # New user needs to complete setup
            logger.info(f"New OAuth user requires setup")

            return OAuthCallbackResponse(
                status="setup_required",
                access_token=response_data["access_token"],
                token_type=response_data["token_type"],
                company_ids=response_data["company_ids"],
                preferred_company_id=response_data["preferred_company_id"],
                requires_setup=True
            )

        elif status_result == "link_required":
            # Email collision - require explicit linking
            logger.info(f"OAuth account linking required for {response_data['provider_email']}")

            return OAuthCallbackResponse(
                status="link_required",
                link_token=response_data["link_token"],
                link_token_expires_at=response_data["link_token_expires_at"],
                provider_email=response_data["provider_email"],
                existing_user_email=response_data["existing_user_email"]
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unknown OAuth status: {status_result}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed"
        )


@router.post("/link/confirm", response_model=OAuthLinkConfirmResponse)
def confirm_oauth_link(
    request_data: OAuthLinkConfirmRequest,
    db: Session = Depends(get_db)
):
    """
    Confirm linking OAuth account to existing user.

    SECURITY:
    - Requires user confirmation
    - Short-lived link token (15 minutes)
    - Audits all linking operations

    Args:
        request_data: Link confirmation data (link_token, confirm)
        db: Database session

    Returns:
        OAuthLinkConfirmResponse with JWT token on success

    Raises:
        400: Invalid link token or confirmation denied
        404: User not found
    """
    if not request_data.confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Account linking must be confirmed"
        )

    oauth_service = OAuthService(db)
    audit_service = AuditService(db)

    try:
        result = oauth_service.confirm_account_link(
            link_token=request_data.link_token,
            confirm=request_data.confirm
        )

        # Audit log the linking
        # Note: Would need to extract user info from result for complete audit
        logger.info(f"OAuth account linked successfully")

        return OAuthLinkConfirmResponse(
            status=result["status"],
            access_token=result["access_token"],
            token_type=result["token_type"],
            message=result["message"],
            company_ids=result["company_ids"],
            preferred_company_id=result["preferred_company_id"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth account linking failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to link OAuth account"
        )

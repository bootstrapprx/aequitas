"""
OAuth authentication schemas for request/response validation.

Handles Google OAuth flow, account linking, and token exchange.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID


class OAuthStartResponse(BaseModel):
    """Response from OAuth start endpoint with authorization URL."""

    authorization_url: str = Field(
        ...,
        description="URL to redirect user to for OAuth consent"
    )
    state: str = Field(
        ...,
        description="CSRF protection state parameter (signed)"
    )
    provider: str = Field(
        ...,
        description="OAuth provider name (google)"
    )


class OAuthCallbackRequest(BaseModel):
    """Request to OAuth callback endpoint after user grants consent."""

    code: str = Field(
        ...,
        description="Authorization code from OAuth provider"
    )
    state: str = Field(
        ...,
        description="CSRF protection state parameter (must match start)"
    )


class OAuthCallbackResponse(BaseModel):
    """Response from OAuth callback endpoint."""

    status: str = Field(
        ...,
        description="Status of OAuth flow: 'success', 'link_required', 'setup_required'"
    )
    access_token: Optional[str] = Field(
        None,
        description="Aequitas JWT token (only if status=success)"
    )
    token_type: Optional[str] = Field(
        None,
        description="Token type (bearer)"
    )
    link_token: Optional[str] = Field(
        None,
        description="Short-lived token for account linking (only if status=link_required)"
    )
    link_token_expires_at: Optional[datetime] = Field(
        None,
        description="When the link token expires"
    )
    provider_email: Optional[str] = Field(
        None,
        description="Email from OAuth provider (for linking flow)"
    )
    existing_user_email: Optional[str] = Field(
        None,
        description="Existing user email that conflicts (for linking flow)"
    )
    company_ids: Optional[list[UUID]] = Field(
        None,
        description="List of company IDs user has access to"
    )
    preferred_company_id: Optional[UUID] = Field(
        None,
        description="User's preferred company ID"
    )
    requires_setup: Optional[bool] = Field(
        None,
        description="True if user needs to complete PostAuthSetup"
    )


class OAuthLinkConfirmRequest(BaseModel):
    """Request to confirm linking OAuth account to existing user."""

    link_token: str = Field(
        ...,
        description="Short-lived link token from callback response"
    )
    confirm: bool = Field(
        ...,
        description="User confirmation to link accounts"
    )


class OAuthLinkConfirmResponse(BaseModel):
    """Response from account linking confirmation."""

    status: str = Field(
        ...,
        description="Status: 'success' or 'error'"
    )
    access_token: Optional[str] = Field(
        None,
        description="Aequitas JWT token after successful link"
    )
    token_type: Optional[str] = Field(
        None,
        description="Token type (bearer)"
    )
    message: Optional[str] = Field(
        None,
        description="Human-readable message"
    )
    company_ids: Optional[list[UUID]] = Field(
        None,
        description="List of company IDs user has access to"
    )
    preferred_company_id: Optional[UUID] = Field(
        None,
        description="User's preferred company ID"
    )


class OAuthAccountResponse(BaseModel):
    """OAuth account information for user profile."""

    id: UUID
    provider: str
    email_at_provider: EmailStr
    email_verified: bool
    profile_picture_url: Optional[str] = None
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class GoogleIDTokenClaims(BaseModel):
    """Expected claims from Google ID token (subset)."""

    sub: str = Field(..., description="Google user ID (stable)")
    email: EmailStr = Field(..., description="User email")
    email_verified: bool = Field(..., description="Email verification status")
    name: Optional[str] = Field(None, description="Full name")
    given_name: Optional[str] = Field(None, description="First name")
    family_name: Optional[str] = Field(None, description="Last name")
    picture: Optional[str] = Field(None, description="Profile picture URL")
    locale: Optional[str] = Field(None, description="User locale")

    # Optional fields
    hd: Optional[str] = Field(None, description="Hosted domain (G Suite)")


class OAuthConfigResponse(BaseModel):
    """Public OAuth configuration for frontend."""

    google_enabled: bool = Field(
        ...,
        description="Whether Google OAuth is configured"
    )
    microsoft_enabled: bool = Field(
        default=False,
        description="Whether Microsoft OAuth is configured"
    )
    apple_enabled: bool = Field(
        default=False,
        description="Whether Apple Sign In is configured"
    )

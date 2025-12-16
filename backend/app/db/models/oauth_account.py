"""
OAuth Account model for storing external identity provider connections.

This model links external OAuth providers (Google, Microsoft, Apple, etc.)
to internal User accounts, enabling federated authentication.

SECURITY:
- Never grants superuser privileges via OAuth
- Email verification required (email_verified must be true)
- Tokens stored encrypted at rest (application-level responsibility)
- All linking operations require explicit user confirmation
"""
import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Index, Text, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from app.db.base import Base


class OAuthAccount(Base):
    """
    OAuth provider account linked to a User.

    Supports multiple providers per user (Google, Microsoft, Apple, etc.)
    Enables passwordless authentication while maintaining internal JWT security.
    """
    __tablename__ = "oauth_accounts"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Foreign key to User
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Provider information
    provider = Column(
        String(50),
        nullable=False,
        index=True,
        comment="OAuth provider name (google, microsoft, apple)"
    )

    provider_account_id = Column(
        String(255),
        nullable=False,
        comment="Stable user ID from provider (e.g., Google 'sub' claim)"
    )

    email_at_provider = Column(
        String(255),
        nullable=False,
        comment="Email address as registered with provider"
    )

    email_verified = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether provider has verified this email"
    )

    # OAuth tokens (stored for future provider API access; not currently used for refresh logic)
    # TODO: Implement token refresh rotation in Phase 2
    # TODO: Add field-level encryption for production deployments
    access_token = Column(
        Text,
        nullable=True,
        comment="OAuth access token from provider (for future API calls, not active refresh)"
    )

    refresh_token = Column(
        Text,
        nullable=True,
        comment="OAuth refresh token from provider (for future token rotation, not active)"
    )

    expires_at = Column(
        DateTime,
        nullable=True,
        comment="When the access token expires (tracked but not enforced yet)"
    )

    # Additional provider data
    raw_claims = Column(
        JSONB,
        nullable=True,
        comment="Full ID token claims from provider (sanitized)"
    )

    profile_picture_url = Column(
        String(500),
        nullable=True,
        comment="User's profile picture from provider"
    )

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login_at = Column(
        DateTime,
        nullable=True,
        comment="Last successful OAuth login via this provider"
    )

    # Relationships
    user = relationship("User", back_populates="oauth_accounts")

    # Constraints
    __table_args__ = (
        # Unique constraint: one provider account per provider
        Index(
            'uq_oauth_provider_account',
            'provider',
            'provider_account_id',
            unique=True
        ),
        # Index for user lookup
        Index('ix_oauth_user_provider', 'user_id', 'provider'),
    )

    def __repr__(self):
        return f"<OAuthAccount(provider='{self.provider}', user_id='{self.user_id}', email='{self.email_at_provider}')>"

    def is_token_expired(self) -> bool:
        """Check if the access token is expired."""
        if not self.expires_at:
            return True
        return datetime.utcnow() >= self.expires_at

"""
Invitation model for inviting users to companies or groups.

Invitations are resolved by email - when a user with matching email
authenticates (via OAuth or password), they can accept pending invitations.

SECURITY:
- Invitations expire after configured time period
- Email must match exactly (case-insensitive)
- Acceptance creates appropriate membership record
- All operations audited
"""
import uuid
from datetime import datetime, timedelta
from sqlalchemy import Column, String, ForeignKey, DateTime, Boolean, Index
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base


class Invitation(Base):
    """
    User invitation to join a company or group.

    Invitations are email-based and automatically discovered when
    users authenticate with matching email addresses.
    """
    __tablename__ = "invitations"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Invitee information
    email = Column(
        String(255),
        nullable=False,
        index=True,
        comment="Email of person being invited (case-insensitive match)"
    )

    # Target (what they're being invited to)
    # NOTE: For v1, only company invitations are supported
    # Group invitations will be implemented in Phase 2
    target_type = Column(
        String(20),
        nullable=False,
        default="company",
        comment="Type of invitation: 'company' (v1 only) or 'group' (future)"
    )

    # Company invitation (v1 - fully implemented)
    company_id = Column(
        UUID(as_uuid=True),
        ForeignKey("companies.id", ondelete="CASCADE"),
        nullable=True,  # Nullable for future group support, but required for company invitations
        comment="Company ID for company invitations"
    )

    # Group invitation (Phase 2 - not yet implemented)
    group_id = Column(
        UUID(as_uuid=True),
        ForeignKey("group_companies.id", ondelete="CASCADE"),
        nullable=True,
        comment="Group ID for group invitations (not yet implemented)"
    )

    # Role/permissions
    role = Column(
        String(50),
        default="member",
        nullable=False,
        comment="Role: admin, member, viewer, etc."
    )

    is_admin = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether invitee will be admin (for companies)"
    )

    can_edit = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether invitee can edit (for companies)"
    )

    can_view = Column(
        Boolean,
        default=True,
        nullable=False,
        comment="Whether invitee can view (for companies)"
    )

    # Inviter information
    inviter_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who created the invitation"
    )

    # Invitation state
    status = Column(
        String(20),
        default="pending",
        nullable=False,
        comment="Status: pending, accepted, declined, expired"
    )

    accepted_at = Column(
        DateTime,
        nullable=True,
        comment="When invitation was accepted"
    )

    accepted_by_user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who accepted the invitation"
    )

    # Expiration
    expires_at = Column(
        DateTime,
        nullable=False,
        comment="When invitation expires"
    )

    # Audit fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    company = relationship("Company", foreign_keys=[company_id])
    group = relationship("GroupCompany", foreign_keys=[group_id])
    inviter = relationship("User", foreign_keys=[inviter_id])
    accepted_by = relationship("User", foreign_keys=[accepted_by_user_id])

    # Indexes
    __table_args__ = (
        # Index for finding pending invitations by email
        Index('ix_invitations_email_status', 'email', 'status'),
        # Index for finding invitations by target
        Index('ix_invitations_target', 'target_type', 'target_id'),
    )

    def __repr__(self):
        return f"<Invitation(email='{self.email}', target_type='{self.target_type}', status='{self.status}')>"

    @staticmethod
    def default_expiry(days=30) -> datetime:
        """Generate default expiration time (30 days from now)."""
        return datetime.utcnow() + timedelta(days=days)

    def is_expired(self) -> bool:
        """Check if invitation has expired."""
        return datetime.utcnow() >= self.expires_at

    def is_pending(self) -> bool:
        """Check if invitation is pending and not expired."""
        return self.status == "pending" and not self.is_expired()

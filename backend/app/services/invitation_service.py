"""
Invitation service for managing user invitations to companies and groups.

Business logic for creating, accepting, and declining invitations.
"""
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from uuid import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db.models.invitation import Invitation
from app.db.models.user import User
from app.db.models.company import Company
from app.db.models.group_company import GroupCompany
from app.db.models.user_company import UserCompany
from app.db.models.group_company_member import GroupCompanyMember
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class InvitationService:
    """
    Service for managing invitations.

    Handles invitation discovery, acceptance, decline, and expiration.
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def get_pending_invitations(self, email: str) -> List[Invitation]:
        """
        Get all pending invitations for an email address.

        Args:
            email: Email address to check

        Returns:
            List of pending, non-expired invitations
        """
        # Case-insensitive email match
        invitations = self.db.query(Invitation).filter(
            Invitation.email.ilike(email),
            Invitation.status == "pending",
            Invitation.expires_at > datetime.utcnow()
        ).all()

        logger.info(f"Found {len(invitations)} pending invitations for {email}")
        return invitations

    def get_invitation_with_target_name(self, invitation: Invitation) -> Tuple[Invitation, str]:
        """
        Get invitation with target name populated.

        NOTE: Uses company_id/group_id directly (no redundant target_id field).

        Args:
            invitation: Invitation object

        Returns:
            Tuple of (invitation, target_name)
        """
        target_name = "Unknown"

        if invitation.target_type == "company" and invitation.company_id:
            company = self.db.query(Company).filter(Company.id == invitation.company_id).first()
            if company:
                target_name = company.name

        elif invitation.target_type == "group" and invitation.group_id:
            # Note: Group invitations not yet implemented in v1
            group = self.db.query(GroupCompany).filter(GroupCompany.id == invitation.group_id).first()
            if group:
                target_name = group.name

        return invitation, target_name

    def accept_invitation(
        self,
        invitation_id: UUID,
        user: User
    ) -> Tuple[str, UUID, UUID]:
        """
        Accept an invitation and create appropriate membership.

        Args:
            invitation_id: UUID of invitation to accept
            user: User accepting the invitation

        Returns:
            Tuple of (target_type, target_id, membership_id)

        Raises:
            HTTPException: On validation errors
        """
        # Find invitation
        invitation = self.db.query(Invitation).filter(Invitation.id == invitation_id).first()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        # Validate invitation state
        if invitation.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation already {invitation.status}"
            )

        if invitation.is_expired():
            invitation.status = "expired"
            self.db.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invitation has expired"
            )

        # Validate email match (case-insensitive)
        if user.email.lower() != invitation.email.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invitation email does not match your account"
            )

        # Create membership based on target type
        if invitation.target_type == "company":
            if not invitation.company_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invitation missing company_id"
                )
            membership_id = self._create_company_membership(invitation, user)
            target_id = invitation.company_id
            target_name = invitation.company.name if invitation.company else "Unknown Company"

        elif invitation.target_type == "group":
            # Group invitations not yet implemented in v1
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Group invitations will be supported in a future release"
            )

        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target_type: {invitation.target_type}. Must be 'company'"
            )

        # Update invitation status
        invitation.status = "accepted"
        invitation.accepted_at = datetime.utcnow()
        invitation.accepted_by_user_id = user.id
        self.db.commit()

        # Audit log
        self.audit_service.log_invitation_accepted(
            user_id=user.id,
            user_email=user.email,
            target_type=invitation.target_type,
            target_id=target_id,
            target_name=target_name,
            invitation_id=invitation.id,
            membership_id=membership_id
        )

        logger.info(f"User {user.email} accepted invitation {invitation.id} to {target_name}")

        return invitation.target_type, target_id, membership_id

    def decline_invitation(
        self,
        invitation_id: UUID,
        user: User,
        reason: Optional[str] = None
    ) -> None:
        """
        Decline an invitation.

        Args:
            invitation_id: UUID of invitation to decline
            user: User declining the invitation
            reason: Optional reason for declining

        Raises:
            HTTPException: On validation errors
        """
        # Find invitation
        invitation = self.db.query(Invitation).filter(Invitation.id == invitation_id).first()

        if not invitation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Invitation not found"
            )

        # Validate invitation state
        if invitation.status != "pending":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invitation already {invitation.status}"
            )

        # Validate email match (case-insensitive)
        if user.email.lower() != invitation.email.lower():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invitation email does not match your account"
            )

        # Get target name for audit log
        _, target_name = self.get_invitation_with_target_name(invitation)
        target_id = invitation.company_id if invitation.target_type == "company" else invitation.group_id

        # Update invitation status
        invitation.status = "declined"
        self.db.commit()

        # Audit log
        self.audit_service.log_invitation_declined(
            user_id=user.id,
            user_email=user.email,
            target_type=invitation.target_type,
            target_id=target_id,
            target_name=target_name,
            invitation_id=invitation.id,
            reason=reason
        )

        logger.info(f"User {user.email} declined invitation {invitation.id} to {target_name}")

    def _create_company_membership(self, invitation: Invitation, user: User) -> UUID:
        """Create UserCompany membership from invitation."""
        # Check if membership already exists
        existing = self.db.query(UserCompany).filter(
            UserCompany.user_id == user.id,
            UserCompany.company_id == invitation.company_id
        ).first()

        if existing:
            logger.warning(f"User {user.email} already has access to company {invitation.company_id}")
            return existing.id

        # Create new membership
        membership = UserCompany(
            user_id=user.id,
            company_id=invitation.company_id,
            is_admin=invitation.is_admin,
            can_edit=invitation.can_edit,
            can_view=invitation.can_view
        )
        self.db.add(membership)
        self.db.flush()

        # Set as preferred company if user has no preference
        if not user.preferred_company_id:
            user.preferred_company_id = invitation.company_id

        self.db.commit()
        self.db.refresh(membership)

        return membership.id

    def _create_group_membership(self, invitation: Invitation, user: User) -> UUID:
        """
        Create GroupCompanyMember membership from invitation.

        TODO (Phase 2 - Group Invitations):
        - Determine which company to add to the group
        - If user has multiple companies, allow selection
        - Create GroupCompanyMember record
        - Handle duplicate prevention
        - Audit log the group membership creation

        For now, this raises 501 Not Implemented.
        """
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Group invitations not yet implemented. Please use company invitations."
        )

    def create_invitation(
        self,
        inviter: User,
        email: str,
        target_type: str,
        target_id: UUID,
        role: str = "member",
        is_admin: bool = False,
        can_edit: bool = True,
        can_view: bool = True,
        expires_days: int = 30
    ) -> UUID:
        """
        Create a new invitation.

        Args:
            inviter: User creating the invitation
            email: Email address to invite
            target_type: Type of invitation ('company' or 'group')
            target_id: UUID of company or group
            role: Role for invitee
            is_admin: Whether invitee will be admin
            can_edit: Whether invitee can edit
            can_view: Whether invitee can view
            expires_days: Days until invitation expires (1-365)

        Returns:
            UUID of created invitation

        Raises:
            HTTPException: On validation errors or permission denied
        """
        # Validate target_type
        if target_type not in ["company", "group"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid target_type: {target_type}. Must be 'company' or 'group'"
            )

        # For v1, only company invitations are supported
        if target_type == "group":
            raise HTTPException(
                status_code=status.HTTP_501_NOT_IMPLEMENTED,
                detail="Group invitations will be supported in a future release"
            )

        # Validate expires_days
        if not (1 <= expires_days <= 365):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="expires_days must be between 1 and 365"
            )

        # Get target name for audit log
        target_name = "Unknown"
        if target_type == "company":
            company = self.db.query(Company).filter(Company.id == target_id).first()
            if not company:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Company {target_id} not found"
                )
            target_name = company.name

            # Verify inviter has admin access to company
            user_company = self.db.query(UserCompany).filter(
                UserCompany.user_id == inviter.id,
                UserCompany.company_id == target_id,
                UserCompany.is_admin == True
            ).first()

            if not user_company and not inviter.is_superuser:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You must be an admin of this company to send invitations"
                )

        # Check for duplicate pending invitation
        existing = self.db.query(Invitation).filter(
            Invitation.email.ilike(email),
            Invitation.status == "pending",
            Invitation.company_id == target_id if target_type == "company" else Invitation.group_id == target_id,
            Invitation.expires_at > datetime.utcnow()
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"A pending invitation already exists for {email} to this {target_type}"
            )

        # Create invitation
        invitation = Invitation(
            email=email.lower(),
            target_type=target_type,
            company_id=target_id if target_type == "company" else None,
            group_id=target_id if target_type == "group" else None,
            role=role,
            is_admin=is_admin,
            can_edit=can_edit,
            can_view=can_view,
            inviter_id=inviter.id,
            expires_at=Invitation.default_expiry(days=expires_days)
        )
        self.db.add(invitation)
        self.db.flush()

        # Audit log
        self.audit_service.log_invitation_sent(
            inviter_id=inviter.id,
            invitee_email=email,
            target_type=target_type,
            target_id=target_id,
            target_name=target_name,
            invitation_id=invitation.id
        )

        self.db.commit()
        self.db.refresh(invitation)

        logger.info(f"User {inviter.email} created invitation {invitation.id} for {email} to {target_name}")

        return invitation.id

    def get_user_context(self, user: User) -> dict:
        """
        Get user context for routing decisions.

        Args:
            user: User object

        Returns:
            Dict with has_company, company_count, pending_invitations, requires_setup
        """
        # Count companies user has access to
        company_count = len(user.user_companies)

        # Count pending invitations
        pending_invitations = len(self.get_pending_invitations(user.email))

        # Determine if user requires setup
        requires_setup = company_count == 0

        return {
            "has_company": company_count > 0,
            "company_count": company_count,
            "pending_invitations": pending_invitations,
            "requires_setup": requires_setup
        }

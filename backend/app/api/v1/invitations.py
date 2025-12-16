"""
Invitation API routes for user invitation management.

Handles:
- Discovering pending invitations
- Accepting invitations
- Declining invitations
- Getting user context for routing
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
import logging

from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.db.models.user import User
from app.services.invitation_service import InvitationService
from app.schemas.invitation import (
    InvitationResponse,
    InvitationListResponse,
    AcceptInvitationResponse,
    DeclineInvitationRequest,
    DeclineInvitationResponse,
    UserContextResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/pending", response_model=InvitationListResponse)
def get_pending_invitations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all pending invitations for current user.

    Finds invitations matching user's email address that are:
    - Status: pending
    - Not expired
    - Case-insensitive email match

    Returns:
        List of pending invitations with target details
    """
    invitation_service = InvitationService(db)

    try:
        # Get pending invitations
        invitations = invitation_service.get_pending_invitations(current_user.email)

        # Populate target names
        invitation_responses = []
        for invitation in invitations:
            _, target_name = invitation_service.get_invitation_with_target_name(invitation)

            # Get inviter email if available
            inviter_email = None
            if invitation.inviter:
                inviter_email = invitation.inviter.email

            # For v1, target_id is company_id (no redundant field)
            target_id = invitation.company_id if invitation.target_type == "company" else invitation.group_id

            invitation_responses.append(InvitationResponse(
                id=invitation.id,
                email=invitation.email,
                target_type=invitation.target_type,
                target_id=target_id,
                target_name=target_name,
                role=invitation.role,
                is_admin=invitation.is_admin,
                can_edit=invitation.can_edit,
                can_view=invitation.can_view,
                inviter_email=inviter_email,
                status=invitation.status,
                expires_at=invitation.expires_at,
                created_at=invitation.created_at
            ))

        return InvitationListResponse(
            invitations=invitation_responses,
            count=len(invitation_responses)
        )

    except Exception as e:
        logger.error(f"Failed to get pending invitations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve invitations"
        )


@router.post("/{invitation_id}/accept", response_model=AcceptInvitationResponse)
def accept_invitation(
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Accept an invitation.

    Process:
    1. Validate invitation exists and is pending
    2. Validate email match
    3. Create appropriate membership (UserCompany or GroupMember)
    4. Mark invitation as accepted
    5. Audit log the acceptance

    Args:
        invitation_id: UUID of invitation to accept
        current_user: Authenticated user
        db: Database session

    Returns:
        Success response with membership details

    Raises:
        404: Invitation not found
        400: Invitation expired or invalid state
        403: Email mismatch
    """
    invitation_service = InvitationService(db)

    try:
        target_type, target_id, membership_id = invitation_service.accept_invitation(
            invitation_id=invitation_id,
            user=current_user
        )

        return AcceptInvitationResponse(
            success=True,
            message="Invitation accepted successfully",
            membership_id=membership_id,
            target_type=target_type,
            target_id=target_id
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to accept invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to accept invitation"
        )


@router.post("/{invitation_id}/decline", response_model=DeclineInvitationResponse)
def decline_invitation(
    invitation_id: UUID,
    request_data: DeclineInvitationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Decline an invitation.

    Process:
    1. Validate invitation exists and is pending
    2. Validate email match
    3. Mark invitation as declined
    4. Audit log the decline with optional reason

    Args:
        invitation_id: UUID of invitation to decline
        request_data: Decline request (optional reason)
        current_user: Authenticated user
        db: Database session

    Returns:
        Success response

    Raises:
        404: Invitation not found
        400: Invitation invalid state
        403: Email mismatch
    """
    invitation_service = InvitationService(db)

    try:
        invitation_service.decline_invitation(
            invitation_id=invitation_id,
            user=current_user,
            reason=request_data.reason
        )

        return DeclineInvitationResponse(
            success=True,
            message="Invitation declined"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to decline invitation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decline invitation"
        )


@router.get("/context", response_model=UserContextResponse)
def get_user_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user context for routing decisions.

    Used by frontend to determine:
    - Whether to show PostAuthSetup
    - Whether user has pending invitations
    - Company count for dashboard navigation

    Returns:
        UserContextResponse with routing metadata

    This endpoint is called after login/OAuth callback to determine
    where to redirect the user.
    """
    invitation_service = InvitationService(db)

    try:
        context = invitation_service.get_user_context(current_user)

        return UserContextResponse(
            has_company=context["has_company"],
            company_count=context["company_count"],
            pending_invitations=context["pending_invitations"],
            requires_setup=context["requires_setup"]
        )

    except Exception as e:
        logger.error(f"Failed to get user context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user context"
        )

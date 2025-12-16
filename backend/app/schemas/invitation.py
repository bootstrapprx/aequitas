"""
Invitation schemas for request/response validation.

Handles invitation discovery, acceptance, and decline flows.
"""
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID


class InvitationResponse(BaseModel):
    """
    Response schema for an invitation.

    NOTE: Uses company_id/group_id directly (no redundant target_id).
    For v1, only company invitations are supported.
    """

    id: UUID
    email: EmailStr
    target_type: Literal["company", "group"]
    target_id: UUID = Field(
        ...,
        description="ID of company or group (company_id for v1)"
    )
    target_name: Optional[str] = Field(
        None,
        description="Name of company or group (populated by API)"
    )
    role: str
    is_admin: bool
    can_edit: bool
    can_view: bool
    inviter_email: Optional[str] = None
    status: str
    expires_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationListResponse(BaseModel):
    """List of pending invitations."""

    invitations: list[InvitationResponse]
    count: int


class AcceptInvitationRequest(BaseModel):
    """Request to accept an invitation."""

    # No body needed - invitation ID in path


class AcceptInvitationResponse(BaseModel):
    """Response after accepting an invitation."""

    success: bool
    message: str
    membership_id: UUID = Field(..., description="ID of created membership record")
    target_type: Literal["company", "group"]
    target_id: UUID


class DeclineInvitationRequest(BaseModel):
    """Request to decline an invitation."""

    reason: Optional[str] = Field(None, description="Optional reason for declining")


class DeclineInvitationResponse(BaseModel):
    """Response after declining an invitation."""

    success: bool
    message: str


class UserContextResponse(BaseModel):
    """User context for routing decisions."""

    has_company: bool = Field(..., description="Whether user has access to any companies")
    company_count: int = Field(..., description="Number of companies user has access to")
    pending_invitations: int = Field(..., description="Number of pending invitations")
    requires_setup: bool = Field(..., description="Whether user needs to complete setup")


class CreateInvitationRequest(BaseModel):
    """Request to create a new invitation."""

    email: EmailStr
    target_type: Literal["company", "group"]
    target_id: UUID
    role: str = "member"
    is_admin: bool = False
    can_edit: bool = True
    can_view: bool = True
    expires_days: int = Field(30, ge=1, le=365, description="Days until invitation expires")


class CreateInvitationResponse(BaseModel):
    """Response after creating an invitation."""

    success: bool
    invitation_id: UUID
    message: str

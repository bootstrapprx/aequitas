"""
Schemas for Users Management module.
Handles CRUD operations for users with company assignments and permissions.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class CompanyInfo(BaseModel):
    """Basic company information for user displays."""
    id: UUID
    name: str
    ucid: str
    is_admin: bool = False  # Is the user an admin of this company?

    class Config:
        from_attributes = True


class UserListItem(BaseModel):
    """User information for listing in tables."""
    id: UUID
    email: EmailStr
    user_uid: str
    is_active: bool
    is_superuser: bool
    companies: List[CompanyInfo] = Field(default_factory=list)
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserDetail(BaseModel):
    """Detailed user information including all relationships."""
    id: UUID
    email: EmailStr
    user_uid: str
    is_active: bool
    is_superuser: bool
    role: str
    preferred_company_id: Optional[UUID] = None
    companies: List[CompanyInfo] = Field(default_factory=list)
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CompanyRoleAssignment(BaseModel):
    """Company assignment with role information."""
    company_id: UUID
    is_admin: bool = False
    can_edit: bool = True
    can_view: bool = True


class UserCreateRequest(BaseModel):
    """Request schema for creating a new user."""
    email: EmailStr
    password: Optional[str] = Field(None, min_length=8, description="Password (optional, will generate if empty)")
    company_ids: List[UUID] = Field(..., min_length=1, description="At least one company required")
    company_roles: Optional[List[CompanyRoleAssignment]] = Field(None, description="Role assignments per company")
    is_active: bool = Field(True, description="User active status")

    @field_validator('company_ids')
    @classmethod
    def validate_company_ids(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one company must be assigned")
        return v


class UserUpdateRequest(BaseModel):
    """Request schema for updating a user."""
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = None
    company_ids: Optional[List[UUID]] = None
    company_roles: Optional[List[CompanyRoleAssignment]] = None
    password: Optional[str] = Field(None, min_length=8, description="New password (optional)")

    @field_validator('company_ids')
    @classmethod
    def validate_company_ids(cls, v):
        if v is not None and len(v) == 0:
            raise ValueError("Cannot remove all company assignments (must have at least one)")
        return v


class UserCreateResponse(BaseModel):
    """Response after creating a user."""
    user: UserDetail
    temporary_password: Optional[str] = Field(None, description="Generated temporary password if applicable")

    class Config:
        from_attributes = True


class UserDeactivateRequest(BaseModel):
    """Request schema for deactivating a user."""
    reason: Optional[str] = Field(None, description="Reason for deactivation")


class UserPasswordResetRequest(BaseModel):
    """Request schema for resetting user password."""
    new_password: str = Field(..., min_length=8, description="New password")


class UserBatchActionRequest(BaseModel):
    """Request schema for batch actions on users."""
    user_ids: List[UUID] = Field(..., min_length=1)
    action: str = Field(..., description="Action to perform: 'deactivate', 'activate', 'delete'")


class UsersFilterParams(BaseModel):
    """Filter parameters for user listing."""
    company_id: Optional[UUID] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    search: Optional[str] = Field(None, description="Search by email")
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)

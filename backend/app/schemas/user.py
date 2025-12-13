from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from datetime import datetime
from uuid import UUID

# User schemas
class UserBase(BaseModel):
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    company_ids: Optional[list[UUID]] = Field(None, description="List of company IDs to assign user to")
    is_initial_signup: Optional[bool] = Field(False, description="True if this is initial sign-up (create new company)")
    company_name: Optional[str] = Field(None, description="Company name for initial sign-up")

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None

class UserResponse(UserBase):
    id: UUID
    user_uid: str
    is_active: bool
    is_superuser: bool
    role: str
    preferred_company_id: Optional[UUID] = None
    force_password_reset: bool
    created_at: datetime
    updated_at: datetime
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True


# Council Member (Super User) schemas
class CouncilMemberCreate(BaseModel):
    """
    Schema for creating a Council Member (Super User).

    SECURITY NOTES:
    - Only accessible to existing Council Members
    - Requires strict password policy validation
    - Creates user with elevated privileges
    - Forces password reset on first login
    """
    email: EmailStr = Field(..., description="Email address for the Council Member")
    password: Optional[str] = Field(
        None,
        min_length=12,
        description="Password (auto-generated if not provided). Must meet strict policy."
    )
    full_name: Optional[str] = Field(None, description="Full name of the Council Member")

    @validator('email')
    def validate_email_domain(cls, v):
        """Optional: Enforce email domain restrictions for Council Members."""
        # You can add domain restrictions here if needed
        # Example: if not v.endswith('@aequitas.local'):
        #     raise ValueError('Council Members must use company email domain')
        return v


class CouncilMemberCreateResponse(BaseModel):
    """
    Response schema for Council Member creation.

    CRITICAL SECURITY:
    - This is the ONLY time the password is ever shown
    - Password must be securely communicated to the new Council Member
    - Frontend should display password in a secure manner and confirm it was saved
    """
    user: UserResponse
    temporary_password: str = Field(
        ...,
        description="IMPORTANT: This password will only be shown once. Save it securely."
    )
    password_policy: str = Field(
        ...,
        description="Description of password requirements"
    )
    force_password_reset: bool = Field(
        True,
        description="User must change password on first login"
    )
    message: str = Field(
        default="Council Member account created successfully. Password must be changed on first login.",
        description="Success message with instructions"
    )


class PasswordChangeRequest(BaseModel):
    """Schema for password change (including forced resets)."""
    current_password: str = Field(..., description="Current password for verification")
    new_password: str = Field(..., min_length=8, description="New password")

    @validator('new_password')
    def passwords_must_differ(cls, v, values):
        """Ensure new password is different from current password."""
        if 'current_password' in values and v == values['current_password']:
            raise ValueError('New password must be different from current password')
        return v


class PasswordChangeResponse(BaseModel):
    """Response for password change operation."""
    success: bool
    message: str
    force_password_reset: bool = Field(
        default=False,
        description="Whether user still needs to reset password"
    )

# Authentication schemas
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    company_ids: Optional[list[UUID]] = None
    preferred_company_id: Optional[UUID] = None

class TokenData(BaseModel):
    user_id: Optional[UUID] = None
    email: Optional[str] = None
    company_ids: Optional[list[UUID]] = None
    preferred_company_id: Optional[UUID] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

# Registration schemas
class RegistrationRequest(BaseModel):
    """Request schema for user registration."""
    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters")
    company_name: str = Field(..., min_length=2, description="Name for the new company")
    register_type: Literal["free", "paid"] = Field("free", description="Registration type")
    plan: Literal["starter", "pro"] = Field("starter", description="Subscription plan")
    cuid: Optional[str] = Field(None, description="Existing company UCID to join (optional)")

class RegistrationConfirmRequest(BaseModel):
    """Request schema for confirming pending registration."""
    token: str = Field(..., description="Confirmation token from pending registration")

class CheckoutSessionResponse(BaseModel):
    """Response schema for Stripe checkout session."""
    checkout_url: str
    session_id: str
    pending_token: str

# Database configuration schemas
class DatabaseConfigBase(BaseModel):
    db_host: str = Field(..., description="Database host")
    db_port: str = Field(default="5432", description="Database port")
    db_name: str = Field(..., description="Database name")
    db_user: str = Field(..., description="Database user")
    db_password: str = Field(..., description="Database password")

class DatabaseConfigCreate(DatabaseConfigBase):
    pass

class DatabaseConfigResponse(BaseModel):
    id: UUID
    user_id: UUID
    db_host: str
    db_port: str
    db_name: str
    db_user: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True



from pydantic import BaseModel, EmailStr, Field
from typing import Optional
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
    preferred_company_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

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


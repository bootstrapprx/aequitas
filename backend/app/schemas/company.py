from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, field_validator
from app.db.models.company import SubscriptionType

def _normalize_optional_email(value):
    """Convert empty/whitespace-only email strings to None to satisfy EmailStr."""
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == "":
        return None
    return value

class CompanyBase(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def set_empty_email_to_none(cls, v):
        return _normalize_optional_email(v)

class CompanyCreate(CompanyBase):
    subscription_type: Optional[SubscriptionType] = SubscriptionType.STRIPE

class CompanyInactivate(BaseModel):
    confirmation: str

class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    tax_id: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None

    @field_validator("email", mode="before")
    @classmethod
    def set_empty_email_to_none(cls, v):
        return _normalize_optional_email(v)

class CompanyResponse(CompanyBase):
    id: UUID
    ucid: str
    subscription_type: SubscriptionType
    
    class Config:
        from_attributes = True

class CompanyChartStatus(BaseModel):
    master_chart_loaded: bool
    company_chart_initialized: bool
    account_count: int
    mapping_coverage: float
    onboarding_status: str

    class Config:
        from_attributes = True

class DashboardActivity(BaseModel):
    id: UUID
    user: str
    action: str
    timestamp: datetime
    type: str  # 'mapping', 'user', 'export', 'sync', 'info', 'success', 'warning'

class CompanyDashboardStats(BaseModel):
    chart_status: CompanyChartStatus
    active_users_count: int
    pending_reviews_count: int
    recent_activity: list[DashboardActivity]
    account_distribution: dict[str, int]

"""
Pydantic schemas for Phase 5 Company Onboarding Wizard.

CANONICAL REFERENCE:
- docs/canonical/PHASE_5_ONBOARDING_GUIDE.md

These schemas enforce the wizard state machine and validation rules.
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from app.db.models.enums import OnboardingStatus, KernelLayer


# ============================================================================
# Onboarding Status & Progress
# ============================================================================

class OnboardingStatusResponse(BaseModel):
    """Current onboarding wizard state and progress."""

    company_id: UUID
    company_name: str
    onboarding_status: OnboardingStatus
    current_step: int = Field(..., ge=0, le=8)
    can_resume: bool
    is_locked: bool  # Multi-session lock
    locked_by_session: Optional[UUID] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Company details snapshot for resume
    trade_name: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    legal_nature: Optional[str] = None
    economic_activity: Optional[str] = None
    is_standalone: Optional[bool] = None
    kernel_version: Optional[str] = None
    kernel_layer: Optional[KernelLayer] = None

    # Step completion flags
    step_0_welcome_seen: bool = False
    step_1_company_details_complete: bool = False
    step_2_company_type_complete: bool = False
    step_3_template_selected: bool = False
    step_4_modules_complete: bool = False
    step_5_scope_complete: bool = False
    step_6_account_review_complete: bool = False
    step_7_fiscal_periods_complete: bool = False
    step_8_activated: bool = False

    class Config:
        from_attributes = True


# ============================================================================
# Step 1: Company Details
# ============================================================================

class CompanyDetailsRequest(BaseModel):
    """Step 1: Company Details form submission."""

    name: str = Field(..., min_length=1, max_length=255)
    trade_name: Optional[str] = Field(None, max_length=255)
    country: str = Field(..., min_length=2, max_length=2)  # ISO 3166-1 alpha-2
    currency: str = Field(..., min_length=3, max_length=3)  # ISO 4217
    timezone: str = Field(..., min_length=1)  # IANA timezone

    legal_nature: Optional[str] = None
    economic_activity: Optional[str] = None

    # Optional contact info
    email: Optional[str] = None
    phone: Optional[str] = None

    @field_validator('country')
    @classmethod
    def validate_country(cls, v):
        """Validate country code format."""
        if not v.isupper():
            raise ValueError('Country code must be uppercase (e.g., US, CA, GB)')
        return v

    @field_validator('currency')
    @classmethod
    def validate_currency(cls, v):
        """Validate currency code format."""
        if not v.isupper():
            raise ValueError('Currency code must be uppercase (e.g., USD, CAD, GBP)')
        return v


class CompanyDetailsResponse(BaseModel):
    """Step 1 completion response."""

    success: bool
    message: str
    company_id: UUID
    current_step: int
    next_step: int


# ============================================================================
# Step 2: Company Type & Activity (New Step)
# ============================================================================

class CompanyTypeRequest(BaseModel):
    """Step 2: Define company legal nature and activity."""
    
    legal_nature: str = Field(..., description="LLC, Corporation, etc.")
    economic_activity: str = Field(..., description="Commerce, Services, etc.")

class CompanyTypeResponse(BaseModel):
    success: bool
    message: str
    current_step: int
    next_step: int


# ============================================================================
# Step 2b/3 (Legacy 2): Template Selection
# ============================================================================


# ============================================================================
# Step 2: Template Selection
# ============================================================================

class TemplateSelectionRequest(BaseModel):
    """Step 2: Template selection with confirmation."""

    template_id: UUID
    confirmed: bool = Field(..., description="User must confirm template cannot be changed")

    @field_validator('confirmed')
    @classmethod
    def validate_confirmation(cls, v):
        """Ensure user confirmed the irreversible choice."""
        if not v:
            raise ValueError('You must confirm that you understand this choice cannot be changed.')
        return v


class TemplateSelectionResponse(BaseModel):
    """Step 2 completion response."""

    success: bool
    message: str
    template_id: UUID
    template_name: str
    current_step: int
    next_step: int


# ============================================================================
# Step 3: Chart Materialization
# ============================================================================

class ChartMaterializationRequest(BaseModel):
    """Step 3: Trigger chart materialization (no additional data needed)."""

    confirm_proceed: bool = Field(..., description="User confirms chart creation")


class ChartMaterializationProgress(BaseModel):
    """Step 3: Progress indicator during materialization."""

    status: str  # "in_progress", "completed", "failed"
    progress_percent: int = Field(..., ge=0, le=100)
    current_action: str
    accounts_created: int = 0
    total_accounts: int = 0


class ChartMaterializationResponse(BaseModel):
    """Step 3 completion response."""

    success: bool
    message: str
    accounts_created: int
    mandatory_accounts: int
    optional_accounts: int
    current_step: int
    next_step: int


# ============================================================================
# Step 4: Module Selection (New Step)
# ============================================================================

class ModuleSelectionRequest(BaseModel):
    """Step 4: Select active modules."""
    
    modules: List[str] = Field(..., description="List of module IDs (e.g., ['INVOICING', 'PAYROLL'])")

class ModuleSelectionResponse(BaseModel):
    success: bool
    message: str
    current_step: int
    next_step: int


# ============================================================================
# Step 5: Organization Scope (New Step)
# ============================================================================

class OrganizationScopeRequest(BaseModel):
    """Step 5: Define organization structure."""
    
    is_standalone: bool = Field(..., description="True if standalone, False if part of a group")
    # Future: Parent company ID, etc.

class OrganizationScopeResponse(BaseModel):
    success: bool
    message: str
    current_step: int
    next_step: int


# ============================================================================
# Step 6: Account Review & Customization (Legacy 4)
# ============================================================================

class AccountCustomization(BaseModel):
    """Individual account customization action."""

    account_id: UUID
    action: str = Field(..., pattern="^(rename|disable|enable)$")
    new_name: Optional[str] = Field(None, max_length=255)


class CustomAccountCreate(BaseModel):
    """Create a new custom account."""

    parent_id: Optional[UUID] = None
    code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    account_type: str  # Asset, Liability, Equity, Revenue, Expense
    normal_balance: str  # Debit, Credit


class AccountReviewRequest(BaseModel):
    """Step 4: Account customization submission."""

    customizations: List[AccountCustomization] = []
    custom_accounts: List[CustomAccountCreate] = []
    finalized: bool = Field(..., description="User confirms chart is ready")


class AccountReviewResponse(BaseModel):
    """Step 4 completion response."""

    success: bool
    message: str
    total_accounts: int
    mandatory_accounts: int
    custom_accounts: int
    disabled_accounts: int
    current_step: int
    next_step: int


# ============================================================================
# Step 7: Fiscal Periods
# ============================================================================

class FiscalPeriodCreate(BaseModel):
    """Individual fiscal period definition."""

    name: str = Field(..., min_length=1, max_length=100)
    start_date: datetime
    end_date: datetime
    period_type: str = Field(..., pattern="^(MONTH|QUARTER|YEAR)$")
    is_open: bool = True  # At least one must be open

    @field_validator('end_date')
    @classmethod
    def validate_dates(cls, v, info):
        """Ensure end_date is after start_date."""
        if 'start_date' in info.data and v <= info.data['start_date']:
            raise ValueError('End date must be after start date')
        return v


class FiscalPeriodSetupRequest(BaseModel):
    """Step 7: Fiscal periods setup."""

    fiscal_year_start: str = Field(..., pattern="^(01|02|03|04|05|06|07|08|09|10|11|12)-01$")  # MM-DD format
    periods: List[FiscalPeriodCreate] = Field(..., min_length=1)

    @field_validator('periods')
    @classmethod
    def validate_periods(cls, v):
        """Ensure at least one OPEN period exists."""
        if not any(p.is_open for p in v):
            raise ValueError('At least one fiscal period must be OPEN')

        # Check for overlapping dates
        sorted_periods = sorted(v, key=lambda p: p.start_date)
        for i in range(len(sorted_periods) - 1):
            if sorted_periods[i].end_date >= sorted_periods[i + 1].start_date:
                raise ValueError('Fiscal periods cannot overlap')

        return v


class FiscalPeriodSetupResponse(BaseModel):
    """Step 7 completion response."""

    success: bool
    message: str
    periods_created: int
    open_periods: int
    current_step: int
    next_step: int


# ============================================================================
# Step 8: Activation
# ============================================================================

class ActivationRequest(BaseModel):
    """Step 8: Final activation (point of no return)."""

    confirmed: bool = Field(..., description="User confirms activation")
    acknowledgment_text: str = Field(
        ...,
        description="User must type confirmation phrase"
    )
    joint_stock_amount: Optional[Decimal] = Field(
        None,
        description="Initial joint-stock (share capital) balance to record"
    )

    @field_validator('confirmed')
    @classmethod
    def validate_confirmation(cls, v):
        """Ensure user confirmed activation."""
        if not v:
            raise ValueError('You must confirm activation to proceed')
        return v

    @field_validator('acknowledgment_text')
    @classmethod
    def validate_acknowledgment(cls, v):
        """Ensure user typed the confirmation phrase."""
        expected = "I understand that accounting will be activated"
        if v.strip().lower() != expected.lower():
            raise ValueError(f'Please type exactly: "{expected}"')
        return v

    @field_validator('joint_stock_amount')
    @classmethod
    def validate_joint_stock_amount(cls, v):
        """Ensure joint-stock amount is not negative."""
        if v is not None and v < 0:
            raise ValueError('Joint-stock amount cannot be negative')
        return v


class ActivationResponse(BaseModel):
    """Step 8 completion response."""

    success: bool
    message: str
    company_id: UUID
    company_name: str
    activated_at: datetime
    total_accounts: int
    open_periods: int
    next_actions: List[str]  # Suggested next steps


# ============================================================================
# Session Lock Management
# ============================================================================

class SessionLockRequest(BaseModel):
    """Request to acquire session lock."""

    session_id: UUID
    force: bool = False


class SessionLockResponse(BaseModel):
    """Session lock status."""

    locked: bool
    session_id: Optional[UUID] = None
    locked_at: Optional[datetime] = None
    lock_expires_at: Optional[datetime] = None


# ============================================================================
# Error Responses
# ============================================================================

class OnboardingError(BaseModel):
    """User-friendly onboarding error."""

    error_code: str
    message: str  # Human-readable, non-technical
    field: Optional[str] = None  # Field-level error
    suggested_action: Optional[str] = None


# Export
__all__ = [
    "OnboardingStatusResponse",
    "CompanyDetailsRequest",
    "CompanyDetailsResponse",
    "CompanyTypeRequest",
    "CompanyTypeResponse",
    "TemplateSelectionRequest",
    "TemplateSelectionResponse",
    "ChartMaterializationRequest",
    "ChartMaterializationProgress",
    "ChartMaterializationResponse",
    "ModuleSelectionRequest",
    "ModuleSelectionResponse",
    "OrganizationScopeRequest",
    "OrganizationScopeResponse",
    "AccountCustomization",
    "CustomAccountCreate",
    "AccountReviewRequest",
    "AccountReviewResponse",
    "FiscalPeriodCreate",
    "FiscalPeriodSetupRequest",
    "FiscalPeriodSetupResponse",
    "ActivationRequest",
    "ActivationResponse",
    "SessionLockRequest",
    "SessionLockResponse",
    "OnboardingError",
]

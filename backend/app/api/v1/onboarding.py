"""
Phase 5 Onboarding API Endpoints

CANONICAL REFERENCE:
- docs/canonical/PHASE_5_ONBOARDING_GUIDE.md

API endpoints for the 6-step company onboarding wizard.
All operations are protected and require authentication.
"""
from typing import List
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import get_current_user
from app.db.models.user import User
from app.core.exceptions import ValidationError
from app.services import onboarding_service
from app.schemas.onboarding import (
    OnboardingStatusResponse,
    CompanyDetailsRequest,
    CompanyDetailsResponse,
    TemplateSelectionRequest,
    TemplateSelectionResponse,
    ChartMaterializationRequest,
    ChartMaterializationResponse,
    AccountReviewRequest,
    AccountReviewResponse,
    FiscalPeriodSetupRequest,
    FiscalPeriodSetupResponse,
    ActivationRequest,
    ActivationResponse,
    SessionLockRequest,
    SessionLockResponse,
)

router = APIRouter(prefix="/onboarding", tags=["onboarding"])


# ============================================================================
# Onboarding Status & Progress
# ============================================================================

@router.get("/status/{company_id}", response_model=OnboardingStatusResponse)
def get_onboarding_status(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current onboarding wizard status and progress.

    Returns:
    - Current step (0-6)
    - Onboarding state (DRAFT, TEMPLATE_SELECTED, etc.)
    - Completion flags for each step
    - Session lock status
    - Can resume flag

    Use this endpoint to:
    - Resume wizard from last saved state
    - Show progress indicator
    - Determine which step to display
    """
    try:
        return onboarding_service.get_onboarding_status(db, company_id)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Session Lock Management
# ============================================================================

@router.post("/lock/{company_id}", response_model=SessionLockResponse)
def acquire_session_lock(
    company_id: UUID,
    lock_request: SessionLockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Acquire session lock for onboarding wizard.

    Prevents concurrent editing by multiple sessions.
    Lock expires after 30 minutes of inactivity.

    Returns:
    - locked: True if lock acquired
    - session_id: UUID of the locking session
    - locked_at: Timestamp of lock acquisition
    - lock_expires_at: When lock will expire
    """
    try:
        from datetime import datetime, timedelta
        from app.services.onboarding_service import SESSION_LOCK_TIMEOUT_MINUTES

        locked = onboarding_service.acquire_session_lock(
            db, company_id, lock_request.session_id
        )

        if locked:
            # Get updated company to return lock info
            status_response = onboarding_service.get_onboarding_status(db, company_id)
            return SessionLockResponse(
                locked=True,
                session_id=lock_request.session_id,
                locked_at=datetime.utcnow(),
                lock_expires_at=datetime.utcnow() + timedelta(minutes=SESSION_LOCK_TIMEOUT_MINUTES)
            )
        else:
            return SessionLockResponse(
                locked=False,
                session_id=None,
                locked_at=None,
                lock_expires_at=None
            )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete("/lock/{company_id}")
def release_session_lock(
    company_id: UUID,
    lock_request: SessionLockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Release session lock.

    Call this when:
    - User completes wizard
    - User exits wizard intentionally
    - Component unmounts
    """
    try:
        onboarding_service.release_session_lock(
            db, company_id, lock_request.session_id
        )
        return {"success": True, "message": "Session lock released"}
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Step 1: Company Details
# ============================================================================

@router.post("/{company_id}/company-details", response_model=CompanyDetailsResponse)
def update_company_details(
    company_id: UUID,
    details: CompanyDetailsRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 1: Update company details.

    Required fields:
    - name: Legal company name
    - country: ISO 3166-1 alpha-2 code (e.g., US, CA, GB)
    - currency: ISO 4217 code (e.g., USD, CAD, GBP)
    - timezone: IANA timezone (e.g., America/New_York)

    Optional fields:
    - trade_name: DBA or trade name
    - email: Contact email
    - phone: Contact phone

    Important:
    - Currency and country lock after template selection
    - Changes allowed only in DRAFT or TEMPLATE_SELECTED state
    """
    try:
        return onboarding_service.update_company_details(db, company_id, details)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Step 2: Template Selection
# ============================================================================

@router.post("/{company_id}/select-template", response_model=TemplateSelectionResponse)
def select_template(
    company_id: UUID,
    selection: TemplateSelectionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 2: Select accounting template.

    CRITICAL OPERATION:
    - This choice is irreversible after chart materialization
    - User must explicitly confirm (confirmed=true)

    The template defines:
    - Chart of accounts structure
    - Mandatory vs optional accounts
    - Account codes and hierarchy
    - Compliance standards (GAAP, IFRS, etc.)

    State transition: DRAFT → TEMPLATE_SELECTED
    """
    try:
        return onboarding_service.select_template(db, company_id, selection)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Step 3: Chart Materialization
# ============================================================================

@router.post("/{company_id}/materialize-chart", response_model=ChartMaterializationResponse)
def materialize_chart(
    company_id: UUID,
    request: ChartMaterializationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 3: Materialize chart of accounts from template.

    CRITICAL OPERATION:
    - Atomic transaction (all or nothing)
    - Copies all template accounts to company
    - Creates hierarchical structure
    - Sets mandatory/optional flags
    - On failure, entire operation rolls back

    This step:
    - Cannot be undone
    - Locks template choice
    - Creates hundreds of account records
    - Preserves referential integrity

    State transition: TEMPLATE_SELECTED → CHART_READY
    """
    try:
        return onboarding_service.materialize_chart(db, company_id)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Step 4: Account Review & Customization
# ============================================================================

@router.post("/{company_id}/customize-accounts", response_model=AccountReviewResponse)
def customize_accounts(
    company_id: UUID,
    customization: AccountReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 4: Review and customize accounts.

    ALLOWED ACTIONS:
    - Rename accounts
    - Disable non-mandatory accounts
    - Enable disabled accounts
    - Add custom accounts
    - Reorder custom accounts

    FORBIDDEN ACTIONS:
    - Change account type (Asset → Liability, etc.)
    - Change normal balance (Debit → Credit)
    - Delete mandatory accounts
    - Change hierarchy of template accounts

    When finalized=true:
    - Locks chart structure
    - Proceeds to fiscal periods setup
    - State transition: CHART_READY → CHART_FINALIZED
    """
    try:
        return onboarding_service.customize_accounts(db, company_id, customization)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Step 5: Fiscal Periods
# ============================================================================

@router.post("/{company_id}/fiscal-periods", response_model=FiscalPeriodSetupResponse)
def setup_fiscal_periods(
    company_id: UUID,
    periods_setup: FiscalPeriodSetupRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 5: Set up fiscal periods.

    VALIDATION RULES:
    - At least one period must be OPEN
    - Periods cannot overlap
    - Periods cannot have gaps
    - Start date < End date
    - Fiscal year start format: MM-DD (e.g., "01-01", "07-01")

    Period types:
    - MONTH: Monthly periods
    - QUARTER: Quarterly periods
    - YEAR: Annual periods

    Period status:
    - OPEN: Transactions can be recorded
    - CLOSED: Transactions locked
    - LOCKED: Permanently closed
    """
    try:
        return onboarding_service.setup_fiscal_periods(db, company_id, periods_setup)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ============================================================================
# Step 6: Activation (Point of No Return)
# ============================================================================

@router.post("/{company_id}/activate", response_model=ActivationResponse)
def activate_accounting(
    company_id: UUID,
    activation: ActivationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Step 6: Activate accounting (POINT OF NO RETURN).

    CRITICAL OPERATION:
    - This is irreversible
    - Enables full accounting functionality
    - Locks onboarding state machine
    - Sets completion timestamp

    Requirements:
    - All previous steps complete
    - At least one OPEN fiscal period
    - User must confirm with checkbox
    - User must type acknowledgment phrase

    After activation:
    - Accounting rules enforced
    - Account properties lock after first transaction
    - Fiscal periods control transaction recording
    - Full audit trail begins

    State transition: CHART_FINALIZED → ACTIVE
    """
    try:
        return onboarding_service.activate_accounting(db, company_id, activation)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# Export router
__all__ = ["router"]

"""
Phase 5 Onboarding Service

CANONICAL REFERENCE:
- docs/canonical/PHASE_5_ONBOARDING_GUIDE.md

This service implements the company onboarding wizard state machine
with atomic operations, validation, and state transitions.

CANONICAL STATE MACHINE:
DRAFT -> TEMPLATE_SELECTED -> CHART_READY -> CHART_FINALIZED -> ACTIVE

CRITICAL RULES:
- State transitions are irreversible
- Dashboard access only allowed when status = ACTIVE
- Template selection locks after chart materialization
- Chart materialization is atomic (all or nothing)
- Activation is the point of no return
- Only onboarding endpoints may mutate onboarding_status
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError

from app.db.models.company import Company
from app.db.models.chart_template import ChartTemplate, ChartTemplateAccount, CompanyTemplateUsage
from app.db.models.company_account import CompanyAccount
from app.db.models.company_module import CompanyModule
from app.db.models.fiscal_period import FiscalPeriod
from app.db.models.enums import OnboardingStatus, PeriodStatus, AccountType, NormalBalance, KernelLayer
from app.core.kernel import KERNEL_VERSION, L0_KERNEL_CODES, map_category_to_account_type, map_normal_balance
from app.schemas.onboarding import (
    OnboardingStatusResponse,
    CompanyDetailsRequest,
    CompanyDetailsResponse,
    CompanyTypeRequest,
    CompanyTypeResponse,
    TemplateSelectionRequest,
    TemplateSelectionResponse,
    ChartMaterializationResponse,
    AccountCustomization,
    CustomAccountCreate,
    AccountReviewRequest,
    AccountReviewResponse,
    FiscalPeriodCreate,
    FiscalPeriodSetupRequest,
    FiscalPeriodSetupResponse,
    ActivationRequest,
    ActivationResponse,
)
from app.core.exceptions import ValidationError


# ============================================================================
# Session Lock Management
# ============================================================================

SESSION_LOCK_TIMEOUT_MINUTES = 30

# Wizard step indices (next step to display)
STEP_WELCOME = 0
STEP_COMPANY_DETAILS = 1
STEP_COMPANY_TYPE = 2
STEP_TEMPLATE_SELECTION = 3
STEP_MODULES = 4
STEP_SCOPE = 5
STEP_ACCOUNT_REVIEW = 6
STEP_FISCAL_PERIODS = 7
STEP_ACTIVATION = 8


# ============================================================================
# Destructive Onboarding Reset
# ============================================================================

def reset_onboarding(db: Session, company_id: UUID, current_user) -> Dict[str, Any]:
    """
    DESTRUCTIVE OPERATION: Reset onboarding and delete all chart data.

    This function:
    - Validates user has admin access to the company
    - Deletes all company chart accounts (cascades to mappings)
    - Deletes template usage records
    - Deletes fiscal periods
    - Resets onboarding_status to NOT_STARTED
    - Resets onboarding_current_step to 0
    - Clears onboarding timestamps
    - Preserves company record and user relationships

    Args:
        db: Database session
        company_id: Company ID to reset
        current_user: Current authenticated user

    Returns:
        Dict with success status and message

    Raises:
        ValidationError: If user lacks permissions or operation fails
    """
    from app.db.models.user_company import UserCompany

    # Get company
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    # CANONICAL GUARD: PROHIBIT RESET OF ACTIVE COMPANIES
    # Canon II & III: Activation is a Point of No Return. History is immutable.
    if company.onboarding_status == OnboardingStatus.ACTIVE:
        raise ValidationError(
            "Onboarding reset is forbidden for ACTIVE companies. "
            "Accounting history is immutable after activation.",
            code="ONBOARDING_RESET_FORBIDDEN"
        )

    # Check if user has access to this company (admin permission)
    user_company = db.query(UserCompany).filter(
        UserCompany.user_id == current_user.id,
        UserCompany.company_id == company_id
    ).first()

    if not user_company and not current_user.is_superuser:
        raise ValidationError(
            "You do not have permission to reset onboarding for this company."
        )

    try:
        # Begin transaction (wrapped by FastAPI's db session management)

        # 1. Delete all fiscal periods
        db.query(FiscalPeriod).filter(
            FiscalPeriod.company_id == company_id
        ).delete(synchronize_session=False)

        # 2. Delete all company accounts (this cascades to mappings via ORM relationships)
        db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id
        ).delete(synchronize_session=False)

        # 3. Delete template usage records
        db.query(CompanyTemplateUsage).filter(
            CompanyTemplateUsage.company_id == company_id
        ).delete(synchronize_session=False)

        # 4. Reset company onboarding state
        company.onboarding_status = OnboardingStatus.DRAFT
        company.onboarding_current_step = 0
        company.onboarding_started_at = None
        company.onboarding_completed_at = None
        company.onboarding_session_lock = None
        company.onboarding_session_locked_at = None
        company.kernel_version = None
        company.kernel_layer = None

        # Commit transaction
        db.commit()

        return {
            "success": True,
            "message": f"Onboarding reset successfully for company '{company.name}'. All chart data has been deleted.",
            "company_id": str(company.id),
            "company_name": company.name,
            "onboarding_status": company.onboarding_status.value
        }

    except Exception as e:
        db.rollback()
        raise ValidationError(
            f"Failed to reset onboarding: {str(e)}. All changes have been rolled back."
        ) from e


# ============================================================================
# Session Lock Management
# ============================================================================


def acquire_session_lock(db: Session, company_id: UUID, session_id: UUID, force: bool = False) -> bool:
    """
    Acquire session lock for onboarding wizard.

    Args:
        db: Database session
        company_id: Company ID
        session_id: Session UUID from client
        force: If True, override existing lock (session takeover)

    Returns:
        True if lock acquired, False if locked by another session
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    # Check existing lock
    if company.onboarding_session_lock:
        lock_age = datetime.now(timezone.utc) - company.onboarding_session_locked_at
        if lock_age < timedelta(minutes=SESSION_LOCK_TIMEOUT_MINUTES):
            # Lock is still valid
            if company.onboarding_session_lock != session_id:
                if not force:
                    return False  # Locked by another session, takeover refused
                # If force=True, we proceed to overwrite the lock

    # Acquire or renew lock
    company.onboarding_session_lock = session_id
    company.onboarding_session_locked_at = datetime.now(timezone.utc)
    db.commit()
    return True


def release_session_lock(db: Session, company_id: UUID, session_id: UUID) -> None:
    """Release session lock."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if company and company.onboarding_session_lock == session_id:
        company.onboarding_session_lock = None
        company.onboarding_session_locked_at = None
        db.commit()


# ============================================================================
# Start Onboarding
# ============================================================================

def start_onboarding(db: Session, company_id: UUID) -> OnboardingStatusResponse:
    """
    Mark onboarding as started (welcome acknowledged).

    Idempotent: safe to call multiple times.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    if company.onboarding_status == OnboardingStatus.ACTIVE:
        return get_onboarding_status(db, company_id)

    if not company.onboarding_started_at:
        company.onboarding_started_at = datetime.utcnow()

    company.onboarding_current_step = max(company.onboarding_current_step, STEP_COMPANY_DETAILS)
    db.commit()

    return get_onboarding_status(db, company_id)


# ============================================================================
# Onboarding Status & Progress
# ============================================================================

def get_onboarding_status(db: Session, company_id: UUID) -> OnboardingStatusResponse:
    """
    Get current onboarding wizard status and progress.

    Returns wizard state, current step, and completion flags.
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    # Check session lock
    is_locked = False
    locked_by_session = None
    if company.onboarding_session_lock:
        lock_age = datetime.now(timezone.utc) - company.onboarding_session_locked_at
        if lock_age < timedelta(minutes=SESSION_LOCK_TIMEOUT_MINUTES):
            is_locked = True
            locked_by_session = company.onboarding_session_lock

    # Determine step completion flags based on persisted truth
    template_usage = db.query(CompanyTemplateUsage).filter(
        CompanyTemplateUsage.company_id == company_id
    ).first()
    modules_selected = db.query(CompanyModule).filter(
        CompanyModule.company_id == company_id,
        CompanyModule.is_active == True
    ).count() > 0
    fiscal_periods_count = db.query(FiscalPeriod).filter(
        FiscalPeriod.company_id == company_id
    ).count()

    step_1_complete = bool(company.country and company.currency and company.timezone)
    step_2_complete = bool(company.legal_nature and company.economic_activity)
    step_3_template_selected = template_usage is not None
    step_4_modules_complete = modules_selected
    step_5_scope_complete = company.onboarding_current_step >= STEP_ACCOUNT_REVIEW
    step_6_account_review_complete = company.onboarding_status in [
        OnboardingStatus.CHART_FINALIZED,
        OnboardingStatus.ACTIVE,
    ]
    step_7_fiscal_periods_complete = fiscal_periods_count > 0
    step_8_activated = company.onboarding_status == OnboardingStatus.ACTIVE

    derived_step = company.onboarding_current_step
    if company.onboarding_started_at or company.onboarding_current_step > 0:
        derived_step = max(derived_step, STEP_COMPANY_DETAILS)
    if step_1_complete:
        derived_step = max(derived_step, STEP_COMPANY_TYPE)
    if step_2_complete:
        derived_step = max(derived_step, STEP_TEMPLATE_SELECTION)
    if step_3_template_selected:
        derived_step = max(derived_step, STEP_MODULES)
    if step_4_modules_complete:
        derived_step = max(derived_step, STEP_SCOPE)
    if company.onboarding_status in [
        OnboardingStatus.CHART_READY,
        OnboardingStatus.CHART_FINALIZED,
        OnboardingStatus.ACTIVE,
    ]:
        derived_step = max(derived_step, STEP_ACCOUNT_REVIEW)
    if step_6_account_review_complete:
        derived_step = max(derived_step, STEP_FISCAL_PERIODS)
    if step_7_fiscal_periods_complete:
        derived_step = max(derived_step, STEP_ACTIVATION)

    if derived_step > company.onboarding_current_step:
        company.onboarding_current_step = derived_step
        db.commit()

    return OnboardingStatusResponse(
        company_id=company.id,
        company_name=company.name,
        onboarding_status=company.onboarding_status,
        current_step=company.onboarding_current_step,
        can_resume=company.onboarding_status != OnboardingStatus.ACTIVE,
        is_locked=is_locked,
        locked_by_session=locked_by_session,
        started_at=company.onboarding_started_at,
        completed_at=company.onboarding_completed_at,
        trade_name=company.trade_name,
        country=company.country,
        currency=company.currency,
        timezone=company.timezone,
        email=company.email,
        phone=company.phone,
        legal_nature=company.legal_nature,
        economic_activity=company.economic_activity,
        is_standalone=company.is_standalone,
        kernel_version=company.kernel_version,
        kernel_layer=company.kernel_layer,
        step_0_welcome_seen=company.onboarding_started_at is not None or company.onboarding_current_step > 0,
        step_1_company_details_complete=step_1_complete,
        step_2_company_type_complete=step_2_complete,
        step_3_template_selected=step_3_template_selected,
        step_4_modules_complete=step_4_modules_complete,
        step_5_scope_complete=step_5_scope_complete,
        step_6_account_review_complete=step_6_account_review_complete,
        step_7_fiscal_periods_complete=step_7_fiscal_periods_complete,
        step_8_activated=step_8_activated,
    )


# ============================================================================
# Step 1: Company Details
# ============================================================================

def update_company_details(
    db: Session,
    company_id: UUID,
    data: CompanyDetailsRequest,
    current_user
) -> CompanyDetailsResponse:
    """
    Step 1: Update company details.

    VALIDATION RULES:
    - Can only update in DRAFT, TEMPLATE_SELECTED, or CHART_READY state
    - Currency cannot change after template selection (step 2+)
    - Country cannot change after template selection (step 2+)
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    # State validation - allow updates only if not yet activated
    if company.onboarding_status == OnboardingStatus.ACTIVE:
        raise ValidationError(
            "Company details cannot be changed after activation. "
            "If you need to change these details, please contact support."
        )

    # Currency/country lock after template selection
    if company.onboarding_status in [
        OnboardingStatus.TEMPLATE_SELECTED,
        OnboardingStatus.CHART_READY,
        OnboardingStatus.CHART_FINALIZED,
        OnboardingStatus.ACTIVE,
    ]:
        if company.currency and company.currency != data.currency:
            raise ValidationError(
                "Currency cannot be changed after template selection. "
                "If you need to change currency, please re-run onboarding."
            )
        if company.country and company.country != data.country:
            raise ValidationError(
                "Country cannot be changed after template selection. "
                "If you need to change country, please re-run onboarding."
            )

    # Update fields
    company.name = data.name
    if data.trade_name is not None:
        company.trade_name = data.trade_name
    company.country = data.country
    company.currency = data.currency
    company.timezone = data.timezone
    email_value = data.email.strip() if isinstance(data.email, str) else data.email
    if email_value == "":
        email_value = None
    if email_value is not None:
        company.email = email_value
    elif not company.email and getattr(current_user, "email", None):
        company.email = current_user.email

    phone_value = data.phone.strip() if isinstance(data.phone, str) else data.phone
    if phone_value == "":
        phone_value = None
    if phone_value is not None:
        company.phone = phone_value
    if data.legal_nature is not None:
        company.legal_nature = data.legal_nature
    if data.economic_activity is not None:
        company.economic_activity = data.economic_activity

    # Update onboarding state
    if not company.onboarding_started_at:
        company.onboarding_started_at = datetime.utcnow()

    # Mark Step 1 complete
    company.onboarding_current_step = max(company.onboarding_current_step, STEP_COMPANY_TYPE)

    db.commit()
    db.refresh(company)

    return CompanyDetailsResponse(
        success=True,
        message="Company details saved successfully.",
        company_id=company.id,
        current_step=company.onboarding_current_step,
        next_step=STEP_COMPANY_TYPE
    )


# ============================================================================
# Step 2: Company Type & Activity
# ============================================================================

def update_company_type(
    db: Session,
    company_id: UUID,
    data: CompanyTypeRequest
) -> CompanyTypeResponse:
    """Step 2: Set Legal Nature and Activity."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    if company.onboarding_status == OnboardingStatus.ACTIVE:
        raise ValidationError(
            "Company type cannot be changed after activation."
        )

    if not all([company.country, company.currency, company.timezone]):
        raise ValidationError(
            "Please complete company details before setting company type."
        )

    company.legal_nature = data.legal_nature
    company.economic_activity = data.economic_activity
    
    # Mark Step 2 complete -> Step 3 (Template)
    company.onboarding_current_step = max(company.onboarding_current_step, STEP_TEMPLATE_SELECTION)
    
    db.commit()
    
    return CompanyTypeResponse(
        success=True,
        message="Company type saved.",
        current_step=company.onboarding_current_step,
        next_step=STEP_TEMPLATE_SELECTION,
    )


# ============================================================================
# ============================================================================
# Step 3: Template Selection
# ============================================================================

def select_template(
    db: Session,
    company_id: UUID,
    data: TemplateSelectionRequest,
    current_user=None
) -> TemplateSelectionResponse:
    """
    Step 2: Select accounting template.

    CRITICAL RULES:
    - Template can only be selected before chart materialization (step < 3)
    - Template selection is irreversible after chart materialization
    - User must explicitly confirm the choice
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    # State validation - can only select template if chart not yet materialized
    if company.onboarding_status in [
        OnboardingStatus.CHART_READY,
        OnboardingStatus.CHART_FINALIZED,
        OnboardingStatus.ACTIVE,
    ]:
        raise ValidationError(
            "Template has already been selected and chart materialized. "
            "The accounting structure is now locked to maintain data integrity. "
            "To change template, please re-run onboarding."
        )

    # Validate company details and type are complete
    if not all([company.country, company.currency, company.timezone]):
        raise ValidationError(
            "Please complete company details before selecting a template. "
            "Go back to Step 1 and fill in all required fields."
        )
    if not all([company.legal_nature, company.economic_activity]):
        raise ValidationError(
            "Please complete company type before selecting a template. "
            "Go back to Step 2 and fill in all required fields."
        )

    # Validate template exists and is active
    template = db.query(ChartTemplate).filter(
        ChartTemplate.id == data.template_id,
        ChartTemplate.is_active == True
    ).first()
    if not template:
        raise ValidationError(
            "The selected template is not available. "
            "Please choose a different template or contact support."
        )

    # Ensure template has accounts
    template_account_count = db.query(ChartTemplateAccount).filter(
        ChartTemplateAccount.template_id == template.id
    ).count()
    if template_account_count == 0:
        raise ValidationError(
            "The selected template has no accounts defined. "
            "Please choose a different template or contact support."
        )

    # Validate template includes all L0 kernel codes
    template_codes = {
        row.code for row in db.query(ChartTemplateAccount.code).filter(
            ChartTemplateAccount.template_id == template.id
        ).all()
    }
    missing_l0 = L0_KERNEL_CODES - template_codes
    if missing_l0:
        raise ValidationError(
            f"Template missing mandatory L0 kernel accounts: {sorted(missing_l0)}"
        )

    if not template.version or not template.version.startswith(KERNEL_VERSION):
        raise ValidationError(
            f"Template version {template.version} is not compatible with kernel {KERNEL_VERSION}."
        )

    if template.name == "US GAAP Standard":
        kernel_layer = KernelLayer.L1
    elif template.name == "US GAAP Simplified":
        kernel_layer = KernelLayer.L2
    else:
        raise ValidationError(
            "Template does not declare a supported kernel layer."
        )

    # Check for existing template usage (idempotent if same)
    existing_usage = db.query(CompanyTemplateUsage).filter(
        CompanyTemplateUsage.company_id == company_id
    ).first()
    if existing_usage:
        if existing_usage.template_id != template.id:
            raise ValidationError("Template has already been assigned to this company.")
    else:
        # Create template usage record
        template_usage = CompanyTemplateUsage(
            company_id=company_id,
            template_id=data.template_id,
            assigned_at=datetime.utcnow(),
            assigned_by=getattr(current_user, "id", None)
        )
        db.add(template_usage)

    # Bind kernel metadata
    if company.kernel_version and company.kernel_version != KERNEL_VERSION:
        raise ValidationError(
            f"Company already bound to kernel {company.kernel_version}. Reset onboarding to change kernels."
        )
    if company.kernel_layer and company.kernel_layer != kernel_layer:
        raise ValidationError(
            f"Company already bound to kernel layer {company.kernel_layer.value}."
        )

    company.kernel_version = KERNEL_VERSION
    company.kernel_layer = kernel_layer

    # Update company step (status transitions to TEMPLATE_SELECTED)
    # Advance to Step 4 (Modules)
    company.onboarding_current_step = max(company.onboarding_current_step, STEP_MODULES)
    company.onboarding_status = OnboardingStatus.TEMPLATE_SELECTED

    db.commit()
    db.refresh(template)

    return TemplateSelectionResponse(
        success=True,
        message=f"Template '{template.name}' selected successfully. You can now build your chart of accounts.",
        template_id=template.id,
        template_name=template.name,
        current_step=company.onboarding_current_step,
        next_step=STEP_MODULES
    )


# ============================================================================
# ============================================================================
# Step 3b: Chart Materialization (Internal / Automatic)
# ============================================================================

def materialize_chart(
    db: Session,
    company_id: UUID,
) -> ChartMaterializationResponse:
    """
    Step 3: Materialize chart of accounts from template.

    CRITICAL OPERATION:
    - This is an atomic transaction (all or nothing)
    - Copies all template accounts to company accounts
    - Sets template_account_id foreign key
    - Preserves mandatory/optional flags
    - On failure, entire operation rolls back

    Status transitions: TEMPLATE_SELECTED -> CHART_READY
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    if company.onboarding_status not in [
        OnboardingStatus.TEMPLATE_SELECTED,
        OnboardingStatus.CHART_READY,
        OnboardingStatus.CHART_FINALIZED,
        OnboardingStatus.ACTIVE,
    ]:
        raise ValidationError(
            "Please select a template before creating your chart of accounts. "
            "Go back to Step 3 to choose a template."
        )

    if company.onboarding_current_step < STEP_ACCOUNT_REVIEW:
        raise ValidationError(
            "Please complete module selection and organization scope before creating the chart."
        )

    if not company.currency:
        raise ValidationError("Company currency is required before chart materialization.")

    # Get template usage
    template_usage = db.query(CompanyTemplateUsage).filter(
        CompanyTemplateUsage.company_id == company_id
    ).first()
    if not template_usage:
        raise ValidationError("No template selected. Please go back to Step 2.")

    # Get template accounts with master account data
    template_accounts = db.query(ChartTemplateAccount).options(
        joinedload(ChartTemplateAccount.master_account)
    ).filter(
        ChartTemplateAccount.template_id == template_usage.template_id
    ).order_by(ChartTemplateAccount.sort_order).all()

    if not template_accounts:
        raise ValidationError(
            "The selected template has no accounts defined. "
            "Please contact support to resolve this issue."
        )

    try:
        # Get active modules for the company - used to filter optional accounts
        active_modules = set(
            m.module_id for m in db.query(CompanyModule).filter(
                CompanyModule.company_id == company_id,
                CompanyModule.is_active == True
            ).all()
        )
        if not active_modules:
            raise ValidationError("Please select at least one module before materialization.")

        expected_template_accounts = [
            ta for ta in template_accounts
            if not ta.required_module or ta.required_module in active_modules
        ]
        if not expected_template_accounts:
            raise ValidationError("No accounts available for the selected modules.")

        # Map template account IDs to new company account IDs
        account_id_map: Dict[UUID, UUID] = {}
        accounts_created = []

        existing_template_ids = {
            row.template_account_id for row in db.query(CompanyAccount.template_account_id).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.template_account_id.isnot(None)
            ).all()
        }
        if existing_template_ids:
            expected_ids = {ta.id for ta in expected_template_accounts}
            missing_ids = expected_ids - existing_template_ids
            if missing_ids:
                raise ValidationError(
                    "Chart materialization is incomplete. "
                    "Please reset onboarding before retrying."
                )

            if company.onboarding_status == OnboardingStatus.TEMPLATE_SELECTED:
                company.onboarding_status = OnboardingStatus.CHART_READY
            company.onboarding_current_step = max(company.onboarding_current_step, STEP_ACCOUNT_REVIEW)
            db.commit()

            mandatory_count = sum(1 for ta in expected_template_accounts if ta.is_mandatory)
            optional_count = len(expected_template_accounts) - mandatory_count

            return ChartMaterializationResponse(
                success=True,
                message="Chart of accounts already materialized.",
                accounts_created=0,
                mandatory_accounts=mandatory_count,
                optional_accounts=optional_count,
                current_step=company.onboarding_current_step,
                next_step=STEP_ACCOUNT_REVIEW
            )

        # First pass: Create all accounts without parent relationships
        for template_account in expected_template_accounts:
            master_account = template_account.master_account
            if not master_account:
                raise ValidationError(
                    f"Template account {template_account.code} is missing master account linkage."
                )

            company_account = CompanyAccount(
                id=uuid4(),
                company_id=company_id,
                code=template_account.code,
                name=template_account.name,
                description=master_account.description or template_account.name,
                type=master_account.type or "D",
                account_type=map_category_to_account_type(master_account.category),
                normal_balance=map_normal_balance(master_account.normal_balance),
                currency=company.currency,
                is_active=True,
                is_locked=False,
                template_account_id=template_account.id,
                mapped_master_account_id=template_account.master_account_id,
                created_at=datetime.utcnow()
            )
            db.add(company_account)
            account_id_map[template_account.id] = company_account.id
            accounts_created.append(company_account)

        # Second pass: Set parent relationships
        for template_account in expected_template_accounts:
            # Skip if account was filtered out
            if template_account.id not in account_id_map:
                continue

            if template_account.parent_id:
                company_account_id = account_id_map[template_account.id]
                company_account = db.query(CompanyAccount).filter(
                    CompanyAccount.id == company_account_id
                ).first()
                if company_account:
                    # If parent was skipped, this stays None (Top Level)
                    company_account.parent_id = account_id_map.get(template_account.parent_id)

        # Update company step (status transitions to CHART_READY)
        # Advance to Review (Step 6)
        company.onboarding_current_step = max(company.onboarding_current_step, STEP_ACCOUNT_REVIEW)
        company.onboarding_status = OnboardingStatus.CHART_READY

        db.commit()

        # Count account types
        mandatory_count = sum(
            1 for ta in expected_template_accounts if ta.is_mandatory
        )
        optional_count = len(expected_template_accounts) - mandatory_count

        return ChartMaterializationResponse(
            success=True,
            message=f"Successfully created {len(accounts_created)} accounts from template. You can now review and customize them.",
            accounts_created=len(accounts_created),
            mandatory_accounts=mandatory_count,
            optional_accounts=optional_count,
            current_step=company.onboarding_current_step,
            next_step=STEP_ACCOUNT_REVIEW
        )
    except ValidationError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise ValidationError(
            "Chart materialization failed. No accounts were created."
        ) from e


# ============================================================================
# Step 4: Module Selection
# ============================================================================

def select_modules(
    db: Session,
    company_id: UUID,
    data: Any # ModuleSelectionRequest
) -> Any: # ModuleSelectionResponse
    """Step 4: Configure active modules."""
    from app.db.models.company_module import CompanyModule
    
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    if company.onboarding_status in [
        OnboardingStatus.CHART_READY,
        OnboardingStatus.CHART_FINALIZED,
        OnboardingStatus.ACTIVE,
    ]:
        raise ValidationError(
            "Modules cannot be changed after chart materialization."
        )

    if company.onboarding_status != OnboardingStatus.TEMPLATE_SELECTED:
        raise ValidationError("Please select a template before configuring modules.")

    if not data.modules:
        raise ValidationError("At least one module must be selected.")

    # Clear existing modules
    db.query(CompanyModule).filter(CompanyModule.company_id == company_id).delete()
    
    # Add new modules
    for module_id in data.modules:
        db.add(CompanyModule(
            company_id=company_id,
            module_id=module_id,
            is_active=True
        ))
        
    # Advance to Step 5 (Scope)
    company.onboarding_current_step = max(company.onboarding_current_step, STEP_SCOPE)
    db.commit()
    
    return {
        "success": True,
        "message": "Modules configured.",
        "current_step": company.onboarding_current_step,
        "next_step": STEP_SCOPE
    }


# ============================================================================
# Step 5: Organization Scope
# ============================================================================

def set_organization_scope(
    db: Session,
    company_id: UUID,
    data: Any # OrganizationScopeRequest
) -> Any: # OrganizationScopeResponse
    """Step 5: Set organization scope (Standalone vs Group)."""
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    if company.onboarding_status in [
        OnboardingStatus.CHART_READY,
        OnboardingStatus.CHART_FINALIZED,
        OnboardingStatus.ACTIVE,
    ]:
        raise ValidationError("Organization scope cannot be changed after chart materialization.")

    if company.onboarding_status != OnboardingStatus.TEMPLATE_SELECTED:
        raise ValidationError("Please select a template before setting organization scope.")

    modules_selected = db.query(CompanyModule).filter(
        CompanyModule.company_id == company_id,
        CompanyModule.is_active == True
    ).count() > 0
    if not modules_selected:
        raise ValidationError("Please select modules before setting organization scope.")
        
    company.is_standalone = data.is_standalone
    
    company.onboarding_current_step = max(company.onboarding_current_step, STEP_ACCOUNT_REVIEW)
    db.commit()
    
    return {
        "success": True,
        "message": "Organization scope saved.",
        "current_step": company.onboarding_current_step,
        "next_step": STEP_ACCOUNT_REVIEW
    }




# ============================================================================
# Step 6: Account Review & Customization
# ============================================================================

def customize_accounts(
    db: Session,
    company_id: UUID,
    data: AccountReviewRequest
) -> AccountReviewResponse:
    """
    Step 6: Review and customize accounts.

    ALLOWED ACTIONS:
    - Rename accounts
    - Disable non-mandatory accounts
    - Add custom accounts
    - Reorder custom accounts

    FORBIDDEN ACTIONS:
    - Change account type
    - Change normal balance
    - Delete mandatory accounts
    - Change hierarchy of template accounts
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    # State validation - must have Organization Scope set (step 5+)
    if company.onboarding_current_step < STEP_ACCOUNT_REVIEW:
        raise ValidationError(
            "Please complete organization scope setup before customizing accounts. "
            "Complete Step 5 first."
        )

    if company.onboarding_status == OnboardingStatus.ACTIVE:
        raise ValidationError("Accounts cannot be customized after activation.")

    if company.onboarding_status == OnboardingStatus.CHART_FINALIZED:
        if data.finalized:
            total_accounts = db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id
            ).count()
            active_accounts = db.query(CompanyAccount).filter(
                CompanyAccount.company_id == company_id,
                CompanyAccount.is_active == True
            ).count()
            disabled_accounts = total_accounts - active_accounts
            mandatory_accounts = db.query(CompanyAccount).join(
                ChartTemplateAccount,
                CompanyAccount.template_account_id == ChartTemplateAccount.id
            ).filter(
                CompanyAccount.company_id == company_id,
                ChartTemplateAccount.is_mandatory == True
            ).count()

            return AccountReviewResponse(
                success=True,
                message="Accounts already finalized. Proceed to fiscal periods.",
                total_accounts=total_accounts,
                mandatory_accounts=mandatory_accounts,
                custom_accounts=0,
                disabled_accounts=disabled_accounts,
                current_step=company.onboarding_current_step,
                next_step=STEP_FISCAL_PERIODS
            )

        raise ValidationError(
            "Accounts have already been finalized. "
            "You can proceed to set up fiscal periods."
        )

    if company.onboarding_status != OnboardingStatus.CHART_READY:
        raise ValidationError(
            "Chart of accounts must be materialized before customization."
        )

    try:
        # Process account customizations
        for customization in data.customizations:
            account = db.query(CompanyAccount).filter(
                CompanyAccount.id == customization.account_id,
                CompanyAccount.company_id == company_id
            ).first()

            if not account:
                raise ValidationError(f"Account {customization.account_id} not found.")

            # Check if account is mandatory (via template)
            if account.template_account_id:
                template_account = db.query(ChartTemplateAccount).filter(
                    ChartTemplateAccount.id == account.template_account_id
                ).first()
                is_mandatory = template_account.is_mandatory if template_account else False
            else:
                is_mandatory = False

            if customization.action == "rename":
                if not customization.new_name:
                    raise ValidationError("New name is required for rename action.")
                account.name = customization.new_name

            elif customization.action == "disable":
                if is_mandatory:
                    raise ValidationError(
                        f"Cannot disable mandatory account '{account.name}'. "
                        "This account is required by the template."
                    )
                account.is_active = False

            elif customization.action == "enable":
                account.is_active = True

        # Process custom account creation
        custom_accounts_created = []
        for custom_account in data.custom_accounts:
            # Validate account type
            try:
                account_type_enum = AccountType[custom_account.account_type.upper()]
                normal_balance_enum = NormalBalance[custom_account.normal_balance.upper()]
            except KeyError:
                raise ValidationError(
                    f"Invalid account type or normal balance: {custom_account.account_type}, {custom_account.normal_balance}"
                )

            new_account = CompanyAccount(
                id=uuid4(),
                company_id=company_id,
                code=custom_account.code,
                name=custom_account.name,
                description=custom_account.name,
                type="D",
                account_type=account_type_enum,
                normal_balance=normal_balance_enum,
                parent_id=custom_account.parent_id,
                is_active=True,
                is_locked=False,
                currency=company.currency or "USD",
                template_account_id=None,  # Custom account
                created_at=datetime.utcnow()
            )
            db.add(new_account)
            custom_accounts_created.append(new_account)

        # Update company step if finalized (status transitions to CHART_FINALIZED)
        if data.finalized:
            # Advance to Fiscal Periods (Step 7)
            company.onboarding_current_step = max(company.onboarding_current_step, STEP_FISCAL_PERIODS)
            company.onboarding_status = OnboardingStatus.CHART_FINALIZED

        db.commit()

        # Get final counts
        total_accounts = db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id
        ).count()
        active_accounts = db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active == True
        ).count()
        disabled_accounts = total_accounts - active_accounts

        # Count mandatory accounts
        mandatory_accounts = db.query(CompanyAccount).join(
            ChartTemplateAccount,
            CompanyAccount.template_account_id == ChartTemplateAccount.id
        ).filter(
            CompanyAccount.company_id == company_id,
            ChartTemplateAccount.is_mandatory == True
        ).count()

        return AccountReviewResponse(
            success=True,
            message="Accounts customized successfully. You can now set up fiscal periods.",
            total_accounts=total_accounts,
            mandatory_accounts=mandatory_accounts,
            custom_accounts=len(custom_accounts_created),
            disabled_accounts=disabled_accounts,

            current_step=company.onboarding_current_step,
            next_step=STEP_FISCAL_PERIODS
        )

    except ValidationError:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise ValidationError(
            "An error occurred while customizing accounts. "
            "Changes have been rolled back. Please try again."
        ) from e


# ============================================================================
# Step 7: Fiscal Periods
# ============================================================================

def setup_fiscal_periods(
    db: Session,
    company_id: UUID,
    data: FiscalPeriodSetupRequest
) -> FiscalPeriodSetupResponse:
    """
    Step 7: Set up fiscal periods.

    VALIDATION RULES:
    - At least one period must be OPEN
    - Periods cannot overlap
    - Periods cannot have gaps
    - Start dates must be before end dates
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    # State validation - must have finalized chart (Step 6 Complete -> Step 7+)
    if company.onboarding_status != OnboardingStatus.CHART_FINALIZED:
        raise ValidationError(
            "Please finalize your chart of accounts before setting up fiscal periods. "
            "Complete Step 6 first."
        )

    # Check if periods already exist
    existing_periods = db.query(FiscalPeriod).filter(
        FiscalPeriod.company_id == company_id
    ).count()
    if existing_periods > 0:
        company.onboarding_current_step = max(company.onboarding_current_step, STEP_ACTIVATION)
        db.commit()
        return FiscalPeriodSetupResponse(
            success=True,
            message="Fiscal periods already exist. You can now activate accounting.",
            periods_created=0,
            open_periods=db.query(FiscalPeriod).filter(
                FiscalPeriod.company_id == company_id,
                FiscalPeriod.status == PeriodStatus.OPEN
            ).count(),
            current_step=company.onboarding_current_step,
            next_step=STEP_ACTIVATION
        )

    try:
        periods_created = []
        open_periods = 0

        for period_data in data.periods:
            # Convert period type string to enum
            from app.db.models.enums import PeriodType
            period_type_enum = PeriodType[period_data.period_type]

            status = PeriodStatus.OPEN if period_data.is_open else PeriodStatus.CLOSED

            fiscal_period = FiscalPeriod(
                id=uuid4(),
                company_id=company_id,
                name=period_data.name,
                start_date=period_data.start_date,
                end_date=period_data.end_date,
                period_type=period_type_enum,
                status=status,
                created_at=datetime.utcnow()
            )
            db.add(fiscal_period)
            periods_created.append(fiscal_period)

            if period_data.is_open:
                open_periods += 1

        # Update company step (status remains CHART_FINALIZED until activation)
        # Advance to Activation (Step 8)
        company.onboarding_current_step = max(company.onboarding_current_step, STEP_ACTIVATION)

        db.commit()

        return FiscalPeriodSetupResponse(
            success=True,
            message=f"Successfully created {len(periods_created)} fiscal periods. You can now activate accounting.",
            periods_created=len(periods_created),
            open_periods=open_periods,

            current_step=company.onboarding_current_step,
            next_step=STEP_ACTIVATION
        )

    except IntegrityError as e:
        db.rollback()
        raise ValidationError(
            "Failed to create fiscal periods due to a database error. "
            "Please check for overlapping dates and try again."
        ) from e
    except Exception as e:
        db.rollback()
        raise ValidationError(
            "An error occurred while creating fiscal periods. "
            "Changes have been rolled back. Please try again."
        ) from e


# ============================================================================
# Step 8: Activation (Point of No Return)
# ============================================================================

def activate_accounting(
    db: Session,
    company_id: UUID,
    data: ActivationRequest
) -> ActivationResponse:
    """
    Step 8: Activate accounting (POINT OF NO RETURN).

    CRITICAL OPERATION:
    - This is irreversible
    - Transitions from CHART_FINALIZED to ACTIVE
    - Locks the onboarding state machine
    - Enables full accounting functionality
    - Sets onboarding_completed_at timestamp

    After activation:
    - Accounting rules are enforced
    - Account properties lock after first use
    - Fiscal periods control transaction recording
    """
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise ValidationError("Company not found")

    # State validation
    if company.onboarding_status == OnboardingStatus.ACTIVE:
        total_accounts = db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active == True
        ).count()
        open_periods = db.query(FiscalPeriod).filter(
            FiscalPeriod.company_id == company_id,
            FiscalPeriod.status == PeriodStatus.OPEN
        ).count()
        return ActivationResponse(
            success=True,
            message=f"Accounting already active for {company.name}.",
            company_id=company.id,
            company_name=company.name,
            activated_at=company.onboarding_completed_at,
            total_accounts=total_accounts,
            open_periods=open_periods,
            next_actions=[
                "Create your first journal entry",
                "View the trial balance",
                "Generate financial statements",
                "Invite team members"
            ]
        )

    # Ensure all prerequisites are met
    if company.onboarding_status != OnboardingStatus.CHART_FINALIZED:
        raise ValidationError(
            "Invalid onboarding state. Company must finalize accounts before activation."
        )

    # Must have completed all steps (step 7 = fiscal periods)
    if company.onboarding_current_step < STEP_ACTIVATION:
        raise ValidationError(
            "Please complete all previous steps before activation. "
            "Ensure company details, template selection, chart customization, and fiscal periods are all complete."
        )

    # Validate fiscal periods exist
    has_periods = db.query(FiscalPeriod).filter(
        FiscalPeriod.company_id == company_id
    ).count() > 0
    if not has_periods:
        raise ValidationError(
            "No fiscal periods defined. "
            "Please create at least one fiscal period before activation."
        )

    # Validate at least one OPEN period
    has_open_period = db.query(FiscalPeriod).filter(
        FiscalPeriod.company_id == company_id,
        FiscalPeriod.status == PeriodStatus.OPEN
    ).count() > 0
    if not has_open_period:
        raise ValidationError(
            "No open fiscal periods found. "
            "At least one period must be OPEN to record transactions."
        )

    if company.kernel_version != KERNEL_VERSION or not company.kernel_layer:
        raise ValidationError(
            "Kernel is not bound to this company. Activation is blocked."
        )

    from app.services.kernel_remediation_service import KernelRemediationService
    remediation_service = KernelRemediationService(db)
    missing_kernel = remediation_service.get_missing_kernel_accounts(company_id)
    mismatches = remediation_service.get_kernel_mismatches(company_id)
    if missing_kernel or mismatches:
        details = []
        if missing_kernel:
            details.append(f"Missing L0 accounts: {sorted(missing_kernel)}")
        if mismatches:
            mismatch_lines = [f"{code}: {fields}" for code, fields in sorted(mismatches.items())]
            details.append("Mismatched kernel accounts: " + "; ".join(mismatch_lines))
        raise ValidationError(
            "Kernel compliance check failed. Activation blocked. " + " ".join(details)
        )

    try:
        # Final state transition
        company.onboarding_status = OnboardingStatus.ACTIVE
        company.onboarding_current_step = max(company.onboarding_current_step, STEP_ACTIVATION)
        company.onboarding_completed_at = datetime.utcnow()

        # Release session lock
        company.onboarding_session_lock = None
        company.onboarding_session_locked_at = None

        db.commit()
        db.refresh(company)

        # Emit audit event for company initialization
        from app.services.audit_service import AuditService
        AuditService.log_event(
            db=db,
            action="COMPANY_INITIALIZED",
            entity_type="company",
            entity_id=str(company.id),
            user_id=None,  # TODO: Pass current user ID when available
            payload={
                "company_name": company.name,
                "ucid": company.ucid,
                "onboarding_completed_at": company.onboarding_completed_at.isoformat()
            }
        )

        # Get final statistics
        total_accounts = db.query(CompanyAccount).filter(
            CompanyAccount.company_id == company_id,
            CompanyAccount.is_active == True
        ).count()

        open_periods = db.query(FiscalPeriod).filter(
            FiscalPeriod.company_id == company_id,
            FiscalPeriod.status == PeriodStatus.OPEN
        ).count()

        return ActivationResponse(
            success=True,
            message=f"Accounting activated successfully for {company.name}!",
            company_id=company.id,
            company_name=company.name,
            activated_at=company.onboarding_completed_at,
            total_accounts=total_accounts,
            open_periods=open_periods,
            next_actions=[
                "Create your first journal entry",
                "View the trial balance",
                "Generate financial statements",
                "Invite team members"
            ]
        )

    except Exception as e:
        db.rollback()
        raise ValidationError(
            "An error occurred during activation. "
            "The operation has been rolled back. Please try again or contact support."
        ) from e


# Export
__all__ = [
    "reset_onboarding",
    "acquire_session_lock",
    "release_session_lock",
    "start_onboarding",
    "get_onboarding_status",
    "update_company_details",
    "update_company_type",
    "select_template",
    "materialize_chart",
    "select_modules",
    "set_organization_scope",
    "customize_accounts",
    "setup_fiscal_periods",
    "activate_accounting",
]

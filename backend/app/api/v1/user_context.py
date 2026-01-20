"""
User Context API

Provides authoritative context for dashboard rendering.

CANONICAL RULE: Backend is the ONLY source of truth.
UI must never infer state from absence or side effects.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.company import Company
from app.db.models.company_account import CompanyAccount
from app.db.models.fiscal_period import FiscalPeriod, PeriodStatus
from app.db.models.user_company import UserCompany
from app.db.models.enums import OnboardingStatus
from app.api.v1.auth import get_current_user
from app.schemas.user_context import UserContextResponse

router = APIRouter()


@router.get("/context", response_model=UserContextResponse)
def get_user_context(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get authoritative user context for dashboard hydration.
    
    CANON II: Backend Creates Truth
    - UI must render ONLY from this response
    - No inference, no optimistic rendering
    - This is the single source of truth
    
    Returns:
        UserContextResponse with all canonical state flags
    """
    # Get all companies the user has access to
    companies = (
        db.query(Company)
        .join(UserCompany, Company.id == UserCompany.company_id)
        .filter(UserCompany.user_id == current_user.id)
        .all()
    )
    
    total_companies = len(companies)
    
    # Determine current company
    # Priority: 1) preferred_company_id, 2) first company, 3) None
    current_company = None
    preferred_company_id = getattr(current_user, "preferred_company_id", None)
    if preferred_company_id:
        current_company = next(
            (company for company in companies if company.id == preferred_company_id),
            None
        )
    if not current_company and total_companies > 0:
        current_company = companies[0]
    
    # If no current company, return minimal context
    if not current_company:
        return UserContextResponse(
            user_id=current_user.id,
            email=current_user.email,
            full_name=getattr(current_user, "full_name", None),
            current_company_id=None,
            current_company_name=None,
            current_company_ucid=None,
            total_companies=0,
            accounting_active=False,
            onboarding_status=None,
            kernel_version=None,
            kernel_layer=None,
            protected_structure=False,
            total_accounts=0,
            open_periods=0,
        )
    
    # CANONICAL STATE DERIVATION (Backend Authority Only)
    
    # Accounting Active = ACTIVE status
    accounting_active = current_company.onboarding_status == OnboardingStatus.ACTIVE
    
    # Protected Structure = has kernel binding + ACTIVE
    protected_structure = (
        accounting_active and
        current_company.kernel_version is not None and
        current_company.kernel_layer is not None
    )
    
    # Count accounts (from DB, not inferred)
    total_accounts = db.query(func.count(CompanyAccount.id)).filter(
        CompanyAccount.company_id == current_company.id,
        CompanyAccount.is_active == True
    ).scalar() or 0
    
    # Count open fiscal periods (from DB, not inferred)
    open_periods = db.query(func.count(FiscalPeriod.id)).filter(
        FiscalPeriod.company_id == current_company.id,
        FiscalPeriod.status == PeriodStatus.OPEN
    ).scalar() or 0
    
    return UserContextResponse(
        user_id=current_user.id,
        email=current_user.email,
        full_name=getattr(current_user, "full_name", None),
        current_company_id=current_company.id,
        current_company_name=current_company.name,
        current_company_ucid=current_company.ucid,
        total_companies=total_companies,
        accounting_active=accounting_active,
        onboarding_status=current_company.onboarding_status.value,
        kernel_version=current_company.kernel_version,
        kernel_layer=current_company.kernel_layer.value if current_company.kernel_layer else None,
        protected_structure=protected_structure,
        total_accounts=total_accounts,
        open_periods=open_periods,
    )

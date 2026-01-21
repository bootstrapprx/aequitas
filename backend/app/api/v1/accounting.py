from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional
from datetime import date

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.company import Company
from app.db.models.enums import KernelLayer
from app.api.v1.auth import get_current_user
from app.core.security import check_superuser
from app.core.rate_limiting import rate_limit_critical, rate_limit_write
from app.core.access_control import require_company_access
from app.schemas.ledger import (
    AccountLedger,
    TrialBalanceResponse,
    AccountBalanceResponse
)
from app.schemas.financial_statements import (
    BalanceSheetResponse,
    IncomeStatementResponse,
    CashFlowStatementResponse
)
from app.schemas.kernel_dashboard import KernelL0CoreMetricsResponse, KernelLayerBindingsResponse
from app.schemas.fiscal_period import (
    FiscalPeriodCreate,
    FiscalPeriodResponse,
    FiscalPeriodClose
)
from app.services.ledger_service import LedgerService
from app.services.financial_statement_service import FinancialStatementService
from app.services.kernel_l0_dashboard_service import KernelL0DashboardService
from app.services.fiscal_period_service import FiscalPeriodService
from app.services.permission_service import PermissionService

router = APIRouter()


# ===== Ledger Endpoints =====

@router.get("/ledger/account/{account_id}", response_model=AccountLedger)
def get_account_ledger(
    account_id: UUID,
    company_id: UUID,
    fiscal_period_id: Optional[UUID] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the ledger for a specific account.

    Shows all posted journal entries affecting this account with running balance.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view ledger for this company")

    service = LedgerService(db)
    try:
        ledger = service.get_account_ledger(
            company_id=company_id,
            company_account_id=account_id,
            fiscal_period_id=fiscal_period_id,
            start_date=start_date,
            end_date=end_date
        )
        return ledger

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/trial-balance", response_model=TrialBalanceResponse)
def get_trial_balance(
    company_id: UUID,
    fiscal_period_id: Optional[UUID] = None,
    as_of_date: Optional[date] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the trial balance report.

    Must provide either fiscal_period_id or as_of_date.
    Shows all accounts with debit/credit balances.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view trial balance for this company")

    if not fiscal_period_id and not as_of_date:
        raise HTTPException(status_code=400, detail="Must provide either fiscal_period_id or as_of_date")

    service = LedgerService(db)
    try:
        trial_balance = service.get_trial_balance(
            company_id=company_id,
            fiscal_period_id=fiscal_period_id,
            as_of_date=as_of_date
        )
        return trial_balance

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/balances", response_model=list[AccountBalanceResponse])
def get_account_balances(
    company_id: UUID,
    fiscal_period_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all account balances for a fiscal period.

    Shows beginning balance, debits, credits, and ending balance for each account.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view balances for this company")

    service = LedgerService(db)
    balances = service.get_account_balances(company_id, fiscal_period_id)

    return balances


# ===== Financial Statement Endpoints =====

@router.get("/balance-sheet", response_model=BalanceSheetResponse)
def get_balance_sheet(
    company_id: UUID,
    as_of_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a balance sheet as of a specific date.

    Shows assets, liabilities, and equity with totals.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view balance sheet for this company")

    service = FinancialStatementService(db)
    try:
        balance_sheet = service.generate_balance_sheet(company_id, as_of_date)
        return balance_sheet

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/income-statement", response_model=IncomeStatementResponse)
def get_income_statement(
    company_id: UUID,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate an income statement (P&L) for a period.

    Shows revenue, COGS, expenses, and net income with profit margins.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view income statement for this company")

    service = FinancialStatementService(db)
    try:
        income_statement = service.generate_income_statement(company_id, start_date, end_date)
        return income_statement

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/cash-flow", response_model=CashFlowStatementResponse)
def get_cash_flow_statement(
    company_id: UUID,
    start_date: date,
    end_date: date,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a cash flow statement (indirect method) for a period.

    Shows operating, investing, and financing activities.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view cash flow for this company")

    service = FinancialStatementService(db)
    try:
        cash_flow = service.generate_cash_flow_statement(company_id, start_date, end_date)
        return cash_flow

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Kernel L0 Dashboard (Tier 1 Core Metrics) =====

@router.get("/core-metrics", response_model=KernelL0CoreMetricsResponse)
def get_core_metrics(
    company_id: UUID,
    fiscal_period_id: Optional[UUID] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Compute Kernel L0 Dashboard Tier 1 Core Metrics for a fiscal period.

    If fiscal_period_id is omitted, a single OPEN period is used when unambiguous.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view metrics for this company")

    service = KernelL0DashboardService(db)
    try:
        return service.get_core_metrics(company_id, fiscal_period_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ===== Kernel Layer Placeholders =====

@router.get("/kernel-layers", response_model=KernelLayerBindingsResponse)
def get_kernel_layer_bindings(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Return Kernel layer bindings and placeholders (L0 implemented, L1/L2 placeholders).
    """
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view kernel bindings for this company")

    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    layers = [
        {"layer": KernelLayer.L0, "state": "implemented"},
        {"layer": KernelLayer.L1, "state": "placeholder"},
        {"layer": KernelLayer.L2, "state": "placeholder"},
    ]

    return {
        "company_id": company_id,
        "kernel_version": company.kernel_version,
        "kernel_layer": company.kernel_layer,
        "layers": layers,
    }


# ===== Fiscal Period Endpoints =====

@router.post(
    "/fiscal-periods",
    response_model=FiscalPeriodResponse,
    status_code=201,
    dependencies=[Depends(rate_limit_write())]
)
def create_fiscal_period(
    period_data: FiscalPeriodCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new fiscal period.

    Period types: month, quarter, year
    Status: open, closed, locked
    """
    require_company_access(
        db,
        current_user,
        period_data.company_id,
        require_admin=True,
        allow_superuser=True,
    )

    service = FiscalPeriodService(db)
    try:
        period = service.create_fiscal_period(period_data)
        return FiscalPeriodResponse(**period.__dict__)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/fiscal-periods", response_model=list[FiscalPeriodResponse])
def list_fiscal_periods(
    company_id: UUID,
    period_type: Optional[str] = None,
    status: Optional[str] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List fiscal periods with optional filters.

    Query params:
    - company_id: Required
    - period_type: Optional (month, quarter, year)
    - status: Optional (open, closed, locked)
    - year: Optional year filter
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=True,
    )

    service = FiscalPeriodService(db)

    from app.db.models.fiscal_period import PeriodType, PeriodStatus

    period_type_enum = PeriodType(period_type) if period_type else None
    status_enum = PeriodStatus(status) if status else None

    periods = service.get_fiscal_periods(
        company_id=company_id,
        period_type=period_type_enum,
        status=status_enum,
        year=year
    )

    return [FiscalPeriodResponse(**p.__dict__) for p in periods]


@router.post(
    "/fiscal-periods/{period_id}/close",
    response_model=FiscalPeriodResponse,
    dependencies=[Depends(rate_limit_critical())]
)
def close_fiscal_period(
    period_id: UUID,
    close_data: FiscalPeriodClose,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Close a fiscal period.

    Requirements:
    - All journal entries must be posted (no drafts)
    - Period must be open
    """
    service = FiscalPeriodService(db)
    period = service.get_fiscal_period(period_id)

    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")

    require_company_access(
        db,
        current_user,
        period.company_id,
        require_admin=True,
        allow_superuser=True,
    )

    try:
        closed_period = service.close_fiscal_period(period_id, current_user.id)
        return FiscalPeriodResponse(**closed_period.__dict__)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/fiscal-periods/{period_id}/reopen",
    response_model=FiscalPeriodResponse,
    dependencies=[Depends(rate_limit_critical())]
)
def reopen_fiscal_period(
    period_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reopen a closed fiscal period (requires superuser privileges).

    SECURITY:
    - Requires superuser privileges (enforced)
    - Cannot reopen locked periods (GAAP compliance)
    - Creates audit trail of reopen operation

    RESTRICTIONS:
    - LOCKED periods cannot be reopened (immutable)
    - Only CLOSED periods can transition to OPEN

    USE CASES:
    - Correcting period close errors
    - Emergency adjustments after premature close
    - Reversing accidental period closure
    """
    # CRITICAL SECURITY: Enforce superuser privileges
    check_superuser(current_user)

    service = FiscalPeriodService(db)
    period = service.get_fiscal_period(period_id)

    if not period:
        raise HTTPException(status_code=404, detail="Fiscal period not found")

    require_company_access(
        db,
        current_user,
        period.company_id,
        require_admin=True,
        allow_superuser=True,
    )

    try:
        reopened_period = service.reopen_fiscal_period(period_id, reopened_by=current_user.id)
        return FiscalPeriodResponse(**reopened_period.__dict__)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/fiscal-periods/create-monthly/{company_id}/{year}", response_model=list[FiscalPeriodResponse])
def create_monthly_periods(
    company_id: UUID,
    year: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create all 12 monthly periods for a year.

    Convenience endpoint to quickly set up a full year of monthly periods.
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )

    service = FiscalPeriodService(db)
    try:
        periods = service.create_monthly_periods(company_id, year)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return [FiscalPeriodResponse(**p.__dict__) for p in periods]

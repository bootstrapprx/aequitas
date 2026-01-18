"""API endpoints for managing company-specific charts of accounts."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.db.models.user import User
from app.services.companychart_service import CompanyChartService
from app.core.exceptions import ValidationError
from app.core.security import check_superuser
from app.core.rate_limiting import rate_limit_critical, rate_limit_write
from app.core.access_control import require_company_access
from app.db.models.enums import LockedReason
from app.schemas.company_account import (
    CompanyAccountSchema,
    CompanyAccountCreate,
    CompanyAccountUpdate,
    CompanyAccountLockRequest,
    CompanyAccountUnlockRequest
)
from app.api.v1.auth import get_current_user

router = APIRouter()


@router.get("/companies/{company_id}/chart", response_model=List[CompanyAccountSchema])
def get_company_chart(
    company_id: UUID,
    active_only: bool = Query(True, description="Filter only active accounts"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all accounts for a company's chart of accounts."""
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=True,
    )
    service = CompanyChartService(db)
    accounts = service.get_company_chart(company_id, active_only=active_only)
    return accounts


@router.get("/companies/{company_id}/chart/tree", response_model=List[Dict[str, Any]])
def get_company_chart_tree(
    company_id: UUID,
    active_only: bool = Query(True, description="Filter only active accounts"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get company's chart of accounts as a hierarchical tree structure."""
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=True,
    )
    service = CompanyChartService(db)
    accounts = service.get_company_chart(company_id, active_only=active_only)
    tree = service.build_tree(accounts)
    return tree


@router.get("/companies/{company_id}/chart/stats", response_model=Dict[str, Any])
def get_company_chart_stats(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get statistics about a company's chart of accounts."""
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=True,
    )
    service = CompanyChartService(db)
    stats = service.get_chart_stats(company_id)
    return stats


@router.get("/companies/{company_id}/chart/{code}", response_model=CompanyAccountSchema)
def get_company_account_by_code(
    company_id: UUID,
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific account by code."""
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=True,
    )
    service = CompanyChartService(db)
    account = service.get_account_by_code(company_id, code)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account with code {code} not found")
    return account


@router.post(
    "/companies/{company_id}/chart",
    response_model=CompanyAccountSchema,
    status_code=201,
    dependencies=[Depends(rate_limit_write())]
)
def create_company_account(
    company_id: UUID,
    account_data: CompanyAccountCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new account in the company's chart of accounts."""
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )
    # Ensure company_id in path matches the one in the request body
    if account_data.company_id != company_id:
        raise HTTPException(
            status_code=400,
            detail="Company ID in path does not match company ID in request body"
        )

    service = CompanyChartService(db)
    try:
        account = service.create_account(company_id, account_data)
        return account
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put(
    "/companies/{company_id}/chart/{code}",
    response_model=CompanyAccountSchema,
    dependencies=[Depends(rate_limit_write())]
)
def update_company_account(
    company_id: UUID,
    code: str,
    account_data: CompanyAccountUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing account in the company's chart of accounts.

    LOCKED ACCOUNT RESTRICTIONS:
    - Cannot change: name, type, code, account_type, normal_balance, parent_id, mapped_master_account_id
    - Can change: description, currency, json_data
    - To modify immutable fields, unlock the account first (requires superuser)
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )
    service = CompanyChartService(db)
    try:
        account = service.update_account(company_id, code, account_data)
        if not account:
            raise HTTPException(status_code=404, detail=f"Account with code {code} not found")
        return account
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete(
    "/companies/{company_id}/chart/{code}",
    status_code=204,
    dependencies=[Depends(rate_limit_write())]
)
def delete_company_account(
    company_id: UUID,
    code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete (soft delete) an account from the company's chart of accounts.

    DELETION RESTRICTIONS:
    - Cannot delete accounts with children (must remove or reparent children first)
    - Cannot delete locked accounts (must unlock first)
    - Cannot delete template-mandatory accounts
    - Cannot delete accounts with transactions (GAAP compliance)
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )
    service = CompanyChartService(db)
    try:
        success = service.delete_account(company_id, code)
        if not success:
            raise HTTPException(status_code=404, detail=f"Account with code {code} not found")
        return None
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/companies/{company_id}/chart/reset", response_model=Dict[str, Any])
def reset_company_chart_to_master(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reset company's chart of accounts to match the master chart.
    This will deactivate all existing accounts and create new ones from master.
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )
    service = CompanyChartService(db)
    try:
        result = service.reset_to_master_chart(company_id)
        return result
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/companies/{company_id}/chart/initialize", response_model=Dict[str, Any])
def initialize_company_chart(
    company_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initialize company's chart of accounts from master chart.
    This is typically called automatically during company creation,
    but can be called manually for companies that were created before this feature.
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )
    service = CompanyChartService(db)
    try:
        result = service.initialize_from_master_chart(company_id)
        return result
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


# ==============================================================================
# ACCOUNT LOCKING ENDPOINTS
# ==============================================================================

@router.post(
    "/companies/{company_id}/chart/{account_id}/lock",
    response_model=CompanyAccountSchema,
    dependencies=[Depends(rate_limit_write())]
)
def lock_company_account(
    company_id: UUID,
    account_id: UUID,
    lock_request: CompanyAccountLockRequest,
    user_id: Optional[UUID] = Query(None, description="User ID (required for Manual locks)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lock an account to prevent immutable field changes.

    LOCKED ACCOUNTS CANNOT CHANGE:
    - name (account name)
    - type (H/D)
    - code (account code)
    - account_type (Asset, Liability, etc.)
    - normal_balance (Debit/Credit)
    - parent_id (hierarchy)
    - mapped_master_account_id (master chart mapping)

    LOCKING REASONS:
    - FirstTransaction: Automatically locked after first posted transaction
    - PeriodClose: Locked during fiscal period close
    - Manual: Manually locked by superuser (requires user_id)

    GAAP COMPLIANCE:
    - Ensures accounting consistency
    - Prevents retroactive structural changes
    - Maintains audit trail integrity
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )
    service = CompanyChartService(db)
    try:
        # Verify account belongs to company
        account = service.get_account_by_id(account_id)
        if not account or account.company_id != company_id:
            raise HTTPException(
                status_code=404,
                detail=f"Account {account_id} not found in company {company_id}"
            )

        # Convert reason string to enum
        reason = LockedReason(lock_request.reason)

        # Lock the account
        locked_account = service.lock_account(account_id, reason, user_id)
        return locked_account
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post(
    "/companies/{company_id}/chart/{account_id}/unlock",
    response_model=CompanyAccountSchema,
    dependencies=[Depends(rate_limit_critical())]
)
def unlock_company_account(
    company_id: UUID,
    account_id: UUID,
    unlock_request: CompanyAccountUnlockRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Unlock an account (requires superuser privileges).

    WARNING: Only allowed if no posted transactions in current fiscal period.

    SECURITY:
    - Requires superuser privileges (enforced)
    - Requires authenticated user for audit trail
    - Creates unlock event in audit log

    USE CASES:
    - Correcting account structure before period close
    - Emergency fixes during period transition
    - Reverting accidental locks

    RESTRICTIONS:
    - Cannot unlock if transactions exist in current period
    - Unlock reason must be provided for audit
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )
    # CRITICAL SECURITY: Enforce superuser privileges
    check_superuser(current_user)

    service = CompanyChartService(db)
    try:
        # Verify account belongs to company
        account = service.get_account_by_id(account_id)
        if not account or account.company_id != company_id:
            raise HTTPException(
                status_code=404,
                detail=f"Account {account_id} not found in company {company_id}"
            )

        # Unlock the account (using current_user.id for audit trail)
        unlocked_account = service.unlock_account(account_id, current_user.id)
        return unlocked_account
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/companies/{company_id}/chart/{account_id}/can-delete", response_model=Dict[str, Any])
def check_account_deletable(
    company_id: UUID,
    account_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Check if an account can be deleted.

    DELETION VALIDATION CHECKS:
    - Account must not have children (must remove or reparent first)
    - Account must not be locked (must unlock first)
    - Account must not be template-mandatory
    - Account must not have posted transactions (GAAP compliance)

    RETURNS:
    - can_delete: boolean (true if deletable)
    - reason: string (explanation if not deletable)

    USE CASES:
    - Pre-deletion validation UI
    - Bulk deletion planning
    - Account cleanup workflows
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=True,
    )
    service = CompanyChartService(db)
    try:
        # Verify account belongs to company
        account = service.get_account_by_id(account_id)
        if not account or account.company_id != company_id:
            raise HTTPException(
                status_code=404,
                detail=f"Account {account_id} not found in company {company_id}"
            )

        # Check if account can be deleted
        can_delete, reason = service.can_delete_account(account_id)

        return {
            "account_id": str(account_id),
            "can_delete": can_delete,
            "reason": reason
        }
    except (ValueError, ValidationError) as e:
        raise HTTPException(status_code=400, detail=str(e))

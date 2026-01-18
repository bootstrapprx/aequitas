"""
Kernel Remediation API Endpoints

Provides user-guided remediation for companies missing L0 kernel accounts.

Authority: Canon III - Additive changes only, history preserved.
"""

from uuid import UUID
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.session import get_db
from app.services.kernel_remediation_service import KernelRemediationService, log_remediation_event
from app.api.dependencies import get_current_user
from app.db.models.user import User
from app.core.access_control import require_company_access
from app.core.security import check_superuser


router = APIRouter()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class RemediationStatusResponse(BaseModel):
    """Response model for remediation status check."""
    is_compliant: bool
    missing_account_count: int
    missing_accounts: List[str]
    mismatched_account_count: int
    mismatched_accounts: Dict[str, Dict[str, str]]
    has_posted_transactions: bool
    remediation_recommended: bool


class RemediationExecuteResponse(BaseModel):
    """Response model for remediation execution."""
    success: bool
    added_count: int
    added_codes: List[str]
    message: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/companies/{company_id}/kernel-status", response_model=RemediationStatusResponse)
def get_kernel_status(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if company's chart is Kernel 2025.2 compliant.

    Returns:
        Status indicating missing accounts and remediation recommendation
    """
    service = KernelRemediationService(db)

    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=True,
    )

    is_compliant = service.is_company_kernel_compliant(company_id)
    missing = service.get_missing_kernel_accounts(company_id)
    mismatches = service.get_kernel_mismatches(company_id)
    has_transactions = service.has_posted_transactions(company_id)

    return RemediationStatusResponse(
        is_compliant=is_compliant,
        missing_account_count=len(missing),
        missing_accounts=missing,
        mismatched_account_count=len(mismatches),
        mismatched_accounts=mismatches,
        has_posted_transactions=has_transactions,
        remediation_recommended=not is_compliant
    )


@router.post("/companies/{company_id}/remediate-chart", response_model=RemediationExecuteResponse)
def remediate_company_chart(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Add missing L0 kernel accounts to company's chart.

    This operation is SAFE because:
    - Only ADDS accounts (never deletes)
    - Does not modify existing accounts
    - Does not create journal entries
    - Requires explicit user consent (this API call)

    Requires:
        - User authentication
        - Company ownership (authorization)

    Returns:
        Summary of accounts added
    """
    service = KernelRemediationService(db)

    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )

    # Check if remediation needed
    if service.is_company_kernel_compliant(company_id):
        return RemediationExecuteResponse(
            success=True,
            added_count=0,
            added_codes=[],
            message="Chart is already kernel-compliant. No changes needed."
        )

    try:
        # Execute remediation
        result = service.auto_remediate_company(company_id, dry_run=False)

        # Log event
        log_remediation_event(
            db=db,
            company_id=company_id,
            user_id=current_user.id,
            added_codes=result['added_codes'],
            triggered_by='user_action'
        )

        return RemediationExecuteResponse(
            success=True,
            added_count=result['added_count'],
            added_codes=result['added_codes'],
            message=result['message']
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Remediation failed: {str(e)}")


@router.post("/admin/remediate-all-companies")
def remediate_all_companies_admin(
    dry_run: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Admin endpoint: Remediate all non-compliant companies.

    Args:
        dry_run: If True, only report what would be done (default: True)

    Requires:
        - Admin user role

    Returns:
        Summary statistics
    """
    check_superuser(current_user)

    service = KernelRemediationService(db)

    try:
        results = service.remediate_all_companies(
            dry_run=dry_run,
            only_without_transactions=True
        )

        return {
            "success": True,
            "dry_run": dry_run,
            "summary": {
                "total_companies": results['total'],
                "compliant": results['compliant'],
                "remediated": results['remediated'],
                "skipped": results['skipped'],
                "failed": results['failed']
            },
            "details": results['details']
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Bulk remediation failed: {str(e)}")

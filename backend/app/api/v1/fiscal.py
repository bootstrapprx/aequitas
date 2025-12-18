"""
API endpoints for the Fiscal Engine.

All endpoints return tax exposure estimates with mandatory disclaimers.
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.tax_run import TaxRun
from app.db.models.tax_position import TaxPosition
from app.db.models.tax_fact import TaxFact
from app.db.models.tax_adjustment import TaxAdjustment
from app.api.v1.auth import get_current_user
from app.services.permission_service import PermissionService
from app.services.fiscal_engine import (
    ProfileService,
    CalculationService,
    ConsolidationService
)
from app.schemas.fiscal_engine import (
    EntityTaxProfileCreate,
    EntityTaxProfileUpdate,
    EntityTaxProfileResponse,
    TaxRunRequest,
    TaxRunConsolidatedRequest,
    TaxRunResponse,
    TaxRunDetailResponse,
    TaxPositionResponse,
    TaxFactResponse,
    TaxAdjustmentResponse,
    LatestPositionResponse
)

router = APIRouter()


# ===== Profile Endpoints =====

@router.post("/profile/{company_id}", response_model=EntityTaxProfileResponse)
def upsert_tax_profile(
    company_id: UUID,
    profile_data: EntityTaxProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create or update tax profile for a company.

    Requires user to have access to the company.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_edit_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to edit this company")

    profile_service = ProfileService(db)

    # Check if profile exists
    existing = profile_service.get_profile(company_id)

    if existing:
        # Update existing profile
        profile = profile_service.update_profile(company_id, profile_data)
    else:
        # Create new profile
        create_data = EntityTaxProfileCreate(
            company_id=company_id,
            **profile_data.model_dump(exclude_unset=True)
        )
        profile = profile_service.create_profile(create_data)

    return profile


@router.get("/profile/{company_id}", response_model=EntityTaxProfileResponse)
def get_tax_profile(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get tax profile for a company.

    Returns default profile if none exists.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view this company")

    profile_service = ProfileService(db)
    profile = profile_service.get_or_create_profile(company_id)

    return profile


# ===== Tax Run Endpoints =====

@router.post("/runs/company/{company_id}", response_model=TaxRunResponse)
def run_company_tax_calculation(
    company_id: UUID,
    run_request: TaxRunRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run tax exposure calculation for a single company.

    Returns:
        Tax run with status, confidence score, and missing inputs.
        Response includes mandatory disclaimer label.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to run calculations for this company")

    # Override company_id from path
    run_request.company_id = company_id

    calc_service = CalculationService(db)
    try:
        tax_run = calc_service.run_company_exposure(
            company_id=company_id,
            period_start=run_request.period_start,
            period_end=run_request.period_end,
            as_of_date=run_request.as_of_date,
            ruleset_version=run_request.ruleset_version
        )
        return tax_run
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tax calculation failed: {str(e)}")


@router.post("/runs/consolidated", response_model=TaxRunResponse)
def run_consolidated_tax_calculation(
    run_request: TaxRunConsolidatedRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Run consolidated tax exposure calculation across multiple companies.

    User must have access to all specified companies.
    """
    # Check permissions for all companies
    perm_service = PermissionService(db)
    for company_id in run_request.company_ids:
        if not perm_service.can_view_company(current_user.id, company_id):
            raise HTTPException(
                status_code=403,
                detail=f"No permission to run calculations for company {company_id}"
            )

    consol_service = ConsolidationService(db)
    try:
        tax_run = consol_service.run_consolidated_exposure(
            company_ids=run_request.company_ids,
            period_start=run_request.period_start,
            period_end=run_request.period_end,
            as_of_date=run_request.as_of_date,
            ruleset_version=run_request.ruleset_version
        )
        return tax_run
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Consolidated calculation failed: {str(e)}")


@router.get("/runs/{run_id}", response_model=TaxRunDetailResponse)
def get_tax_run(
    run_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get detailed tax run information including facts, adjustments, and position.
    """
    tax_run = db.query(TaxRun).filter(TaxRun.id == run_id).first()
    if not tax_run:
        raise HTTPException(status_code=404, detail="Tax run not found")

    # Check permissions
    if tax_run.company_id:
        perm_service = PermissionService(db)
        if not perm_service.can_view_company(current_user.id, tax_run.company_id):
            raise HTTPException(status_code=403, detail="No permission to view this tax run")

    # Get facts summary
    facts = db.query(TaxFact).filter(TaxFact.tax_run_id == run_id).all()
    facts_summary = {
        "total_facts": len(facts),
        "total_amount": float(sum(f.amount for f in facts))
    }

    # Get adjustments summary
    adjustments = db.query(TaxAdjustment).filter(TaxAdjustment.tax_run_id == run_id).all()
    adjustments_summary = {
        "total_adjustments": len(adjustments),
        "total_amount": float(sum(a.amount for a in adjustments))
    }

    # Get position
    position = db.query(TaxPosition).filter(TaxPosition.tax_run_id == run_id).first()

    return TaxRunDetailResponse(
        **tax_run.__dict__,
        facts_summary=facts_summary,
        adjustments_summary=adjustments_summary,
        position=position
    )


@router.get("/positions/latest", response_model=LatestPositionResponse)
def get_latest_position(
    company_id: UUID = Query(..., description="Company ID"),
    tax_type: str = Query("PASS_THROUGH_INCOME", description="Tax type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the latest tax position for a company.
    """
    # Check permissions
    perm_service = PermissionService(db)
    if not perm_service.can_view_company(current_user.id, company_id):
        raise HTTPException(status_code=403, detail="No permission to view this company")

    # Find latest position
    position = db.query(TaxPosition).join(TaxRun).filter(
        TaxPosition.company_id == company_id,
        TaxPosition.tax_type == tax_type
    ).order_by(TaxRun.created_at.desc()).first()

    if not position:
        return LatestPositionResponse(position=None, run=None)

    # Get the associated run
    run = db.query(TaxRun).filter(TaxRun.id == position.tax_run_id).first()

    return LatestPositionResponse(position=position, run=run)

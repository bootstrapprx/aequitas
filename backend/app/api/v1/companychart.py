"""API endpoints for managing company-specific charts of accounts."""

from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.services.companychart_service import CompanyChartService
from app.schemas.company_account import (
    CompanyAccountSchema,
    CompanyAccountCreate,
    CompanyAccountUpdate
)

router = APIRouter()


@router.get("/companies/{company_id}/chart", response_model=List[CompanyAccountSchema])
def get_company_chart(
    company_id: UUID,
    active_only: bool = Query(True, description="Filter only active accounts"),
    db: Session = Depends(get_db)
):
    """Get all accounts for a company's chart of accounts."""
    service = CompanyChartService(db)
    accounts = service.get_company_chart(company_id, active_only=active_only)
    return accounts


@router.get("/companies/{company_id}/chart/tree", response_model=List[Dict[str, Any]])
def get_company_chart_tree(
    company_id: UUID,
    active_only: bool = Query(True, description="Filter only active accounts"),
    db: Session = Depends(get_db)
):
    """Get company's chart of accounts as a hierarchical tree structure."""
    service = CompanyChartService(db)
    accounts = service.get_company_chart(company_id, active_only=active_only)
    tree = service.build_tree(accounts)
    return tree


@router.get("/companies/{company_id}/chart/stats", response_model=Dict[str, Any])
def get_company_chart_stats(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """Get statistics about a company's chart of accounts."""
    service = CompanyChartService(db)
    stats = service.get_chart_stats(company_id)
    return stats


@router.get("/companies/{company_id}/chart/{code}", response_model=CompanyAccountSchema)
def get_company_account_by_code(
    company_id: UUID,
    code: str,
    db: Session = Depends(get_db)
):
    """Get a specific account by code."""
    service = CompanyChartService(db)
    account = service.get_account_by_code(company_id, code)
    if not account:
        raise HTTPException(status_code=404, detail=f"Account with code {code} not found")
    return account


@router.post("/companies/{company_id}/chart", response_model=CompanyAccountSchema, status_code=201)
def create_company_account(
    company_id: UUID,
    account_data: CompanyAccountCreate,
    db: Session = Depends(get_db)
):
    """Create a new account in the company's chart of accounts."""
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
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/companies/{company_id}/chart/{code}", response_model=CompanyAccountSchema)
def update_company_account(
    company_id: UUID,
    code: str,
    account_data: CompanyAccountUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing account in the company's chart of accounts."""
    service = CompanyChartService(db)
    try:
        account = service.update_account(company_id, code, account_data)
        if not account:
            raise HTTPException(status_code=404, detail=f"Account with code {code} not found")
        return account
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/companies/{company_id}/chart/{code}", status_code=204)
def delete_company_account(
    company_id: UUID,
    code: str,
    db: Session = Depends(get_db)
):
    """Delete (soft delete) an account from the company's chart of accounts."""
    service = CompanyChartService(db)
    try:
        success = service.delete_account(company_id, code)
        if not success:
            raise HTTPException(status_code=404, detail=f"Account with code {code} not found")
        return None
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/companies/{company_id}/chart/reset", response_model=Dict[str, Any])
def reset_company_chart_to_master(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Reset company's chart of accounts to match the master chart.
    This will deactivate all existing accounts and create new ones from master.
    """
    service = CompanyChartService(db)
    try:
        result = service.reset_to_master_chart(company_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/companies/{company_id}/chart/initialize", response_model=Dict[str, Any])
def initialize_company_chart(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Initialize company's chart of accounts from master chart.
    This is typically called automatically during company creation,
    but can be called manually for companies that were created before this feature.
    """
    service = CompanyChartService(db)
    try:
        result = service.initialize_from_master_chart(company_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from app.db.session import get_db
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyInactivate
from app.services.company_service import CompanyService

router = APIRouter()

@router.get("/", response_model=list[CompanyResponse])
def list_companies(
    status: str = "active",
    db: Session = Depends(get_db)
):
    """
    Get all companies.
    Query param `status` can be "active", "inactive", or "all".
    """
    if status == "active":
        return CompanyService.get_all_companies(db, active_only=True)
    elif status == "inactive":
        # Get all and filter in python (or update service to handle this better)
        # For now, let's update service to handle 'active_only' as a filter?
        # Service currently has `active_only: bool`.
        # Let's fetch all and filter here if needed, or better, update service.
        # But for now, let's just use what we have.
        all_companies = CompanyService.get_all_companies(db, active_only=False)
        return [c for c in all_companies if not c.is_active]
    else:
        return CompanyService.get_all_companies(db, active_only=False)

@router.post("/", response_model=CompanyResponse)
def create_company(
    company_in: CompanyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new company and generate its UCID.
    """
    try:
        return CompanyService.create_company(db, company_in)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{company_id}", response_model=CompanyResponse)
def get_company_by_id(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get a company by its ID.
    """
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.get("/ucid/{ucid}", response_model=CompanyResponse)
def get_company_by_ucid(
    ucid: str,
    db: Session = Depends(get_db)
):
    """
    Get a company by its UCID.
    """
    company = CompanyService.get_company_by_ucid(db, ucid)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    company_update: CompanyUpdate,
    db: Session = Depends(get_db)
):
    """
    Update a company.
    """
    company = CompanyService.update_company(db, company_id, company_update)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.delete("/{company_id}")
def delete_company(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Soft delete a company.
    """
    success = CompanyService.delete_company(db, company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted successfully"}

@router.patch("/{ucid}/inactivate", response_model=CompanyResponse)
def inactivate_company(
    ucid: str,
    confirmation: CompanyInactivate,
    db: Session = Depends(get_db)
    # TODO: Add user dependency to get user_id
):
    """
    Inactivate a company. Requires name confirmation.
    """
    try:
        # Mock user_id for now until auth is fully integrated in this context
        user_id = "system" 
        return CompanyService.inactivate_company(db, ucid, confirmation.confirmation, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{ucid}/activate", response_model=CompanyResponse)
def activate_company(
    ucid: str,
    confirmation: CompanyInactivate,
    db: Session = Depends(get_db)
):
    """
    Activate a company. Requires name confirmation.
    """
    try:
        user_id = "system"
        return CompanyService.activate_company(db, ucid, confirmation.confirmation, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{ucid}/restore", response_model=CompanyResponse, deprecated=True)
def restore_company(
    ucid: str,
    db: Session = Depends(get_db)
):
    """
    Restore a soft-deleted company. Deprecated in favor of /activate.
    """
    company = CompanyService.restore_company(db, ucid)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

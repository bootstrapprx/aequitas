from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.api.v1.auth import get_current_user
from app.schemas.company import CompanyCreate, CompanyUpdate, CompanyResponse, CompanyInactivate
from app.db.models.company import SubscriptionType
from app.schemas.user import UserResponse
from app.services.company_service import CompanyService
from app.services.permission_service import PermissionService

router = APIRouter()

def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.replace("Bearer ", "")
    try:
        return get_current_user(token, db)
    except:
        return None

@router.get("/", response_model=list[CompanyResponse])
def list_companies(
    status: str = "active",
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
):
    """
    Get companies accessible to the current user.

    If not authenticated: Returns empty list (this should be a protected page)
    If authenticated as SuperUser: Returns all companies
    If authenticated as regular user: Returns only companies they're assigned to

    Query param `status` can be "active", "inactive", or "all".
    """
    from app.services.permission_service import PermissionService

    # If not authenticated, return empty list
    if not current_user:
        return []

    # Get all companies based on status filter
    if status == "active":
        all_companies = CompanyService.get_all_companies(db, active_only=True)
    elif status == "inactive":
        all_companies = CompanyService.get_all_companies(db, active_only=False)
        all_companies = [c for c in all_companies if not c.is_active]
    else:
        all_companies = CompanyService.get_all_companies(db, active_only=False)

    # Filter by user access if not superuser
    if not current_user.is_superuser:
        permission_service = PermissionService(db)
        user_company_ids = [
            uc.company_id for uc in permission_service.get_user_companies(current_user.id)
        ]
        all_companies = [c for c in all_companies if c.id in user_company_ids]

    return all_companies

@router.post("/", response_model=CompanyResponse)
def create_company(
    company_in: CompanyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new company and generate its UCID.
    """
    if company_in.subscription_type == SubscriptionType.NATIVE and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only superusers can create native subscriptions."
        )
    if company_in.subscription_type == SubscriptionType.NATIVE and not current_user.is_superuser:
        raise HTTPException(
            status_code=403,
            detail="Only superusers can create native subscriptions."
        )
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

@router.get("/{company_id}/users", response_model=List[UserResponse])
def get_company_users(
    company_id: UUID,
    db: Session = Depends(get_db)
):
    """
    Get all users assigned to a specific company.

    Args:
        company_id: UUID of the company
        db: Database session

    Returns:
        List of users with access to the company
    """
    # Verify company exists
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")

    # Get all user-company relationships for this company
    permission_service = PermissionService(db)
    user_companies = permission_service.get_company_users(company_id)

    # Extract users from the relationships
    users = [uc.user for uc in user_companies]
    return users

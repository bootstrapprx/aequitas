from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List, Optional
from app.db.session import get_db
from app.db.models.user import User
from app.api.v1.auth import get_current_user
from app.schemas.company import (
    CompanyCreate, 
    CompanyUpdate, 
    CompanyResponse, 
    CompanyInactivate, 
    CompanyChartStatus,
    CompanyDashboardStats,
    DashboardActivity
)
from app.db.models.company import SubscriptionType
from app.db.models.master_account import MasterAccount
from app.db.models.company_account import CompanyAccount
from app.db.models.audit_log import AuditLog
from app.db.models.user_company import UserCompany
from app.schemas.user import UserResponse
from app.services.company_service import CompanyService
from app.services.permission_service import PermissionService
from app.core.access_control import require_company_access
from sqlalchemy import or_, cast
from sqlalchemy.dialects.postgresql import JSONB

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

    try:
        # Create the company
        company = CompanyService.create_company(db, company_in)

        # Assign creating user as admin
        permission_service = PermissionService(db)
        try:
            permission_service.assign_user_to_company(
                user_id=current_user.id,
                company_id=company.id,
                is_admin=True,
                can_edit=True,
                can_view=True
            )
        except ValueError:
            # User already assigned (idempotent)
            pass

        return company
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{company_id}", response_model=CompanyResponse)
def get_company_by_id(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a company by its ID.
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=True,
    )
    company = CompanyService.get_company_by_id(db, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.get("/ucid/{ucid}", response_model=CompanyResponse)
def get_company_by_ucid(
    ucid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a company by its UCID.
    """
    company = CompanyService.get_company_by_ucid(db, ucid)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    require_company_access(
        db,
        current_user,
        company.id,
        require_admin=False,
        allow_superuser=True,
    )
    return company

@router.put("/{company_id}", response_model=CompanyResponse)
def update_company(
    company_id: UUID,
    company_update: CompanyUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a company.
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )
    company = CompanyService.update_company(db, company_id, company_update)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.delete("/{company_id}")
def delete_company(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Soft delete a company.
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )
    success = CompanyService.delete_company(db, company_id)
    if not success:
        raise HTTPException(status_code=404, detail="Company not found")
    return {"message": "Company deleted successfully"}

@router.patch("/{ucid}/inactivate", response_model=CompanyResponse)
def inactivate_company(
    ucid: str,
    confirmation: CompanyInactivate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
    # TODO: Add user dependency to get user_id
):
    """
    Inactivate a company. Requires name confirmation.
    """
    try:
        company = CompanyService.get_company_by_ucid(db, ucid)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        require_company_access(
            db,
            current_user,
            company.id,
            require_admin=True,
            allow_superuser=True,
        )
        user_id = str(current_user.id)
        return CompanyService.inactivate_company(db, ucid, confirmation.confirmation, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.patch("/{ucid}/activate", response_model=CompanyResponse)
def activate_company(
    ucid: str,
    confirmation: CompanyInactivate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Activate a company. Requires name confirmation.
    """
    try:
        company = CompanyService.get_company_by_ucid(db, ucid)
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        require_company_access(
            db,
            current_user,
            company.id,
            require_admin=True,
            allow_superuser=True,
        )
        user_id = str(current_user.id)
        return CompanyService.activate_company(db, ucid, confirmation.confirmation, user_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{ucid}/restore", response_model=CompanyResponse, deprecated=True)
def restore_company(
    ucid: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Restore a soft-deleted company. Deprecated in favor of /activate.
    """
    company = CompanyService.get_company_by_ucid(db, ucid)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    require_company_access(
        db,
        current_user,
        company.id,
        require_admin=True,
        allow_superuser=True,
    )
    company = CompanyService.restore_company(db, ucid)
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
    return company

@router.get("/{company_id}/users-basic", response_model=List[UserResponse])
def get_company_users_basic(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all users assigned to a specific company (basic profile view).

    Args:
        company_id: UUID of the company
        db: Database session

    Returns:
        List of users with access to the company
    """
    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=True,
        allow_superuser=True,
    )
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


@router.get("/{company_id}/chart-status", response_model=CompanyChartStatus)
def get_company_chart_status(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get company-scoped chart initialization status.
    
    Start of Canonical Fix:
    - Replaces admin-based status check
    - Enforces strict company membership (no superuser bypass)
    - Returns only data relevant to this company
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=False,
    )
    
    # Master chart status (Global check, but context-aware)
    master_count = db.query(MasterAccount).count()
    
    # Company chart status
    company_accounts = db.query(CompanyAccount).filter(
        CompanyAccount.company_id == company_id,
        CompanyAccount.is_active == True
    ).all()
    
    account_count = len(company_accounts)
    
    # Mapping coverage calculation
    mapped_count = sum(1 for acc in company_accounts if acc.mapped_master_account_id)
    coverage = (mapped_count / account_count * 100) if account_count > 0 else 0.0
    
    # Determine Onboarding Status
    if account_count == 0:
        status = "not_started"
    elif coverage < 100:
        # In a real scenario, we might check for specific mandatory accounts
        status = "in_progress" 
    else:
        status = "ready"

    return {
        "master_chart_loaded": master_count > 0,
        "company_chart_initialized": account_count > 0,
        "account_count": account_count,
        "mapping_coverage": round(coverage, 2),
        "onboarding_status": status
    }


@router.get("/{company_id}/dashboard-stats", response_model=CompanyDashboardStats)
def get_company_dashboard_stats(
    company_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get aggregated dashboard statistics for a company.
    
    Includes:
    - Chart Status (reused logic)
    - Active User Count
    - Pending Reviews (Unmapped Accounts)
    - Recent Activity (Audit Logs)
    """
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    require_company_access(
        db,
        current_user,
        company_id,
        require_admin=False,
        allow_superuser=True,
    )
    
    # 2. Chart Status Logic (Inlined for performance/atomicity)
    master_count = db.query(MasterAccount).count()
    company_accounts = db.query(CompanyAccount).filter(
        CompanyAccount.company_id == company_id,
        CompanyAccount.is_active == True
    ).all()
    
    account_count = len(company_accounts)
    mapped_count = sum(1 for acc in company_accounts if acc.mapped_master_account_id)
    coverage = (mapped_count / account_count * 100) if account_count > 0 else 0.0
    
    if account_count == 0:
        onboarding_status = "not_started"
    elif coverage < 100:
        onboarding_status = "in_progress"
    else:
        onboarding_status = "ready"

    chart_status = {
        "master_chart_loaded": master_count > 0,
        "company_chart_initialized": account_count > 0,
        "account_count": account_count,
        "mapping_coverage": round(coverage, 2),
        "onboarding_status": onboarding_status
    }

    # 3. Active User Count
    active_users_count = db.query(UserCompany).filter(
        UserCompany.company_id == company_id
    ).count()

    # 4. Pending Reviews (Unmapped Accounts)
    # We define "Pending Reviews" as accounts that need mapping attention
    pending_reviews_count = account_count - mapped_count

    # 5. Recent Activity (Audit Logs)
    # Fetch logs where entity_id IS company_id OR payload has company_id
    # We use cast to JSONB to ensure 'astext' accessor works even if column is generic JSON
    recent_logs = db.query(AuditLog).filter(
        or_(
            AuditLog.entity_id == str(company_id),
            cast(AuditLog.payload, JSONB)['company_id'].astext == str(company_id)
        )
    ).order_by(AuditLog.timestamp.desc()).limit(5).all()

    formatted_activity = []
    for log in recent_logs:
        # Determine accessible user name (without exposing PII if possible)
        # For now, we use user_id or "System"
        actor = "System"
        if log.user_id:
             # Ideally fetch user name, but careful with N+1. 
             # For MVP dashboard, "User X" or logic to fetch names if needed.
             # We'll fetch the user email if we have it in session, otherwise generic.
             actor_user = db.query(User).filter(User.id == log.user_id).first()
             if actor_user:
                 actor = actor_user.email.split('@')[0]
        
        # Determine Type for UI Color
        activity_type = "info"
        if "ERROR" in log.action or "FAIL" in log.action:
            activity_type = "warning"
        elif "SUCCESS" in log.action or "CREATE" in log.action:
            activity_type = "success"
        elif "MAPPING" in log.action:
            activity_type = "mapping"

        formatted_activity.append({
            "id": log.id,
            "user": actor,
            "action": log.action.replace('_', ' ').title(),
            "timestamp": log.timestamp,
            "type": activity_type
        })

    # 6. Account Distribution
    distribution = {
        "Asset": 0,
        "Liability": 0,
        "Equity": 0,
        "Revenue": 0,
        "Expense": 0
    }
    for acc in company_accounts:
        # account_type is an Enum, getting value. Title case just in case.
        if acc.account_type:
            # Assumes AccountType enum values are standard strings or comparable
            atype = str(acc.account_type.value if hasattr(acc.account_type, 'value') else acc.account_type)
            # Simple mapping or usage
            if "Asset" in atype: distribution["Asset"] += 1
            elif "Liability" in atype: distribution["Liability"] += 1
            elif "Equity" in atype: distribution["Equity"] += 1
            elif "Revenue" in atype: distribution["Revenue"] += 1
            elif "Expense" in atype: distribution["Expense"] += 1

    return {
        "chart_status": chart_status,
        "active_users_count": active_users_count,
        "pending_reviews_count": pending_reviews_count,
        "recent_activity": formatted_activity,
        "account_distribution": distribution
    }

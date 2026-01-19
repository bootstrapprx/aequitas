"""
Admin API endpoints for superuser operations.
All endpoints require superuser privileges.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.session import get_db
from app.db.models.user import User
from app.db.models.company import Company
from app.api.v1.auth import get_current_user
from app.core.security import check_superuser
from app.schemas.user import (
    UserResponse,
    CouncilMemberCreate,
    CouncilMemberCreateResponse
)
from app.schemas.system_settings import SystemSettingsResponse, SystemSettingsUpdate
from app.services.admin_service import AdminService
from app.core.kernel import L0_KERNEL_CODES
from app.services.kernel_remediation_service import KernelRemediationService
from app.services.council_service import CouncilService
from app.core.password_policy import PasswordPolicy

router = APIRouter()


# Dependency to get admin service
def get_admin_service(db: Session = Depends(get_db)) -> AdminService:
    return AdminService(db)


@router.get("/users", response_model=List[UserResponse])
def get_all_users(
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service),
    db: Session = Depends(get_db)
):
    """
    Get all users in the system with their company associations.
    Requires superuser privileges.
    """
    # Check superuser
    check_superuser(current_user)

    users = admin_service.get_all_users()
    return users


@router.put("/users/{user_id}/promote", response_model=UserResponse)
def promote_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Promote a user to superuser.
    Requires superuser privileges.
    """
    # Check superuser
    check_superuser(current_user)

    try:
        user = admin_service.promote_user(user_id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put("/users/{user_id}/demote", response_model=UserResponse)
def demote_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Demote a user from superuser.
    Requires superuser privileges.
    Safety rule: A superuser cannot demote themselves.
    """
    # Check superuser
    check_superuser(current_user)

    try:
        user = admin_service.demote_user(user_id, current_user.id)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/settings", response_model=SystemSettingsResponse)
def get_settings(
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Get system settings.
    Requires superuser privileges.
    """
    # Check superuser
    check_superuser(current_user)

    return admin_service.get_settings()


@router.put("/settings", response_model=SystemSettingsResponse)
def update_settings(
    settings: SystemSettingsUpdate,
    current_user: User = Depends(get_current_user),
    admin_service: AdminService = Depends(get_admin_service)
):
    """
    Update system settings.
    Requires superuser privileges.
    """
    # Check superuser
    check_superuser(current_user)

    return admin_service.update_settings(settings)


@router.post("/migrate-company-charts")
def migrate_company_charts(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ensure existing companies have required kernel accounts.
    Requires superuser privileges.
    """
    # Check superuser
    check_superuser(current_user)

    remediation_service = KernelRemediationService(db)

    # Get all active companies
    companies = db.query(Company).filter(Company.is_active == True).all()

    results = {
        "total_companies": len(companies),
        "remediated": 0,
        "skipped": 0,
        "errors": [],
        "details": []
    }

    for company in companies:
        try:
            missing = remediation_service.get_missing_kernel_accounts(company.id)
            if not missing:
                results["skipped"] += 1
                results["details"].append({
                    "company_id": str(company.id),
                    "ucid": company.ucid,
                    "name": company.name,
                    "status": "skipped",
                    "reason": "Kernel accounts already present"
                })
                continue

            remediation_result = remediation_service.auto_remediate_company(company.id, dry_run=False)
            results["remediated"] += 1
            results["details"].append({
                "company_id": str(company.id),
                "ucid": company.ucid,
                "name": company.name,
                "status": "remediated",
                "accounts_added": remediation_result.get("added_count", 0),
                "added_codes": remediation_result.get("added_codes", []),
            })
        except Exception as e:
            results["errors"].append({
                "company_id": str(company.id),
                "ucid": company.ucid,
                "name": company.name,
                "error": str(e)
            })

    return results


@router.get("/chart-status")
def get_chart_initialization_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get status of kernel compliance and optional master chart catalog.
    Requires superuser privileges.
    """
    # Check superuser
    check_superuser(current_user)

    from app.db.models.master_account import MasterAccount

    # Master chart status
    master_count = db.query(MasterAccount).count()

    # Companies status
    companies = db.query(Company).filter(Company.is_active == True).all()

    remediation_service = KernelRemediationService(db)
    company_status = []
    kernel_compliant = 0
    kernel_missing = 0
    for company in companies:
        missing_codes = remediation_service.get_missing_kernel_accounts(company.id)
        missing_count = len(missing_codes)
        status = "kernel_compliant" if missing_count == 0 else "missing_kernel"

        if missing_count == 0:
            kernel_compliant += 1
        else:
            kernel_missing += 1

        company_status.append({
            "company_id": str(company.id),
            "ucid": company.ucid,
            "name": company.name,
            "status": status,
            "missing_kernel_codes": missing_codes,
        })

    return {
        "catalog": {
            "loaded": master_count > 0,
            "account_count": master_count,
        },
        "kernel": {
            "required_count": len(L0_KERNEL_CODES),
            "required_codes": sorted(L0_KERNEL_CODES),
        },
        "companies": {
            "total": len(companies),
            "kernel_compliant": kernel_compliant,
            "kernel_missing": kernel_missing,
            "details": company_status
        }
    }


# --- Council Member (Super User) Management ---

@router.post("/council-members", response_model=CouncilMemberCreateResponse, status_code=status.HTTP_201_CREATED)
def create_council_member(
    member_data: CouncilMemberCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new Council Member (Super User) account.

    SECURITY:
    - Only accessible to existing Council Members (superusers)
    - Enforces strict password policy (12+ chars, complexity requirements)
    - Auto-generates secure password if not provided
    - Forces password reset on first login
    - All operations are audited

    CRITICAL:
    - The temporary password is ONLY shown in this response
    - It cannot be retrieved later
    - Securely communicate this to the new Council Member

    Args:
        member_data: Council member creation data (email, optional password)
        current_user: Current authenticated user (must be superuser)
        db: Database session

    Returns:
        CouncilMemberCreateResponse with user details and temporary password

    Raises:
        403: If current user is not a Council Member
        400: If user already exists or password policy violation
    """
    # Check superuser privilege
    check_superuser(current_user)

    council_service = CouncilService(db)

    try:
        # Create the Council Member
        new_member, temporary_password = council_service.create_council_member(
            member_data=member_data,
            creator_id=current_user.id
        )

        # Build response with password (ONLY time it's visible)
        response = CouncilMemberCreateResponse(
            user=UserResponse.from_orm(new_member),
            temporary_password=temporary_password,
            password_policy=PasswordPolicy.get_policy_description(is_privileged=True),
            force_password_reset=True,
            message=(
                "Council Member account created successfully. "
                "IMPORTANT: Save this password securely - it will not be shown again. "
                "The user must change this password on first login."
            )
        )

        return response

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/council-members", response_model=List[UserResponse])
def list_council_members(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all active Council Members.

    SECURITY:
    - Only accessible to Council Members
    - Returns sanitized user information (no passwords)

    Args:
        current_user: Current authenticated user (must be superuser)
        db: Database session

    Returns:
        List of UserResponse objects for all Council Members

    Raises:
        403: If current user is not a Council Member
    """
    check_superuser(current_user)

    council_service = CouncilService(db)
    members = council_service.list_council_members()

    return [UserResponse.from_orm(member) for member in members]


@router.delete("/council-members/{member_id}", response_model=UserResponse)
def revoke_council_membership(
    member_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Revoke Council Member privileges from a user.

    SECURITY:
    - Only accessible to Council Members
    - Cannot revoke own privileges (prevents lockout)
    - Cannot revoke last Council Member (prevents system lockout)
    - All operations are audited

    Args:
        member_id: UUID of the Council Member to revoke
        current_user: Current authenticated user (must be superuser)
        db: Database session

    Returns:
        UserResponse of the demoted user

    Raises:
        403: If current user is not a Council Member or trying to revoke themselves
        400: If user not found or invalid operation
    """
    check_superuser(current_user)

    council_service = CouncilService(db)

    try:
        demoted_user = council_service.revoke_council_membership(
            member_id=member_id,
            revoker_id=current_user.id
        )

        return UserResponse.from_orm(demoted_user)

    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

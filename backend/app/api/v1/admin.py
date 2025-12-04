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
from app.api.v1.auth import get_current_user
from app.core.security import check_superuser
from app.schemas.user import UserResponse
from app.schemas.system_settings import SystemSettingsResponse, SystemSettingsUpdate
from app.services.admin_service import AdminService

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

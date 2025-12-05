"""
Users Management API Routes.

Provides endpoints for managing users with company assignments and permissions.
Enforces strict access control based on superuser and company admin roles.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging

from app.db.session import get_db
from app.db.models.user import User
from app.api.v1.auth import get_current_user
from app.services.users_management_service import UsersManagementService
from app.schemas.user_management import (
    UserListItem,
    UserDetail,
    UserCreateRequest,
    UserUpdateRequest,
    UserCreateResponse,
    UserDeactivateRequest,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def get_users_management_service(db: Session = Depends(get_db)) -> UsersManagementService:
    """Dependency to get users management service."""
    return UsersManagementService(db)


@router.get("/admin/users", response_model=List[UserListItem])
def list_all_users(
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Max results per page"),
    search: Optional[str] = Query(None, description="Search by email"),
    current_user: User = Depends(get_current_user),
    service: UsersManagementService = Depends(get_users_management_service)
):
    """
    List all users in the system (superuser only).

    Returns all users with their company assignments, roles, and status.
    Supports pagination and email search.

    **Permissions:**
    - Requires superuser access

    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - search: Optional email search filter (case-insensitive)

    **Returns:**
    - List of UserListItem with basic user info and company assignments
    """
    try:
        return service.list_all_users(
            current_user=current_user,
            skip=skip,
            limit=limit,
            search=search
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing all users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.get("/companies/{company_id}/users", response_model=List[UserListItem])
def list_company_users(
    company_id: UUID,
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=1000, description="Max results per page"),
    search: Optional[str] = Query(None, description="Search by email"),
    current_user: User = Depends(get_current_user),
    service: UsersManagementService = Depends(get_users_management_service)
):
    """
    List all users belonging to a specific company.

    Returns users assigned to the specified company with their roles and status.

    **Permissions:**
    - Superuser: Can list users for any company
    - Company admin: Can ONLY list users for their own company

    **Parameters:**
    - company_id: UUID of the company

    **Query Parameters:**
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return
    - search: Optional email search filter (case-insensitive)

    **Returns:**
    - List of UserListItem for users in the specified company
    """
    try:
        return service.list_users_by_company(
            company_id=company_id,
            current_user=current_user,
            skip=skip,
            limit=limit,
            search=search
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing users for company {company_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list company users"
        )


@router.get("/users/{user_id}", response_model=UserDetail)
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UsersManagementService = Depends(get_users_management_service)
):
    """
    Get detailed information about a specific user.

    Returns complete user information including all company assignments,
    roles, permissions, and metadata.

    **Permissions:**
    - Superuser: Can view any user
    - Company admin: Can view users in their companies

    **Parameters:**
    - user_id: UUID of the user to retrieve

    **Returns:**
    - UserDetail with complete user information
    """
    try:
        return service.get_user_details(
            user_id=user_id,
            current_user=current_user
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user details"
        )


@router.post("/users", response_model=UserCreateResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    request: UserCreateRequest,
    current_user: User = Depends(get_current_user),
    service: UsersManagementService = Depends(get_users_management_service)
):
    """
    Create a new user with company assignments.

    Creates a new user account and assigns them to one or more companies
    with specified roles and permissions.

    **Permissions:**
    - Superuser: Can create users and assign ANY companies
    - Company admin: Can create users ONLY in their own companies

    **Validation Rules:**
    - Email must be unique
    - Must assign at least one company (unless creating superuser)
    - Company admin cannot assign companies they don't administer
    - Password is optional; if not provided, a temporary password is generated

    **Request Body:**
    - email: User's email address (unique)
    - password: Optional password (generated if omitted)
    - company_ids: List of company UUIDs (required, min 1)
    - company_roles: Optional role assignments per company
    - is_active: User active status (default: true)

    **Returns:**
    - UserCreateResponse with user details and temporary password (if generated)
    """
    try:
        return service.create_user_with_companies(
            request=request,
            current_user=current_user
        )
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
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.put("/users/{user_id}", response_model=UserDetail)
def update_user(
    user_id: UUID,
    request: UserUpdateRequest,
    current_user: User = Depends(get_current_user),
    service: UsersManagementService = Depends(get_users_management_service)
):
    """
    Update user information and company assignments.

    Updates user details, company assignments, roles, and permissions.
    All fields are optional; only provided fields will be updated.

    **Permissions:**
    - Superuser: Can update any user
    - Company admin: Can ONLY update users in their companies
    - Cannot modify superuser unless you are superuser
    - Cannot remove all company assignments (unless target is superuser)

    **Parameters:**
    - user_id: UUID of the user to update

    **Request Body (all optional):**
    - email: New email address
    - is_active: Active status
    - company_ids: New list of company assignments
    - company_roles: Role assignments per company
    - password: New password

    **Validation Rules:**
    - Must be admin of all current AND new companies (unless superuser)
    - Cannot orphan a user (remove all companies) unless user is superuser
    - Email must remain unique

    **Returns:**
    - Updated UserDetail
    """
    try:
        return service.update_user_with_companies(
            user_id=user_id,
            request=request,
            current_user=current_user
        )
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
    except Exception as e:
        logger.error(f"Error updating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post("/users/{user_id}/deactivate", response_model=UserDetail)
def deactivate_user(
    user_id: UUID,
    request: Optional[UserDeactivateRequest] = None,
    current_user: User = Depends(get_current_user),
    service: UsersManagementService = Depends(get_users_management_service)
):
    """
    Deactivate a user (soft delete).

    Sets user's is_active flag to False. User can be reactivated later.
    This is the recommended way for company admins to remove users.

    **Permissions:**
    - Superuser: Can deactivate anyone
    - Company admin: Can deactivate users in their companies

    **Restrictions:**
    - Cannot deactivate yourself
    - Cannot deactivate the last active superuser

    **Parameters:**
    - user_id: UUID of the user to deactivate

    **Request Body (optional):**
    - reason: Optional reason for deactivation (logged)

    **Returns:**
    - Updated UserDetail with is_active=False
    """
    try:
        return service.deactivate_user(
            user_id=user_id,
            current_user=current_user
        )
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
    except Exception as e:
        logger.error(f"Error deactivating user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    service: UsersManagementService = Depends(get_users_management_service)
):
    """
    Permanently delete a user (hard delete, superuser only).

    Permanently removes the user and all associated data from the database.
    This operation CANNOT be undone.

    **Permissions:**
    - ONLY superusers can hard delete users
    - Company admins should use deactivate instead

    **Restrictions:**
    - Cannot delete yourself
    - Cannot delete the last superuser

    **Parameters:**
    - user_id: UUID of the user to permanently delete

    **Returns:**
    - 204 No Content on success
    """
    try:
        service.delete_user(
            user_id=user_id,
            current_user=current_user
        )
        return None
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
    except Exception as e:
        logger.error(f"Error deleting user {user_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete user"
        )

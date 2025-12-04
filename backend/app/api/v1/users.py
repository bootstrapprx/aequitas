"""
User management API endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List

from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.api.deps import check_company_admin
from app.db.models.user import User
from app.db.models.company import Company
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from app.schemas.user_company import UserCompanyUpdate
from app.services.user_service import UserService
from app.services.permission_service import PermissionService
from app.services.company_service import CompanyService
from app.schemas.company import CompanyCreate

router = APIRouter()

@router.get("/", response_model=List[UserResponse])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all users. Only superusers can access this endpoint.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can list all users"
        )
    
    user_service = UserService(db)
    return user_service.get_all_users()

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user(
    user_data: UserCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new user.

    Permissions:
    - SuperUsers: Can create users for any company
    - Company Admins: Can create users only for companies they admin

    For initial company setup: provide is_initial_signup=True and company_name
    For adding to existing company: provide company_ids list
    """
    permission_service = PermissionService(db)
    user_service = UserService(db)

    # Handle initial sign-up (create company + user) - SuperUser only
    if user_data.is_initial_signup:
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superusers can create new companies with users"
            )

        if not user_data.company_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Company name is required for initial sign-up"
            )

        try:
            # Create company
            company_service = CompanyService()
            company_data = CompanyCreate(name=user_data.company_name)
            company = company_service.create_company(db, company_data)

            # Create user with company association
            user = user_service.create_user(user_data, company_ids=[company.id])

            # Make user admin of their company
            user_company = permission_service.get_user_company(user.id, company.id)
            if user_company:
                permission_service.update_user_company_permissions(
                    user.id,
                    company.id,
                    UserCompanyUpdate(is_admin=True)
                )

            db.refresh(user)
            return user
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    # Regular user creation - SuperUser or Company Admin
    company_ids = user_data.company_ids or []

    if not company_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one company_id must be provided"
        )

    # Check permissions
    if not current_user.is_superuser:
        # Get companies where current user is admin
        user_companies = permission_service.get_user_companies(current_user.id)
        admin_company_ids = [
            uc.company_id for uc in user_companies if uc.is_admin
        ]

        if not admin_company_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You must be a company admin to create users"
            )

        # Verify current user is admin of all requested companies
        for company_id in company_ids:
            if company_id not in admin_company_ids:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"You are not an admin of company {company_id}"
                )

    try:
        user = user_service.create_user(user_data, company_ids=company_ids)
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a user by ID. Users can only view their own profile unless they're superusers.
    """
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own profile"
        )
    
    user_service = UserService(db)
    user = user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

@router.put("/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a user. Users can only update their own profile unless they're superusers.
    Superusers can also update is_active and is_superuser flags.
    """
    if not current_user.is_superuser and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own profile"
        )
    
    # Non-superusers cannot update is_superuser flag
    if not current_user.is_superuser and hasattr(user_data, 'is_superuser'):
        user_data.is_superuser = None
    
    user_service = UserService(db)
    try:
        user = user_service.update_user(user_id, user_data)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user. Only superusers can delete users.
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only superusers can delete users"
        )
    
    if current_user.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot delete your own account"
        )
    
    user_service = UserService(db)
    try:
        success = user_service.delete_user(user_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


"""
Users Management Service - Business logic for user CRUD operations.

This service enforces the identity hierarchy:
- Superusers can manage all users globally
- Company admins can ONLY manage users within their own company(ies)
- Normal users cannot create or modify other users
- Users must belong to at least one company (except superuser)
"""
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from uuid import UUID
import secrets
import string
import logging

from app.db.models.user import User
from app.db.models.company import Company
from app.db.models.user_company import UserCompany
from app.schemas.user_management import (
    UserListItem,
    UserDetail,
    UserCreateRequest,
    UserUpdateRequest,
    UserCreateResponse,
    CompanyInfo,
    CompanyRoleAssignment,
)
from app.core.security import get_password_hash

logger = logging.getLogger(__name__)


class UsersManagementService:
    """Service for managing users with company assignments and permissions."""

    def __init__(self, db: Session):
        self.db = db

    def _generate_temp_password(self, length: int = 12) -> str:
        """Generate a secure temporary password."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))

    def _validate_superuser_or_company_admin(
        self,
        current_user: User,
        required_company_ids: Optional[List[UUID]] = None
    ) -> bool:
        """
        Validate that the current user is either:
        - A superuser (can do anything), OR
        - A company admin for ALL required companies

        Args:
            current_user: The user performing the action
            required_company_ids: Company IDs that need admin access (None = any admin)

        Returns:
            True if authorized

        Raises:
            PermissionError: If user lacks required permissions
        """
        if current_user.is_superuser:
            return True

        # Get companies where user is admin
        admin_company_ids = [
            uc.company_id
            for uc in current_user.user_companies
            if uc.is_admin
        ]

        if not admin_company_ids:
            raise PermissionError("User must be a company admin or superuser to manage users")

        # If specific companies required, check admin for ALL of them
        if required_company_ids:
            if not all(cid in admin_company_ids for cid in required_company_ids):
                raise PermissionError(
                    "User must be admin of all specified companies to perform this action"
                )

        return True

    def _get_user_companies_info(self, user: User) -> List[CompanyInfo]:
        """Get list of companies with admin status for a user."""
        companies_info = []
        for uc in user.user_companies:
            companies_info.append(CompanyInfo(
                id=uc.company.id,
                name=uc.company.name,
                ucid=uc.company.ucid,
                is_admin=uc.is_admin
            ))
        return companies_info

    def list_all_users(
        self,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[UserListItem]:
        """
        List all users in the system (superuser only).

        Args:
            current_user: Must be superuser
            skip: Pagination offset
            limit: Max results
            search: Optional email search filter

        Returns:
            List of UserListItem

        Raises:
            PermissionError: If user is not superuser
        """
        if not current_user.is_superuser:
            raise PermissionError("Only superusers can list all users")

        query = self.db.query(User).options(
            joinedload(User.user_companies).joinedload(UserCompany.company)
        )

        if search:
            query = query.filter(User.email.ilike(f"%{search}%"))

        users = query.offset(skip).limit(limit).all()

        return [
            UserListItem(
                id=user.id,
                email=user.email,
                user_uid=user.user_uid,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                companies=self._get_user_companies_info(user),
                last_login=None,  # TODO: Add last_login tracking
                created_at=user.created_at
            )
            for user in users
        ]

    def list_users_by_company(
        self,
        company_id: UUID,
        current_user: User,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None
    ) -> List[UserListItem]:
        """
        List all users belonging to a specific company.

        Args:
            company_id: Company to list users for
            current_user: Must be superuser or company admin for this company
            skip: Pagination offset
            limit: Max results
            search: Optional email search filter

        Returns:
            List of UserListItem

        Raises:
            PermissionError: If user lacks access
        """
        # Validate permissions
        self._validate_superuser_or_company_admin(current_user, [company_id])

        # Get all users in this company
        query = self.db.query(User).join(UserCompany).filter(
            UserCompany.company_id == company_id
        ).options(
            joinedload(User.user_companies).joinedload(UserCompany.company)
        )

        if search:
            query = query.filter(User.email.ilike(f"%{search}%"))

        users = query.offset(skip).limit(limit).all()

        return [
            UserListItem(
                id=user.id,
                email=user.email,
                user_uid=user.user_uid,
                is_active=user.is_active,
                is_superuser=user.is_superuser,
                companies=self._get_user_companies_info(user),
                last_login=None,
                created_at=user.created_at
            )
            for user in users
        ]

    def get_user_details(
        self,
        user_id: UUID,
        current_user: User
    ) -> UserDetail:
        """
        Get detailed information about a specific user.

        Args:
            user_id: User to retrieve
            current_user: Must be superuser or company admin for user's companies

        Returns:
            UserDetail

        Raises:
            PermissionError: If user lacks access
            ValueError: If user not found
        """
        user = self.db.query(User).options(
            joinedload(User.user_companies).joinedload(UserCompany.company)
        ).filter(User.id == user_id).first()

        if not user:
            raise ValueError("User not found")

        # Validate permissions (superuser or admin of any of user's companies)
        if not current_user.is_superuser:
            user_company_ids = [uc.company_id for uc in user.user_companies]
            self._validate_superuser_or_company_admin(current_user, user_company_ids)

        return UserDetail(
            id=user.id,
            email=user.email,
            user_uid=user.user_uid,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
            role=user.role,
            preferred_company_id=user.preferred_company_id,
            companies=self._get_user_companies_info(user),
            last_login=None,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    def create_user_with_companies(
        self,
        request: UserCreateRequest,
        current_user: User
    ) -> UserCreateResponse:
        """
        Create a new user with company assignments.

        Permission rules:
        - Superuser: Can assign ANY companies
        - Company admin: Can ONLY assign their own companies
        - Must assign at least one company (unless creating superuser)

        Args:
            request: UserCreateRequest with user data and company assignments
            current_user: User creating the new user

        Returns:
            UserCreateResponse with user details and temp password if generated

        Raises:
            PermissionError: If user lacks permissions
            ValueError: If validation fails
        """
        # Validate permissions for all requested companies
        self._validate_superuser_or_company_admin(current_user, request.company_ids)

        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == request.email).first()
        if existing_user:
            raise ValueError(f"User with email {request.email} already exists")

        # Validate all companies exist
        companies = self.db.query(Company).filter(Company.id.in_(request.company_ids)).all()
        if len(companies) != len(request.company_ids):
            raise ValueError("One or more companies not found")

        # Generate password if not provided
        temp_password = None
        if request.password:
            password = request.password
        else:
            password = self._generate_temp_password()
            temp_password = password

        try:
            # Create user
            new_user = User(
                email=request.email,
                hashed_password=get_password_hash(password),
                is_active=request.is_active,
                is_superuser=False,  # Only superusers can create other superusers
                role="COUNCIL_MEMBER",
                preferred_company_id=request.company_ids[0] if request.company_ids else None
            )

            self.db.add(new_user)
            self.db.flush()  # Get user ID

            # Create company assignments
            for company_id in request.company_ids:
                # Find role assignment for this company (if provided)
                role_assignment = None
                if request.company_roles:
                    role_assignment = next(
                        (r for r in request.company_roles if r.company_id == company_id),
                        None
                    )

                user_company = UserCompany(
                    user_id=new_user.id,
                    company_id=company_id,
                    is_admin=role_assignment.is_admin if role_assignment else False,
                    can_edit=role_assignment.can_edit if role_assignment else True,
                    can_view=role_assignment.can_view if role_assignment else True
                )
                self.db.add(user_company)

            self.db.commit()
            self.db.refresh(new_user)

            # Load relationships for response
            self.db.refresh(new_user)
            user_detail = self.get_user_details(new_user.id, current_user)

            logger.info(
                f"User created: {request.email} by {current_user.email} "
                f"with {len(request.company_ids)} company assignments"
            )

            return UserCreateResponse(
                user=user_detail,
                temporary_password=temp_password
            )

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise ValueError(f"Failed to create user: {e}")

    def update_user_with_companies(
        self,
        user_id: UUID,
        request: UserUpdateRequest,
        current_user: User
    ) -> UserDetail:
        """
        Update user information and company assignments.

        Permission rules:
        - Superuser: Can modify any user
        - Company admin: Can ONLY modify users in their companies
        - Cannot remove all company assignments (unless superuser modifying superuser)
        - Cannot modify superuser (unless you are superuser)

        Args:
            user_id: User to update
            request: UserUpdateRequest with fields to update
            current_user: User performing the update

        Returns:
            Updated UserDetail

        Raises:
            PermissionError: If user lacks permissions
            ValueError: If validation fails
        """
        # Get target user
        target_user = self.db.query(User).options(
            joinedload(User.user_companies)
        ).filter(User.id == user_id).first()

        if not target_user:
            raise ValueError("User not found")

        # Cannot modify superuser unless you are superuser
        if target_user.is_superuser and not current_user.is_superuser:
            raise PermissionError("Only superusers can modify other superusers")

        # Validate permissions for current companies
        current_company_ids = [uc.company_id for uc in target_user.user_companies]
        self._validate_superuser_or_company_admin(current_user, current_company_ids)

        # If changing companies, validate permissions for new companies
        if request.company_ids is not None:
            self._validate_superuser_or_company_admin(current_user, request.company_ids)

            # Prevent removing all companies (unless target is superuser)
            if len(request.company_ids) == 0 and not target_user.is_superuser:
                raise ValueError("Cannot remove all company assignments from non-superuser")

        try:
            # Update basic fields
            if request.email is not None:
                target_user.email = request.email

            if request.is_active is not None:
                target_user.is_active = request.is_active

            if request.password is not None:
                target_user.hashed_password = get_password_hash(request.password)

            # Update company assignments
            if request.company_ids is not None:
                # Remove existing assignments
                self.db.query(UserCompany).filter(
                    UserCompany.user_id == user_id
                ).delete(synchronize_session='fetch')

                # Add new assignments
                for company_id in request.company_ids:
                    # Find role assignment for this company
                    role_assignment = None
                    if request.company_roles:
                        role_assignment = next(
                            (r for r in request.company_roles if r.company_id == company_id),
                            None
                        )

                    user_company = UserCompany(
                        user_id=user_id,
                        company_id=company_id,
                        is_admin=role_assignment.is_admin if role_assignment else False,
                        can_edit=role_assignment.can_edit if role_assignment else True,
                        can_view=role_assignment.can_view if role_assignment else True
                    )
                    self.db.add(user_company)

                # Update preferred company if no longer in list
                if target_user.preferred_company_id not in request.company_ids:
                    target_user.preferred_company_id = request.company_ids[0] if request.company_ids else None

            self.db.commit()
            self.db.refresh(target_user)

            logger.info(f"User updated: {target_user.email} by {current_user.email}")

            return self.get_user_details(user_id, current_user)

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise ValueError(f"Failed to update user: {e}")

    def deactivate_user(
        self,
        user_id: UUID,
        current_user: User
    ) -> UserDetail:
        """
        Deactivate a user (soft delete).

        Permission rules:
        - Superuser: Can deactivate anyone
        - Company admin: Can deactivate users in their companies
        - Cannot deactivate yourself
        - Cannot deactivate last superuser

        Args:
            user_id: User to deactivate
            current_user: User performing the deactivation

        Returns:
            Updated UserDetail

        Raises:
            PermissionError: If user lacks permissions
            ValueError: If validation fails
        """
        if user_id == current_user.id:
            raise PermissionError("Cannot deactivate yourself")

        target_user = self.db.query(User).options(
            joinedload(User.user_companies)
        ).filter(User.id == user_id).first()

        if not target_user:
            raise ValueError("User not found")

        # Validate permissions
        user_company_ids = [uc.company_id for uc in target_user.user_companies]
        self._validate_superuser_or_company_admin(current_user, user_company_ids)

        # Prevent deactivating last superuser
        if target_user.is_superuser:
            superuser_count = self.db.query(User).filter(
                User.is_superuser == True,
                User.is_active == True
            ).count()
            if superuser_count <= 1:
                raise ValueError("Cannot deactivate the last active superuser")

        target_user.is_active = False
        self.db.commit()

        logger.info(f"User deactivated: {target_user.email} by {current_user.email}")

        return self.get_user_details(user_id, current_user)

    def delete_user(
        self,
        user_id: UUID,
        current_user: User
    ) -> bool:
        """
        Permanently delete a user (hard delete, superuser only).

        Permission rules:
        - ONLY superusers can hard delete
        - Cannot delete yourself
        - Cannot delete last superuser

        Args:
            user_id: User to delete
            current_user: Must be superuser

        Returns:
            True if successful

        Raises:
            PermissionError: If user is not superuser
            ValueError: If validation fails
        """
        if not current_user.is_superuser:
            raise PermissionError("Only superusers can permanently delete users")

        if user_id == current_user.id:
            raise PermissionError("Cannot delete yourself")

        target_user = self.db.query(User).filter(User.id == user_id).first()

        if not target_user:
            raise ValueError("User not found")

        # Prevent deleting last superuser
        if target_user.is_superuser:
            superuser_count = self.db.query(User).filter(
                User.is_superuser == True
            ).count()
            if superuser_count <= 1:
                raise ValueError("Cannot delete the last superuser")

        try:
            self.db.delete(target_user)
            self.db.commit()

            logger.info(f"User deleted: {target_user.email} by {current_user.email}")
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user: {e}")
            raise ValueError(f"Failed to delete user: {e}")

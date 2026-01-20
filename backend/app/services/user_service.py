"""
Service for user management and authentication.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import Optional, List
from uuid import UUID
import logging

from app.db.models.user import User
from app.db.models.user_company import UserCompany
from app.core.security import get_password_hash, verify_password
from app.schemas.user import UserCreate, UserUpdate

logger = logging.getLogger(__name__)

class UserService:
    """Service for managing users."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate, company_ids: Optional[List[UUID]] = None) -> User:
        """
        Create a new user with hashed password and company associations.

        Args:
            user_data: UserCreate schema with email and password
            company_ids: List of company IDs to assign user to (from user_data if not provided)

        Returns:
            Created User object

        Raises:
            ValueError: If user already exists or no company assignment provided
        """
        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise ValueError(f"User with email {user_data.email} already exists")

        # Get company IDs from parameter or user_data
        if company_ids is None:
            company_ids = user_data.company_ids or []

        # Validate company assignment (unless this is initial sign-up or superuser)
        if not company_ids and not user_data.is_initial_signup:
            raise ValueError("User must be assigned to at least one company")

        # Create new user
        hashed_password = get_password_hash(user_data.password)
        db_user = User(
            email=user_data.email,
            hashed_password=hashed_password,
            role="COUNCIL_MEMBER"
        )

        try:
            self.db.add(db_user)
            self.db.flush()  # Flush to get user ID

            # Create UserCompany associations
            if company_ids:
                for company_id in company_ids:
                    user_company = UserCompany(
                        user_id=db_user.id,
                        company_id=company_id,
                        is_admin=False,  # Default to non-admin
                        can_edit=True,
                        can_view=True
                    )
                    self.db.add(user_company)

                # Set preferred company to first one
                db_user.preferred_company_id = company_ids[0]

            self.db.commit()
            self.db.refresh(db_user)
            logger.info(f"Created user: {user_data.email} with {len(company_ids)} company assignments")
            return db_user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise ValueError(f"Failed to create user: {e}")
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate a user by email and password.

        Args:
            email: User email
            password: Plain text password

        Returns:
            User object if authentication successful, None otherwise
        """
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            return None

        # OAuth-only users have no password
        if not user.hashed_password:
            logger.warning(f"Password login attempted for OAuth-only user: {email}")
            return None

        if not verify_password(password, user.hashed_password):
            return None

        if not user.is_active:
            return None

        return user
    
    def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def update_user(self, user_id: UUID, user_data: UserUpdate) -> Optional[User]:
        """
        Update user information.
        
        Args:
            user_id: UUID of the user to update
            user_data: UserUpdate schema with fields to update
        
        Returns:
            Updated User object, or None if user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return None
        
        if user_data.email is not None:
            user.email = user_data.email
        if user_data.password is not None:
            user.hashed_password = get_password_hash(user_data.password)
        if user_data.is_active is not None:
            user.is_active = user_data.is_active
        
        try:
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise ValueError(f"Failed to update user: {e}")
    
    def get_all_users(self) -> List[User]:
        """Get all users."""
        return self.db.query(User).all()
    
    def delete_user(self, user_id: UUID) -> bool:
        """
        Delete a user.
        
        Args:
            user_id: UUID of the user to delete
        
        Returns:
            True if successful, False if user not found
        """
        user = self.get_user_by_id(user_id)
        if not user:
            return False
        
        try:
            self.db.delete(user)
            self.db.commit()
            logger.info(f"Deleted user: {user_id}")
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting user: {e}")
            raise ValueError(f"Failed to delete user: {e}")

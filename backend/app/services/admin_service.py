"""
Admin service for superuser operations.
"""
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
import logging

from app.db.models.user import User
from app.db.models.system_settings import SystemSettings
from app.schemas.system_settings import SystemSettingsUpdate

logger = logging.getLogger(__name__)


class AdminService:
    """Service for admin/superuser operations."""

    def __init__(self, db: Session):
        self.db = db

    def get_all_users(self) -> List[User]:
        """
        Get all users in the system.

        Returns:
            List of all User objects with their relationships loaded
        """
        return self.db.query(User).all()

    def promote_user(self, user_id: UUID) -> User:
        """
        Promote a user to superuser.

        Args:
            user_id: UUID of the user to promote

        Returns:
            Updated User object

        Raises:
            ValueError: If user not found
        """
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if user.is_superuser:
            logger.info(f"User {user.email} is already a superuser")
            return user

        user.is_superuser = True
        user.role = "SU"
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Promoted user {user.email} to superuser")
        return user

    def demote_user(self, user_id: UUID, current_user_id: UUID) -> User:
        """
        Demote a user from superuser.

        Args:
            user_id: UUID of the user to demote
            current_user_id: UUID of the current user (to prevent self-demotion)

        Returns:
            Updated User object

        Raises:
            ValueError: If user not found or trying to demote self
        """
        if user_id == current_user_id:
            raise ValueError("You cannot demote yourself")

        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise ValueError(f"User with ID {user_id} not found")

        if not user.is_superuser:
            logger.info(f"User {user.email} is already not a superuser")
            return user

        user.is_superuser = False
        user.role = "COUNCIL_MEMBER"
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Demoted user {user.email} from superuser")
        return user

    def get_settings(self) -> SystemSettings:
        """
        Get system settings. Creates default settings if none exist.

        Returns:
            SystemSettings object
        """
        settings = self.db.query(SystemSettings).filter(SystemSettings.id == 1).first()

        if not settings:
            # Create default settings
            settings = SystemSettings(
                id=1,
                maintenance_mode=False,
                allow_public_signup=False
            )
            self.db.add(settings)
            self.db.commit()
            self.db.refresh(settings)
            logger.info("Created default system settings")

        return settings

    def update_settings(self, settings_update: SystemSettingsUpdate) -> SystemSettings:
        """
        Update system settings.

        Args:
            settings_update: SystemSettingsUpdate schema with fields to update

        Returns:
            Updated SystemSettings object
        """
        settings = self.get_settings()

        # Update fields if provided
        if settings_update.maintenance_mode is not None:
            settings.maintenance_mode = settings_update.maintenance_mode
        if settings_update.allow_public_signup is not None:
            settings.allow_public_signup = settings_update.allow_public_signup

        self.db.commit()
        self.db.refresh(settings)

        logger.info(f"Updated system settings: {settings}")
        return settings

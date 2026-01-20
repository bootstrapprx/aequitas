"""
Council Member (Super User) management service.

Handles creation, management, and security of privileged Council Member accounts.
All operations are audited and follow strict security protocols.
"""
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Tuple
from uuid import UUID
import secrets
import string
import logging

from app.db.models.user import User
from app.schemas.user import CouncilMemberCreate
from app.core.security import get_password_hash
from app.core.password_policy import validate_council_password, PasswordPolicy, PasswordValidationError
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)


class CouncilService:
    """
    Service for managing Council Members (Super Users).

    SECURITY REQUIREMENTS:
    - Only Council Members can create other Council Members
    - All Council Member creations are audited
    - Passwords must meet strict policy requirements
    - Newly created members must reset password on first login
    - No privilege escalation vulnerabilities
    """

    def __init__(self, db: Session):
        self.db = db
        self.audit_service = AuditService(db)

    def create_council_member(
        self,
        member_data: CouncilMemberCreate,
        creator_id: UUID
    ) -> Tuple[User, str]:
        """
        Create a new Council Member account.

        Args:
            member_data: Council member creation data
            creator_id: UUID of the Council Member creating this account

        Returns:
            Tuple of (created User object, plain text temporary password)

        Raises:
            ValueError: If user already exists, password validation fails, or other errors
            PermissionError: If creator is not a Council Member
        """
        # Verify creator is a Council Member
        creator = self.db.query(User).filter(User.id == creator_id).first()
        if not creator or not creator.is_superuser:
            raise PermissionError("Only Council Members can create other Council Members")

        # Check if user already exists
        existing_user = self.db.query(User).filter(User.email == member_data.email).first()
        if existing_user:
            raise ValueError(f"User with email {member_data.email} already exists")

        # Generate or validate password
        if member_data.password:
            # Use provided password - validate against policy
            password = member_data.password
            try:
                validate_council_password(password)
            except PasswordValidationError as e:
                raise ValueError(f"Password does not meet Council Member policy: {'; '.join(e.details)}")
        else:
            # Auto-generate a secure password
            password = self._generate_secure_password()
            logger.info(f"Auto-generated secure password for new Council Member: {member_data.email}")

        # Create the user
        try:
            new_member = User(
                email=member_data.email,
                hashed_password=get_password_hash(password),
                is_active=True,
                is_superuser=True,
                role="SU",
                force_password_reset=True,
                password_reset_required_at=datetime.utcnow(),
                created_by=creator_id,
                created_at=datetime.utcnow()
            )

            self.db.add(new_member)
            self.db.flush()  # Get the ID before commit

            # Audit log the creation
            self.audit_service.log_council_member_create(
                creator_id=creator_id,
                new_member_id=new_member.id,
                new_member_email=new_member.email
            )

            self.db.commit()
            self.db.refresh(new_member)

            logger.info(
                f"Council Member created: {new_member.email} (ID: {new_member.id}) "
                f"by {creator.email} (ID: {creator_id})"
            )

            # Return user and plain password (ONLY time it's ever accessible)
            return new_member, password

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to create Council Member: {e}")
            raise ValueError(f"Failed to create Council Member: {e}")

    def _generate_secure_password(self) -> str:
        """
        Generate a cryptographically secure password meeting Council policy.

        Returns:
            Secure password string (16 characters with mixed complexity)
        """
        # Ensure we have at least one of each required character type
        password_chars = [
            secrets.choice(string.ascii_uppercase),  # At least one uppercase
            secrets.choice(string.ascii_lowercase),  # At least one lowercase
            secrets.choice(string.digits),           # At least one digit
            secrets.choice("!@#$%^&*()_+-="),        # At least one special char
        ]

        # Fill the rest with random characters from all categories
        all_chars = string.ascii_letters + string.digits + "!@#$%^&*()_+-="
        password_chars += [secrets.choice(all_chars) for _ in range(12)]

        # Shuffle to avoid predictable patterns
        password_list = password_chars[:]
        secrets.SystemRandom().shuffle(password_list)
        password = ''.join(password_list)

        # Validate it meets policy (should always pass, but be safe)
        try:
            validate_council_password(password)
        except PasswordValidationError:
            # Recursively try again if somehow it fails (extremely rare)
            return self._generate_secure_password()

        return password

    def revoke_council_membership(
        self,
        member_id: UUID,
        revoker_id: UUID
    ) -> User:
        """
        Revoke Council Member privileges from a user.

        Args:
            member_id: UUID of the Council Member to demote
            revoker_id: UUID of the Council Member performing the revocation

        Returns:
            Updated User object

        Raises:
            ValueError: If user not found or invalid operation
            PermissionError: If revoker is not a Council Member or trying to demote themselves
        """
        # Verify revoker is a Council Member
        revoker = self.db.query(User).filter(User.id == revoker_id).first()
        if not revoker or not revoker.is_superuser:
            raise PermissionError("Only Council Members can revoke Council membership")

        # Prevent self-revocation
        if member_id == revoker_id:
            raise PermissionError("Council Members cannot revoke their own privileges")

        # Find the member to revoke
        member = self.db.query(User).filter(User.id == member_id).first()
        if not member:
            raise ValueError(f"User with ID {member_id} not found")

        if not member.is_superuser:
            raise ValueError(f"User {member.email} is not a Council Member")

        # Check if this is the last Council Member (prevent lockout)
        council_member_count = self.db.query(User).filter(
            User.is_superuser == True,
            User.is_active == True
        ).count()

        if council_member_count <= 1:
            raise ValueError("Cannot revoke the last Council Member. At least one must remain.")

        try:
            # Revoke privileges
            member.is_superuser = False
            member.role = "COUNCIL_MEMBER"

            # Audit the revocation
            self.audit_service.log_user_demote(
                demoter_id=revoker_id,
                demoted_user_id=member.id,
                demoted_user_email=member.email
            )

            self.db.commit()
            self.db.refresh(member)

            logger.info(
                f"Council membership revoked for {member.email} (ID: {member.id}) "
                f"by {revoker.email} (ID: {revoker_id})"
            )

            return member

        except Exception as e:
            self.db.rollback()
            logger.error(f"Failed to revoke Council membership: {e}")
            raise ValueError(f"Failed to revoke Council membership: {e}")

    def list_council_members(self) -> list[User]:
        """
        List all active Council Members.

        Returns:
            List of User objects with is_superuser=True
        """
        return self.db.query(User).filter(
            User.is_superuser == True,
            User.is_active == True
        ).all()

    def get_council_member_count(self) -> int:
        """
        Get count of active Council Members.

        Returns:
            Number of active Council Members
        """
        return self.db.query(User).filter(
            User.is_superuser == True,
            User.is_active == True
        ).count()

"""
Password policy validation utilities for secure credential management.

Enforces strict password requirements for Council Members (Super Users)
and standard users according to security best practices.
"""
import re
from typing import Optional, List


class PasswordValidationError(Exception):
    """Custom exception for password validation failures."""
    def __init__(self, message: str, details: Optional[List[str]] = None):
        self.message = message
        self.details = details or []
        super().__init__(self.message)


class PasswordPolicy:
    """
    Centralized password policy enforcement.

    Council Member (Super User) passwords have stricter requirements
    than standard user passwords to ensure maximum security for
    privileged accounts.
    """

    # Standard user password policy
    STANDARD_MIN_LENGTH = 8
    STANDARD_REQUIRE_UPPERCASE = False
    STANDARD_REQUIRE_LOWERCASE = False
    STANDARD_REQUIRE_DIGIT = False
    STANDARD_REQUIRE_SPECIAL = False

    # Council Member (Super User) password policy - STRICT
    COUNCIL_MIN_LENGTH = 12
    COUNCIL_REQUIRE_UPPERCASE = True
    COUNCIL_REQUIRE_LOWERCASE = True
    COUNCIL_REQUIRE_DIGIT = True
    COUNCIL_REQUIRE_SPECIAL = True

    # Special characters allowed
    SPECIAL_CHARS = r"!@#$%^&*()_+-=[]{}|;:,.<>?"

    @classmethod
    def validate_password(cls, password: str, is_privileged: bool = False) -> None:
        """
        Validate password against policy requirements.

        Args:
            password: Plain text password to validate
            is_privileged: True if this is for a Council Member/Super User

        Raises:
            PasswordValidationError: If password does not meet policy
        """
        errors = []

        # Select appropriate policy
        if is_privileged:
            min_length = cls.COUNCIL_MIN_LENGTH
            require_uppercase = cls.COUNCIL_REQUIRE_UPPERCASE
            require_lowercase = cls.COUNCIL_REQUIRE_LOWERCASE
            require_digit = cls.COUNCIL_REQUIRE_DIGIT
            require_special = cls.COUNCIL_REQUIRE_SPECIAL
            user_type = "Council Member"
        else:
            min_length = cls.STANDARD_MIN_LENGTH
            require_uppercase = cls.STANDARD_REQUIRE_UPPERCASE
            require_lowercase = cls.STANDARD_REQUIRE_LOWERCASE
            require_digit = cls.STANDARD_REQUIRE_DIGIT
            require_special = cls.STANDARD_REQUIRE_SPECIAL
            user_type = "user"

        # Check minimum length
        if len(password) < min_length:
            errors.append(f"Password must be at least {min_length} characters long")

        # Check uppercase requirement
        if require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        # Check lowercase requirement
        if require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        # Check digit requirement
        if require_digit and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")

        # Check special character requirement
        if require_special and not re.search(f'[{re.escape(cls.SPECIAL_CHARS)}]', password):
            errors.append(f"Password must contain at least one special character ({cls.SPECIAL_CHARS})")

        # Check for common weak patterns
        weak_patterns = [
            (r'(.)\1{2,}', "Password cannot contain three or more repeated characters"),
            (r'(012|123|234|345|456|567|678|789|890)', "Password cannot contain sequential digits"),
            (r'(abc|bcd|cde|def|efg|fgh|ghi|hij|ijk|jkl|klm|lmn|mno|nop|opq|pqr|qrs|rst|stu|tuv|uvw|vwx|wxy|xyz)',
             "Password cannot contain sequential letters"),
        ]

        for pattern, error_msg in weak_patterns:
            if re.search(pattern, password.lower()):
                errors.append(error_msg)

        # Check for common weak passwords (partial list)
        common_weak = ['password', 'admin', 'user', 'root', 'superuser', 'council', 'member']
        if any(weak in password.lower() for weak in common_weak):
            errors.append("Password cannot contain common weak words")

        if errors:
            raise PasswordValidationError(
                f"Password does not meet {user_type} policy requirements",
                details=errors
            )

    @classmethod
    def get_policy_description(cls, is_privileged: bool = False) -> str:
        """
        Get human-readable description of password policy.

        Args:
            is_privileged: True if this is for a Council Member/Super User

        Returns:
            String describing the password requirements
        """
        if is_privileged:
            return (
                f"Council Member password requirements:\n"
                f"- Minimum {cls.COUNCIL_MIN_LENGTH} characters\n"
                f"- At least one uppercase letter\n"
                f"- At least one lowercase letter\n"
                f"- At least one digit\n"
                f"- At least one special character ({cls.SPECIAL_CHARS})\n"
                f"- No repeated characters (3+ times)\n"
                f"- No sequential patterns\n"
                f"- No common weak words"
            )
        else:
            return f"Password must be at least {cls.STANDARD_MIN_LENGTH} characters long"


def validate_council_password(password: str) -> None:
    """
    Convenience function to validate Council Member password.

    Args:
        password: Plain text password to validate

    Raises:
        PasswordValidationError: If password does not meet policy
    """
    PasswordPolicy.validate_password(password, is_privileged=True)


def validate_standard_password(password: str) -> None:
    """
    Convenience function to validate standard user password.

    Args:
        password: Plain text password to validate

    Raises:
        PasswordValidationError: If password does not meet policy
    """
    PasswordPolicy.validate_password(password, is_privileged=False)

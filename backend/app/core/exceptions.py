"""
Centralized exception classes for validation and business logic errors.

CANONICAL COMPLIANCE:
- Phase 3B: Standardized validation behavior
- Deterministic, explainable error codes
- Consistent error semantics across all services

ERROR CODE CATEGORIES:
- 1xxx: Account-related errors
- 2xxx: Journal entry errors
- 3xxx: Fiscal period errors
- 4xxx: Template errors
- 5xxx: Permission errors
"""

from typing import Optional, Dict, Any, List
from enum import Enum


class ErrorCode(str, Enum):
    """
    Standardized error codes for Phase 3B validation.

    PATTERN: <Category><Subcategory><Specific>
    - Category: 1=Account, 2=Journal, 3=Period, 4=Template, 5=Permission
    - Use consistent codes across all services
    """

    # Account Errors (1xxx)
    LOCKED_ACCOUNT = "ACCT_1001"
    """Account is locked and cannot be modified"""

    LOCKED_ACCOUNT_NAME = "ACCT_1002"
    """Cannot change name on locked account"""

    LOCKED_ACCOUNT_TYPE = "ACCT_1003"
    """Cannot change type on locked account"""

    LOCKED_ACCOUNT_CODE = "ACCT_1004"
    """Cannot change code on locked account"""

    LOCKED_ACCOUNT_HIERARCHY = "ACCT_1005"
    """Cannot change parent_id on locked account"""

    LOCKED_ACCOUNT_MAPPING = "ACCT_1006"
    """Cannot change mapped_master_account_id on locked account"""

    LOCKED_ACCOUNT_NORMAL_BALANCE = "ACCT_1007"
    """Cannot change normal_balance on locked account"""

    LOCKED_ACCOUNT_DELETE = "ACCT_1008"
    """Cannot delete locked account"""

    ACCOUNT_HAS_CHILDREN = "ACCT_1010"
    """Account has children and cannot be deleted"""

    ACCOUNT_INACTIVE = "ACCT_1020"
    """Account is inactive and cannot be used in transactions"""

    INVALID_ACCOUNT_TYPE = "ACCT_1030"
    """Invalid account_type enum value"""

    INVALID_NORMAL_BALANCE = "ACCT_1031"
    """Invalid normal_balance enum value"""

    INVALID_PARENT = "ACCT_1040"
    """Parent account does not exist or belongs to different company"""

    CIRCULAR_REFERENCE = "ACCT_1041"
    """Circular reference detected in account hierarchy"""

    # Journal Entry Errors (2xxx)
    JOURNAL_IMBALANCE = "JRNL_2001"
    """Journal entry debits do not equal credits"""

    JOURNAL_LOCKED_ACCOUNT = "JRNL_2010"
    """Journal entry line references locked account"""

    JOURNAL_INACTIVE_ACCOUNT = "JRNL_2011"
    """Journal entry line references inactive account"""

    JOURNAL_CROSS_COMPANY = "JRNL_2020"
    """Journal entry lines reference accounts from different companies"""

    JOURNAL_EMPTY_LINES = "JRNL_2030"
    """Journal entry must have at least 2 lines"""

    JOURNAL_INVALID_AMOUNT = "JRNL_2031"
    """Journal entry line amount must be positive"""

    # Fiscal Period Errors (3xxx)
    PERIOD_CLOSED = "PERD_3001"
    """Fiscal period is closed and read-only"""

    PERIOD_LOCKED = "PERD_3002"
    """Fiscal period is locked and cannot be modified"""

    PERIOD_NOT_OPEN = "PERD_3003"
    """Fiscal period is not in OPEN status"""

    PERIOD_DATE_OUTSIDE = "PERD_3010"
    """Posting date is outside fiscal period boundaries"""

    PERIOD_NOT_FOUND = "PERD_3020"
    """No fiscal period found for posting date"""

    # Template Errors (4xxx)
    TEMPLATE_VIOLATION = "TMPL_4001"
    """Template rule violation"""

    TEMPLATE_MANDATORY_DELETE = "TMPL_4010"
    """Cannot delete mandatory template account"""

    TEMPLATE_MANDATORY_NORMAL_BALANCE = "TMPL_4011"
    """Cannot change normal_balance on mandatory template account"""

    TEMPLATE_MANDATORY_MAPPING = "TMPL_4012"
    """Cannot change mapped_master_account_id on mandatory template account"""

    TEMPLATE_MISSING_MANDATORY = "TMPL_4020"
    """Company is missing mandatory template accounts"""

    TEMPLATE_NOT_FOUND = "TMPL_4030"
    """Template not found or not active"""

    # Permission Errors (5xxx)
    PERMISSION_DENIED = "PERM_5001"
    """User does not have permission for this operation"""

    SUPERUSER_REQUIRED = "PERM_5010"
    """Operation requires superuser privileges"""

    UNLOCK_NOT_ALLOWED = "PERM_5020"
    """Account unlock not allowed (transactions exist in current period)"""


class ValidationError(Exception):
    """
    Custom exception for validation failures.

    CANONICAL COMPLIANCE:
    - Deterministic error messages
    - Explainable (includes field + reason)
    - Consistent across all endpoints
    - No silent coercion

    USAGE:
        raise ValidationError(
            message="Cannot modify locked account",
            code=ErrorCode.LOCKED_ACCOUNT,
            details={
                "account_id": str(account.id),
                "locked_reason": account.locked_reason.value,
                "attempted_changes": ["name", "type"]
            }
        )
    """

    def __init__(
        self,
        message: str,
        code: Optional[ErrorCode] = None,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ):
        """
        Initialize validation error.

        Args:
            message: Human-readable error message
            code: Standardized error code (from ErrorCode enum)
            details: Additional context about the error
            field: Specific field that caused the error
        """
        self.message = message
        self.code = code
        self.details = details or {}
        self.field = field
        super().__init__(self.message)

    def __str__(self) -> str:
        """Format error message with code and details."""
        parts = []

        # Add error code if present
        if self.code:
            parts.append(f"[{self.code.value}]")

        # Add main message
        parts.append(self.message)

        # Add field if present
        if self.field:
            parts.append(f"(field: {self.field})")

        return " ".join(parts)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert error to dictionary for API responses.

        Returns:
            {
                "error": "LOCKED_ACCOUNT",
                "message": "Cannot modify locked account",
                "field": "name",
                "details": {...}
            }
        """
        return {
            "error": self.code.value if self.code else "VALIDATION_ERROR",
            "message": self.message,
            "field": self.field,
            "details": self.details
        }


class MultipleValidationErrors(ValidationError):
    """
    Exception for multiple validation failures.

    USAGE:
        errors = []
        if not valid_name:
            errors.append(ValidationError("Invalid name", code=ErrorCode.INVALID_ACCOUNT_TYPE))
        if not valid_balance:
            errors.append(ValidationError("Invalid balance", code=ErrorCode.INVALID_NORMAL_BALANCE))

        if errors:
            raise MultipleValidationErrors(errors)
    """

    def __init__(self, errors: List[ValidationError]):
        """
        Initialize with list of validation errors.

        Args:
            errors: List of ValidationError instances
        """
        self.errors = errors
        message = f"{len(errors)} validation error(s):\n"
        message += "\n".join(f"  - {error}" for error in errors)
        super().__init__(message=message, code=None)

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary with all sub-errors.

        Returns:
            {
                "error": "MULTIPLE_VALIDATION_ERRORS",
                "message": "2 validation error(s)",
                "errors": [
                    {"error": "LOCKED_ACCOUNT", "message": "...", ...},
                    {"error": "INVALID_PARENT", "message": "...", ...}
                ]
            }
        """
        return {
            "error": "MULTIPLE_VALIDATION_ERRORS",
            "message": f"{len(self.errors)} validation error(s)",
            "errors": [error.to_dict() for error in self.errors]
        }


# Export all
__all__ = [
    "ErrorCode",
    "ValidationError",
    "MultipleValidationErrors"
]

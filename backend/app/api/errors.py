"""
Canonical Error System for Aequitas API

This module provides a single, stable error translation layer that maps
service layer exceptions to standardized HTTP responses with explicit error codes.

AUTHORITATIVE REFERENCE: docs/canonical/PHASE_3C2_WRITE_APIS.md

All API endpoints must use this error system to ensure:
- Deterministic error codes
- Consistent error response format
- No leakage of internal exceptions
- Machine-readable error classification
"""

from enum import Enum
from typing import Dict, Any, Optional
from fastapi import HTTPException
from app.core.exceptions import ValidationError


class ErrorCode(str, Enum):
    """
    Canonical error codes for Aequitas API.

    These codes are machine-readable identifiers that clients can programmatically
    handle. Error codes are stable across releases.

    NEVER change existing error code values. Only add new codes.
    """
    # Permission & Authentication Errors
    PERMISSION_DENIED = "PERMISSION_DENIED"
    UNAUTHORIZED = "UNAUTHORIZED"

    # Resource Errors
    NOT_FOUND = "NOT_FOUND"
    ALREADY_EXISTS = "ALREADY_EXISTS"

    # Accounting Domain Errors
    LOCKED_ACCOUNT = "LOCKED_ACCOUNT"
    STATE_CONFLICT = "STATE_CONFLICT"
    JOURNAL_IMBALANCE = "JOURNAL_IMBALANCE"
    PERIOD_CLOSED = "PERIOD_CLOSED"
    TEMPLATE_VIOLATION = "TEMPLATE_VIOLATION"

    # Validation Errors
    VALIDATION_ERROR = "VALIDATION_ERROR"
    INVALID_INPUT = "INVALID_INPUT"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"

    # System Errors
    INTERNAL_ERROR = "INTERNAL_ERROR"


class CanonicalError:
    """
    Canonical error response builder.

    Constructs standardized error responses that match the specification:

    {
      "error_code": "LOCKED_ACCOUNT | STATE_CONFLICT | ...",
      "message": "Human-readable explanation",
      "details": { "field": "context" }
    }
    """

    @staticmethod
    def build_response(
        error_code: ErrorCode,
        message: str,
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Build canonical error response payload.

        Args:
            error_code: Machine-readable error code
            message: Human-readable explanation
            details: Optional context (field names, values, etc.)

        Returns:
            Standardized error payload
        """
        response = {
            "error_code": error_code.value,
            "message": message
        }

        if details:
            response["details"] = details

        return response

    @staticmethod
    def permission_denied(message: str = "Permission denied", details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """User lacks required permission."""
        return HTTPException(
            status_code=403,
            detail=CanonicalError.build_response(
                ErrorCode.PERMISSION_DENIED,
                message,
                details
            )
        )

    @staticmethod
    def not_found(resource: str, identifier: Any, details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """Resource not found."""
        error_details = details or {}
        error_details["resource"] = resource
        error_details["identifier"] = str(identifier)

        return HTTPException(
            status_code=404,
            detail=CanonicalError.build_response(
                ErrorCode.NOT_FOUND,
                f"{resource} not found: {identifier}",
                error_details
            )
        )

    @staticmethod
    def locked_account(message: str, account_code: Optional[str] = None) -> HTTPException:
        """Attempt to modify immutable fields on locked account."""
        details = {"code": account_code} if account_code else None

        return HTTPException(
            status_code=400,
            detail=CanonicalError.build_response(
                ErrorCode.LOCKED_ACCOUNT,
                message,
                details
            )
        )

    @staticmethod
    def state_conflict(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """Invalid state transition (e.g., update POSTED entry)."""
        return HTTPException(
            status_code=400,
            detail=CanonicalError.build_response(
                ErrorCode.STATE_CONFLICT,
                message,
                details
            )
        )

    @staticmethod
    def journal_imbalance(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """Journal entry debits != credits or invalid line structure."""
        return HTTPException(
            status_code=400,
            detail=CanonicalError.build_response(
                ErrorCode.JOURNAL_IMBALANCE,
                message,
                details
            )
        )

    @staticmethod
    def period_closed(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """Attempt to create/post entry in non-OPEN period."""
        return HTTPException(
            status_code=400,
            detail=CanonicalError.build_response(
                ErrorCode.PERIOD_CLOSED,
                message,
                details
            )
        )

    @staticmethod
    def validation_error(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """General validation failure."""
        return HTTPException(
            status_code=400,
            detail=CanonicalError.build_response(
                ErrorCode.VALIDATION_ERROR,
                message,
                details
            )
        )

    @staticmethod
    def template_violation(message: str, details: Optional[Dict[str, Any]] = None) -> HTTPException:
        """Template-mandatory account rule violated."""
        return HTTPException(
            status_code=400,
            detail=CanonicalError.build_response(
                ErrorCode.TEMPLATE_VIOLATION,
                message,
                details
            )
        )


def translate_service_exception(e: Exception, context: Optional[Dict[str, Any]] = None) -> HTTPException:
    """
    Translate service layer exceptions to canonical HTTP errors.

    This function implements the error mapping strategy:
    - ValidationError → Specific error codes based on message content
    - ValueError → VALIDATION_ERROR
    - Other exceptions → INTERNAL_ERROR (with logging)

    Args:
        e: Exception from service layer
        context: Optional context for error details

    Returns:
        HTTPException with canonical error payload

    Usage:
        try:
            service.do_something()
        except Exception as e:
            raise translate_service_exception(e, {"account_id": account_id})
    """
    error_message = str(e).lower()

    # Check for specific accounting domain errors
    if "locked" in error_message and "account" in error_message:
        return CanonicalError.locked_account(str(e), context.get("code") if context else None)

    if any(keyword in error_message for keyword in ["posted", "draft", "void", "status"]):
        return CanonicalError.state_conflict(str(e), context)

    if any(keyword in error_message for keyword in ["balance", "debit", "credit", "imbalance"]):
        return CanonicalError.journal_imbalance(str(e), context)

    if any(keyword in error_message for keyword in ["period", "closed", "locked"]) and "fiscal" in error_message:
        return CanonicalError.period_closed(str(e), context)

    if "template" in error_message and "mandatory" in error_message:
        return CanonicalError.template_violation(str(e), context)

    # Default to validation error for ValidationError and ValueError
    if isinstance(e, (ValidationError, ValueError)):
        return CanonicalError.validation_error(str(e), context)

    # Unexpected error - log and return generic error
    # In production, this would trigger alerting
    import logging
    logger = logging.getLogger(__name__)
    logger.error(f"Unexpected error in API layer: {e}", exc_info=True)

    return HTTPException(
        status_code=500,
        detail=CanonicalError.build_response(
            ErrorCode.INTERNAL_ERROR,
            "An internal error occurred. Please contact support.",
            {"error_type": type(e).__name__} if context and context.get("include_error_type") else None
        )
    )


# Export public interface
__all__ = [
    "ErrorCode",
    "CanonicalError",
    "translate_service_exception"
]

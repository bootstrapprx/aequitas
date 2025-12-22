from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from app.core.request_context import ensure_request_ids, get_request_id, get_correlation_id


class AequitasError(Exception):
    """
    Canonical error for API responses.

    Attributes:
        code: Canonical AEQ code (e.g., AEQ_QBO_IDEMPOTENCY_REUSED)
        message: Human-readable summary
        details: Additional structured context
        http_status: HTTP status code to return
    """

    def __init__(
        self,
        code: str,
        message: str,
        *,
        details: Optional[Dict[str, Any]] = None,
        http_status: int = status.HTTP_400_BAD_REQUEST,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        self.http_status = http_status
        super().__init__(message)


def make_error_envelope(
    code: str,
    message: str,
    *,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Build the canonical error envelope including trace identifiers."""
    ensure_request_ids()
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details or {},
            "request_id": get_request_id(),
            "correlation_id": get_correlation_id(),
        }
    }


def http_exception_to_aequitas_error(exc: HTTPException) -> AequitasError:
    """Translate FastAPI HTTPException into canonical AEQ error."""
    status_code = exc.status_code
    code = f"AEQ_HTTP_{status_code}"
    message = exc.detail if exc.detail else "HTTP exception occurred"
    details: Dict[str, Any] = {}

    if isinstance(exc.detail, dict):
        details = exc.detail  # type: ignore[assignment]
    else:
        details = {"detail": exc.detail}

    return AequitasError(
        code=code,
        message=message if isinstance(message, str) else str(message),
        details=details,
        http_status=status_code,
    )

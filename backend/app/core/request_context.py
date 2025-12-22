import contextvars
from typing import Optional, Tuple
from uuid import uuid4

request_id_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)
correlation_id_ctx_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "correlation_id", default=None
)


def set_request_context(request_id: str, correlation_id: str) -> None:
    """Store request identifiers in context for the current task."""
    request_id_ctx_var.set(request_id)
    correlation_id_ctx_var.set(correlation_id)


def get_request_id() -> Optional[str]:
    """Return the current request id if set."""
    return request_id_ctx_var.get()


def get_correlation_id() -> Optional[str]:
    """Return the current correlation id if set."""
    return correlation_id_ctx_var.get()


def ensure_request_ids(
    request_id: Optional[str] = None, correlation_id: Optional[str] = None
) -> Tuple[str, str]:
    """
    Guarantee request and correlation ids exist, generating them when missing.
    Returns a tuple of (request_id, correlation_id).
    """
    current_request_id = request_id or get_request_id() or str(uuid4())
    current_correlation_id = correlation_id or get_correlation_id() or str(uuid4())

    set_request_context(current_request_id, current_correlation_id)
    return current_request_id, current_correlation_id

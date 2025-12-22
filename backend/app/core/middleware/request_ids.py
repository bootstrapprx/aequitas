from typing import Callable
from uuid import uuid4

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.request_context import ensure_request_ids, get_request_id, get_correlation_id


class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that injects canonical request tracing headers.

    - Accepts/propagates X-Aequitas-Request-Id and X-Aequitas-Correlation-Id
    - Ensures they are available via contextvars for logging/error envelopes
    - Echoes headers on every response
    """

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        header_request_id = request.headers.get("X-Aequitas-Request-Id")
        header_correlation_id = request.headers.get("X-Aequitas-Correlation-Id")

        request_id = header_request_id or str(uuid4())
        correlation_id = header_correlation_id or str(uuid4())

        ensure_request_ids(request_id, correlation_id)

        response = await call_next(request)
        response.headers["X-Aequitas-Request-Id"] = get_request_id() or request_id
        response.headers["X-Aequitas-Correlation-Id"] = (
            get_correlation_id() or correlation_id
        )
        return response

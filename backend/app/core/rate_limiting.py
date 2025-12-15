"""
Rate limiting middleware for API endpoints.

SECURITY:
- Prevents abuse of write operations
- Protects against DoS attacks
- Configurable limits per endpoint type

IMPLEMENTATION:
- In-memory rate limiting using dict
- Per-user tracking based on JWT token
- Sliding window algorithm
- Automatic cleanup of expired entries

PHASE 3B COMPLIANCE:
- 10 requests per minute for write operations (default)
- 100 requests per minute for read operations (default)
- Stricter limits for critical operations (unlock, reopen)
"""

from typing import Dict, Optional, Tuple
from datetime import datetime, timedelta
from collections import deque
from fastapi import HTTPException, status, Request, Depends
from app.db.models.user import User
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    In-memory rate limiter using sliding window algorithm.

    PRODUCTION NOTE:
    For distributed systems, use Redis-backed rate limiting.
    This implementation is suitable for single-instance deployments.
    """

    def __init__(self):
        # Store: user_id -> endpoint -> deque of timestamps
        self._requests: Dict[str, Dict[str, deque]] = {}
        self._cleanup_threshold = 1000  # Cleanup after 1000 entries
        self._request_count = 0

    def _get_window_start(self, window_minutes: int) -> datetime:
        """Calculate the start of the current time window."""
        return datetime.utcnow() - timedelta(minutes=window_minutes)

    def _cleanup_old_entries(self, user_id: str, endpoint: str, window_start: datetime) -> None:
        """Remove timestamps outside the current window."""
        if user_id not in self._requests:
            return

        if endpoint not in self._requests[user_id]:
            return

        # Remove old timestamps
        while (self._requests[user_id][endpoint] and
               self._requests[user_id][endpoint][0] < window_start):
            self._requests[user_id][endpoint].popleft()

        # Remove empty endpoint entry
        if not self._requests[user_id][endpoint]:
            del self._requests[user_id][endpoint]

        # Remove empty user entry
        if not self._requests[user_id]:
            del self._requests[user_id]

    def _periodic_cleanup(self) -> None:
        """Periodically cleanup all expired entries."""
        self._request_count += 1

        if self._request_count % self._cleanup_threshold != 0:
            return

        logger.info("Running periodic rate limiter cleanup")

        # Cleanup all entries older than 60 minutes
        cutoff = datetime.utcnow() - timedelta(minutes=60)
        users_to_remove = []

        for user_id, endpoints in self._requests.items():
            endpoints_to_remove = []

            for endpoint, timestamps in endpoints.items():
                # Remove old timestamps
                while timestamps and timestamps[0] < cutoff:
                    timestamps.popleft()

                if not timestamps:
                    endpoints_to_remove.append(endpoint)

            # Remove empty endpoints
            for endpoint in endpoints_to_remove:
                del endpoints[endpoint]

            if not endpoints:
                users_to_remove.append(user_id)

        # Remove empty users
        for user_id in users_to_remove:
            del self._requests[user_id]

        logger.info(f"Rate limiter cleanup complete. Active users: {len(self._requests)}")

    def check_rate_limit(
        self,
        user_id: str,
        endpoint: str,
        limit: int,
        window_minutes: int
    ) -> Tuple[bool, int]:
        """
        Check if request is within rate limit.

        Args:
            user_id: Unique user identifier
            endpoint: Endpoint identifier (e.g., "POST /companies/{id}/chart")
            limit: Maximum requests allowed in window
            window_minutes: Time window in minutes

        Returns:
            Tuple of (is_allowed, current_count)
        """
        # Periodic cleanup
        self._periodic_cleanup()

        # Initialize user entry
        if user_id not in self._requests:
            self._requests[user_id] = {}

        # Initialize endpoint entry
        if endpoint not in self._requests[user_id]:
            self._requests[user_id][endpoint] = deque()

        # Get current window
        window_start = self._get_window_start(window_minutes)

        # Cleanup old entries
        self._cleanup_old_entries(user_id, endpoint, window_start)

        # Get current count
        current_count = len(self._requests[user_id].get(endpoint, []))

        # Check limit
        if current_count >= limit:
            return False, current_count

        # Record this request
        self._requests[user_id][endpoint].append(datetime.utcnow())

        return True, current_count + 1


# Global rate limiter instance
_rate_limiter = RateLimiter()


def get_rate_limiter() -> RateLimiter:
    """Get the global rate limiter instance."""
    return _rate_limiter


def rate_limit(
    limit: int = 10,
    window_minutes: int = 1,
    endpoint_name: Optional[str] = None
):
    """
    Dependency for rate limiting endpoints.

    Args:
        limit: Maximum requests per window (default: 10)
        window_minutes: Time window in minutes (default: 1)
        endpoint_name: Custom endpoint identifier (default: derived from request)

    Usage:
        @router.post("/resource", dependencies=[Depends(rate_limit(limit=5))])
        def create_resource(...):
            ...

    Raises:
        HTTPException 429: Too Many Requests if limit exceeded
    """
    from app.api.v1.auth import get_current_user

    async def dependency(
        request: Request,
        current_user = Depends(get_current_user)
    ):
        """Rate limit dependency."""
        # Get endpoint identifier
        endpoint = endpoint_name or f"{request.method} {request.url.path}"

        # Check rate limit
        limiter = get_rate_limiter()
        is_allowed, current_count = limiter.check_rate_limit(
            user_id=str(current_user.id),
            endpoint=endpoint,
            limit=limit,
            window_minutes=window_minutes
        )

        if not is_allowed:
            logger.warning(
                f"Rate limit exceeded for user {current_user.email} "
                f"on endpoint {endpoint} ({current_count}/{limit} requests)"
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Too many requests. Limit: {limit} per {window_minutes} minute(s).",
                    "limit": limit,
                    "window_minutes": window_minutes,
                    "retry_after_seconds": window_minutes * 60
                }
            )

        logger.debug(
            f"Rate limit check passed for user {current_user.email} "
            f"on endpoint {endpoint} ({current_count}/{limit} requests)"
        )

        return None

    return dependency


# Preset rate limit configurations
def rate_limit_write():
    """Rate limit for standard write operations (10/minute)."""
    return rate_limit(limit=10, window_minutes=1)


def rate_limit_critical():
    """Rate limit for critical operations (5/minute)."""
    return rate_limit(limit=5, window_minutes=1)


def rate_limit_read():
    """Rate limit for read operations (100/minute)."""
    return rate_limit(limit=100, window_minutes=1)


# Export
__all__ = [
    "RateLimiter",
    "get_rate_limiter",
    "rate_limit",
    "rate_limit_write",
    "rate_limit_critical",
    "rate_limit_read"
]

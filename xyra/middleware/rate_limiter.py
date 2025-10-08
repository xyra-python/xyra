"""
Rate Limiter Middleware for Xyra Framework

This middleware limits the number of requests per client within a time window.
"""

import time
from collections import defaultdict

from ..request import Request
from ..response import Response


class RateLimiter:
    """In-memory rate limiter using sliding window."""

    def __init__(self, requests: int = 100, window: int = 60):
        """
        Initialize rate limiter.

        Args:
            requests: Maximum number of requests allowed per window
            window: Time window in seconds
        """
        self.requests = requests
        self.window = window
        self._requests: dict[str, list[float]] = defaultdict(list)

    def _cleanup_old_requests(self, key: str, current_time: float):
        """Remove requests outside the current window."""
        cutoff = current_time - self.window
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed for the given key.

        Args:
            key: Identifier for the client (e.g., IP address)

        Returns:
            True if allowed, False if rate limited
        """
        current_time = time.time()
        self._cleanup_old_requests(key, current_time)

        if len(self._requests[key]) < self.requests:
            self._requests[key].append(current_time)
            return True
        return False

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests allowed for the key."""
        current_time = time.time()
        self._cleanup_old_requests(key, current_time)
        return max(0, self.requests - len(self._requests[key]))

    def get_reset_time(self, key: str) -> float:
        """Get time until reset (next window)."""
        if not self._requests[key]:
            return 0
        current_time = time.time()
        oldest_request = min(self._requests[key])
        return max(0, self.window - (current_time - oldest_request))


class RateLimitMiddleware:
    """Middleware for rate limiting requests."""

    def __init__(self, limiter: RateLimiter, key_func=None):
        """
        Initialize rate limit middleware.

        Args:
            limiter: RateLimiter instance
            key_func: Function to extract key from request (default: client IP)
        """
        self.limiter = limiter
        self.key_func = key_func or self._default_key_func

    def _default_key_func(self, request: Request) -> str:
        """Default key function using client IP."""
        # Try to get real IP from headers
        ip = (
            request.get_header("X-Forwarded-For")
            or request.get_header("X-Real-IP")
            or "127.0.0.1"
        )  # fallback for local development
        return ip.split(",")[0].strip()

    def __call__(self, request: Request, response: Response):
        """Apply rate limiting."""
        key = self.key_func(request)

        if not self.limiter.is_allowed(key):
            # Rate limit exceeded
            response.status(429)
            response.header("Retry-After", str(int(self.limiter.get_reset_time(key))))
            response.header("X-RateLimit-Limit", str(self.limiter.requests))
            response.header("X-RateLimit-Remaining", "0")
            response.json(
                {
                    "error": "Too Many Requests",
                    "message": "Rate limit exceeded. Please try again later.",
                    "retry_after": int(self.limiter.get_reset_time(key)),
                }
            )
            response._ended = True
            return

        # Add rate limit headers
        remaining = self.limiter.get_remaining_requests(key)
        response.header("X-RateLimit-Limit", str(self.limiter.requests))
        response.header("X-RateLimit-Remaining", str(remaining))
        response.header(
            "X-RateLimit-Reset",
            str(int(time.time() + self.limiter.get_reset_time(key))),
        )

        # Continue to next middleware/handler (no action needed)


def rate_limiter(requests: int = 100, window: int = 60, key_func=None):
    """
    Create a rate limiter middleware.

    Args:
        requests: Maximum requests per window
        window: Time window in seconds
        key_func: Function to extract key from request

    Returns:
        RateLimitMiddleware instance
    """
    limiter = RateLimiter(requests=requests, window=window)
    return RateLimitMiddleware(limiter, key_func)

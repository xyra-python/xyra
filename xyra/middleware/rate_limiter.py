import threading
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
        self._lock = threading.RLock()  # Thread-safe lock

    def _cleanup_old_requests(self, key: str, current_time: float):
        """Remove requests outside the current window."""
        with self._lock:
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

        with self._lock:
            if len(self._requests[key]) < self.requests:
                self._requests[key].append(current_time)
                return True
            return False

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests allowed for the key."""
        current_time = time.time()
        self._cleanup_old_requests(key, current_time)

        with self._lock:
            return max(0, self.requests - len(self._requests[key]))

    def get_reset_time(self, key: str) -> float:
        """Get time until reset (next window)."""
        with self._lock:
            if not self._requests[key]:
                return 0
            current_time = time.time()
            oldest_request = min(self._requests[key])
            return max(0, self.window - (current_time - oldest_request))


class RateLimitMiddleware:
    """Middleware for rate limiting requests."""

    def __init__(
        self, limiter: RateLimiter, key_func=None, trust_proxy: bool = False
    ):
        """
        Initialize rate limit middleware.

        Args:
            limiter: RateLimiter instance
            key_func: Function to extract key from request (default: client IP)
            trust_proxy: Whether to trust proxy headers (X-Forwarded-For, X-Real-IP)
        """
        self.limiter = limiter
        self.key_func = key_func or self._default_key_func
        self.trust_proxy = trust_proxy

    def _default_key_func(self, request: Request) -> str:
        """
        Default key function using client IP.

        SECURITY:
        By default (trust_proxy=False), we use the direct connection IP (remote_addr)
        to prevent IP spoofing via headers like X-Forwarded-For.
        If the app is behind a trusted proxy, set trust_proxy=True.
        """
        if self.trust_proxy:
            # Try to get real IP from headers if trust_proxy is enabled
            ip = request.get_header("X-Forwarded-For") or request.get_header(
                "X-Real-IP"
            )
            if ip:
                return ip.split(",")[0].strip()

        # Fallback to direct connection IP
        return request.remote_addr or "unknown"

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


def rate_limiter(
    requests: int = 100,
    window: int = 60,
    key_func=None,
    trust_proxy: bool = False,
):
    """
    Create a rate limiter middleware.

    Args:
        requests: Maximum requests per window
        window: Time window in seconds
        key_func: Function to extract key from request
        trust_proxy: Whether to trust proxy headers

    Returns:
        RateLimitMiddleware instance
    """
    limiter = RateLimiter(requests=requests, window=window)
    return RateLimitMiddleware(limiter, key_func, trust_proxy=trust_proxy)

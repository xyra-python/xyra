import threading
import time
from collections import deque

from ..request import Request
from ..response import Response


class RateLimiter:
    """
    In-memory rate limiter using sliding window.

    SECURITY: Implements max_entries and LRU eviction to prevent memory exhaustion DoS.
    """

    def __init__(
        self,
        requests: int = 100,
        window: int = 60,
        cleanup_interval: int = 1000,
        max_entries: int = 10000,
    ):
        """
        Initialize rate limiter.

        Args:
            requests: Maximum number of requests allowed per window
            window: Time window in seconds
            cleanup_interval: Number of requests before triggering cleanup
            max_entries: Maximum number of unique keys to track (LRU eviction)
        """
        self.requests = requests
        self.window = window
        self.cleanup_interval = cleanup_interval
        self.max_entries = max_entries
        self._requests: dict[str, deque[float]] = {}  # Regular dict for O(1) LRU
        self._lock = threading.RLock()  # Thread-safe lock
        self._request_counter = 0

    def cleanup(self):
        """Remove empty keys and expired requests."""
        current_time = time.monotonic()
        with self._lock:
            # Iterate over a copy of keys to allow deletion
            for key in list(self._requests.keys()):
                self._cleanup_old_requests(key, current_time)
                # If key was removed by _cleanup_old_requests (because it didn't exist)
                # or is now empty, delete it.
                if key in self._requests and not self._requests[key]:
                    del self._requests[key]

    def _cleanup_old_requests(self, key: str, current_time: float):
        """Remove requests outside the current window."""
        with self._lock:
            if key not in self._requests:
                return

            cutoff = current_time - self.window
            timestamps = self._requests[key]
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

    def is_allowed(self, key: str) -> bool:
        """
        Check if request is allowed for the given key.

        Args:
            key: Identifier for the client (e.g., IP address)

        Returns:
            True if allowed, False if rate limited
        """
        # SECURITY: Use monotonic() to prevent bypasses via system clock changes
        current_time = time.monotonic()

        with self._lock:
            # 1. Cleanup old entries periodically
            self._request_counter += 1
            if self._request_counter >= self.cleanup_interval:
                self.cleanup()
                self._request_counter = 0

            # 2. Extract or create the entry
            if key in self._requests:
                # Move to end to maintain LRU (Python 3.7+ dicts are ordered)
                timestamps = self._requests.pop(key)
                self._requests[key] = timestamps
            else:
                # LRU Eviction: If we exceed max_entries, remove the oldest one
                if len(self._requests) >= self.max_entries:
                    # Pop the first (oldest) item
                    oldest_key = next(iter(self._requests))
                    del self._requests[oldest_key]

                timestamps = deque()
                self._requests[key] = timestamps

            # 3. Cleanup old timestamps for THIS key
            cutoff = current_time - self.window
            while timestamps and timestamps[0] <= cutoff:
                timestamps.popleft()

            # 4. Check limit and append
            if len(timestamps) < self.requests:
                timestamps.append(current_time)
                return True

            return False

    def get_remaining_requests(self, key: str) -> int:
        """Get remaining requests allowed for the key."""
        current_time = time.monotonic()

        with self._lock:
            if key not in self._requests:
                return self.requests

            self._cleanup_old_requests(key, current_time)
            return max(0, self.requests - len(self._requests[key]))

    def get_reset_time(self, key: str) -> float:
        """Get time until reset (next window)."""
        with self._lock:
            if key not in self._requests or not self._requests[key]:
                return 0

            current_time = time.monotonic()
            # PERF: Requests are ordered by time, so the first element is always the oldest
            oldest_request = self._requests[key][0]
            return max(0, self.window - (current_time - oldest_request))


class RateLimitMiddleware:
    """Middleware for rate limiting requests."""

    def __init__(
        self,
        limiter: RateLimiter,
        key_func=None,
        trust_proxy: bool = False,
        trusted_proxy_count: int = 1,
    ):
        """
        Initialize rate limit middleware.

        Args:
            limiter: RateLimiter instance
            key_func: Function to extract key from request (default: client IP)
            trust_proxy: (Deprecated) Whether to trust proxy headers. Use ProxyHeadersMiddleware instead.
            trusted_proxy_count: (Deprecated) Number of trusted proxies.
        """
        self.limiter = limiter
        self.key_func = key_func or self._default_key_func

        if trust_proxy:
            from ..logger import get_logger

            logger = get_logger("xyra")
            logger.warning(
                "🚨 Security Warning: 'trust_proxy' in RateLimitMiddleware is deprecated and unsafe. "
                "It allows IP spoofing via X-Forwarded-For headers if not properly validated. "
                "Please use 'xyra.middleware.ProxyHeadersMiddleware' to securely resolve client IPs "
                "before this middleware runs."
            )

    def _default_key_func(self, request: Request) -> str:
        """
        Default key function using client IP.

        SECURITY:
        We strictly use request.remote_addr to prevent IP spoofing.
        To handle proxies correctly, use ProxyHeadersMiddleware which validates
        X-Forwarded-For and updates request.remote_addr securely.
        """
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
    trusted_proxy_count: int = 1,
    cleanup_interval: int = 1000,
    max_entries: int = 10000,
):
    """
    Create a rate limiter middleware.

    Args:
        requests: Maximum requests per window
        window: Time window in seconds
        key_func: Function to extract key from request
        trust_proxy: Whether to trust proxy headers
        trusted_proxy_count: Number of trusted proxies
        cleanup_interval: Number of requests before triggering cleanup
        max_entries: Maximum number of unique keys to track

    Returns:
        RateLimitMiddleware instance
    """
    limiter = RateLimiter(
        requests=requests,
        window=window,
        cleanup_interval=cleanup_interval,
        max_entries=max_entries,
    )
    return RateLimitMiddleware(
        limiter,
        key_func,
        trust_proxy=trust_proxy,
        trusted_proxy_count=trusted_proxy_count,
    )

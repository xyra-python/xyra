"""
Xyra Framework Middleware Module

This module contains various middleware components for the Xyra web framework.
Middleware functions are executed in the order they are added to the application
and can modify requests and responses or perform actions before/after route handlers.
"""

from .cors import CorsMiddleware, cors
from .gzip import GzipMiddleware, gzip_middleware
from .httpsredirect import HTTPSRedirectMiddleware, https_redirect_middleware
from .rate_limiter import RateLimiter, RateLimitMiddleware, rate_limiter
from .trustedhost import TrustedHostMiddleware, trusted_host_middleware

__all__ = [
    "CorsMiddleware",
    "cors",
    "GzipMiddleware",
    "gzip_middleware",
    "HTTPSRedirectMiddleware",
    "https_redirect_middleware",
    "RateLimiter",
    "RateLimitMiddleware",
    "rate_limiter",
    "TrustedHostMiddleware",
    "trusted_host_middleware",
]

# Version info
__version__ = "0.1.6"

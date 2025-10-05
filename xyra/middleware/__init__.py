"""
Xyra Framework Middleware Module

This module contains various middleware components for the Xyra web framework.
Middleware functions are executed in the order they are added to the application
and can modify requests and responses or perform actions before/after route handlers.
"""

from .cors import CorsMiddleware, cors

__all__ = ["CorsMiddleware", "cors"]

# Version info
__version__ = "0.1.0"

"""
Exception classes for Xyra framework.

This module defines custom exceptions used throughout the Xyra framework
for handling various error conditions in web applications.
"""

from typing import Any


class XyraException(Exception):
    """Base exception class for all Xyra-specific exceptions."""

    def __init__(self, message: str = "An error occurred"):
        self.message = message
        super().__init__(message)


class HTTPException(XyraException):
    """
    HTTP exception for handling HTTP error responses.

    This exception is raised to indicate HTTP errors that should result
    in specific status codes and error messages in the response.

    Attributes:
        status_code: HTTP status code (e.g., 404, 500).
        detail: Detailed error message.
        headers: Additional headers to include in the error response.
    """

    def __init__(
        self,
        status_code: int,
        detail: str | None = None,
        headers: dict[str, str] | None = None,
    ):
        """
        Initialize HTTP exception.

        Args:
            status_code: HTTP status code for the error.
            detail: Custom error message. If None, uses default for status code.
            headers: Optional headers to add to the response.
        """
        self.status_code = status_code
        self.detail = detail or self._get_default_detail(status_code)
        self.headers = headers or {}
        super().__init__(f"{status_code}: {self.detail}")

    @staticmethod
    def _get_default_detail(status_code: int) -> str:
        """
        Get default error message for a given HTTP status code.

        Args:
            status_code: HTTP status code integer.

        Returns:
            Default error message string for the status code.
        """
        status_messages = {
            400: "Bad Request",
            401: "Unauthorized",
            403: "Forbidden",
            404: "Not Found",
            405: "Method Not Allowed",
            406: "Not Acceptable",
            409: "Conflict",
            410: "Gone",
            422: "Unprocessable Entity",
            429: "Too Many Requests",
            500: "Internal Server Error",
            501: "Not Implemented",
            502: "Bad Gateway",
            503: "Service Unavailable",
            504: "Gateway Timeout",
        }
        return status_messages.get(status_code, "HTTP Error")


class WebSocketException(XyraException):
    """Exception for WebSocket-related errors."""

    def __init__(self, code: int, reason: str | None = None):
        self.code = code
        self.reason = reason or self._get_default_reason(code)
        super().__init__(f"WebSocket Error {code}: {self.reason}")

    @staticmethod
    def _get_default_reason(code: int) -> str:
        """Get default reason for WebSocket close code."""
        close_codes = {
            1000: "Normal Closure",
            1001: "Going Away",
            1002: "Protocol Error",
            1003: "Unsupported Data",
            1005: "No Status Code",
            1006: "Abnormal Closure",
            1007: "Invalid Frame Payload Data",
            1008: "Policy Violation",
            1009: "Message Too Big",
            1010: "Mandatory Extension",
            1011: "Internal Server Error",
            1015: "TLS Handshake",
        }
        return close_codes.get(code, "Unknown Error")


class ValidationException(XyraException):
    """Exception for request validation errors."""

    def __init__(self, message: str, errors: dict[str, Any] | None = None):
        self.errors = errors or {}
        super().__init__(message)


class MiddlewareException(XyraException):
    """Exception for middleware-related errors."""

    pass


class TemplateException(XyraException):
    """Exception for template rendering errors."""

    def __init__(self, message: str, template_name: str | None = None):
        self.template_name = template_name
        super().__init__(message)


class RouteException(XyraException):
    """Exception for routing-related errors."""

    pass


class ConfigurationException(XyraException):
    """Exception for configuration-related errors."""

    pass


# Convenience functions for common HTTP exceptions
def bad_request(detail: str = "Bad Request") -> HTTPException:
    """Create a 400 Bad Request exception."""
    return HTTPException(400, detail)


def unauthorized(detail: str = "Unauthorized") -> HTTPException:
    """Create a 401 Unauthorized exception."""
    return HTTPException(401, detail)


def forbidden(detail: str = "Forbidden") -> HTTPException:
    """Create a 403 Forbidden exception."""
    return HTTPException(403, detail)


def not_found(detail: str = "Not Found") -> HTTPException:
    """Create a 404 Not Found exception."""
    return HTTPException(404, detail)


def method_not_allowed(detail: str = "Method Not Allowed") -> HTTPException:
    """Create a 405 Method Not Allowed exception."""
    return HTTPException(405, detail)


def conflict(detail: str = "Conflict") -> HTTPException:
    """Create a 409 Conflict exception."""
    return HTTPException(409, detail)


def unprocessable_entity(detail: str = "Unprocessable Entity") -> HTTPException:
    """Create a 422 Unprocessable Entity exception."""
    return HTTPException(422, detail)


def too_many_requests(detail: str = "Too Many Requests") -> HTTPException:
    """Create a 429 Too Many Requests exception."""
    return HTTPException(429, detail)


def internal_server_error(detail: str = "Internal Server Error") -> HTTPException:
    """Create a 500 Internal Server Error exception."""
    return HTTPException(500, detail)


def not_implemented(detail: str = "Not Implemented") -> HTTPException:
    """Create a 501 Not Implemented exception."""
    return HTTPException(501, detail)


def service_unavailable(detail: str = "Service Unavailable") -> HTTPException:
    """Create a 503 Service Unavailable exception."""
    return HTTPException(503, detail)

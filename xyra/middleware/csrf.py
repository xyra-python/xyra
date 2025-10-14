import secrets

from ..request import Request
from ..response import Response


class CSRFMiddleware:
    """CSRF (Cross-Site Request Forgery) protection middleware for Xyra applications."""

    def __init__(
        self,
        secret_key: str | None = None,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        exempt_methods: list[str] | None = None,
        secure: bool = False,
        http_only: bool = True,
        same_site: str = "Lax",
    ):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.exempt_methods = exempt_methods or ["GET", "HEAD", "OPTIONS"]
        self.secure = secure
        self.http_only = http_only
        self.same_site = same_site

    def _generate_token(self) -> str:
        """Generate a new CSRF token."""
        return secrets.token_urlsafe(32)

    def _get_cookie(self, request: Request, name: str) -> str | None:
        """Extract cookie value from request headers."""
        cookie_header = request.get_header("cookie")
        if not cookie_header:
            return None
        cookies = {}
        for item in cookie_header.split(";"):
            if "=" in item:
                key, value = item.strip().split("=", 1)
                cookies[key] = value
        return cookies.get(name)

    def _get_token_from_request(self, request: Request) -> str | None:
        """Extract CSRF token from request header."""
        return request.get_header(self.header_name)

    def __call__(self, request: Request, response: Response):
        """Handle CSRF protection for the request."""
        # Skip CSRF check for exempt methods
        if request.method in self.exempt_methods:
            # Set CSRF token cookie if not present
            if not self._get_cookie(request, self.cookie_name):
                token = self._generate_token()
                response.set_cookie(
                    self.cookie_name,
                    token,
                    secure=self.secure,
                    http_only=self.http_only,
                    same_site=self.same_site,
                )
            return

        # Get expected token from cookie
        expected_token = self._get_cookie(request, self.cookie_name)
        if not expected_token:
            response.status(403)
            response.json({"error": "CSRF token missing"})
            response._ended = True
            return

        # Get token from request
        request_token = self._get_token_from_request(request)
        if not request_token or not secrets.compare_digest(
            request_token, expected_token
        ):
            response.status(403)
            response.json({"error": "CSRF token invalid"})
            response._ended = True
            return

        # Token valid, continue


def csrf(
    secret_key: str | None = None,
    cookie_name: str = "csrf_token",
    header_name: str = "X-CSRF-Token",
    exempt_methods: list[str] | None = None,
    secure: bool = False,
    http_only: bool = True,
    same_site: str = "Lax",
):
    """
    Create a CSRF middleware function.

    This is a convenience function that creates and returns a CSRF middleware instance.
    """
    return CSRFMiddleware(
        secret_key=secret_key,
        cookie_name=cookie_name,
        header_name=header_name,
        exempt_methods=exempt_methods,
        secure=secure,
        http_only=http_only,
        same_site=same_site,
    )

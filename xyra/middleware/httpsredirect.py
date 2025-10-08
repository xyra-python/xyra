"""
HTTPS Redirect Middleware for Xyra Framework

This middleware redirects HTTP requests to HTTPS.
"""


from ..request import Request
from ..response import Response


class HTTPSRedirectMiddleware:
    """Middleware for redirecting HTTP requests to HTTPS."""

    def __init__(self, redirect_status_code: int = 301):
        """
        Initialize HTTPS redirect middleware.

        Args:
            redirect_status_code: HTTP status code for redirect (301 or 302)
        """
        self.redirect_status_code = redirect_status_code

    def __call__(self, req: Request, res: Response):
        """Redirect HTTP requests to HTTPS."""
        # Check if request is HTTP
        if req.headers.get(
            "X-Forwarded-Proto", ""
        ).lower() == "http" or not req.url.startswith("https://"):
            # Build HTTPS URL
            https_url = req.url.replace("http://", "https://", 1)

            # Redirect to HTTPS
            res.status(self.redirect_status_code)
            res.header("Location", https_url)
            res.send("")
            res._ended = True
            return

        # Continue to next middleware


def https_redirect_middleware(
    redirect_status_code: int = 301,
) -> HTTPSRedirectMiddleware:
    """Create an HTTPS redirect middleware instance."""
    return HTTPSRedirectMiddleware(redirect_status_code)

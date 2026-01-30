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
        # Check X-Forwarded-Proto (standard for load balancers)
        # Headers keys are lowercase in Xyra Request
        forwarded_proto = req.headers.get("x-forwarded-proto", "http").lower()

        # If we are already https, do nothing
        if forwarded_proto == "https":
            return

        # If no host header, we can't redirect reliably
        host = req.headers.get("host")
        if not host:
            # If we can't determine host, we can't redirect safely.
            res.status(400)
            res.send("Bad Request: Missing Host header")
            res._ended = True
            return

        # Construct HTTPS URL
        # req.url in Xyra/socketify is just the path (e.g. /foo/bar)
        path = req.url
        query = req.query

        if query:
            full_path = f"{path}?{query}"
        else:
            full_path = path

        https_url = f"https://{host}{full_path}"

        # Redirect to HTTPS
        res.status(self.redirect_status_code)
        res.header("Location", https_url)
        res.send("")
        res._ended = True
        return


def https_redirect_middleware(
    redirect_status_code: int = 301,
) -> HTTPSRedirectMiddleware:
    """Create an HTTPS redirect middleware instance."""
    return HTTPSRedirectMiddleware(redirect_status_code)

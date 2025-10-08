"""
Trusted Host Middleware for Xyra Framework

This middleware validates that the request's Host header is in a list of allowed hosts.
"""


from ..request import Request
from ..response import Response


class TrustedHostMiddleware:
    """Middleware for validating trusted hosts."""

    def __init__(self, allowed_hosts: list[str]):
        """
        Initialize trusted host middleware.

        Args:
            allowed_hosts: List of allowed hostnames
        """
        self.allowed_hosts = allowed_hosts

    def __call__(self, req: Request, res: Response):
        """Validate the request's Host header."""
        host = req.headers.get("Host", "").split(":")[0]  # Remove port

        if host not in self.allowed_hosts:
            # Return 400 Bad Request for untrusted host
            res.status(400)
            res.json({"error": "Bad Request", "message": "Untrusted host"})
            res._ended = True
            return

        # Continue to next middleware


def trusted_host_middleware(allowed_hosts: list[str]) -> TrustedHostMiddleware:
    """Create a trusted host middleware instance."""
    return TrustedHostMiddleware(allowed_hosts)

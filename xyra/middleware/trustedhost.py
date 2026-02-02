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
        # Headers keys are lowercase in Xyra Request
        host = req.headers.get("host", "")

        # Correctly handle IPv6 literals
        if host.startswith("["):
            # Find the closing bracket
            end_index = host.find("]")
            if end_index != -1:
                host = host[:end_index + 1]
            else:
                # Malformed IPv6 literal? Fallback or treat as is
                pass
        else:
            # IPv4 or domain name: remove port
            host = host.split(":")[0]

        is_allowed = False
        for allowed in self.allowed_hosts:
            if allowed == "*":
                is_allowed = True
                break
            if allowed.startswith("*."):
                # Wildcard subdomain
                domain = allowed[2:]
                if host == domain or host.endswith("." + domain):
                    is_allowed = True
                    break
            if allowed == host:
                is_allowed = True
                break

        if not is_allowed:
            # Return 400 Bad Request for untrusted host
            res.status(400)
            res.json({"error": "Bad Request", "message": "Untrusted host"})
            res._ended = True
            return

        # Continue to next middleware


def trusted_host_middleware(allowed_hosts: list[str]) -> TrustedHostMiddleware:
    """Create a trusted host middleware instance."""
    return TrustedHostMiddleware(allowed_hosts)

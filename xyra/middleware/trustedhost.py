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
            allowed_hosts: List of allowed hostnames.
                           Example: ["example.com", "*.example.com", "example.com:8080"]
        """
        self.allowed_hosts = allowed_hosts
        # Pre-parse allowed hosts for performance
        self._patterns = [self._parse_host(host) for host in allowed_hosts]

    def _parse_host(self, host: str) -> tuple[str, str | None]:
        """
        Parse a host string into (domain, port).
        Handles IPv6 literals like [::1] or [::1]:8080 correctly.
        """
        if host.startswith("["):
            # IPv6 literal
            end_bracket = host.find("]")
            if end_bracket != -1:
                domain = host[: end_bracket + 1]
                rest = host[end_bracket + 1 :]
                if rest.startswith(":"):
                    return domain, rest[1:]
                return domain, None
            # Malformed IPv6, treat as opaque string
            return host, None

        # IPv4 or domain name
        if ":" in host:
            domain, port = host.rsplit(":", 1)
            return domain, port

        return host, None

    def __call__(self, req: Request, res: Response):
        """Validate the request's Host header."""
        # Headers keys are lowercase in Xyra Request
        host = req.get_header("host", "")

        if not host:
            res.status(400)
            res.json({"error": "Bad Request", "message": "Missing Host header"})
            res._ended = True
            return

        # SECURITY: Sanity check for invalid characters that could alter the URL structure
        if any(char in host for char in ["/", "?", "#", "\\", "@"]):
            res.status(400)
            res.json({"error": "Bad Request", "message": "Invalid Host header"})
            res._ended = True
            return

        # Lowercase host for case-insensitive matching
        host = host.lower()

        # Parse request host
        req_domain, req_port = self._parse_host(host)

        is_allowed = False
        for allowed_domain, allowed_port in self._patterns:
            if allowed_domain == "*":
                is_allowed = True
                break

            # Check domain match
            domain_match = False
            if allowed_domain.startswith("*."):
                # Wildcard subdomain matching
                suffix = allowed_domain[2:]
                # Matches "sub.example.com" AND "example.com"
                if req_domain == suffix or req_domain.endswith("." + suffix):
                    domain_match = True
            elif allowed_domain == req_domain:
                domain_match = True

            # Check port match if domain matched
            if domain_match:
                # If allowed pattern specifies a port, request MUST match it exactly
                if allowed_port is not None:
                    if req_port == allowed_port:
                        is_allowed = True
                        break
                else:
                    # Allowed pattern has no port -> allow any port
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

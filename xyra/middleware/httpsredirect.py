"""
HTTPS Redirect Middleware for Xyra Framework

This middleware redirects HTTP requests to HTTPS.
"""

from ..request import Request
from ..response import Response


class HTTPSRedirectMiddleware:
    """Middleware for redirecting HTTP requests to HTTPS."""

    def __init__(
        self,
        redirect_status_code: int = 301,
        trust_proxy: bool = False,
        allowed_hosts: list[str] | None = None,
    ):
        """
        Initialize HTTPS redirect middleware.

        Args:
            redirect_status_code: HTTP status code for redirect (301 or 302)
            trust_proxy: (Deprecated) Whether to trust proxy headers.
                         Use ProxyHeadersMiddleware to securely resolve scheme.
            allowed_hosts: List of allowed hosts (e.g. ["example.com", "*.example.com"])
        """
        self.redirect_status_code = redirect_status_code
        self.trust_proxy = trust_proxy
        self.allowed_hosts = allowed_hosts

        if self.trust_proxy:
            from ..logger import get_logger

            logger = get_logger("xyra")
            logger.warning(
                "🚨 Security Warning: 'trust_proxy' in HTTPSRedirectMiddleware is deprecated and unsafe. "
                "It allows scheme spoofing via X-Forwarded-Proto headers if not properly validated. "
                "Please use 'xyra.middleware.ProxyHeadersMiddleware' to securely resolve the scheme "
                "before this middleware runs."
            )

    def __call__(self, req: Request, res: Response):
        """Redirect HTTP requests to HTTPS."""
        # Check scheme (resolved by ProxyHeadersMiddleware if configured)
        # SECURITY: Do NOT read X-Forwarded-Proto directly unless verified by ProxyHeadersMiddleware.
        # req.scheme defaults to "http", but is updated to "https" if ProxyHeadersMiddleware verifies it.
        if req.scheme == "https":
            return

        # If no host header, we can't redirect reliably
        host = req.get_header("host")
        if not host:
            # If we can't determine host, we can't redirect safely.
            res.status(400)
            res.send("Bad Request: Missing Host header")
            res._ended = True
            return

        # SECURITY: Validate Host header to prevent Host Header Injection
        # 1. Sanity check for invalid characters that could alter the URL structure
        if any(char in host for char in ["/", "?", "#", "\\", "@"]):
            res.status(400)
            res.send("Bad Request: Invalid Host header")
            res._ended = True
            return

        # 2. Check against allowed_hosts if configured
        if self.allowed_hosts:
            is_allowed = False

            # Correctly handle IPv6 literals
            if host.startswith("["):
                # Find the closing bracket
                end_index = host.find("]")
                if end_index != -1:
                    hostname = host[: end_index + 1]
                else:
                    hostname = host
            else:
                hostname = host.split(":")[0]

            for allowed in self.allowed_hosts:
                if allowed == "*":
                    is_allowed = True
                    break
                if allowed == host or allowed == hostname:
                    is_allowed = True
                    break
                if allowed.startswith("*."):
                    domain = allowed[2:]
                    if hostname == domain or hostname.endswith("." + domain):
                        is_allowed = True
                        break

            if not is_allowed:
                res.status(400)
                res.send("Bad Request: Untrusted Host")
                res._ended = True
                return

        # Construct HTTPS URL
        # req.url in Xyra/native is just the path (e.g. /foo/bar)
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
    trust_proxy: bool = False,
    allowed_hosts: list[str] | None = None,
) -> HTTPSRedirectMiddleware:
    """Create an HTTPS redirect middleware instance."""
    return HTTPSRedirectMiddleware(
        redirect_status_code, trust_proxy=trust_proxy, allowed_hosts=allowed_hosts
    )

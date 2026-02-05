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
            trust_proxy: Whether to trust proxy headers (X-Forwarded-Proto)
            allowed_hosts: List of allowed hosts (e.g. ["example.com", "*.example.com"])
        """
        self.redirect_status_code = redirect_status_code
        self.trust_proxy = trust_proxy
        self.allowed_hosts = allowed_hosts

    def __call__(self, req: Request, res: Response):
        """Redirect HTTP requests to HTTPS."""
        # Check X-Forwarded-Proto (standard for load balancers)
        # Headers keys are lowercase in Xyra Request
        forwarded_proto = "http"
        if self.trust_proxy:
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

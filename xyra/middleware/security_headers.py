from ..request import Request
from ..response import Response


class SecurityHeadersMiddleware:
    """
    Middleware that adds security headers to responses.

    By default, it adds:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: SAMEORIGIN
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    """

    def __init__(
        self,
        hsts_seconds: int = 0,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        content_security_policy: str | dict | None = None,
        permissions_policy: str | dict | None = None,
        frame_options: str = "SAMEORIGIN",
        xss_protection: str = "1; mode=block",
        content_type_options: str = "nosniff",
        referrer_policy: str = "strict-origin-when-cross-origin",
    ):
        self.hsts_seconds = hsts_seconds
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        self.content_security_policy = content_security_policy
        self.permissions_policy = permissions_policy
        self.frame_options = frame_options
        self.xss_protection = xss_protection
        self.content_type_options = content_type_options
        self.referrer_policy = referrer_policy

    def __call__(self, request: Request, response: Response):
        # HSTS
        if self.hsts_seconds > 0:
            hsts_value = f"max-age={self.hsts_seconds}"
            if self.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.hsts_preload:
                hsts_value += "; preload"
            response.header("Strict-Transport-Security", hsts_value)

        # Content-Security-Policy
        if self.content_security_policy:
            if isinstance(self.content_security_policy, dict):
                policy_parts = []
                for directive, sources in self.content_security_policy.items():
                    if isinstance(sources, list):
                        sources_str = " ".join(sources)
                    else:
                        sources_str = str(sources)
                    policy_parts.append(f"{directive} {sources_str}")
                csp_value = "; ".join(policy_parts)
                response.header("Content-Security-Policy", csp_value)
            else:
                response.header(
                    "Content-Security-Policy", str(self.content_security_policy)
                )

        # Permissions-Policy
        if self.permissions_policy:
            if isinstance(self.permissions_policy, dict):
                policy_parts = []
                for feature, value in self.permissions_policy.items():
                    if isinstance(value, list):
                        # If list, format as (value1 value2) or similar?
                        # Standard is: geolocation=(self "https://example.com")
                        # But simpler implementation might just expect strings
                        # Let's assume list means list of origins
                        sources_str = " ".join(value)
                        policy_parts.append(f"{feature}=({sources_str})")
                    else:
                        policy_parts.append(f"{feature}={value}")
                pp_value = ", ".join(policy_parts)
                response.header("Permissions-Policy", pp_value)
            else:
                response.header("Permissions-Policy", str(self.permissions_policy))

        # Other Headers
        if self.frame_options:
            response.header("X-Frame-Options", self.frame_options)

        if self.xss_protection:
            response.header("X-XSS-Protection", self.xss_protection)

        if self.content_type_options:
            response.header("X-Content-Type-Options", self.content_type_options)

        if self.referrer_policy:
            response.header("Referrer-Policy", self.referrer_policy)


def security_headers(
    hsts_seconds: int = 0,
    hsts_include_subdomains: bool = True,
    hsts_preload: bool = False,
    content_security_policy: str | dict | None = None,
    permissions_policy: str | dict | None = None,
    frame_options: str = "SAMEORIGIN",
    xss_protection: str = "1; mode=block",
    content_type_options: str = "nosniff",
    referrer_policy: str = "strict-origin-when-cross-origin",
):
    """
    Create a SecurityHeaders middleware function.
    """
    return SecurityHeadersMiddleware(
        hsts_seconds=hsts_seconds,
        hsts_include_subdomains=hsts_include_subdomains,
        hsts_preload=hsts_preload,
        content_security_policy=content_security_policy,
        permissions_policy=permissions_policy,
        frame_options=frame_options,
        xss_protection=xss_protection,
        content_type_options=content_type_options,
        referrer_policy=referrer_policy,
    )

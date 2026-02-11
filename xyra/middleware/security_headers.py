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
    - X-Permitted-Cross-Domain-Policies: none
    - Cross-Origin-Opener-Policy: same-origin

    PERF: Headers are pre-calculated in __init__ to avoid overhead on every request.
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
        cross_domain_policy: str = "none",
        opener_policy: str = "same-origin",
    ):
        self.headers: list[tuple[str, str]] = []

        # HSTS
        if hsts_seconds > 0:
            hsts_value = f"max-age={hsts_seconds}"
            if hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if hsts_preload:
                hsts_value += "; preload"
            self.headers.append(("Strict-Transport-Security", hsts_value))

        # Content-Security-Policy
        if content_security_policy:
            if isinstance(content_security_policy, dict):
                policy_parts = []
                for directive, sources in content_security_policy.items():
                    if isinstance(sources, list):
                        sources_str = " ".join(sources)
                    else:
                        sources_str = str(sources)
                    policy_parts.append(f"{directive} {sources_str}")
                csp_value = "; ".join(policy_parts)
                self.headers.append(("Content-Security-Policy", csp_value))
            else:
                self.headers.append(
                    ("Content-Security-Policy", str(content_security_policy))
                )

        # Permissions-Policy
        if permissions_policy:
            if isinstance(permissions_policy, dict):
                policy_parts = []
                for feature, value in permissions_policy.items():
                    if isinstance(value, list):
                        # If list, format as (value1 value2) or similar?
                        # Standard is: geolocation=(self "https://example.com")
                        sources_str = " ".join(value)
                        policy_parts.append(f"{feature}=({sources_str})")
                    else:
                        policy_parts.append(f"{feature}={value}")
                pp_value = ", ".join(policy_parts)
                self.headers.append(("Permissions-Policy", pp_value))
            else:
                self.headers.append(("Permissions-Policy", str(permissions_policy)))

        # Other Headers
        if frame_options:
            self.headers.append(("X-Frame-Options", frame_options))

        if xss_protection:
            self.headers.append(("X-XSS-Protection", xss_protection))

        if content_type_options:
            self.headers.append(("X-Content-Type-Options", content_type_options))

        if referrer_policy:
            self.headers.append(("Referrer-Policy", referrer_policy))

        if cross_domain_policy:
            self.headers.append(("X-Permitted-Cross-Domain-Policies", cross_domain_policy))

        if opener_policy:
            self.headers.append(("Cross-Origin-Opener-Policy", opener_policy))

        # SECURITY:
        # Risk: Missing or weak security headers expose users to XSS, Clickjacking, and other attacks.
        # Attack: Attacker exploits lack of COOP/CSP to perform cross-origin attacks.
        # Mitigation: Add defense-in-depth headers (COOP, CSP, HSTS) by default.

    def __call__(self, request: Request, response: Response):
        # PERF: Iterate over pre-calculated headers
        for key, value in self.headers:
            response.header(key, value)


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
    cross_domain_policy: str = "none",
    opener_policy: str = "same-origin",
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
        cross_domain_policy=cross_domain_policy,
        opener_policy=opener_policy,
    )

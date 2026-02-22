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
    - Permissions-Policy: geolocation=(), camera=(), microphone=()

    PERF: Headers are pre-calculated in __init__ to avoid overhead on every request.
    """

    def __init__(
        self,
        hsts_seconds: int = 0,
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        content_security_policy: str | dict | None = None,
        permissions_policy: str
        | dict
        | None = "geolocation=(), camera=(), microphone=()",
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
                        sources_str = " ".join(value)

                        # SECURITY: Validate list content does not contain unquoted ')' which could close the list
                        # and allow injection of other features.
                        if not self._is_safe_policy_value(sources_str):
                            raise ValueError(
                                f"Invalid Permissions-Policy value for '{feature}': '{value}'. "
                                "Value contains unsafe characters (unquoted closing parenthesis) which could allow injection."
                            )

                        policy_parts.append(f"{feature}=({sources_str})")
                    else:
                        val_str = str(value)
                        # Check if it looks wrapped
                        is_wrapped = val_str.startswith("(") and val_str.endswith(")")
                        content = val_str[1:-1] if is_wrapped else val_str

                        # SECURITY: Validate content does not contain unquoted ')' which could close the list
                        # and allow injection of other features.
                        if not self._is_safe_policy_value(content):
                            raise ValueError(
                                f"Invalid Permissions-Policy value for '{feature}': '{value}'. "
                                "Value contains unsafe characters (unquoted closing parenthesis) which could allow injection."
                            )

                        if is_wrapped:
                            policy_parts.append(f"{feature}={val_str}")
                        else:
                            policy_parts.append(f"{feature}=({val_str})")
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
            self.headers.append(
                ("X-Permitted-Cross-Domain-Policies", cross_domain_policy)
            )

        if opener_policy:
            self.headers.append(("Cross-Origin-Opener-Policy", opener_policy))

        # SECURITY:
        # Risk: Missing or weak security headers expose users to XSS, Clickjacking, and other attacks.
        # Attack: Attacker exploits lack of COOP/CSP to perform cross-origin attacks.
        # Mitigation: Add defense-in-depth headers (COOP, CSP, HSTS) by default.

    def _is_safe_policy_value(self, val: str) -> bool:
        """
        Check if the policy value is safe from injection.
        Disallows unquoted ')' characters.
        """
        in_quote = False
        for char in val:
            if char == '"':
                in_quote = not in_quote
            elif char == ')' and not in_quote:
                return False
        return True

    def __call__(self, request: Request, response: Response):
        # PERF: Iterate over pre-calculated headers
        for key, value in self.headers:
            response.header(key, value)


def security_headers(
    hsts_seconds: int = 0,
    hsts_include_subdomains: bool = True,
    hsts_preload: bool = False,
    content_security_policy: str | dict | None = None,
    permissions_policy: str | dict | None = "geolocation=(), camera=(), microphone=()",
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

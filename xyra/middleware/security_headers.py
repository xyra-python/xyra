from ..request import Request
from ..response import Response


class SecurityHeadersMiddleware:
    """
    Middleware that adds security headers to responses.

    By default, it adds:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY
    - X-XSS-Protection: 1; mode=block
    - Referrer-Policy: strict-origin-when-cross-origin
    - X-Permitted-Cross-Domain-Policies: none
    - Cross-Origin-Opener-Policy: same-origin
    - Cross-Origin-Resource-Policy: same-origin
    - X-DNS-Prefetch-Control: off
    - X-Download-Options: noopen
    - Permissions-Policy: geolocation=(), camera=(), microphone=()

    PERF: Headers are pre-calculated in __init__ to avoid overhead on every request.
    """

    def __init__(self, config: dict | None = None, **kwargs):
        self.headers: list[tuple[str, str]] = []

        options = {
            "hsts_seconds": 31536000,
            "hsts_include_subdomains": True,
            "hsts_preload": False,
            "content_security_policy": None,
            "permissions_policy": "geolocation=(), camera=(), microphone=()",
            "frame_options": "DENY",
            "xss_protection": "1; mode=block",
            "content_type_options": "nosniff",
            "referrer_policy": "strict-origin-when-cross-origin",
            "cross_domain_policy": "none",
            "opener_policy": "same-origin",
            "resource_policy": "same-origin",
            "dns_prefetch_control": "off",
            "download_options": "noopen",
        }

        if config:
            options.update(config)
        options.update(kwargs)

        # HSTS
        hsts_seconds = options.get("hsts_seconds")
        if hsts_seconds is not None and hsts_seconds > 0:
            hsts_value = f"max-age={hsts_seconds}"
            if options.get("hsts_include_subdomains"):
                hsts_value += "; includeSubDomains"
            if options.get("hsts_preload"):
                hsts_value += "; preload"
            self.headers.append(("Strict-Transport-Security", hsts_value))

        # Content-Security-Policy
        content_security_policy = options.get("content_security_policy")
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
        permissions_policy = options.get("permissions_policy")
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
        if frame_options := options.get("frame_options"):
            self.headers.append(("X-Frame-Options", frame_options))

        if xss_protection := options.get("xss_protection"):
            self.headers.append(("X-XSS-Protection", xss_protection))

        if content_type_options := options.get("content_type_options"):
            self.headers.append(("X-Content-Type-Options", content_type_options))

        if referrer_policy := options.get("referrer_policy"):
            self.headers.append(("Referrer-Policy", referrer_policy))

        if cross_domain_policy := options.get("cross_domain_policy"):
            self.headers.append(
                ("X-Permitted-Cross-Domain-Policies", cross_domain_policy)
            )

        if opener_policy := options.get("opener_policy"):
            self.headers.append(("Cross-Origin-Opener-Policy", opener_policy))

        if resource_policy := options.get("resource_policy"):
            self.headers.append(("Cross-Origin-Resource-Policy", resource_policy))

        if dns_prefetch_control := options.get("dns_prefetch_control"):
            self.headers.append(("X-DNS-Prefetch-Control", dns_prefetch_control))

        if download_options := options.get("download_options"):
            self.headers.append(("X-Download-Options", download_options))

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


def security_headers(config: dict | None = None, **kwargs):
    """
    Create a SecurityHeaders middleware function.
    """
    return SecurityHeadersMiddleware(config, **kwargs)

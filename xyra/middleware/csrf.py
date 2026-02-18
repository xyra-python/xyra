import base64
import hashlib
import hmac
import secrets
from http.cookies import SimpleCookie

from ..request import Request
from ..response import Response


class CSRFMiddleware:
    """
    CSRF (Cross-Site Request Forgery) protection middleware for Xyra applications.

    SECURITY:
    - Uses Double Submit Cookie pattern with signed cookies.
    - Implements token masking to prevent BREACH attacks.
    - Supports __Host- cookie prefix for enhanced subdomain protection.
    """

    def __init__(
        self,
        secret_key: str | None = None,
        cookie_name: str = "csrf_token",
        header_name: str = "X-CSRF-Token",
        exempt_methods: list[str] | None = None,
        secure: bool = False,
        http_only: bool = True,
        same_site: str = "Lax",
    ):
        self.secret_key = secret_key or secrets.token_hex(32)
        self.header_name = header_name
        self.exempt_methods = exempt_methods or ["GET", "HEAD", "OPTIONS"]
        self.secure = secure
        self.http_only = http_only
        self.same_site = same_site

        # SECURITY: Use __Host- prefix if secure is enabled to prevent cookie tossing
        # from subdomains. This requires Path=/ and no Domain attribute.
        if self.secure and not cookie_name.startswith("__Host-"):
            self.cookie_name = f"__Host-{cookie_name}"
        else:
            self.cookie_name = cookie_name

    def _sign_token(self, token: str) -> str:
        """Sign a token using HMAC."""
        signature = hmac.new(
            self.secret_key.encode(), token.encode(), hashlib.sha256
        ).hexdigest()
        return f"{token}.{signature}"

    def _verify_signed_token(self, signed_token: str) -> str | None:
        """Verify a signed token and return the original token if valid."""
        if not signed_token or "." not in signed_token:
            return None

        try:
            token, signature = signed_token.rsplit(".", 1)
            expected_signature = hmac.new(
                self.secret_key.encode(), token.encode(), hashlib.sha256
            ).hexdigest()

            if hmac.compare_digest(signature, expected_signature):
                return token
            return None
        except Exception:
            return None

    def _generate_token(self) -> str:
        """Generate a new signed CSRF token."""
        token = secrets.token_urlsafe(32)
        return self._sign_token(token)

    def _mask_token(self, token: str) -> str:
        """
        Mask a token using a random 32-byte salt (BREACH protection).
        Returns base64(salt + XOR(token, salt)).
        """
        salt = secrets.token_bytes(32)
        token_bytes = token.encode()
        # XOR token with salt (repeating salt if necessary)
        masked = bytes(t ^ salt[i % 32] for i, t in enumerate(token_bytes))
        return base64.urlsafe_b64encode(salt + masked).decode().rstrip("=")

    def _unmask_token(self, masked_token: str) -> str | None:
        """Unmask a token masked with _mask_token."""
        try:
            # Add back base64 padding if missing
            missing_padding = len(masked_token) % 4
            if missing_padding:
                masked_token += "=" * (4 - missing_padding)

            decoded = base64.urlsafe_b64decode(masked_token)
            if len(decoded) <= 32:
                return None

            salt = decoded[:32]
            masked = decoded[32:]
            unmasked = bytes(t ^ salt[i % 32] for i, t in enumerate(masked))
            return unmasked.decode()
        except Exception:
            return None

    def _get_cookie(self, request: Request, name: str) -> str | None:
        """Extract cookie value from request headers using SimpleCookie."""
        cookie_header = request.get_header("cookie")
        if not cookie_header:
            return None

        try:
            # SimpleCookie handles complex parsing (quotes, etc.)
            cookie = SimpleCookie()
            cookie.load(cookie_header)
            if name in cookie:
                return cookie[name].value
        except Exception:
            # Malformed cookie header, treat as no cookie
            return None

        return None

    async def _get_token_from_request(self, request: Request) -> str | None:
        """Extract CSRF token from request header or form body."""
        # 1. Check header
        header_token = request.get_header(self.header_name)
        if header_token:
            return header_token

        # 2. Check form body for traditional HTML form submissions
        if request.is_form():
            try:
                form_data = await request.form()
                return form_data.get("_csrf") or form_data.get("csrf_token")
            except Exception:
                return None

        return None

    async def __call__(self, request: Request, response: Response):
        """Handle CSRF protection for the request."""
        # Always try to get the existing token from cookie
        signed_cookie_token = self._get_cookie(request, self.cookie_name)

        # If valid, use it. If invalid or missing, generate new one.
        if signed_cookie_token:
            # Verify signature to prevent cookie injection
            if not self._verify_signed_token(signed_cookie_token):
                # Invalid signature, treat as missing/invalid
                signed_cookie_token = None

        if not signed_cookie_token:
            signed_cookie_token = self._generate_token()
            # SECURITY: When using __Host- prefix, Domain must NOT be set and Path must be /
            # response.set_cookie defaults to Path=/ and Domain=None.
            response.set_cookie(
                self.cookie_name,
                signed_cookie_token,
                secure=self.secure,
                http_only=self.http_only,
                same_site=self.same_site,
            )

        # SECURITY: Mask the token for the request (BREACH protection)
        # request.csrf_token is what should be used in HTML forms
        request.csrf_token = self._mask_token(signed_cookie_token)

        # Skip CSRF check for exempt methods
        if request.method.upper() in self.exempt_methods:
            return

        # SECURITY: For HTTPS requests, verify the Origin/Referer (Defense in Depth).
        # This prevents CSRF even if the token is somehow leaked.
        # Check if request is secure (HTTPS) based on configuration.
        # SECURITY: Do not trust X-Forwarded-Proto blindly as it can be spoofed.
        # Users behind proxies should configure secure=True.
        is_https = self.secure

        if is_https:
            source = request.get_header("origin") or request.get_header("referer")
            host = request.get_header("host")

            if not host:
                response.status(400)
                response.json({"error": "Host header missing"})
                response._ended = True
                return

            expected = f"https://{host}"

            if not source or (source != expected and not source.startswith(f"{expected}/")):
                response.status(403)
                response.json({"error": "Origin/Referer verification failed"})
                response._ended = True
                return

        # For unsafe methods, verify the request token
        masked_request_token = await self._get_token_from_request(request)

        if not masked_request_token:
            response.status(403)
            response.json({"error": "CSRF token missing"})
            response._ended = True
            return

        # Unmask to get the signed token
        request_token = self._unmask_token(masked_request_token)

        # If unmasking failed (or wasn't masked), try using the token as-is
        # This supports SPAs that read the cookie (if http_only=False) and send it directly
        if request_token is None:
            request_token = masked_request_token

        if not request_token or not secrets.compare_digest(
            request_token, signed_cookie_token
        ):
            response.status(403)
            response.json({"error": "CSRF token invalid"})
            response._ended = True
            return

        # Token valid, continue


def csrf(
    secret_key: str | None = None,
    cookie_name: str = "csrf_token",
    header_name: str = "X-CSRF-Token",
    exempt_methods: list[str] | None = None,
    secure: bool = False,
    http_only: bool = True,
    same_site: str = "Lax",
):
    """
    Create a CSRF middleware function.

    This is a convenience function that creates and returns a CSRF middleware instance.
    """
    return CSRFMiddleware(
        secret_key=secret_key,
        cookie_name=cookie_name,
        header_name=header_name,
        exempt_methods=exempt_methods,
        secure=secure,
        http_only=http_only,
        same_site=same_site,
    )

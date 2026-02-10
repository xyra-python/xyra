import hashlib
import hmac
import secrets
from http.cookies import SimpleCookie

from ..request import Request
from ..response import Response


class CSRFMiddleware:
    """CSRF (Cross-Site Request Forgery) protection middleware for Xyra applications."""

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
        self.cookie_name = cookie_name
        self.header_name = header_name
        self.exempt_methods = exempt_methods or ["GET", "HEAD", "OPTIONS"]
        self.secure = secure
        self.http_only = http_only
        self.same_site = same_site

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
        """Mask the token using a random 32-byte mask to prevent BREACH attacks."""
        mask = secrets.token_bytes(32)
        token_bytes = token.encode("utf-8")
        cipher = bytes(b ^ mask[i % 32] for i, b in enumerate(token_bytes))
        return mask.hex() + cipher.hex()

    def _unmask_token(self, masked_token: str) -> str | None:
        """Unmask a token. Returns None if invalid format."""
        # Mask (32 bytes) is 64 hex chars
        mask_len = 64
        if not masked_token or len(masked_token) <= mask_len:
            return None

        try:
            mask_hex = masked_token[:mask_len]
            cipher_hex = masked_token[mask_len:]

            mask = bytes.fromhex(mask_hex)
            cipher = bytes.fromhex(cipher_hex)

            if len(mask) != 32:
                return None

            token_bytes = bytes(b ^ mask[i % 32] for i, b in enumerate(cipher))
            return token_bytes.decode("utf-8")
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

    def _get_token_from_request(self, request: Request) -> str | None:
        """Extract CSRF token from request header."""
        return request.get_header(self.header_name)

    def __call__(self, request: Request, response: Response):
        """Handle CSRF protection for the request."""
        # Always try to get the existing token from cookie
        signed_cookie_token = self._get_cookie(request, self.cookie_name)

        # If valid, use it. If invalid or missing, generate new one.
        if signed_cookie_token:
            # Verify signature to prevent cookie injection
            raw_token = self._verify_signed_token(signed_cookie_token)
            if not raw_token:
                # Invalid signature, treat as missing/invalid
                signed_cookie_token = None

        if not signed_cookie_token:
            signed_cookie_token = self._generate_token()
            response.set_cookie(
                self.cookie_name,
                signed_cookie_token,
                secure=self.secure,
                http_only=self.http_only,
                same_site=self.same_site,
            )

        # Attach the MASKED token to the request so it can be used in templates/views (safe for BREACH)
        request.csrf_token = self._mask_token(signed_cookie_token)

        # Skip CSRF check for exempt methods
        if request.method in self.exempt_methods:
            return

        # For unsafe methods, verify the header matches the cookie
        request_token = self._get_token_from_request(request)

        is_valid = False
        if request_token:
            # 1. Try unmasking first (standard secure flow)
            unmasked_token = self._unmask_token(request_token)
            if unmasked_token and secrets.compare_digest(
                unmasked_token, signed_cookie_token
            ):
                is_valid = True

            # 2. Fallback: Try raw token (backward compatibility / SPAs reading cookie directly)
            # Note: This is safe because request.csrf_token (in HTML) is masked, so BREACH cannot target the raw token.
            if not is_valid and secrets.compare_digest(
                request_token, signed_cookie_token
            ):
                is_valid = True

        if not is_valid:
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

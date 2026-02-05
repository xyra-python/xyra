import hashlib
import hmac
import secrets
from unittest.mock import Mock

from xyra.middleware import CSRFMiddleware, csrf


def _sign_token(token, secret_key):
    signature = hmac.new(
        secret_key.encode(), token.encode(), hashlib.sha256
    ).hexdigest()
    return f"{token}.{signature}"


# CSRF Tests
def test_csrf_middleware_init():
    middleware = CSRFMiddleware()
    assert middleware.secret_key
    assert middleware.cookie_name == "csrf_token"
    assert middleware.header_name == "X-CSRF-Token"
    assert middleware.exempt_methods == ["GET", "HEAD", "OPTIONS"]
    assert middleware.secure is False
    assert middleware.same_site == "Lax"


def test_csrf_middleware_custom():
    middleware = CSRFMiddleware(
        secret_key="This My Key",
        cookie_name="csrf_token",
        header_name="X-CSRF-Token",
        exempt_methods=["GET", "POST"],
        secure=False,
        same_site="Lax",
    )

    assert "This My Key" in middleware.secret_key
    assert "csrf_token" in middleware.cookie_name
    assert "X-CSRF-Token" in middleware.header_name
    assert middleware.exempt_methods == ["GET", "POST"]
    assert False is middleware.secure
    assert "Lax" in middleware.same_site


def test_csrf_middleware_option():
    middleware = CSRFMiddleware()
    request = Mock()
    request.method = "OPTIONS"
    request.get_header.return_value = None  # No cookie header
    response = Mock()
    response._ended = False
    middleware(request, response)
    # For OPTIONS, should not set status or end response
    response.status.assert_not_called()
    assert response._ended is False


def test_csrf_function():
    middleware = csrf()
    assert middleware.secret_key  # Should be generated
    assert middleware.cookie_name == "csrf_token"
    assert middleware.header_name == "X-CSRF-Token"
    assert middleware.exempt_methods == ["GET", "HEAD", "OPTIONS"]
    assert middleware.secure is False
    assert middleware.same_site == "Lax"


def test_csrf_custom_function():
    middleware = csrf(
        secret_key="This My Key",
        cookie_name="csrf_token",
        header_name="X-CSRF-Token",
        exempt_methods=["GET", "POST"],
        secure=False,
        same_site="Lax",
    )

    assert "This My Key" in middleware.secret_key
    assert "csrf_token" in middleware.cookie_name
    assert "X-CSRF-Token" in middleware.header_name
    assert middleware.exempt_methods == ["GET", "POST"]
    assert False is middleware.secure
    assert "Lax" in middleware.same_site


def test_csrf_middleware_post_without_token():
    middleware = CSRFMiddleware()
    request = Mock()
    request.method = "POST"
    request.get_header.return_value = None  # No cookie header
    response = Mock()
    response._ended = False
    middleware(request, response)
    response.status.assert_called_once_with(403)
    # Message might be "CSRF token missing" or "invalid" depending on impl
    # In my impl, if cookie is missing, it creates new one, then checks header vs new one.
    # Header is missing. So "CSRF token invalid".
    response.json.assert_called_once_with({"error": "CSRF token invalid"})
    assert response._ended is True


def test_csrf_middleware_post_with_invalid_token():
    middleware = CSRFMiddleware()
    request = Mock()
    request.method = "POST"
    # Even if cookie is valid signed token, header mismatch should fail
    token = secrets.token_urlsafe(32)
    signed_token = _sign_token(token, middleware.secret_key)

    request.get_header.side_effect = lambda name: {
        "cookie": f"csrf_token={signed_token}",
        "X-CSRF-Token": "invalid_token",
    }.get(name)
    response = Mock()
    response._ended = False
    middleware(request, response)
    response.status.assert_called_once_with(403)
    response.json.assert_called_once_with({"error": "CSRF token invalid"})
    assert response._ended is True


def test_csrf_middleware_post_with_valid_token():
    middleware = CSRFMiddleware()
    token = secrets.token_urlsafe(32)
    signed_token = _sign_token(token, middleware.secret_key)

    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        "cookie": f"csrf_token={signed_token}",
        "X-CSRF-Token": signed_token,
    }.get(name)
    response = Mock()
    response._ended = False
    middleware(request, response)
    # Should not call status or json for valid token
    response.status.assert_not_called()
    response.json.assert_not_called()
    assert response._ended is False


def test_csrf_middleware_get_sets_cookie():
    middleware = CSRFMiddleware()
    request = Mock()
    request.method = "GET"
    request.get_header.return_value = None  # No cookie header
    response = Mock()
    response._ended = False
    middleware(request, response)
    # Should set cookie
    response.set_cookie.assert_called_once()
    args, kwargs = response.set_cookie.call_args
    assert args[0] == "csrf_token"
    # assert len(args[1]) == 43 # Old check
    assert len(args[1]) > 43 # New signed token is longer
    assert "." in args[1]
    assert kwargs["secure"] is False
    assert kwargs["http_only"] is True
    assert kwargs["same_site"] == "Lax"


def test_csrf_middleware_cookie_parsing():
    middleware = CSRFMiddleware()
    token = secrets.token_urlsafe(32)
    signed_token = _sign_token(token, middleware.secret_key)

    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        # Note: SimpleCookie might handle spacing differently, standard is semicolon+space
        "cookie": f"csrf_token=\"{signed_token}\"; other=value",
        "X-CSRF-Token": signed_token,
    }.get(name)
    response = Mock()
    response._ended = False
    middleware(request, response)
    # Should not call status for valid token
    response.status.assert_not_called()
    assert response._ended is False


def test_csrf_middleware_head_method():
    """Test that HEAD method is exempt by default."""
    middleware = CSRFMiddleware()
    request = Mock()
    request.method = "HEAD"
    request.get_header.return_value = None
    response = Mock()
    response._ended = False
    middleware(request, response)
    # Should not set status for exempt method
    response.status.assert_not_called()
    assert response._ended is False


def test_csrf_middleware_custom_cookie_settings():
    """Test CSRF with custom cookie settings."""
    middleware = CSRFMiddleware(secure=True, http_only=False, same_site="Strict")
    request = Mock()
    request.method = "GET"
    request.get_header.return_value = None
    response = Mock()
    response._ended = False
    middleware(request, response)

    # Should set cookie with custom settings
    response.set_cookie.assert_called_once()
    args, kwargs = response.set_cookie.call_args
    assert kwargs["secure"] is True
    assert kwargs["http_only"] is False
    assert kwargs["same_site"] == "Strict"


def test_csrf_middleware_multiple_cookies():
    """Test parsing CSRF token from multiple cookies."""
    middleware = CSRFMiddleware()
    token = secrets.token_urlsafe(32)
    signed_token = _sign_token(token, middleware.secret_key)

    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        "cookie": f"session=abc123; csrf_token={signed_token}; user=john",
        "X-CSRF-Token": signed_token,
    }.get(name)
    response = Mock()
    response._ended = False
    middleware(request, response)
    # Should not call status for valid token
    response.status.assert_not_called()
    assert response._ended is False


def test_csrf_middleware_no_cookie_header():
    """Test when there's no cookie header at all."""
    middleware = CSRFMiddleware()
    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        "cookie": None,  # No cookie header
        "X-CSRF-Token": "some_token",
    }.get(name)
    response = Mock()
    response._ended = False
    middleware(request, response)
    # Should return 403 for missing token (it will try to generate one, but validation fails as header won't match)
    response.status.assert_called_once_with(403)
    response.json.assert_called_once_with({"error": "CSRF token invalid"})
    assert response._ended is True


def test_csrf_middleware_empty_cookie():
    """Test when cookie header exists but CSRF token is not present."""
    middleware = CSRFMiddleware()
    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        "cookie": "session=abc123; user=john",  # No CSRF token
        "X-CSRF-Token": "some_token",
    }.get(name)
    response = Mock()
    response._ended = False
    middleware(request, response)
    # Should return 403
    response.status.assert_called_once_with(403)
    response.json.assert_called_once_with({"error": "CSRF token invalid"})
    assert response._ended is True


def test_csrf_rejection_of_unsigned_token():
    """Test that unsigned or spoofed tokens are rejected."""
    middleware = CSRFMiddleware(secret_key="my_secret")

    # Attacker tries to use a random token
    attacker_token = "random_string"

    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        "cookie": f"csrf_token={attacker_token}",
        "X-CSRF-Token": attacker_token,
    }.get(name)

    response = Mock()
    response._ended = False

    middleware(request, response)

    # Validation should fail because the cookie token signature is invalid
    # So middleware treats cookie as missing, generates a NEW token.
    # Header contains 'attacker_token', NEW token != attacker_token.
    # So it fails.

    response.status.assert_called_once_with(403)
    response.json.assert_called_once_with({"error": "CSRF token invalid"})
    assert response._ended is True


def test_csrf_rejection_of_invalid_signature():
    """Test that a token with invalid signature is rejected."""
    middleware = CSRFMiddleware(secret_key="my_secret")

    token = secrets.token_urlsafe(32)
    # Sign with WRONG key
    fake_signature = hmac.new(
        b"wrong_key", token.encode(), hashlib.sha256
    ).hexdigest()
    spoofed_token = f"{token}.{fake_signature}"

    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        "cookie": f"csrf_token={spoofed_token}",
        "X-CSRF-Token": spoofed_token,
    }.get(name)

    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(403)
    assert response._ended is True


def test_csrf_token_on_request():
    """Test that the CSRF token is attached to the request object."""
    middleware = CSRFMiddleware()
    request = Mock()
    request.method = "GET"
    request.get_header.return_value = None

    response = Mock()
    response._ended = False

    middleware(request, response)

    assert hasattr(request, "csrf_token")
    assert request.csrf_token is not None
    assert "." in request.csrf_token

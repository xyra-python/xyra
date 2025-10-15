from unittest.mock import Mock
from xyra.middleware import CSRFMiddleware, csrf


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
    response.json.assert_called_once_with({"error": "CSRF token missing"})
    assert response._ended is True


def test_csrf_middleware_post_with_invalid_token():
    middleware = CSRFMiddleware()
    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        "cookie": "csrf_token=valid_token",
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
    token = "valid_token"
    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        "cookie": f"csrf_token={token}",
        "X-CSRF-Token": token,
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
    assert len(args[1]) == 43  # token_urlsafe(32) length
    assert kwargs["secure"] is False
    assert kwargs["http_only"] is True
    assert kwargs["same_site"] == "Lax"


def test_csrf_middleware_cookie_parsing():
    middleware = CSRFMiddleware()
    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        "cookie": "csrf_token=parsed_token; other=value",
        "X-CSRF-Token": "parsed_token",
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
    request = Mock()
    request.method = "POST"
    request.get_header.side_effect = lambda name: {
        "cookie": "session=abc123; csrf_token=test_token; user=john",
        "X-CSRF-Token": "test_token",
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
    # Should return 403 for missing token
    response.status.assert_called_once_with(403)
    response.json.assert_called_once_with({"error": "CSRF token missing"})
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
    # Should return 403 for missing token
    response.status.assert_called_once_with(403)
    response.json.assert_called_once_with({"error": "CSRF token missing"})
    assert response._ended is True

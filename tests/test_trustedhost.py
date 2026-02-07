from unittest.mock import Mock

from xyra.middleware import TrustedHostMiddleware, trusted_host_middleware


# Trusted Host Tests
def test_trusted_host_middleware_init():
    middleware = TrustedHostMiddleware(["example.com"])
    assert middleware.allowed_hosts == ["example.com"]


def test_trusted_host_function():
    middleware = trusted_host_middleware(["example.com"])
    assert isinstance(middleware, TrustedHostMiddleware)


def test_trusted_host_allowed():
    middleware = TrustedHostMiddleware(["example.com", "trusted.org"])
    request = Mock()
    request.headers = {"host": "example.com"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should allow and continue
    response.status.assert_not_called()
    response.json.assert_not_called()
    assert response._ended is False


def test_trusted_host_not_allowed():
    middleware = TrustedHostMiddleware(["example.com"])
    request = Mock()
    request.headers = {"host": "malicious.com"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(400)
    response.json.assert_called_once_with(
        {"error": "Bad Request", "message": "Untrusted host"}
    )
    assert response._ended is True


def test_trusted_host_with_port():
    middleware = TrustedHostMiddleware(["example.com"])
    request = Mock()
    request.headers = {"host": "example.com:8080"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should strip port and allow
    response.status.assert_not_called()
    response.json.assert_not_called()
    assert response._ended is False


def test_trusted_host_no_host_header():
    middleware = TrustedHostMiddleware(["example.com"])
    request = Mock()
    request.headers = {}  # No Host header
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Empty host should be rejected
    response.status.assert_called_once_with(400)
    response.json.assert_called_once_with(
        {"error": "Bad Request", "message": "Untrusted host"}
    )
    assert response._ended is True


def test_trusted_host_multiple_hosts():
    middleware = TrustedHostMiddleware(
        ["example.com", "trusted.org", "api.example.com"]
    )
    request = Mock()
    request.headers = {"host": "api.example.com"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should allow
    response.status.assert_not_called()
    response.json.assert_not_called()
    assert response._ended is False


def test_trusted_host_ipv6_literal():
    """Test that IPv6 literals are handled correctly."""
    # Allow local IPv6
    middleware = TrustedHostMiddleware(["[::1]"])
    request = Mock()
    # Host header with port
    request.headers = {"host": "[::1]:8080"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should allow and continue
    response.status.assert_not_called()
    response.json.assert_not_called()
    assert response._ended is False


def test_trusted_host_ipv6_wildcard():
    """Test that IPv6 literals work with wildcard."""
    middleware = TrustedHostMiddleware(["*"])
    request = Mock()
    request.headers = {"host": "[::1]:8080"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_not_called()
    assert response._ended is False

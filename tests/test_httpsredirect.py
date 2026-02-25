from unittest.mock import Mock, patch

from xyra.middleware import HTTPSRedirectMiddleware, https_redirect_middleware


# HTTPS Redirect Tests
def test_https_redirect_middleware_init():
    middleware = HTTPSRedirectMiddleware()
    assert middleware.redirect_status_code == 301


def test_https_redirect_function():
    middleware = https_redirect_middleware(redirect_status_code=302)
    assert isinstance(middleware, HTTPSRedirectMiddleware)
    assert middleware.redirect_status_code == 302


def test_https_redirect_http_request():
    middleware = HTTPSRedirectMiddleware()
    request = Mock()
    request.url = "/path"
    request.query = ""
    # Mock scheme as http (default)
    request.scheme = "http"
    request.headers = {"host": "example.com"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(301)
    response.header.assert_called_with("Location", "https://example.com/path")
    response.send.assert_called_once_with("")
    assert response._ended is True


def test_https_redirect_http_request_with_query():
    middleware = HTTPSRedirectMiddleware()
    request = Mock()
    request.url = "/search"
    request.query = "q=python"
    request.scheme = "http"
    request.headers = {"host": "example.com"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(301)
    response.header.assert_called_with(
        "Location", "https://example.com/search?q=python"
    )
    response.send.assert_called_once_with("")
    assert response._ended is True


def test_https_redirect_https_request():
    # Even if trust_proxy=True is passed (legacy), we rely on req.scheme
    # We mock req.scheme as "https" (simulating ProxyHeadersMiddleware having run)
    middleware = HTTPSRedirectMiddleware(trust_proxy=True)
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.scheme = "https"
    request.headers = {"host": "example.com", "x-forwarded-proto": "https"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should not redirect
    response.status.assert_not_called()
    response.header.assert_not_called()
    response.send.assert_not_called()
    assert response._ended is False


def test_https_redirect_bypass_attempt_untrusted():
    # If attacker sends header but req.scheme is http (not validated by ProxyHeaders),
    # it MUST redirect.
    middleware = HTTPSRedirectMiddleware(trust_proxy=False)
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.scheme = "http" # Default
    request.headers = {"host": "example.com", "x-forwarded-proto": "https"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should redirect despite header because scheme is http
    response.status.assert_called_once_with(301)
    response.header.assert_called_with("Location", "https://example.com/path")
    response.send.assert_called_once_with("")
    assert response._ended is True


def test_https_redirect_missing_host():
    middleware = HTTPSRedirectMiddleware()
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.scheme = "http"
    request.headers = {"x-forwarded-proto": "http"}  # Missing host
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should return 400 Bad Request
    response.status.assert_called_once_with(400)
    response.send.assert_called_once_with("Bad Request: Missing Host header")
    assert response._ended is True


def test_https_redirect_custom_status_code():
    middleware = HTTPSRedirectMiddleware(redirect_status_code=302)
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.scheme = "http"
    request.headers = {"host": "example.com"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(302)
    response.header.assert_called_with("Location", "https://example.com/path")
    assert response._ended is True


def test_https_redirect_no_headers_assumes_http():
    middleware = HTTPSRedirectMiddleware()
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.scheme = "http"
    request.headers = {"host": "example.com"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(301)
    response.header.assert_called_with("Location", "https://example.com/path")
    assert response._ended is True


def test_https_redirect_allowed_hosts_success():
    middleware = HTTPSRedirectMiddleware(allowed_hosts=["example.com"])
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.scheme = "http"
    request.headers = {"host": "example.com"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(301)
    response.header.assert_called_with("Location", "https://example.com/path")
    assert response._ended is True


def test_https_redirect_allowed_hosts_failure():
    middleware = HTTPSRedirectMiddleware(allowed_hosts=["example.com"])
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.scheme = "http"
    request.headers = {"host": "evil.com"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(400)
    response.send.assert_called_once_with("Bad Request: Untrusted Host")
    assert response._ended is True


def test_https_redirect_invalid_host_chars():
    middleware = HTTPSRedirectMiddleware()
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.scheme = "http"
    # Host header injection attempt
    request.headers = {"host": "example.com/evil"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(400)
    response.send.assert_called_once_with("Bad Request: Invalid Host header")
    assert response._ended is True


def test_https_redirect_wildcard_host():
    middleware = HTTPSRedirectMiddleware(allowed_hosts=["*.example.com"])
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.scheme = "http"
    request.headers = {"host": "sub.example.com"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(301)
    response.header.assert_called_with("Location", "https://sub.example.com/path")
    assert response._ended is True


def test_https_redirect_ipv6_host_with_port():
    middleware = HTTPSRedirectMiddleware(allowed_hosts=["[::1]"])
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.scheme = "http"
    # Headers keys are lowercase in Xyra
    request.headers = {"host": "[::1]:8080"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(301)
    response.header.assert_called_with("Location", "https://[::1]:8080/path")
    assert response._ended is True

def test_https_redirect_trust_proxy_deprecation_warning():
    # Patch xyra.logger.get_logger
    with patch("xyra.logger.get_logger") as mock_get_logger:
        logger_mock = Mock()
        mock_get_logger.return_value = logger_mock

        HTTPSRedirectMiddleware(trust_proxy=True)

        logger_mock.warning.assert_called_once()
        args = logger_mock.warning.call_args[0]
        assert "deprecated" in args[0]

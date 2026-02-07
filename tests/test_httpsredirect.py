from unittest.mock import Mock

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
    # Headers keys are lowercase in Xyra
    request.headers = {"host": "example.com", "x-forwarded-proto": "http"}
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
    request.headers = {"host": "example.com", "x-forwarded-proto": "http"}
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
    middleware = HTTPSRedirectMiddleware(trust_proxy=True)
    request = Mock()
    request.url = "/path"
    request.query = ""
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
    # trust_proxy=False (default) should ignore x-forwarded-proto and redirect
    middleware = HTTPSRedirectMiddleware(trust_proxy=False)
    request = Mock()
    request.url = "/path"
    request.query = ""
    request.headers = {"host": "example.com", "x-forwarded-proto": "https"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should redirect despite header because proxy is not trusted
    response.status.assert_called_once_with(301)
    response.header.assert_called_with("Location", "https://example.com/path")
    response.send.assert_called_once_with("")
    assert response._ended is True


def test_https_redirect_missing_host():
    middleware = HTTPSRedirectMiddleware()
    request = Mock()
    request.url = "/path"
    request.query = ""
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
    request.headers = {"host": "example.com", "x-forwarded-proto": "http"}
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
    request.headers = {"host": "example.com", "x-forwarded-proto": "http"}
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
    request.headers = {"host": "evil.com", "x-forwarded-proto": "http"}
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
    # Host header injection attempt
    request.headers = {"host": "example.com/evil", "x-forwarded-proto": "http"}
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
    request.headers = {"host": "sub.example.com", "x-forwarded-proto": "http"}
    request.get_header = request.headers.get
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(301)
    response.header.assert_called_with("Location", "https://sub.example.com/path")
    assert response._ended is True

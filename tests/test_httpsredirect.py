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
    request.url = "http://example.com/path"
    request.headers = {}
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(301)
    response.header.assert_called_with("Location", "https://example.com/path")
    response.send.assert_called_once_with("")
    assert response._ended is True


def test_https_redirect_https_request():
    middleware = HTTPSRedirectMiddleware()
    request = Mock()
    request.url = "https://example.com/path"
    request.headers = {}
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should not redirect
    response.status.assert_not_called()
    response.header.assert_not_called()
    response.send.assert_not_called()
    assert response._ended is False


def test_https_redirect_x_forwarded_proto():
    middleware = HTTPSRedirectMiddleware()
    request = Mock()
    request.url = "http://example.com/path"  # URL might be http due to proxy
    request.headers = {"X-Forwarded-Proto": "http"}
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(301)
    response.header.assert_called_with("Location", "https://example.com/path")
    assert response._ended is True


def test_https_redirect_x_forwarded_proto_https():
    middleware = HTTPSRedirectMiddleware()
    request = Mock()
    request.url = "https://example.com/path"  # HTTPS URL
    request.headers = {"X-Forwarded-Proto": "https"}
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should not redirect because URL is already HTTPS
    response.status.assert_not_called()
    response.header.assert_not_called()
    response.send.assert_not_called()
    assert response._ended is False


def test_https_redirect_custom_status_code():
    middleware = HTTPSRedirectMiddleware(redirect_status_code=302)
    request = Mock()
    request.url = "http://example.com/path"
    request.headers = {}
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(302)
    response.header.assert_called_with("Location", "https://example.com/path")
    assert response._ended is True

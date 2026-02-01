
from unittest.mock import Mock
from xyra.middleware import TrustedHostMiddleware

def test_ipv6_host_allowed():
    # IPv6 loopback with brackets
    middleware = TrustedHostMiddleware(["[::1]", "localhost"])

    # Test with port
    request = Mock()
    request.headers = {"host": "[::1]:8000"}
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_not_called()
    assert response._ended is False

def test_ipv6_host_exact_match():
    # IPv6 loopback with brackets
    middleware = TrustedHostMiddleware(["[::1]"])

    # Test without port
    request = Mock()
    request.headers = {"host": "[::1]"}
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_not_called()
    assert response._ended is False

def test_ipv6_host_denied():
    middleware = TrustedHostMiddleware(["[::1]"])

    # Different IPv6 address
    request = Mock()
    request.headers = {"host": "[2001:db8::1]:80"}
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(400)
    assert response._ended is True

def test_malformed_ipv6():
    middleware = TrustedHostMiddleware(["[::1]"])

    # Malformed (missing closing bracket in header but starts with [)
    request = Mock()
    request.headers = {"host": "[::1"}
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Should fail as it won't match [::1]
    response.status.assert_called_once_with(400)
    assert response._ended is True

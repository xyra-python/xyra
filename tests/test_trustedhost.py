from unittest.mock import MagicMock

import pytest

from xyra.middleware.trustedhost import TrustedHostMiddleware
from xyra.request import Request
from xyra.response import Response


@pytest.fixture
def mock_req_res():
    req = MagicMock(spec=Request)
    res = MagicMock(spec=Response)
    res._ended = False

    # Mock methods to be callable
    res.status = MagicMock(return_value=res)
    res.json = MagicMock(return_value=res)

    return req, res


def test_trusted_host_exact_match(mock_req_res):
    """Test exact domain match allows any port."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["example.com"])

    # Matching domain, any port allowed
    req.host = "example.com"
    req.port = 80
    middleware(req, res)
    assert not res._ended

    req.host = "example.com"
    req.port = 8080
    middleware(req, res)
    assert not res._ended

    # Mismatch domain
    req.host = "evil.com"
    req.port = 80
    middleware(req, res)
    assert res._ended


def test_trusted_host_port_strict(mock_req_res):
    """Test specifying a port enforces strict matching."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["example.com:8080"])

    # Correct port
    req.host = "example.com"
    req.port = 8080
    middleware(req, res)
    assert not res._ended

    # Incorrect port
    req.host = "example.com"
    req.port = 9090
    middleware(req, res)
    assert res._ended

    # No port (default)
    res._ended = False  # reset
    req.host = "example.com"
    req.port = 80
    middleware(req, res)
    assert res._ended


def test_trusted_host_wildcard(mock_req_res):
    """Test wildcard subdomain matching."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["*.example.com"])

    # Subdomain
    req.host = "sub.example.com"
    req.port = 80
    middleware(req, res)
    assert not res._ended

    # Root domain (usually included in *.example.com)
    req.host = "example.com"
    req.port = 80
    middleware(req, res)
    assert not res._ended

    # Nested subdomain
    req.host = "nested.sub.example.com"
    req.port = 80
    middleware(req, res)
    assert not res._ended

    # Wrong domain
    req.host = "evil.com"
    req.port = 80
    middleware(req, res)
    assert res._ended


def test_trusted_host_wildcard_strict_port(mock_req_res):
    """Test wildcard subdomain with strict port."""
    req, res = mock_req_res
    # Note: *.example.com:8080 is valid syntax in our parser
    middleware = TrustedHostMiddleware(["*.example.com:8080"])

    # Correct domain and port
    req.host = "sub.example.com"
    req.port = 8080
    middleware(req, res)
    assert not res._ended

    # Correct domain wrong port
    req.host = "sub.example.com"
    req.port = 9090
    middleware(req, res)
    assert res._ended

    # Root domain with correct port
    res._ended = False
    req.host = "example.com"
    req.port = 8080
    middleware(req, res)
    assert not res._ended


def test_trusted_host_ipv6(mock_req_res):
    """Test IPv6 literal matching."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["[::1]"])

    req.host = "[::1]"
    req.port = 80
    middleware(req, res)
    assert not res._ended

    # Any port allowed
    req.host = "[::1]"
    req.port = 8080
    middleware(req, res)
    assert not res._ended


def test_trusted_host_ipv6_with_port(mock_req_res):
    """Test IPv6 literal with strict port."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["[::1]:8080"])

    req.host = "[::1]"
    req.port = 8080
    middleware(req, res)
    assert not res._ended

    req.host = "[::1]"
    req.port = 9090
    middleware(req, res)
    assert res._ended

    res._ended = False
    req.host = "[::1]"
    req.port = 80
    middleware(req, res)
    assert res._ended


def test_trusted_host_malformed(mock_req_res):
    """Test malformed Host headers are rejected."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["example.com"])

    # Injection chars
    req.host = "example.com/evil"
    req.port = 80
    middleware(req, res)
    assert res._ended

    res._ended = False
    req.host = "example.com?query"
    req.port = 80
    middleware(req, res)
    assert res._ended


def test_trusted_host_multiple_allowed(mock_req_res):
    """Test multiple allowed hosts with different rules."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["example.com", "api.example.com:8080"])

    req.host = "example.com"
    req.port = 80
    middleware(req, res)
    assert not res._ended

    req.host = "api.example.com"
    req.port = 8080
    middleware(req, res)
    assert not res._ended

    req.host = "api.example.com"
    req.port = 80  # Missing port
    middleware(req, res)
    assert res._ended


def test_trusted_host_mixed_case(mock_req_res):
    """Test mixed-case host header is accepted."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["example.com"])

    req.host = "Example.com"
    req.port = 80
    middleware(req, res)
    assert not res._ended, "Should accept mixed-case host 'Example.com'"

    res._ended = False
    req.host = "EXAMPLE.COM"
    req.port = 80
    middleware(req, res)
    assert not res._ended, "Should accept upper-case host 'EXAMPLE.COM'"


def test_trusted_host_case_insensitive_config(mock_req_res):
    """Test that configuration is case-insensitive."""
    req, res = mock_req_res
    # Config with uppercase
    middleware = TrustedHostMiddleware(["Example.com"])

    # Request with lowercase (standard browser behavior)
    req.host = "example.com"
    req.port = 80
    middleware(req, res)
    assert not res._ended, "Should accept 'example.com' when config is 'Example.com'"

    # Request with uppercase
    res._ended = False
    req.host = "Example.com"
    req.port = 80
    middleware(req, res)
    assert not res._ended, "Should accept 'Example.com' when config is 'Example.com'"

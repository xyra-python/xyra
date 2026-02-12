import pytest
from unittest.mock import MagicMock
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
    req.get_header.return_value = "example.com"
    middleware(req, res)
    assert not res._ended

    req.get_header.return_value = "example.com:8080"
    middleware(req, res)
    assert not res._ended

    # Mismatch domain
    req.get_header.return_value = "evil.com"
    middleware(req, res)
    assert res._ended

def test_trusted_host_port_strict(mock_req_res):
    """Test specifying a port enforces strict matching."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["example.com:8080"])

    # Correct port
    req.get_header.return_value = "example.com:8080"
    middleware(req, res)
    assert not res._ended

    # Incorrect port
    req.get_header.return_value = "example.com:9090"
    middleware(req, res)
    assert res._ended

    # No port (default)
    res._ended = False # reset
    req.get_header.return_value = "example.com"
    middleware(req, res)
    assert res._ended

def test_trusted_host_wildcard(mock_req_res):
    """Test wildcard subdomain matching."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["*.example.com"])

    # Subdomain
    req.get_header.return_value = "sub.example.com"
    middleware(req, res)
    assert not res._ended

    # Root domain (usually included in *.example.com)
    req.get_header.return_value = "example.com"
    middleware(req, res)
    assert not res._ended

    # Nested subdomain
    req.get_header.return_value = "nested.sub.example.com"
    middleware(req, res)
    assert not res._ended

    # Wrong domain
    req.get_header.return_value = "evil.com"
    middleware(req, res)
    assert res._ended

def test_trusted_host_wildcard_strict_port(mock_req_res):
    """Test wildcard subdomain with strict port."""
    req, res = mock_req_res
    # Note: *.example.com:8080 is valid syntax in our parser
    middleware = TrustedHostMiddleware(["*.example.com:8080"])

    # Correct domain and port
    req.get_header.return_value = "sub.example.com:8080"
    middleware(req, res)
    assert not res._ended

    # Correct domain wrong port
    req.get_header.return_value = "sub.example.com:9090"
    middleware(req, res)
    assert res._ended

    # Root domain with correct port
    res._ended = False
    req.get_header.return_value = "example.com:8080"
    middleware(req, res)
    assert not res._ended

def test_trusted_host_ipv6(mock_req_res):
    """Test IPv6 literal matching."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["[::1]"])

    req.get_header.return_value = "[::1]"
    middleware(req, res)
    assert not res._ended

    # Any port allowed
    req.get_header.return_value = "[::1]:8080"
    middleware(req, res)
    assert not res._ended

def test_trusted_host_ipv6_with_port(mock_req_res):
    """Test IPv6 literal with strict port."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["[::1]:8080"])

    req.get_header.return_value = "[::1]:8080"
    middleware(req, res)
    assert not res._ended

    req.get_header.return_value = "[::1]:9090"
    middleware(req, res)
    assert res._ended

    res._ended = False
    req.get_header.return_value = "[::1]"
    middleware(req, res)
    assert res._ended

def test_trusted_host_malformed(mock_req_res):
    """Test malformed Host headers are rejected."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["example.com"])

    # Injection chars
    req.get_header.return_value = "example.com/evil"
    middleware(req, res)
    assert res._ended

    res._ended = False
    req.get_header.return_value = "example.com?query"
    middleware(req, res)
    assert res._ended

def test_trusted_host_multiple_allowed(mock_req_res):
    """Test multiple allowed hosts with different rules."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["example.com", "api.example.com:8080"])

    req.get_header.return_value = "example.com"
    middleware(req, res)
    assert not res._ended

    req.get_header.return_value = "api.example.com:8080"
    middleware(req, res)
    assert not res._ended

    req.get_header.return_value = "api.example.com" # Missing port
    middleware(req, res)
    assert res._ended

def test_trusted_host_mixed_case(mock_req_res):
    """Test mixed-case host header is accepted."""
    req, res = mock_req_res
    middleware = TrustedHostMiddleware(["example.com"])

    req.get_header.return_value = "Example.com"
    middleware(req, res)
    assert not res._ended, "Should accept mixed-case host 'Example.com'"

    res._ended = False
    req.get_header.return_value = "EXAMPLE.COM"
    middleware(req, res)
    assert not res._ended, "Should accept upper-case host 'EXAMPLE.COM'"

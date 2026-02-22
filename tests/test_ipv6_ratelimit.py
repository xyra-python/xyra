from unittest.mock import Mock
from xyra.middleware import RateLimiter, RateLimitMiddleware

def _setup_response_mock():
    """Helper to setup response mock with proper header method."""
    response = Mock()
    response.headers = {}
    response._ended = False

    def header_func(key, value):
        response.headers[key] = value

    response.header = header_func
    # Mock status method to return self for chaining
    response.status = Mock(return_value=response)
    # Mock json method
    response.json = Mock()
    return response

def test_ipv6_subnet_rate_limiting():
    """
    Verify that requests from different IPv6 addresses in the same /64 subnet
    are treated as the same client for rate limiting purposes.
    """
    # Allow 1 request per minute
    limiter = RateLimiter(requests=1, window=60)
    middleware = RateLimitMiddleware(limiter)

    # Request 1 from Client A (2001:db8::1)
    req1 = Mock()
    req1.remote_addr = "2001:db8::1"
    res1 = _setup_response_mock()

    middleware(req1, res1)

    # First request should be allowed
    assert res1._ended is False
    assert res1.headers.get("X-RateLimit-Remaining") == "0"

    # Request 2 from Client B (2001:db8::2) - Same /64 subnet
    req2 = Mock()
    req2.remote_addr = "2001:db8::2"
    res2 = _setup_response_mock()

    middleware(req2, res2)

    # Second request should be BLOCKED because it's from the same subnet
    # Currently (before fix), this assertion will FAIL because they are treated as separate clients.
    assert res2._ended is True
    res2.status.assert_called_with(429)

def test_ipv4_mapped_ipv6_rate_limiting():
    """
    Verify that IPv4-mapped IPv6 addresses are treated as individual IPv4 addresses
    and NOT aggregated into a single /64 subnet (which would cause global rate limiting).
    """
    # Allow 1 request per minute
    limiter = RateLimiter(requests=1, window=60)
    middleware = RateLimitMiddleware(limiter)

    # Request 1 from Client A (::ffff:192.0.2.1)
    req1 = Mock()
    req1.remote_addr = "::ffff:192.0.2.1"
    res1 = _setup_response_mock()

    middleware(req1, res1)

    # First request should be allowed
    assert res1._ended is False

    # Request 2 from Client B (::ffff:192.0.2.2) - Different IPv4, same /96 prefix
    req2 = Mock()
    req2.remote_addr = "::ffff:192.0.2.2"
    res2 = _setup_response_mock()

    middleware(req2, res2)

    # Second request should be ALLOWED because they are different IPv4 addresses
    assert res2._ended is False

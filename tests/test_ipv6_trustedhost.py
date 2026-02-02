from unittest.mock import Mock
import pytest
from xyra.middleware import TrustedHostMiddleware

def test_trusted_host_ipv6_basic():
    """Test IPv6 address support."""
    # Allow localhost IPv6
    middleware = TrustedHostMiddleware(["[::1]"])
    request = Mock()
    # Browser sends Host: [::1]:8080 or just [::1]
    request.headers = {"host": "[::1]:8080"}
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Current implementation splits at first colon:
    # "[::1]:8080".split(":")[0] -> "[", which != "[::1]"
    # So this should fail in current code

    # We want to assert that it passes (after fix), but for now we expect failure?
    # No, I should write the test as it "should be", see it fail, then fix.

    # Assert successful pass-through (no 400 status)
    if response.status.called:
        assert False, f"Should have allowed IPv6 host, but got status {response.status.call_args}"

    assert response._ended is False

def test_trusted_host_ipv6_no_port():
    middleware = TrustedHostMiddleware(["[::1]"])
    request = Mock()
    request.headers = {"host": "[::1]"}
    response = Mock()
    response._ended = False

    middleware(request, response)

    # Current implementation: "[::1]".split(":")[0] -> "["
    if response.status.called:
        assert False, "Should have allowed IPv6 host without port"

def test_trusted_host_ipv6_mismatch():
    middleware = TrustedHostMiddleware(["[::1]"])
    request = Mock()
    request.headers = {"host": "[2001:db8::1]:8080"}
    response = Mock()
    response._ended = False

    middleware(request, response)

    response.status.assert_called_once_with(400)
    assert response._ended is True

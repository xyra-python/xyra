import sys
from unittest.mock import Mock

# Mock libxyra
mock_libxyra = Mock()
sys.modules["xyra.libxyra"] = mock_libxyra

# Now import middleware
from xyra.middleware import HTTPSRedirectMiddleware

def test_https_redirect_bypass_regression():
    """
    Test that HTTPSRedirectMiddleware does not allow bypass via spoofed X-Forwarded-Proto
    when trust_proxy=True (legacy config) but req.scheme is not updated (ProxyHeadersMiddleware absent).
    """
    # Test vulnerable config (legacy usage)
    middleware = HTTPSRedirectMiddleware(trust_proxy=True)

    # Mock request
    request = Mock()
    request.url = "/login"
    request.query = ""
    # Attacker sends spoofed header
    request.headers = {"host": "example.com", "x-forwarded-proto": "https"}
    request.get_header = request.headers.get

    # IMPORTANT: Mock default scheme as "http".
    # In a real attack, ProxyHeadersMiddleware is NOT running or NOT trusting the proxy,
    # so req.scheme remains "http".
    request.scheme = "http"

    # Mock response
    response = Mock()
    response._ended = False
    response.status = Mock()
    response.header = Mock()
    response.send = Mock()

    # Execute
    middleware(request, response)

    # Verification:
    # If vulnerable, it would NOT redirect (bypass).
    # If safe, it MUST redirect.
    assert response.status.called, "VULNERABLE: Failed to redirect to HTTPS (Bypass via spoofed header)"
    response.status.assert_called_with(301)

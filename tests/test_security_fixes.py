
import pytest
from unittest.mock import Mock
from xyra.middleware.security_headers import SecurityHeadersMiddleware
from xyra.middleware.cors import CorsMiddleware
from xyra.request import Request

def test_permissions_policy_header():
    """Test that Permissions-Policy header is correctly set."""
    middleware = SecurityHeadersMiddleware(
        permissions_policy={"geolocation": ["self", "https://example.com"], "camera": "()"}
    )
    request = Mock()
    response = Mock()

    middleware(request, response)

    # Check if header is set
    calls = [call for call in response.header.call_args_list if call[0][0] == "Permissions-Policy"]
    assert len(calls) == 1
    value = calls[0][0][1]
    assert "geolocation=(self https://example.com)" in value
    assert "camera=()" in value

def test_cors_wildcard_with_credentials_does_not_reflect_origin():
    """Test that using * with credentials DOES NOT reflect the origin (secure behavior)."""
    middleware = CorsMiddleware(
        allowed_origins=["*"],
        allow_credentials=True
    )

    request = Mock()
    request.get_header.return_value = "https://evil.com"
    request.method = "GET"
    response = Mock()

    middleware(request, response)

    # Should NOT reflect origin because * + credentials is insecure
    # We iterate over calls to ensure Access-Control-Allow-Origin was NOT called with the origin
    for call_args in response.header.call_args_list:
        name, value = call_args[0]
        if name == "Access-Control-Allow-Origin":
            assert value != "https://evil.com", "Should not reflect origin when wildcard is used with credentials"

    # Credentials might still be set true globally, but without Origin, browser blocks it
    response.header.assert_any_call("Access-Control-Allow-Credentials", "true")

def test_json_parsing_raises_exception():
    """Test that Request.parse_json raises ValueError on invalid JSON."""
    # We need a real Request object or mock enough of it
    # But parse_json is a method on Request that uses orjson directly.
    # We can just check the method behavior if we can instantiate Request.

    # Mocking socketify request/response
    req_mock = Mock()
    res_mock = Mock()

    request = Request(req_mock, res_mock)

    with pytest.raises(ValueError, match="Invalid JSON"):
        request.parse_json("{invalid}")

from unittest.mock import Mock

import pytest

from xyra.middleware.cors import CorsMiddleware
from xyra.middleware.security_headers import SecurityHeadersMiddleware
from xyra.request import Request


def test_permissions_policy_header():
    """Test that Permissions-Policy header is correctly set."""
    middleware = SecurityHeadersMiddleware(
        permissions_policy={
            "geolocation": ["self", "https://example.com"],
            "camera": "()",
        }
    )
    request = Mock()
    response = Mock()

    middleware(request, response)

    # Check if header is set
    calls = [
        call
        for call in response.header.call_args_list
        if call[0][0] == "Permissions-Policy"
    ]
    assert len(calls) == 1
    value = calls[0][0][1]
    assert "geolocation=(self https://example.com)" in value
    assert "camera=()" in value


def test_cors_wildcard_with_credentials_does_not_reflect_origin():
    """Test that using * with credentials DOES NOT reflect the origin (secure behavior)."""
    middleware = CorsMiddleware(allowed_origins=["*"], allow_credentials=True)

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
            assert value != "https://evil.com", (
                "Should not reflect origin when wildcard is used with credentials"
            )

    # Credentials should NOT be set when using * + credentials as it is an invalid/insecure state
    for call_args in response.header.call_args_list:
        name, value = call_args[0]
        assert name != "Access-Control-Allow-Credentials"


@pytest.mark.asyncio
async def test_json_parsing_raises_exception():
    """Test that Request.json() raises HTTPException on invalid JSON."""
    # Mocking socketify request/response
    req_mock = Mock()
    res_mock = Mock()
    res_mock.get_data = pytest.importorskip("unittest.mock").AsyncMock(return_value=b"{invalid}")

    request = Request(req_mock, res_mock)
    request.get_header = Mock(return_value="application/json")

    from xyra.exceptions import HTTPException
    with pytest.raises(HTTPException, match="Invalid JSON"):
        await request.json()

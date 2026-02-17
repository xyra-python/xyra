
import pytest

from xyra.application import App
from xyra.middleware.csrf import CSRFMiddleware
from xyra.middleware.security_headers import SecurityHeadersMiddleware
from xyra.request import Request
from xyra.response import Response


class MockSocketifyRequest:
    def __init__(self, method="GET", url="/", headers=None):
        self._method = method
        self._url = url
        self._headers = headers or {}

    def get_method(self):
        return self._method

    def get_url(self):
        return self._url

    def get_headers(self):
        return self._headers

    def get_header(self, key):
        return self._headers.get(key.lower(), "")

    def for_each_header(self, callback):
        for k, v in self._headers.items():
            callback(k, v)

    def get_parameter(self, idx):
        return ""

class MockSocketifyResponse:
    def __init__(self):
        self.headers = {}
        self.status_code = 200
        self.ended = False
        self.body = None

    def write_header(self, key, value):
        self.headers[key] = value

    def write_status(self, status):
        self.status_code = int(status)

    def end(self, data):
        self.ended = True
        self.body = data

    def on_aborted(self, callback):
        pass

    def on_data(self, callback):
        pass

@pytest.mark.asyncio
async def test_security_headers_defaults():
    app = App()
    app.enable_security_headers()

    middleware = app.middlewares[0]
    assert isinstance(middleware, SecurityHeadersMiddleware)

    mock_req_native = MockSocketifyRequest()
    mock_res_native = MockSocketifyResponse()

    req = Request(mock_req_native, Response(mock_res_native))
    res = Response(mock_res_native)

    # Run middleware directly
    middleware(req, res)

    headers = res.headers
    assert headers["Permissions-Policy"] == "geolocation=(), camera=(), microphone=()"
    assert headers["X-Permitted-Cross-Domain-Policies"] == "none"
    assert headers["Cross-Origin-Opener-Policy"] == "same-origin"

@pytest.mark.asyncio
async def test_csrf_hardening_https_forwarded_reject():
    # Test that Origin is checked if X-Forwarded-Proto is https, even if secure=False
    csrf = CSRFMiddleware(secure=False)

    mock_req_native = MockSocketifyRequest(
        method="POST",
        headers={
            "x-forwarded-proto": "https",
            "host": "example.com",
            "origin": "http://attacker.com" # Mismatch scheme
        }
    )
    mock_res_native = MockSocketifyResponse()

    req = Request(mock_req_native, Response(mock_res_native))
    res = Response(mock_res_native)

    # Run middleware
    await csrf(req, res)

    # Should be rejected due to Origin mismatch
    assert res.status_code == 403
    assert res._ended is True
    assert b"Origin/Referer verification failed" in mock_res_native.body

@pytest.mark.asyncio
async def test_csrf_hardening_https_forwarded_allow_check_token():
    # Test that if Origin matches on HTTPS (forwarded), it proceeds to Token check
    csrf = CSRFMiddleware(secure=False)

    mock_req_native = MockSocketifyRequest(
        method="POST",
        headers={
            "x-forwarded-proto": "https",
            "host": "example.com",
            "origin": "https://example.com"
        }
    )
    mock_res_native = MockSocketifyResponse()

    req = Request(mock_req_native, Response(mock_res_native))
    res = Response(mock_res_native)

    await csrf(req, res)

    # Should fail because Token is missing, NOT because of Origin
    assert res.status_code == 403
    assert b"CSRF token missing" in mock_res_native.body

@pytest.mark.asyncio
async def test_csrf_hardening_host_missing():
    # Test that missing Host header on HTTPS results in 400
    csrf = CSRFMiddleware(secure=False)

    mock_req_native = MockSocketifyRequest(
        method="POST",
        headers={
            "x-forwarded-proto": "https",
            # Host missing
            "origin": "https://example.com"
        }
    )
    mock_res_native = MockSocketifyResponse()

    req = Request(mock_req_native, Response(mock_res_native))
    res = Response(mock_res_native)

    await csrf(req, res)

    assert res.status_code == 400
    assert b"Host header missing" in mock_res_native.body

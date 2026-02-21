from unittest.mock import MagicMock

import pytest
from multidict import CIMultiDict

from xyra.middleware.cors import CorsMiddleware
from xyra.middleware.csrf import CSRFMiddleware
from xyra.middleware.gzip import GzipMiddleware


class MockHeaders(CIMultiDict):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.added = []

    def add(self, key, value):
        self.added.append((key, value))
        super().add(key, value)


class MockRequest:
    def __init__(self, headers, method="GET"):
        self._headers = CIMultiDict(headers)
        self.method = method
        self.csrf_token = None

    @property
    def headers(self):
        return self._headers

    def get_header(self, name, default=None):
        return self._headers.get(name.lower(), default)

    def is_form(self):
        return False


class MockResponse:
    def __init__(self):
        self.headers = MockHeaders()
        self.status_code = 200
        self._ended = False

    def header(self, name, value):
        self.headers[name] = value

    def vary(self, name):
        self.headers.add("Vary", name)
        return self

    def status(self, code):
        self.status_code = code
        return self

    def json(self, data):
        pass

    def send(self, body):
        self._ended = True

    def set_cookie(self, *args, **kwargs):
        pass


def test_cors_vary_origin():
    middleware = CorsMiddleware(allowed_origins=["http://good.com"])

    # Case 1: Allowed origin
    req = MockRequest(headers={"Origin": "http://good.com"})
    res = MockResponse()
    middleware(req, res)

    assert res.headers.get("Access-Control-Allow-Origin") == "http://good.com"
    # Check if Vary: Origin was added
    assert ("Vary", "Origin") in res.headers.added

    # Case 2: Wildcard origin
    middleware = CorsMiddleware(allowed_origins=["*"])
    req = MockRequest(headers={"Origin": "http://any.com"})
    res = MockResponse()
    middleware(req, res)

    assert res.headers.get("Access-Control-Allow-Origin") == "*"
    assert ("Vary", "Origin") in res.headers.added


def test_cors_default_allowed_headers_includes_csrf():
    middleware = CorsMiddleware()
    assert "X-CSRF-Token" in middleware.allowed_headers


def test_cors_and_gzip_vary_coexistence():
    cors = CorsMiddleware(allowed_origins=["*"])
    gzip = GzipMiddleware(minimum_size=0)

    req = MockRequest(headers={"Origin": "http://any.com", "Accept-Encoding": "gzip"})
    res = MockResponse()

    # Apply CORS
    cors(req, res)

    # Mock original send for gzip
    # original_send = res.send
    gzip(req, res)

    # Trigger gzip send
    res.send("some data that is long enough to compress")

    # Verify both Vary values are present
    vary_values = [v for k, v in res.headers.added if k == "Vary"]
    assert res.headers.get("Content-Encoding") == "gzip"
    assert "Origin" in vary_values
    assert "Accept-Encoding" in vary_values


@pytest.mark.asyncio
async def test_csrf_origin_check_https():
    # Middleware with secure=True (HTTPS)
    middleware = CSRFMiddleware(secure=True, secret_key="test_secret")

    # Mock token in cookie
    token = middleware._generate_token()

    # Case 1: Valid Origin
    req = MockRequest(
        headers={
            "Origin": "https://example.com",
            "Host": "example.com",
            "Cookie": f"__Host-csrf_token={token}",
            "X-CSRF-Token": middleware._mask_token(token),
        },
        method="POST",
    )
    res = MockResponse()

    # We need to mock _get_cookie because MockRequest doesn't handle complex cookie parsing
    middleware._get_cookie = MagicMock(return_value=token)

    await middleware(req, res)
    assert not res._ended
    assert res.status_code == 200

    # Case 2: Mismatched Origin
    req = MockRequest(
        headers={
            "Origin": "https://evil.com",
            "Host": "example.com",
            "Cookie": f"__Host-csrf_token={token}",
            "X-CSRF-Token": middleware._mask_token(token),
        },
        method="POST",
    )
    res = MockResponse()
    middleware._get_cookie = MagicMock(return_value=token)

    await middleware(req, res)
    assert res._ended
    assert res.status_code == 403

    # Case 3: Valid Referer fallback
    req = MockRequest(
        headers={
            "Referer": "https://example.com/page",
            "Host": "example.com",
            "Cookie": f"__Host-csrf_token={token}",
            "X-CSRF-Token": middleware._mask_token(token),
        },
        method="POST",
    )
    res = MockResponse()
    middleware._get_cookie = MagicMock(return_value=token)

    await middleware(req, res)
    assert not res._ended
    assert res.status_code == 200

    # Case 4: Mismatched Referer
    req = MockRequest(
        headers={
            "Referer": "https://evil.com/page",
            "Host": "example.com",
            "Cookie": f"__Host-csrf_token={token}",
            "X-CSRF-Token": middleware._mask_token(token),
        },
        method="POST",
    )
    res = MockResponse()
    middleware._get_cookie = MagicMock(return_value=token)

    await middleware(req, res)
    assert res._ended
    assert res.status_code == 403

    # Case 5: Missing both on HTTPS
    req = MockRequest(
        headers={
            "Host": "example.com",
            "Cookie": f"__Host-csrf_token={token}",
            "X-CSRF-Token": middleware._mask_token(token),
        },
        method="POST",
    )
    res = MockResponse()
    middleware._get_cookie = MagicMock(return_value=token)

    await middleware(req, res)
    assert res._ended
    assert res.status_code == 403

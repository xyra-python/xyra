
import pytest

from xyra import Response


class MockSocketifyResponse:
    def __init__(self):
        self.headers = {}
        self.status = "200"
        self.body = None
        self.ended = False

    def write_header(self, key, value):
        self.headers[key] = value

    def write_status(self, status):
        self.status = status

    def end(self, data):
        self.body = data
        self.ended = True

def test_header_injection_crlf_in_key():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    with pytest.raises(ValueError, match="Header injection detected"):
        res.header("X-Header\r\nInjected", "value")

def test_header_injection_crlf_in_value():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    with pytest.raises(ValueError, match="Header injection detected"):
        res.header("X-Header", "value\r\nInjected: true")

def test_redirect_header_injection():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    with pytest.raises(ValueError, match="Header injection detected"):
        res.redirect("http://example.com\r\nSet-Cookie: evil=true")

def test_set_cookie_safe_formatting():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # Simple case
    res.set_cookie("session", "123")
    assert "session=123" in res.headers["Set-Cookie"]

    # Attribute injection attempt
    res.set_cookie("session", "123; Domain=evil.com")
    cookie = res.headers["Set-Cookie"]

    # Should be quoted and semi-colon escaped or similar
    # SimpleCookie output ensures it's safe.
    # It usually outputs: session="123\073 Domain=evil.com"
    assert '; Domain=evil.com' not in cookie
    assert 'session=' in cookie

def test_set_cookie_attributes():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    res.set_cookie(
        "user",
        "alice",
        max_age=3600,
        secure=True,
        http_only=True,
        same_site="Lax",
        path="/app"
    )

    cookie = res.headers["Set-Cookie"]
    assert "user=alice" in cookie
    # SimpleCookie keys are case-insensitive but output might vary in casing
    # usually Max-Age, Secure, HttpOnly, SameSite, Path

    # We check for presence case-insensitively if needed, but SimpleCookie follows standards.
    assert "Max-Age=3600" in cookie or "max-age=3600" in cookie
    assert "Secure" in cookie or "secure" in cookie
    assert "HttpOnly" in cookie or "httponly" in cookie
    assert "SameSite=Lax" in cookie or "samesite=Lax" in cookie
    assert "Path=/app" in cookie or "path=/app" in cookie


import sys
from unittest.mock import MagicMock

# Mock native extension
sys.modules["xyra.libxyra"] = MagicMock()

import pytest

from xyra.response import Response


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

    # Attribute injection attempt via value
    res.set_cookie("session", "123; Domain=evil.com")
    cookie = res.headers["Set-Cookie"]

    # Should be quoted and semi-colon escaped or similar
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

    # We check for presence case-insensitively
    assert "Max-Age=3600" in cookie or "max-age=3600" in cookie
    assert "Secure" in cookie or "secure" in cookie
    assert "HttpOnly" in cookie or "httponly" in cookie
    assert "SameSite=Lax" in cookie or "samesite=Lax" in cookie
    assert "Path=/app" in cookie or "path=/app" in cookie

def test_set_cookie_path_injection():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # Attempt to inject via path
    with pytest.raises(ValueError, match="Invalid character in cookie path"):
        res.set_cookie("test", "value", path="/; Secure; SameSite=Strict")

    with pytest.raises(ValueError, match="Invalid character in cookie path"):
        res.set_cookie("test", "value", path="/\r\n")

def test_set_cookie_domain_injection():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # Attempt to inject via domain
    with pytest.raises(ValueError, match="Invalid character in cookie domain"):
        res.set_cookie("test", "value", domain="example.com; Secure")

def test_clear_cookie_injection():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # clear_cookie delegates to set_cookie, so it should also fail
    with pytest.raises(ValueError, match="Invalid character in cookie path"):
        res.clear_cookie("test", path="/; Secure")

    with pytest.raises(ValueError, match="Invalid character in cookie domain"):
        res.clear_cookie("test", domain="example.com; Secure")

def test_clear_cookie_valid():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    res.clear_cookie("session_id", path="/")
    cookie = res.headers["Set-Cookie"]
    assert "session_id=" in cookie
    # Check for expires (case-insensitive)
    assert "Expires=Thu, 01 Jan 1970 00:00:00 GMT" in cookie or "expires=Thu, 01 Jan 1970 00:00:00 GMT" in cookie
    assert "Path=/" in cookie or "path=/" in cookie

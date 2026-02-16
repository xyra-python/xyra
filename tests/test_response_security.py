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

    with pytest.raises(ValueError, match="Invalid characters in header"):
        res.header("X-Header\r\nInjected", "value")


def test_header_injection_crlf_in_value():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    with pytest.raises(ValueError, match="Invalid characters in header"):
        res.header("X-Header", "value\r\nInjected: true")


def test_redirect_header_injection():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    with pytest.raises(ValueError, match="Invalid characters in header"):
        res.redirect("http://example.com\r\nSet-Cookie: evil=true")


def test_set_cookie_safe_formatting():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # Simple case
    res.set_cookie("session", "123")
    assert "session=123" in res.headers["Set-Cookie"]

    # Attribute injection attempt
    # Should now raise ValueError because semicolon is forbidden
    with pytest.raises(ValueError, match="Cookie value cannot contain ';'"):
        res.set_cookie("session", "123; Domain=evil.com")


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
        path="/app",
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


def test_set_cookie_semicolon_rejection():
    """Test that setting a cookie value containing a semicolon raises ValueError."""
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    with pytest.raises(ValueError, match="Cookie value cannot contain ';'"):
        res.set_cookie("prefs", "lang=en; Secure")


def test_set_cookie_attribute_injection_prevention():
    """Test prevention of attribute injection via path, domain, and same_site."""
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # Attempt to inject via path
    with pytest.raises(ValueError, match="Invalid characters in Path attribute"):
        res.set_cookie("session", "value", path="/; Secure; SameSite=Strict")

    # Attempt to inject via same_site
    with pytest.raises(ValueError, match="Invalid characters in SameSite attribute"):
        res.set_cookie("session", "value", same_site="Lax; Secure")

    # Attempt to inject via domain
    with pytest.raises(ValueError, match="Invalid characters in Domain attribute"):
        res.set_cookie("session", "value", domain="example.com; Secure")

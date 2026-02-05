
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

def test_set_cookie_path_injection():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # Should raise ValueError due to injection attempt
    with pytest.raises(ValueError, match="Invalid character in cookie path"):
        res.set_cookie("session", "123", path="/; Secure")

    with pytest.raises(ValueError, match="Invalid character in cookie path"):
        res.set_cookie("session", "123", path="/\r\n")

def test_set_cookie_domain_injection():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # Should raise ValueError due to injection attempt
    with pytest.raises(ValueError, match="Invalid character in cookie domain"):
        res.set_cookie("session", "123", domain="example.com; Secure")

def test_clear_cookie_path_injection():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # Should raise ValueError due to injection attempt
    with pytest.raises(ValueError, match="Invalid character in cookie path"):
        res.clear_cookie("session", path="/; Secure")

def test_clear_cookie_domain_injection():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # Should raise ValueError due to injection attempt
    with pytest.raises(ValueError, match="Invalid character in cookie domain"):
        res.clear_cookie("session", domain="example.com; Secure")

def test_valid_cookie_operations():
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    # These should pass
    res.set_cookie("session", "123", path="/app", domain="example.com")
    assert "session=123" in res.headers["Set-Cookie"]
    assert "Path=/app" in res.headers["Set-Cookie"] or "path=/app" in res.headers["Set-Cookie"]

    # Reset headers
    mock_res = MockSocketifyResponse()
    res = Response(mock_res)

    res.clear_cookie("session", path="/app", domain="example.com")
    assert "session=" in res.headers["Set-Cookie"]
    assert "Path=/app" in res.headers["Set-Cookie"] or "path=/app" in res.headers["Set-Cookie"]

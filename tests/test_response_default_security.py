from unittest.mock import Mock

from xyra.response import Response


def test_response_set_cookie_default_samesite_lax():
    """Test that set_cookie defaults to SameSite=Lax."""
    mock_socketify_response = Mock()
    mock_socketify_response.write_status = Mock()
    mock_socketify_response.write_header = Mock()
    mock_socketify_response.end = Mock()

    response = Response(mock_socketify_response)
    response.set_cookie("session", "abc123")

    cookie = response.headers["Set-Cookie"]
    assert "SameSite=Lax" in cookie or "samesite=Lax" in cookie


def test_response_set_cookie_explicit_samesite():
    """Test that set_cookie respects explicit SameSite."""
    mock_socketify_response = Mock()

    response = Response(mock_socketify_response)
    response.set_cookie("session", "abc123", same_site="Strict")

    cookie = response.headers["Set-Cookie"]
    assert "SameSite=Strict" in cookie or "samesite=Strict" in cookie


def test_response_set_cookie_none_samesite():
    """Test that set_cookie can set SameSite=None."""
    mock_socketify_response = Mock()

    response = Response(mock_socketify_response)
    response.set_cookie("session", "abc123", same_site="None", secure=True)

    cookie = response.headers["Set-Cookie"]
    assert "SameSite=None" in cookie or "samesite=None" in cookie

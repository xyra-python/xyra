from unittest.mock import Mock

import pytest

from xyra.response import Response


@pytest.fixture
def mock_socketify_response():
    res = Mock()
    res.write_status = Mock()
    res.write_header = Mock()
    res.end = Mock()
    return res


@pytest.fixture
def mock_templating():
    templating = Mock()
    templating.render.return_value = "<html>Hello</html>"
    return templating


def test_response_creation(mock_socketify_response):
    response = Response(mock_socketify_response)
    assert response._res == mock_socketify_response
    assert response.status_code == 200
    assert response.headers == {}
    assert not response._ended


def test_response_status(mock_socketify_response):
    response = Response(mock_socketify_response)
    result = response.status(404)
    assert response.status_code == 404
    assert result is response


def test_response_header(mock_socketify_response):
    response = Response(mock_socketify_response)
    result = response.header("Content-Type", "application/json")
    assert response.headers["Content-Type"] == "application/json"
    assert result is response


def test_response_send_string(mock_socketify_response):
    response = Response(mock_socketify_response)
    response.send("Hello World")
    mock_socketify_response.write_status.assert_called_once_with("200")
    # Headers are written via _write_headers
    mock_socketify_response.end.assert_called_once_with("Hello World")
    assert response._ended is True


def test_response_send_bytes(mock_socketify_response):
    response = Response(mock_socketify_response)
    response.send(b"Hello World")
    mock_socketify_response.end.assert_called_once_with(b"Hello World")


def test_response_send_after_end(mock_socketify_response):
    response = Response(mock_socketify_response)
    response._ended = True
    response.send("Should not send")
    mock_socketify_response.write_status.assert_not_called()


def test_response_json(mock_socketify_response):
    response = Response(mock_socketify_response)
    data = {"key": "value"}
    response.json(data)
    import sys

    if sys.implementation.name == "pypy":
        import ujson as json_lib
    else:
        import orjson as json_lib

    expected_json = json_lib.dumps(data)
    mock_socketify_response.end.assert_called_once_with(expected_json)
    assert response.headers["Content-Type"] == "application/json"


def test_response_html(mock_socketify_response):
    response = Response(mock_socketify_response)
    response.html("<h1>Hello</h1>")
    mock_socketify_response.end.assert_called_once_with("<h1>Hello</h1>")
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"


def test_response_text(mock_socketify_response):
    response = Response(mock_socketify_response)
    response.text("Hello World")
    mock_socketify_response.end.assert_called_once_with("Hello World")
    assert response.headers["Content-Type"] == "text/plain; charset=utf-8"


def test_response_redirect(mock_socketify_response):
    response = Response(mock_socketify_response)
    response.redirect("/new-path", 301)
    assert response.status_code == 301
    assert response.headers["Location"] == "/new-path"
    mock_socketify_response.end.assert_called_once_with("")


def test_response_custom_serialization():
    """Test custom response serialization like FastAPI."""
    res = Mock()
    res.write_status = Mock()
    res.write_header = Mock()
    res.end = Mock()
    response = Response(res)

    # Test Pydantic-like model serialization
    class User:
        def __init__(self, name, age):
            self.name = name
            self.age = age

        def dict(self):
            return {"name": self.name, "age": self.age}

    user = User("John", 25)
    response.json(user.dict())
    import sys

    if sys.implementation.name == "pypy":
        import ujson as json_lib
    else:
        import orjson as json_lib

    expected = json_lib.dumps(user.dict())
    res.end.assert_called_with(expected)


def test_response_error_handling():
    """Test response error handling."""
    res = Mock()
    res.end = Mock()
    response = Response(res)

    # Test sending error response
    response.status(500).text("Internal Server Error")
    assert response.status_code == 500
    res.end.assert_called_with("Internal Server Error")


def test_response_set_cookie(mock_socketify_response):
    response = Response(mock_socketify_response)
    result = response.set_cookie("session", "abc123", max_age=3600, secure=True)
    cookie = response.headers["Set-Cookie"]
    assert "session=abc123" in cookie
    # SimpleCookie attribute order varies. Check for attributes presence.
    assert "Max-Age=3600" in cookie or "max-age=3600" in cookie
    assert "Path=/" in cookie or "path=/" in cookie
    assert "Secure" in cookie or "secure" in cookie
    assert "HttpOnly" in cookie or "httponly" in cookie
    assert result is response


def test_response_clear_cookie(mock_socketify_response):
    response = Response(mock_socketify_response)
    result = response.clear_cookie("session", path="/app")
    expected_cookie = "session=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Path=/app"
    assert response.headers["Set-Cookie"] == expected_cookie
    assert result is response


def test_response_cors(mock_socketify_response):
    response = Response(mock_socketify_response)
    result = response.cors(origin="https://example.com", credentials=True)
    assert response.headers["Access-Control-Allow-Origin"] == "https://example.com"
    assert response.headers["Access-Control-Allow-Credentials"] == "true"
    assert result is response


def test_response_cache(mock_socketify_response):
    response = Response(mock_socketify_response)
    result = response.cache(7200)
    assert response.headers["Cache-Control"] == "public, max-age=7200"
    assert result is response


def test_response_no_cache(mock_socketify_response):
    response = Response(mock_socketify_response)
    result = response.no_cache()
    assert response.headers["Cache-Control"] == "no-cache, no-store, must-revalidate"
    assert response.headers["Pragma"] == "no-cache"
    assert response.headers["Expires"] == "0"
    assert result is response


def test_response_render(mock_socketify_response, mock_templating):
    response = Response(mock_socketify_response, mock_templating)
    response.render("index.html", name="World")
    mock_templating.render.assert_called_once_with("index.html", name="World")
    assert response.headers["Content-Type"] == "text/html; charset=utf-8"
    mock_socketify_response.end.assert_called_once_with("<html>Hello</html>")


def test_response_render_no_templating(mock_socketify_response):
    response = Response(mock_socketify_response)
    with pytest.raises(RuntimeError, match="Templating is not configured"):
        response.render("index.html")


def test_response_api_stability():
    """Test that Response class has expected public methods to prevent accidental renaming."""
    expected_methods = [
        "status",
        "header",
        "send",
        "json",
        "html",
        "text",
        "redirect",
        "set_cookie",
        "clear_cookie",
        "cors",
        "cache",
        "no_cache",
        "render",
    ]
    for method in expected_methods:
        assert hasattr(Response, method), f"Response is missing method: {method}"
        assert callable(getattr(Response, method)), f"Response.{method} is not callable"


def test_response_set_cookie_quoting(mock_socketify_response):
    response = Response(mock_socketify_response)

    # Space
    response.set_cookie("space", "hello world")
    cookie = response.headers["Set-Cookie"]
    assert 'space="hello world"' in cookie

    # Semicolon
    response.set_cookie("semicolon", "a;b")
    cookie = response.headers["Set-Cookie"]
    assert 'semicolon="a;b"' in cookie

    # Quotes
    response.set_cookie("quotes", 'a"b')
    cookie = response.headers["Set-Cookie"]
    # Expect escaping: "a\"b"
    assert 'quotes="a\\"b"' in cookie

    # Comma
    response.set_cookie("comma", "a,b")
    cookie = response.headers["Set-Cookie"]
    assert 'comma="a,b"' in cookie

    # Safe chars (no quoting)
    response.set_cookie("safe", "abc-123.456")
    cookie = response.headers["Set-Cookie"]
    assert "safe=abc-123.456" in cookie
    assert '"safe=abc-123.456"' not in cookie  # Should not be quoted

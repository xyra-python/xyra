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
    import orjson

    expected_json = orjson.dumps(data).decode("utf-8")
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


def test_response_set_cookie(mock_socketify_response):
    response = Response(mock_socketify_response)
    result = response.set_cookie("session", "abc123", max_age=3600, secure=True)
    expected_cookie = "session=abc123; Max-Age=3600; Path=/; Secure; HttpOnly"
    assert response.headers["Set-Cookie"] == expected_cookie
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

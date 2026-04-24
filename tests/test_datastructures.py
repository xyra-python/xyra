from xyra.datastructures import Headers, QueryParams, has_control_chars


def test_has_control_chars():
    # Empty string
    assert has_control_chars("") is False

    # Normal strings without control characters
    assert has_control_chars("hello") is False
    assert has_control_chars("application/json") is False
    assert has_control_chars("some value with spaces") is False

    # Control characters
    assert has_control_chars("hello\nworld") is True  # LF (ord 10)
    assert has_control_chars("hello\rworld") is True  # CR (ord 13)
    assert has_control_chars("hello\x00world") is True  # NUL (ord 0)
    assert has_control_chars("hello\x1fworld") is True  # US (ord 31)
    assert has_control_chars("hello\x7fworld") is True  # DEL (ord 127)
    assert has_control_chars("\x08") is True  # BS (ord 8)
    assert has_control_chars("\x0b") is True  # VT (ord 11)


def test_headers_creation():
    headers = Headers()
    assert len(headers) == 0


def test_headers_add():
    headers = Headers()
    headers.add("Content-Type", "application/json")
    assert headers["Content-Type"] == "application/json"


def test_headers_case_insensitive():
    headers = Headers()
    headers.add("content-type", "application/json")
    assert headers["Content-Type"] == "application/json"
    assert headers["CONTENT-TYPE"] == "application/json"


def test_headers_multiple_values():
    headers = Headers()
    headers.add("Set-Cookie", "session=abc")
    headers.add("Set-Cookie", "user=123")
    assert headers.getall("Set-Cookie") == ["session=abc", "user=123"]


def test_query_params_creation():
    params = QueryParams()
    assert len(params) == 0


def test_query_params_add():
    params = QueryParams()
    params.add("name", "value")
    assert params["name"] == "value"


def test_query_params_case_insensitive():
    params = QueryParams()
    params.add("Name", "value")
    assert params["name"] == "value"
    assert params["NAME"] == "value"


def test_query_params_multiple_values():
    params = QueryParams()
    params.add("tag", "python")
    params.add("tag", "web")
    assert params.getall("tag") == ["python", "web"]


def test_headers_update():
    # Update from dictionary
    headers = Headers({"Content-Type": "application/json"})
    headers.update({"X-Custom": "value"})
    assert headers["Content-Type"] == "application/json"
    assert headers["X-Custom"] == "value"

    # Update from another Headers instance
    other_headers = Headers({"X-Another": "another-value"})
    headers.update(other_headers)
    assert headers["X-Another"] == "another-value"

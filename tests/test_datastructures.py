from xyra.datastructures import Headers, QueryParams


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

from unittest.mock import AsyncMock, Mock

import pytest

from xyra.request import Request


@pytest.fixture
def mock_socketify_request():
    req = Mock()
    req.get_method.return_value = "GET"
    req.get_url.return_value = "http://example.com/path?key=value"
    req.for_each_header = Mock(
        side_effect=lambda func: func("Content-Type", "application/json")
    )
    req.get_parameter.return_value = "param_value"
    req.text = AsyncMock(return_value='{"key": "value"}')
    return req


@pytest.fixture
def mock_socketify_response():
    res = Mock()
    res.get_data = AsyncMock(return_value=b'{"key": "value"}')
    res.get_json = AsyncMock(return_value={"key": "value"})
    return res


def test_request_creation(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    assert request._req == mock_socketify_request
    assert request.params == {}


def test_request_method(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    assert request.method == "GET"


def test_request_url(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    assert request.url == "http://example.com/path?key=value"


def test_request_headers(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    headers = request.headers
    assert headers == {"content-type": "application/json"}


def test_request_query(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    assert request.query == "key=value"


def test_request_query_params(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    params = request.query_params
    assert params == {"key": ["value"]}


def test_request_get_parameter(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    assert request.get_parameter(0) == "param_value"


def test_request_get_header(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    assert request.get_header("content-type") == "application/json"
    assert request.get_header("nonexistent") is None


@pytest.mark.asyncio
async def test_request_text(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    text = await request.text()
    assert text == '{"key": "value"}'


@pytest.mark.asyncio
async def test_request_json(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    data = await request.json()
    assert data == {"key": "value"}


@pytest.mark.asyncio
async def test_request_json_empty():
    req = Mock()
    res = Mock()
    res.get_data = AsyncMock(return_value=b"")
    res.get_json = AsyncMock(return_value={})
    request = Request(req, res)
    data = await request.json()
    assert data == {}


@pytest.mark.asyncio
async def test_request_json_invalid():
    req = Mock()
    res = Mock()
    res.get_json = AsyncMock(side_effect=ValueError("Invalid JSON"))
    request = Request(req, res)
    with pytest.raises(ValueError, match="Invalid JSON"):
        await request.json()


@pytest.mark.asyncio
async def test_request_form():
    req = Mock()
    res = Mock()
    res.get_data = AsyncMock(return_value=b"name=john&age=30")
    request = Request(req, res)
    form = await request.form()
    assert form == {"name": "john", "age": "30"}


def test_request_content_type(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    assert request.content_type == "application/json"


def test_request_content_length():
    req = Mock()
    res = Mock()
    req.for_each_header = Mock(side_effect=lambda func: func("content-length", "123"))
    request = Request(req, res)
    assert request.content_length == 123


def test_request_is_json(mock_socketify_request, mock_socketify_response):
    request = Request(mock_socketify_request, mock_socketify_response)
    assert request.is_json() is True


def test_request_is_form():
    req = Mock()
    res = Mock()
    req.for_each_header = Mock(
        side_effect=lambda func: func(
            "content-type", "application/x-www-form-urlencoded"
        )
    )
    request = Request(req, res)
    assert request.is_form() is True

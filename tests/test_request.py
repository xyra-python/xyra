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
async def test_request_parsing_json():
    """Test asynchronous JSON parsing."""
    req = Mock()
    res = Mock()
    res.get_json = AsyncMock(return_value={"key": "value"})
    request = Request(req, res)
    data = await request.json()
    assert data == {"key": "value"}


@pytest.mark.asyncio
async def async_test_request_json_invalid():
    req = Mock()
    res = Mock()
    res.get_json = AsyncMock(side_effect=ValueError("Invalid JSON"))
    request = Request(req, res)
    with pytest.raises(ValueError, match="Invalid JSON"):
        await request.json()


def test_request_parse_json():
    """Test synchronous JSON string parsing."""
    req = Mock()
    res = Mock()
    request = Request(req, res)
    data = request.parse_json('{"key": "value"}')
    assert data == {"key": "value"}


@pytest.mark.asyncio
async def test_request_json_invalid():
    """Test invalid JSON."""
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


@pytest.mark.asyncio
async def test_request_body_validation():
    """Test request body validation like in FastAPI."""
    req = Mock()
    res = Mock()
    res.get_data = AsyncMock(return_value=b'{"name": "John", "age": 25}')
    res.get_json = AsyncMock(return_value={"name": "John", "age": 25})
    req.for_each_header = Mock(
        side_effect=lambda func: func("content-type", "application/json")
    )
    request = Request(req, res)

    # Simulate Pydantic-like validation
    data = await request.json()
    # Validate required fields
    if "name" not in data or not isinstance(data["name"], str):
        raise ValueError("Invalid name")
    if "age" not in data or not isinstance(data["age"], int):
        raise ValueError("Invalid age")
    assert data["name"] == "John"
    assert data["age"] == 25


@pytest.mark.asyncio
async def test_request_body_validation_error():
    """Test request body validation error."""
    req = Mock()
    res = Mock()
    res.get_json = AsyncMock(return_value={"name": 123, "age": "invalid"})
    req.for_each_header = Mock(
        side_effect=lambda func: func("content-type", "application/json")
    )
    request = Request(req, res)

    data = await request.json()
    try:
        if not isinstance(data.get("name"), str):
            raise ValueError("Name must be string")
        if not isinstance(data.get("age"), int):
            raise ValueError("Age must be int")
        assert False, "Should raise ValueError"
    except ValueError as e:
        assert "Name must be string" in str(e) or "Age must be int" in str(e)


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


def test_request_api_stability():
    """Test that Request class has expected public methods and properties to prevent accidental renaming."""
    expected_attributes = [
        "method",
        "url",
        "headers",
        "query",
        "query_params",
        "get_parameter",
        "get_header",
        "text",
        "json",
        "form",
        "content_type",
        "content_length",
        "is_json",
        "is_form",
    ]
    for attr in expected_attributes:
        assert hasattr(Request, attr), f"Request is missing attribute: {attr}"

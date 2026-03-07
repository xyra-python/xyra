from unittest.mock import Mock

import pytest

from xyra.request import Request


@pytest.mark.asyncio
async def test_strict_json_parsing_success():
    req_mock = Mock()
    res_mock = Mock()

    request = Request(req_mock, res_mock)
    request.get_header = lambda k, d="": "application/json; charset=utf-8" if k == "content-type" else d

    # Mock async get_data
    async def mock_get_data():
        return b'{"hello": "world"}'
    res_mock.get_data = mock_get_data

    result = await request.json()
    assert result == {"hello": "world"}

@pytest.mark.asyncio
async def test_strict_json_parsing_success_plus_json():
    req_mock = Mock()
    res_mock = Mock()

    request = Request(req_mock, res_mock)
    request.get_header = lambda k, d="": "application/vnd.api+json" if k == "content-type" else d

    # Mock async get_data
    async def mock_get_data():
        return b'{"hello": "world"}'
    res_mock.get_data = mock_get_data

    result = await request.json()
    assert result == {"hello": "world"}

@pytest.mark.asyncio
async def test_strict_json_parsing_failure():
    req_mock = Mock()
    res_mock = Mock()

    request = Request(req_mock, res_mock)
    request.get_header = lambda k, d="": "text/plain" if k == "content-type" else d

    # Mock async get_data
    async def mock_get_data():
        return b'{"hello": "world"}'
    res_mock.get_data = mock_get_data

    with pytest.raises(ValueError, match="Invalid Content-Type for JSON parsing"):
        await request.json()

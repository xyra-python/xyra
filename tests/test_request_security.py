from unittest.mock import AsyncMock, Mock, patch

import pytest

from xyra.request import Request


@pytest.mark.asyncio
async def test_request_form_fallback_security():
    """
    Test that Request.form() does not fall back to insecure parsing
    when parse_qsl fails.
    """
    req = Mock()
    res = Mock()
    # Payload that looks like form data
    payload = "key=value%20encoded&bad=very%bad"
    res.get_data = AsyncMock(return_value=payload.encode())

    request = Request(req, res)

    # Mock parse_qsl to fail, simulating an edge case or malformed input
    try:
        with patch("xyra.request.parse_qsl", side_effect=ValueError("Mocked error")):
            form_data = await request.form()
            assert form_data == {}, f"Expected empty dict on parse error, got {form_data}"
    except AttributeError:
        with patch("urllib.parse.parse_qsl", side_effect=ValueError("Mocked error")):
            form_data = await request.form()
            assert form_data == {}, f"Expected empty dict on parse error, got {form_data}"

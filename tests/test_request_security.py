
import pytest
from unittest.mock import Mock, AsyncMock, patch
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
    with patch("xyra.request.parse_qsl", side_effect=ValueError("Mocked error")):
        # On the current vulnerable code, this will trigger the fallback
        # which splits by '&' and '=', resulting in undecoded values.
        # We want to assert that this does NOT happen after the fix.
        # So we assert that it returns an empty dict (or handles it safely).

        # In TDD, this assertion should fail on the current code.
        form_data = await request.form()

        # If vulnerable, form_data will be {'key': 'value%20encoded', 'bad': 'very%bad'}
        # We want it to be {} or similar safe value.
        assert form_data == {}, f"Expected empty dict on parse error, got {form_data}"

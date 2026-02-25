import sys
from unittest.mock import AsyncMock, Mock
import pytest

# Mock libxyra
mock_libxyra = Mock()
sys.modules["xyra.libxyra"] = mock_libxyra

from xyra.request import Request

@pytest.mark.asyncio
async def test_request_caching_regression():
    """
    Test that Request object caches the body after reading it.
    This prevents data loss when multiple middleware (e.g. CSRF) read the body.
    """
    # Mock native response
    mock_res = Mock()
    # Simulate a stream that returns data once, then empty
    # This mimics behavior where reading consumes the stream
    mock_res.get_data = AsyncMock(side_effect=[b"body_content", b""])

    req = Request(Mock(), mock_res)

    # First read (should consume stream)
    body1 = await req.text()

    # Second read (should use cache)
    body2 = await req.text()

    assert body1 == "body_content", "First read failed"
    assert body2 == "body_content", "Second read failed (Body not cached!)"

    # Verify get_data was called ONLY ONCE
    mock_res.get_data.assert_called_once()

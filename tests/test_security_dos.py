import sys
from unittest.mock import MagicMock

# Mock xyra.libxyra so we can import xyra modules without building the native extension
mock_libxyra = MagicMock()
sys.modules["xyra.libxyra"] = mock_libxyra

import pytest
from unittest.mock import Mock
from xyra.response import Response
import asyncio


@pytest.mark.asyncio
async def test_get_data_body_size_limit():
    """
    Test that get_data enforces the body size limit (MAX_BODY_SIZE).
    """
    # Mock the native response
    mock_res = Mock()

    # We need to capture the callback passed to on_data
    on_data_callback = None

    def capture_on_data(cb):
        nonlocal on_data_callback
        on_data_callback = cb

    mock_res.on_data.side_effect = capture_on_data

    response = Response(mock_res)

    # Start get_data
    future_task = asyncio.create_task(response.get_data())

    # Allow the event loop to run slightly to register callbacks
    await asyncio.sleep(0)

    # Verify on_data was called and we captured the callback
    assert on_data_callback is not None

    # Simulate a stream of data
    # MAX_BODY_SIZE is 10MB. We send 11 chunks of 1MB.
    chunk_size = 1024 * 1024  # 1MB
    chunks_count = 11  # 11MB total

    # Feed data
    for _ in range(chunks_count):
        # Pass is_last=False
        on_data_callback(b"a" * chunk_size, False)
        # Give the loop a chance to process call_soon_threadsafe callbacks
        await asyncio.sleep(0)

    # Finish (though it should have failed already)
    on_data_callback(b"", True)
    await asyncio.sleep(0)

    # The result should raise ValueError
    with pytest.raises(ValueError, match="Request body too large"):
        await future_task

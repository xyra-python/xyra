import asyncio
from unittest.mock import Mock, call

import pytest

from xyra.response import Response, MAX_BODY_SIZE


@pytest.mark.asyncio
async def test_get_data_dos_vulnerability():
    """
    Test that Response.get_data buffers all chunks into the event loop even if MAX_BODY_SIZE is exceeded.
    This demonstrates the vulnerability: loop.call_soon_threadsafe is called for EVERY chunk.
    """
    mock_res = Mock()
    mock_res.on_data = Mock()
    mock_res.on_aborted = Mock()
    mock_res.close = Mock()

    response = Response(mock_res)

    # Start get_data by scheduling it as a task
    task = asyncio.create_task(response.get_data())

    # Allow the task to start (run until first await)
    await asyncio.sleep(0)

    # Capture the callback passed to on_data
    assert mock_res.on_data.called
    on_data_callback = mock_res.on_data.call_args[0][0]

    # Mock the loop to capture call_soon_threadsafe calls
    loop = asyncio.get_running_loop()
    original_call_soon = loop.call_soon_threadsafe
    loop.call_soon_threadsafe = Mock()

    try:
        # Simulate a flood of data: 20 chunks of 1MB each (Total 20MB > 10MB limit)
        chunk_size = 1024 * 1024  # 1MB
        chunk = b"A" * chunk_size
        num_chunks = 20

        # Simulate synchronous calls from uWebSockets thread
        for i in range(num_chunks):
            on_data_callback(chunk, False)

        # Verify fix: call_soon_threadsafe should ONLY be called for chunks within limit + 1 abort.
        # 10 chunks fit in 10MB. The 11th chunk triggers abort.
        # Subsequent 9 chunks should be ignored synchronously.
        # Total calls should be around 11, definitely less than 20.
        assert loop.call_soon_threadsafe.call_count <= 12
        assert loop.call_soon_threadsafe.call_count < num_chunks

        # Verify close was called
        assert mock_res.close.called

    finally:
        # Restore loop
        loop.call_soon_threadsafe = original_call_soon
        # Clean up task
        if not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

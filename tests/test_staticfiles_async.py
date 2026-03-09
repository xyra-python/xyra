import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from xyra import App, Request, Response


@pytest.mark.asyncio
async def test_static_files_non_blocking():
    """
    Verify that static files handler uses asyncio.to_thread for I/O operations.
    """
    app = App()
    static_dir = "/tmp/static_test"
    app.static_files("/static", static_dir)

    # Find the handler
    handler = None
    for route in app.router.routes:
        if route["path"] == "/static/*":
            handler = route["handler"]
            break

    assert handler is not None, "Static file handler not found in router"

    # Mock Request
    req = MagicMock(spec=Request)
    req.get_parameter.return_value = "test.txt"

    # Mock Response
    res = MagicMock(spec=Response)

    # Mock asyncio.to_thread
    with patch("asyncio.to_thread", new_callable=AsyncMock) as mock_to_thread:
        # Setup side_effect to simulate successful file operations
        def side_effect(func, *args, **kwargs):
            # Inspect the function being offloaded
            if func == os.path.exists:
                return True
            if func == os.path.isfile:
                return True
            if func == os.path.getsize:
                return 1024  # 1KB

            # For lambdas (path resolution)
            if callable(func) and func.__name__ == "<lambda>":
                # Execute the lambda to get the path
                return func()

            # For file reading (local function 'read_file' or 'read_file_safely')
            if func.__name__ in ("read_file", "read_file_safely"):
                return b"file content", 200

            return None

        mock_to_thread.side_effect = side_effect

        await handler(req, res)

        # Verify that to_thread was called for critical operations
        calls = mock_to_thread.call_args_list

        # With TOCTOU fix we don't do exists/isfile/getsize in to_thread individually

        # Check if read_file_safely was offloaded
        read_call = any(call.args[0].__name__ == "read_file_safely" for call in calls if hasattr(call.args[0], "__name__"))
        assert read_call, "read_file_safely should be offloaded to thread"

        # The previous checks are commented out
        # getsize_call = any(call.args[0] == os.path.getsize for call in calls)
        # assert getsize_call, "os.path.getsize should be offloaded to thread"

        # Check if file reading was offloaded
        # The function name is 'read_file'
        # read_call = any(call.args[0].__name__ == "read_file" for call in calls)
        # assert read_call, "File reading should be offloaded to thread"

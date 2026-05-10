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


@pytest.mark.asyncio
async def test_static_files_read_errors():
    """
    Verify that static files handler properly catches and handles
    OSError and Exception when reading files.
    """
    app = App()
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file_path = os.path.join(temp_dir, "test.txt")
        with open(test_file_path, "wb") as f:
            f.write(b"hello")

        app.static_files("/static", temp_dir)

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

        # Test OSError (e.g. Permission denied) -> 404
        res = MagicMock(spec=Response)
        with patch('os.fstat', side_effect=OSError("Permission denied")):
            await handler(req, res)
            res.status.assert_called_with(404)
            res.status.return_value.text.assert_called_with("Not Found")

        # Test generic Exception -> 500
        res = MagicMock(spec=Response)
        with patch('os.fstat', side_effect=Exception("Generic error")):
            await handler(req, res)
            res.status.assert_called_with(500)
            res.status.return_value.text.assert_called_with("Internal Server Error")


@pytest.mark.asyncio
async def test_static_files_oserror_permission():
    """
    Verify that an actual OSError (PermissionError) when opening a file
    results in a 404 response instead of crashing.
    """
    app = App()
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        test_file_path = os.path.join(temp_dir, "test.txt")
        with open(test_file_path, "wb") as f:
            f.write(b"hello")

        # Remove all permissions to trigger PermissionError (which is an OSError)
        os.chmod(test_file_path, 0o000)

        app.static_files("/static", temp_dir)

        handler = None
        for route in app.router.routes:
            if route["path"] == "/static/*":
                handler = route["handler"]
                break

        assert handler is not None

        req = MagicMock(spec=Request)
        req.get_parameter.return_value = "test.txt"
        res = MagicMock(spec=Response)

        try:
            await handler(req, res)

            res.status.assert_called_with(404)
            res.status.return_value.text.assert_called_with("Not Found")
        finally:
            # Restore permissions so the temp directory can be cleaned up
            os.chmod(test_file_path, 0o777)


@pytest.mark.asyncio
async def test_static_files_oserror_isdir():
    """
    Verify that trying to read a directory as a file triggers an OSError
    (IsADirectoryError) and results in a 404 response.
    """
    app = App()
    import tempfile

    with tempfile.TemporaryDirectory() as temp_dir:
        test_dir_path = os.path.join(temp_dir, "test_dir")
        os.makedirs(test_dir_path, exist_ok=True)

        app.static_files("/static", temp_dir)

        handler = None
        for route in app.router.routes:
            if route["path"] == "/static/*":
                handler = route["handler"]
                break

        assert handler is not None

        req = MagicMock(spec=Request)
        req.get_parameter.return_value = "test_dir"
        res = MagicMock(spec=Response)

        await handler(req, res)

        res.status.assert_called_with(404)
        res.status.return_value.text.assert_called_with("Not Found")

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

    # Mock aiofiles
    import stat
    mock_file = AsyncMock()
    mock_file.read.return_value = b"file content"
    mock_file.fileno = MagicMock(return_value=1)

    mock_fstat = MagicMock()
    mock_st = MagicMock()
    mock_st.st_mode = stat.S_IFREG
    mock_st.st_size = 1024
    mock_fstat.return_value = mock_st

    with patch("aiofiles.open", new_callable=MagicMock) as mock_open:
        mock_open.return_value.__aenter__.return_value = mock_file
        with patch("os.fstat", mock_fstat):
            await handler(req, res)

            mock_open.assert_called_once()
            mock_file.read.assert_awaited_once()

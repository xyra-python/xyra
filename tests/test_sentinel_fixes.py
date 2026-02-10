import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest

from xyra.application import App
from xyra.middleware.rate_limiter import RateLimiter
from xyra.request import Request
from xyra.response import MAX_BODY_SIZE, Response


@pytest.mark.asyncio
async def test_request_uses_response_wrapper():
    """Verify that Request uses the Response wrapper which enforces MAX_BODY_SIZE."""
    native_res = Mock()

    # Mock native_res.on_data to simulate a large body
    def side_effect(on_data_cb):
        # Send a chunk that exceeds MAX_BODY_SIZE
        on_data_cb(b"a" * (MAX_BODY_SIZE + 1), True)

    native_res.on_data.side_effect = side_effect

    response_wrapper = Response(native_res)
    native_req = Mock()
    request = Request(native_req, response_wrapper)

    with pytest.raises(ValueError, match="Request body too large"):
        await request.json()


@pytest.mark.asyncio
async def test_static_files_wildcard_and_size_limit():
    """Verify that static_files supports subdirectories and enforces size limit."""
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create a nested file
        nested_dir = temp_path / "subdir"
        nested_dir.mkdir()
        nested_file = nested_dir / "test.txt"
        nested_file.write_text("nested content")

        # Create a large file
        large_file = temp_path / "large.bin"
        with open(large_file, "wb") as f:
            f.write(b"a" * (MAX_BODY_SIZE + 1))

        app = App()
        app.static_files("/static", temp_dir)

        # The handler is the last registered route's handler.
        route = app.router.routes[-1]
        handler = route["handler"]

        # Test nested file access
        mock_native_req = Mock()
        mock_native_req.get_parameter.return_value = "subdir/test.txt"

        mock_native_res = Mock()
        mock_native_res.write_status = Mock()
        mock_native_res.write_header = Mock()
        mock_native_res.end = Mock()

        real_res = Response(mock_native_res)
        real_req = Request(mock_native_req, real_res)

        await handler(real_req, real_res)

        mock_native_res.end.assert_called_once_with(b"nested content")
        # Check if Content-Type was written
        content_type_call = [
            call
            for call in mock_native_res.write_header.call_args_list
            if call[0][0] == "Content-Type"
        ]
        assert len(content_type_call) > 0
        assert "text/plain" in content_type_call[0][0][1]

        # Test large file access with a NEW response object
        mock_native_req.get_parameter.return_value = "large.bin"
        mock_native_res_2 = Mock()
        mock_native_res_2.write_status = Mock()
        mock_native_res_2.write_header = Mock()
        mock_native_res_2.end = Mock()

        real_res_2 = Response(mock_native_res_2)
        real_req_2 = Request(mock_native_req, real_res_2)

        await handler(real_req_2, real_res_2)
        mock_native_res_2.write_status.assert_called_with("413")
        mock_native_res_2.end.assert_called_with("Payload Too Large")


def test_ratelimiter_monotonic():
    """Verify that RateLimiter works."""
    limiter = RateLimiter(requests=1, window=10)

    assert limiter.is_allowed("test") is True
    assert limiter.is_allowed("test") is False

    # Check reset time is positive
    assert limiter.get_reset_time("test") > 0
    assert limiter.get_reset_time("test") <= 10

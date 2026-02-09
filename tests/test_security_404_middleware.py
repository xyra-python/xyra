import sys
import asyncio
from unittest.mock import MagicMock

# Mock libxyra
mock_libxyra = MagicMock()
sys.modules["xyra.libxyra"] = mock_libxyra

import pytest
from xyra.application import App

@pytest.mark.asyncio
async def test_404_middleware_applied():
    app = App()

    # Define a middleware that sets a header
    async def test_middleware(req, res):
        res.header("X-Test", "1")

    app.use(test_middleware)

    # Mock app._app.any to spy on registration
    app._app.any = MagicMock()

    # Create an event loop for the app registration logic (if needed)
    # App creates a thread with a new loop if _loop is not set.
    # We can set _loop to current loop to avoid threading issues.
    app._loop = asyncio.get_running_loop()

    # Register routes
    app._register_routes()

    # Capture the handler passed to app.any("/*", ...)
    calls = app._app.any.call_args_list
    not_found_handler_wrapper = None
    for call in calls:
        args, _ = call
        if args[0] == "/*":
            not_found_handler_wrapper = args[1]
            break

    assert not_found_handler_wrapper is not None, "404 handler not registered"

    # Mock asyncio.run_coroutine_threadsafe to capture the coroutine
    # logic in wrap_async: asyncio.run_coroutine_threadsafe(handler(res, req), self._loop)

    captured_coro = None
    original_run = asyncio.run_coroutine_threadsafe

    def mock_run(coro, loop):
        nonlocal captured_coro
        captured_coro = coro
        # Return a dummy future
        f = asyncio.Future()
        f.set_result(None)
        return f

    asyncio.run_coroutine_threadsafe = mock_run

    # Mock native objects
    mock_req_native = MagicMock()
    # Mock Request methods required by Request.__init__ or properties if accessed
    mock_req_native.get_url.return_value = "/404"
    mock_req_native.get_method.return_value = "GET"
    mock_req_native.get_headers.return_value = {}
    mock_req_native.get_query.return_value = ""

    mock_res_native = MagicMock()

    # Run the sync handler wrapper
    not_found_handler_wrapper(mock_res_native, mock_req_native)

    # Restore
    asyncio.run_coroutine_threadsafe = original_run

    assert captured_coro is not None

    # Run the captured coroutine
    await captured_coro

    # Verify X-Test header was set on native response
    # It should be called as write_header("X-Test", "1")
    calls = mock_res_native.write_header.call_args_list
    header_set = False
    for call in calls:
        args, _ = call
        if args[0] == "X-Test" and args[1] == "1":
            header_set = True
            break

    assert header_set, "Middleware header X-Test was not set on 404 response"

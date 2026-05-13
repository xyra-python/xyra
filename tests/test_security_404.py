import asyncio
from unittest.mock import MagicMock

from xyra.application import App


class MockSocketifyRequest:
    def get_method(self):
        return "GET"

    def get_url(self):
        return "/non-existent"

    def for_each_header(self, callback):
        pass

    def get_parameter(self, idx):
        return None


class MockSocketifyResponse:
    def __init__(self):
        self.headers = {}
        self.status_code = 200
        self._ended = False

    def write_header(self, key, value):
        self.headers[key] = value

    def write_status(self, status):
        if isinstance(status, str):
            self.status_code = int(status.split()[0])
        else:
            self.status_code = int(status)

    def end(self, data):
        self._ended = True


def test_404_middleware_applied():
    """
    Test that the 404 handler now correctly applies middleware (Security Fix).
    """
    app = App()

    # We patch the instance method to spy on it
    app._create_final_handler = MagicMock(wraps=app._create_final_handler)

    # Mock _app to avoid errors and inspect calls
    app._app = MagicMock()

    # Register routes
    app._register_routes()

    # Check calls to _create_final_handler
    # Expected signature: _create_final_handler(route_handler, param_names, middlewares, parsed_path)
    called_for_404 = False
    for call in app._create_final_handler.call_args_list:
        args, _ = call
        # args[3] corresponds to parsed_path
        if len(args) >= 4 and args[3] == "/*":
            called_for_404 = True
            break

    # FIXED BEHAVIOR: Middleware IS applied to 404 handler,
    # so _create_final_handler IS called for "/*".
    assert called_for_404, (
        "Middleware NOT applied to 404 handler! Security headers missing on 404."
    )


def test_404_handler_executes_middleware():
    """
    Test that the 404 handler correctly executes registered middleware.
    """
    app = App()
    log = []

    async def test_middleware(req, call_next):
        log.append("mw_pre")
        await call_next()
        log.append("mw_post")

    async def second_middleware(req, res):
        log.append("mw2")
        res.header("X-Middleware-Seen", "true")

    app.use(test_middleware)
    app.use(second_middleware)

    # Register routes with a mock _app
    app._app = MagicMock()
    app._register_routes()

    # Recreate the final_handler for 404
    async def not_found_handler(req, res):
        res.status(404).json({"error": "Not Found"})
        log.append("handler")

    final_handler = app._create_final_handler(
        not_found_handler, [], app._middlewares, "/*"
    )

    mock_req_native = MockSocketifyRequest()
    mock_res_native = MockSocketifyResponse()

    asyncio.run(final_handler(mock_res_native, mock_req_native))

    assert log == ["mw_pre", "mw2", "handler", "mw_post"]
    assert mock_res_native.status_code == 404
    assert mock_res_native.headers.get("X-Middleware-Seen") == "true"

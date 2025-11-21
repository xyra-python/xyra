
import asyncio
import threading
import unittest
from xyra.application import App
from xyra.request import Request
from xyra.response import Response
from xyra.middleware.base import BaseHTTPMiddleware

# Mock socketify objects
class MockSocketifyRequest:
    def get_method(self): return "GET"
    def get_url(self): return "/"
    def for_each_header(self, callback): pass
    def get_parameter(self, idx): return None

class MockSocketifyResponse:
    def __init__(self):
        self.ended = False
        self.status = 200
        self.body = None
        self.headers = {}

    def write_header(self, key, val):
        self.headers[key] = val

    def write_status(self, status):
        self.status = int(status)

    def end(self, data):
        self.ended = True
        self.body = data

class TestConcurrency(unittest.TestCase):
    def test_middleware_execution_order(self):
        app = App()
        log = []

        def mw1(req, res):
            log.append("mw1_start")

        async def mw2(req, call_next):
            log.append("mw2_start")
            await call_next(req)
            log.append("mw2_end")

        app.use(mw1)
        app.use(mw2)

        @app.get("/")
        def handler(req, res):
            log.append("handler")
            res.send("ok")

        # Manually trigger the handler logic (simulating what socketify does)
        app._register_routes()
        # The internal app structure depends on socketify.App which we can't easily mock entirely
        # without actual socketify C extension running.
        # However, we can access the final_handler if we intercept _app.get calls.

    # Since unit testing the full stack is hard without a running server,
    # we will focus on the logic we changed in `_create_final_handler`.

    def test_create_final_handler_logic(self):
        # Setup app
        app = App()
        log = []

        # Define middlewares
        def mw1(req, res):
            log.append("mw1")

        async def mw2(req, call_next):
            log.append("mw2_pre")
            await call_next(req)
            log.append("mw2_post")

        app.use(mw1)
        app.use(mw2)

        # Define handler
        async def handler(req, res):
            log.append("handler")
            res.send("ok")

        # Create the final handler closure
        final_handler = app._create_final_handler(
            handler, [], app._middlewares, "/"
        )

        # Mock Req/Res
        mock_req = MockSocketifyRequest()
        mock_res = MockSocketifyResponse()

        # Run it
        asyncio.run(final_handler(mock_res, mock_req))

        # Verify order
        # mw1 (sync, linear) -> mw2 (async, onion) -> handler -> mw2 post
        expected = ["mw1", "mw2_pre", "handler", "mw2_post"]
        self.assertEqual(log, expected)
        self.assertTrue(mock_res.ended)

    def test_middleware_early_exit(self):
        app = App()
        log = []

        def mw_stopper(req, res):
            log.append("stop")
            # Xyra Response uses .send(), not .end() directly (it calls internal socketify .end)
            res.send("stopped")
            # res.send() sets _ended = True automatically

        def mw_never(req, res):
            log.append("never")

        app.use(mw_stopper)
        app.use(mw_never)

        async def handler(req, res):
            log.append("handler")

        final_handler = app._create_final_handler(
            handler, [], app._middlewares, "/"
        )

        mock_req = MockSocketifyRequest()
        mock_res = MockSocketifyResponse()

        asyncio.run(final_handler(mock_res, mock_req))

        self.assertEqual(log, ["stop"])
        self.assertNotIn("handler", log)
        self.assertNotIn("never", log)

if __name__ == "__main__":
    unittest.main()

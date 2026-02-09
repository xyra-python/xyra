import asyncio
import unittest
import time
from unittest.mock import MagicMock

# Ensure libxyra is mocked before importing App
import sys
if "xyra.libxyra" not in sys.modules:
    sys.modules["xyra.libxyra"] = MagicMock()

from xyra.application import App
from xyra.middleware.security_headers import security_headers

class MockSocketifyRequest:
    def get_method(self):
        return "GET"
    def get_url(self):
        return "/non-existent"
    def get_header(self, name):
        return ""
    def for_each_header(self, callback):
        pass
    def get_parameter(self, idx):
        return None

class MockSocketifyResponse:
    def __init__(self):
        self.ended = False
        self.status = 200
        self.headers = {}
        self.body = None

    def write_header(self, key, val):
        self.headers[key] = val
    def write_status(self, status):
        self.status = int(status)
    def end(self, data):
        self.ended = True
        self.body = data
    def on_aborted(self, handler):
        pass
    def on_data(self, handler):
        pass
    def get_remote_address_bytes(self):
        return b""

class TestSecurity404(unittest.TestCase):
    def test_404_middleware_execution(self):
        """Test that middleware (specifically security headers) is executed for 404 responses."""
        app = App()

        # Use Security Headers middleware
        app.use(security_headers(
            frame_options="DENY",
            xss_protection="1; mode=block"
        ))

        # Also add a custom middleware to verify execution order/flag
        middleware_run = False
        def custom_middleware(req, res):
            nonlocal middleware_run
            middleware_run = True
            res.header("X-Custom-Check", "passed")

        app.use(custom_middleware)

        # This registers routes and starts the async loop thread
        app._register_routes()

        # Find the 404 handler
        mock_app = app._app
        found_handler = None
        for call_args in mock_app.any.call_args_list:
            args, _ = call_args
            if args[0] == "/*":
                found_handler = args[1]
                break

        self.assertIsNotNone(found_handler, "Could not find 404 handler registration")

        mock_req = MockSocketifyRequest()
        mock_res = MockSocketifyResponse()

        # Execute the handler (it submits to the background loop)
        found_handler(mock_res, mock_req)

        # Wait for async execution
        time.sleep(0.5)

        # Assertions
        # Expect 404 status
        self.assertEqual(mock_res.status, 404)

        # Check custom middleware ran
        self.assertTrue(middleware_run, "Custom middleware should have run")
        self.assertIn("X-Custom-Check", mock_res.headers)

        # Check Security Headers
        self.assertIn("X-Frame-Options", mock_res.headers)
        self.assertEqual(mock_res.headers["X-Frame-Options"], "DENY")
        self.assertIn("X-XSS-Protection", mock_res.headers)
        self.assertEqual(mock_res.headers["X-XSS-Protection"], "1; mode=block")

if __name__ == "__main__":
    unittest.main()


import logging

import pytest

from xyra.application import App


class MockNativeRequest:
    def __init__(self, url="/test", method="GET"):
        self.url = url
        self.method = method
        self.headers = {}
        self.params = {}

    def get_url(self): return self.url
    def get_method(self): return self.method
    def get_header(self, name): return self.headers.get(name.lower(), "")

class MockNativeResponse:
    def __init__(self):
        self.headers = []
        self.status = "200"
        self.body = ""
        self.aborted = False

    def write_header(self, k, v): pass
    def write_status(self, s): self.status = s
    def end(self, d): self.body = d
    def on_aborted(self, cb): pass
    def on_data(self, cb): pass
    def get_remote_address_bytes(self): return b""

@pytest.mark.asyncio
async def test_log_injection_sanitization():
    # Setup logging capture
    from xyra.logger import get_logger
    logger = get_logger("xyra")
    log_capture = []

    class CaptureHandler(logging.Handler):
        def emit(self, record):
            log_capture.append(self.format(record))

    handler = CaptureHandler()
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    app = App()
    app.log_requests = True

    # Create malicious request
    malicious_url = "/login?user=admin\nINJECTED_LOG_ENTRY"
    native_req = MockNativeRequest(url=malicious_url)
    native_res = MockNativeResponse()

    # We need to trigger the final handler logic.
    # App._create_final_handler creates a wrapper.
    # But it's hard to get it isolated.
    # Instead, we'll verify that IF the logging logic is triggered, it sanitizes.

    # The logic is:
    # req_logger.info(f"{request.method} {request.url} {response.status_code} {duration}ms")
    # But now request.url should be sanitized.

    # Wait, request.url property returns self._url_cache or calls native get_url().
    # It returns the RAW url string (including \n).
    # The sanitization happens inside App._create_final_handler logic, specifically in the logging block.

    # To test this integration, we need to run a route handler via app.
    # app._register_routes registers handlers with native app.
    # But native app is mocked.

    # We can invoke _create_final_handler manually.
    async def dummy_handler(req, res):
        res.status(200).send("ok")

    final_handler = app._create_final_handler(dummy_handler, [], [], "/test")

    # final_handler is `async def async_final_handler(res, req):` (native interface)
    # We call it with native objects.

    await final_handler(native_res, native_req)

    # Check logs
    # Note: logging happens only if status >= 400 or duration > 100ms
    # Our status is 200. Duration is 0ms.
    # So it won't log!

    # We need to make it log.
    # Either status >= 400 or make it slow.

    # Let's make it status 400.
    async def error_handler(req, res):
        res.status(400).send("bad")

    final_handler = app._create_final_handler(error_handler, [], [], "/test")
    await final_handler(native_res, native_req)

    # Now it should log.
    assert len(log_capture) > 0
    log_entry = log_capture[-1]

    # Verify sanitized
    assert "%0AINJECTED_LOG_ENTRY" in log_entry
    assert "\n" not in log_entry

    # Clean up
    logger.removeHandler(handler)

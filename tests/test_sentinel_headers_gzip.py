
import sys
from unittest.mock import Mock, MagicMock
import gzip

# Mock dependencies if missing
try:
    import multidict
except ImportError:
    multidict = MagicMock()
    sys.modules["multidict"] = multidict

try:
    import orjson
except ImportError:
    orjson = MagicMock()
    sys.modules["orjson"] = orjson

try:
    import jinja2
except ImportError:
    jinja2 = MagicMock()
    sys.modules["jinja2"] = jinja2

try:
    import watchfiles
except ImportError:
    watchfiles = MagicMock()
    sys.modules["watchfiles"] = watchfiles

# Mock libxyra if missing
if "xyra.libxyra" not in sys.modules:
    sys.modules["xyra.libxyra"] = MagicMock()

from xyra.middleware.gzip import GzipMiddleware
from xyra.application import App

def test_gzip_middleware_case_sensitivity():
    """Test that GzipMiddleware handles case-insensitive headers correctly."""
    middleware = GzipMiddleware(minimum_size=10)

    # Mock Request with lowercase headers (simulating Xyra native behavior)
    request = Mock()
    request.headers = {"accept-encoding": "gzip, deflate"}
    # Mock get_header behavior
    request.get_header = lambda k, d=None: request.headers.get(k.lower(), d)

    # Mock Response
    response = Mock()
    response.headers = {}
    response.header = lambda k, v: response.headers.update({k: v})

    def vary_func(name):
        if "Vary" in response.headers:
            response.headers["Vary"] += f", {name}"
        else:
            response.headers["Vary"] = name
    response.vary = vary_func

    # Mock original send
    original_send = Mock()
    response.send = original_send

    # Apply middleware
    middleware(request, response)

    # Send data
    data = "x" * 100
    response.send(data)

    # Verify compression
    assert original_send.called
    sent_data = original_send.call_args[0][0]

    # Data should be compressed (bytes), not original string
    assert isinstance(sent_data, bytes)
    assert sent_data != data

    # Verify it is valid gzip
    decompressed = gzip.decompress(sent_data)
    assert decompressed.decode() == data

def test_app_security_headers_default_csp():
    """Test that App.enable_security_headers sets a default CSP."""
    # We need to mock SecurityHeadersMiddleware import inside App

    app = App()

    # Mock the middleware class to capture arguments
    mock_middleware_cls = MagicMock()

    # Patch sys.modules to return our mock for the middleware module
    with MagicMock() as mock_module:
        mock_module.SecurityHeadersMiddleware = mock_middleware_cls
        # We need to ensure that when App imports it, it gets our mock
        # Since App imports it inside the method, we patch sys.modules temporarily
        original_module = sys.modules.get('xyra.middleware.security_headers')
        sys.modules['xyra.middleware.security_headers'] = mock_module

        try:
            # Call the method
            app.enable_security_headers()

            # Check args
            assert mock_middleware_cls.called
            kwargs = mock_middleware_cls.call_args[1]

            # Verify default CSP
            assert kwargs.get("content_security_policy") == "object-src 'none'; base-uri 'self'"
        finally:
            if original_module:
                sys.modules['xyra.middleware.security_headers'] = original_module
            else:
                del sys.modules['xyra.middleware.security_headers']

def test_app_security_headers_override_csp():
    """Test that default CSP can be overridden."""
    app = App()

    mock_middleware_cls = MagicMock()

    with MagicMock() as mock_module:
        mock_module.SecurityHeadersMiddleware = mock_middleware_cls
        original_module = sys.modules.get('xyra.middleware.security_headers')
        sys.modules['xyra.middleware.security_headers'] = mock_module

        try:
            # Call with override
            app.enable_security_headers(content_security_policy="default-src 'none'")

            # Check args
            assert mock_middleware_cls.called
            kwargs = mock_middleware_cls.call_args[1]

            # Verify overridden CSP
            assert kwargs.get("content_security_policy") == "default-src 'none'"
        finally:
            if original_module:
                sys.modules['xyra.middleware.security_headers'] = original_module
            else:
                del sys.modules['xyra.middleware.security_headers']

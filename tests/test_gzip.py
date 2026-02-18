from unittest.mock import Mock

from multidict import CIMultiDict

from xyra.middleware import GzipMiddleware, gzip_middleware


def _setup_response_mock():
    """Helper to setup response mock with proper header method."""
    response = Mock()
    response.headers = CIMultiDict()

    def header_func(key, value):
        response.headers[key] = value

    response.header = header_func

    def vary_func(name):
        response.headers.add("Vary", name)

    response.vary = vary_func

    response._ended = False
    return response


def _setup_request_mock(headers=None):
    """Helper to setup request mock with proper get_header method."""
    request = Mock()
    request.headers = headers or {}

    # Mock get_header to behave like Request.get_header (case-insensitive lookup)
    def get_header(key, default=None):
        # Request.get_header lowercases the key before lookup
        # and assumes request.headers keys are already lowercase or CIMultiDict
        # But for tests we simulate behavior: lookup key in dict (case-insensitive simulation)
        key_lower = key.lower()
        for k, v in request.headers.items():
            if k.lower() == key_lower:
                return v
        return default or ""

    request.get_header = get_header
    return request


# Gzip Tests
def test_gzip_middleware_init():
    middleware = GzipMiddleware()
    assert middleware.minimum_size == 1024
    assert middleware.compress_level == 6


def test_gzip_function():
    middleware = gzip_middleware(minimum_size=512, compress_level=9)
    assert isinstance(middleware, GzipMiddleware)
    assert middleware.minimum_size == 512
    assert middleware.compress_level == 9


def test_gzip_middleware_compress_large_data():
    middleware = GzipMiddleware(minimum_size=100)
    request = _setup_request_mock({"Accept-Encoding": "gzip"})
    response = _setup_response_mock()

    # Store original send method
    original_send = response.send

    # Call middleware
    middleware(request, response)

    # Create large data
    large_data = "x" * 200

    # Call send through the compressed_send function
    response.send(large_data)

    # Verify compression was applied
    original_send.assert_called_once()
    compressed_data = original_send.call_args[0][0]
    assert isinstance(compressed_data, bytes)
    assert len(compressed_data) < len(large_data.encode())
    assert response.headers["Content-Encoding"] == "gzip"
    assert response.headers["Vary"] == "Accept-Encoding"


def test_gzip_middleware_no_compress_small_data():
    middleware = GzipMiddleware(minimum_size=1000)
    request = _setup_request_mock({"Accept-Encoding": "gzip"})
    response = _setup_response_mock()

    # Store original send method
    original_send = response.send

    # Call middleware
    middleware(request, response)

    # Create small data
    small_data = "small data"

    # Call send
    response.send(small_data)

    # Verify no compression
    original_send.assert_called_once_with(small_data)
    assert "Content-Encoding" not in response.headers


def test_gzip_middleware_no_accept_encoding():
    middleware = GzipMiddleware(minimum_size=100)
    request = _setup_request_mock({})  # No Accept-Encoding
    response = _setup_response_mock()

    # Store original send method
    original_send = response.send

    # Call middleware
    middleware(request, response)

    # Create data
    data = "x" * 200

    # Call send
    response.send(data)

    # Verify no compression
    original_send.assert_called_once_with(data)
    assert "Content-Encoding" not in response.headers


def test_gzip_middleware_already_encoded():
    middleware = GzipMiddleware(minimum_size=100)
    request = _setup_request_mock({"Accept-Encoding": "gzip"})
    response = _setup_response_mock()
    response.headers = {"Content-Encoding": "deflate"}  # Already encoded

    # Store original send method
    original_send = response.send

    # Call middleware
    middleware(request, response)

    # Create data
    data = "x" * 200

    # Call send
    response.send(data)

    # Verify no compression
    original_send.assert_called_once_with(data)
    assert response.headers["Content-Encoding"] == "deflate"  # Unchanged


def test_gzip_middleware_compress_string_data():
    middleware = GzipMiddleware(minimum_size=100)
    request = _setup_request_mock({"Accept-Encoding": "gzip"})
    response = _setup_response_mock()

    # Store original send method
    original_send = response.send

    # Call middleware
    middleware(request, response)

    # Create string data
    string_data = "x" * 200

    # Call send
    response.send(string_data)

    # Verify compression and encoding to bytes
    original_send.assert_called_once()
    compressed_data = original_send.call_args[0][0]
    assert isinstance(compressed_data, bytes)
    assert response.headers["Content-Encoding"] == "gzip"

def test_gzip_middleware_lowercase_header():
    """Regression test for case-insensitive header lookup."""
    middleware = GzipMiddleware(minimum_size=100)
    # Use lowercase header key
    request = _setup_request_mock({"accept-encoding": "gzip"})
    response = _setup_response_mock()

    original_send = response.send
    middleware(request, response)

    large_data = "x" * 200
    response.send(large_data)

    original_send.assert_called_once()
    assert response.headers["Content-Encoding"] == "gzip"

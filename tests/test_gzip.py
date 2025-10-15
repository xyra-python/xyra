from unittest.mock import Mock

from xyra.middleware import GzipMiddleware, gzip_middleware


def _setup_response_mock():
    """Helper to setup response mock with proper header method."""
    response = Mock()
    response.headers = {}

    def header_func(key, value):
        response.headers[key] = value

    response.header = header_func

    response._ended = False
    return response


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
    request = Mock()
    request.headers = {"Accept-Encoding": "gzip"}
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
    request = Mock()
    request.headers = {"Accept-Encoding": "gzip"}
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
    request = Mock()
    request.headers = {}  # No Accept-Encoding
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
    request = Mock()
    request.headers = {"Accept-Encoding": "gzip"}
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
    request = Mock()
    request.headers = {"Accept-Encoding": "gzip"}
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

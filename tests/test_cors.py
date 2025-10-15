from unittest.mock import Mock

from xyra.middleware import CorsMiddleware, cors


# CORS Tests
def test_cors_middleware_init():
    middleware = CorsMiddleware()
    assert middleware.allowed_origins == ["*"]
    assert "GET" in middleware.allowed_methods
    assert "Content-Type" in middleware.allowed_headers
    assert middleware.allow_credentials is False
    assert middleware.max_age == 3600


def test_cors_middleware_init_custom():
    middleware = CorsMiddleware(
        allowed_origins=["https://example.com"],
        allowed_methods=["GET", "POST"],
        allow_credentials=True,
    )
    assert middleware.allowed_origins == ["https://example.com"]
    assert middleware.allowed_methods == ["GET", "POST"]
    assert middleware.allow_credentials is True


def test_cors_is_origin_allowed():
    middleware = CorsMiddleware(allowed_origins=["https://example.com"])
    assert middleware._is_origin_allowed("https://example.com") is True
    assert middleware._is_origin_allowed("https://other.com") is False

    wildcard_middleware = CorsMiddleware(allowed_origins=["*"])
    assert wildcard_middleware._is_origin_allowed("any-origin") is True


def test_cors_middleware_call():
    middleware = CorsMiddleware(allowed_origins=["https://example.com"])
    request = Mock()
    request.get_header.return_value = "https://example.com"
    request.method = "GET"
    response = Mock()

    middleware(request, response)

    response.header.assert_any_call(
        "Access-Control-Allow-Origin", "https://example.com"
    )
    # Should not set _ended for non-OPTIONS
    response._ended = False


def test_cors_middleware_options():
    middleware = CorsMiddleware()
    request = Mock()
    request.method = "OPTIONS"
    response = Mock()

    middleware(request, response)

    response.status.assert_called_once_with(204)
    response.send.assert_called_once_with("")
    assert response._ended is True


def test_cors_function():
    middleware = cors(allowed_origins=["https://test.com"])
    assert isinstance(middleware, CorsMiddleware)
    assert middleware.allowed_origins == ["https://test.com"]


def test_cors_middleware_string_inputs():
    """Test that string inputs are converted to lists."""
    middleware = CorsMiddleware(
        allowed_origins="https://example.com",
        allowed_methods="GET",
        allowed_headers="Content-Type",
    )
    assert middleware.allowed_origins == ["https://example.com"]
    assert middleware.allowed_methods == ["GET"]
    assert middleware.allowed_headers == ["Content-Type"]


def test_cors_middleware_allow_credentials():
    """Test CORS with credentials enabled."""
    middleware = CorsMiddleware(
        allowed_origins=["https://example.com"], allow_credentials=True
    )
    request = Mock()
    request.get_header.return_value = "https://example.com"
    request.method = "GET"
    response = Mock()

    middleware(request, response)

    # Should set specific origin (not wildcard) when credentials enabled
    response.header.assert_any_call(
        "Access-Control-Allow-Origin", "https://example.com"
    )
    response.header.assert_any_call("Access-Control-Allow-Credentials", "true")


def test_cors_middleware_wildcard_with_credentials():
    """Test that wildcard origin is not set when credentials are enabled."""
    middleware = CorsMiddleware(allow_credentials=True)
    request = Mock()
    request.get_header.return_value = "https://example.com"
    request.method = "GET"
    response = Mock()

    middleware(request, response)

    # Should not set wildcard origin when credentials enabled
    wildcard_calls = [
        call for call in response.header.call_args_list if call[0][1] == "*"
    ]
    assert len(wildcard_calls) == 0


def test_cors_middleware_no_origin_header():
    """Test CORS when no Origin header is present."""
    middleware = CorsMiddleware(allowed_origins=["https://example.com"])
    request = Mock()
    request.get_header.return_value = None  # No origin header
    request.method = "GET"
    response = Mock()

    middleware(request, response)

    # Should still set other CORS headers but not Access-Control-Allow-Origin
    origin_calls = [
        call
        for call in response.header.call_args_list
        if call[0][0] == "Access-Control-Allow-Origin"
    ]
    assert len(origin_calls) == 0


def test_cors_middleware_wildcard_origin():
    """Test CORS with wildcard origin when no specific origin is provided."""
    middleware = CorsMiddleware()  # Default is ["*"]
    request = Mock()
    request.get_header.return_value = None  # No origin header
    request.method = "GET"
    response = Mock()

    middleware(request, response)

    # Should set wildcard origin when no origin header and credentials disabled
    response.header.assert_any_call("Access-Control-Allow-Origin", "*")


def test_cors_middleware_custom_max_age():
    """Test CORS with custom max_age."""
    middleware = CorsMiddleware(max_age=7200)
    request = Mock()
    request.get_header.return_value = "https://example.com"
    request.method = "GET"
    response = Mock()

    middleware(request, response)

    response.header.assert_any_call("Access-Control-Max-Age", "7200")

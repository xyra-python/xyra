from unittest.mock import Mock

from xyra.middleware import RateLimiter, RateLimitMiddleware, rate_limiter


def _setup_response_mock():
    """Helper to setup response mock with proper header method."""
    response = Mock()
    response.headers = {}

    def header_func(key, value):
        response.headers[key] = value

    response.header = header_func

    response._ended = False
    return response


# Rate Limiter Tests
def test_rate_limiter_init():
    limiter = RateLimiter(requests=50, window=30)
    assert limiter.requests == 50
    assert limiter.window == 30


def test_rate_limiter_allowed():
    limiter = RateLimiter(requests=2, window=1)
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is True
    assert limiter.is_allowed("127.0.0.1") is False  # Exceeded limit


def test_rate_limiter_cleanup():
    limiter = RateLimiter(requests=1, window=1)
    limiter._requests["127.0.0.1"] = [0]  # Old timestamp
    assert limiter.is_allowed("127.0.0.1") is True  # Should cleanup old requests


def test_rate_limiter_get_remaining_requests():
    limiter = RateLimiter(requests=5, window=60)
    key = "127.0.0.1"
    assert limiter.get_remaining_requests(key) == 5
    limiter.is_allowed(key)
    assert limiter.get_remaining_requests(key) == 4


def test_rate_limiter_get_reset_time():
    limiter = RateLimiter(requests=1, window=60)
    key = "127.0.0.1"
    limiter.is_allowed(key)  # This should set a timestamp
    reset_time = limiter.get_reset_time(key)
    assert reset_time > 0
    assert reset_time <= 60


def test_rate_limit_middleware_init():
    limiter = RateLimiter()
    middleware = RateLimitMiddleware(limiter)
    assert middleware.limiter == limiter


def test_rate_limiter_function():
    middleware = rate_limiter(requests=10, window=60)
    assert isinstance(middleware, RateLimitMiddleware)
    assert middleware.limiter.requests == 10
    assert middleware.limiter.window == 60


def test_rate_limit_middleware_allowed():
    limiter = RateLimiter(requests=10, window=60)
    middleware = RateLimitMiddleware(limiter)
    request = Mock()
    request.get_header.side_effect = lambda h: {"X-Forwarded-For": "127.0.0.1"}.get(h)
    response = _setup_response_mock()

    middleware(request, response)

    # Should set rate limit headers
    assert response.headers["X-RateLimit-Limit"] == "10"
    assert response.headers["X-RateLimit-Remaining"] == "9"
    assert "X-RateLimit-Reset" in response.headers
    assert response._ended is False


def test_rate_limit_middleware_exceeded():
    limiter = RateLimiter(requests=1, window=60)
    middleware = RateLimitMiddleware(limiter)
    request = Mock()
    request.get_header.side_effect = lambda h: {"X-Forwarded-For": "127.0.0.1"}.get(h)
    response = _setup_response_mock()

    # First request should be allowed
    middleware(request, response)
    assert response._ended is False

    # Reset response mock
    response.reset_mock()
    response.headers = {}
    response._ended = False
    response.header = lambda k, v: response.headers.__setitem__(k, v)

    # Second request should be blocked
    middleware(request, response)
    response.status.assert_called_once_with(429)
    assert response.headers["X-RateLimit-Limit"] == "1"
    assert response.headers["X-RateLimit-Remaining"] == "0"
    assert "Retry-After" in response.headers
    response.json.assert_called_once()
    assert response._ended is True


def test_rate_limit_middleware_custom_key_func():
    def custom_key_func(request):
        return "custom_key"

    limiter = RateLimiter(requests=5, window=60)
    middleware = RateLimitMiddleware(limiter, key_func=custom_key_func)
    request = Mock()
    response = _setup_response_mock()

    middleware(request, response)

    # Should use custom key
    assert limiter.get_remaining_requests("custom_key") == 4


def test_rate_limit_middleware_default_key_func():
    limiter = RateLimiter(requests=5, window=60)
    middleware = RateLimitMiddleware(limiter)
    request = Mock()
    request.get_header.side_effect = lambda h: {
        "X-Forwarded-For": "192.168.1.1",
        "X-Real-IP": None,
    }.get(h)

    key = middleware.key_func(request)
    assert key == "192.168.1.1"

    # Test fallback
    request.get_header.side_effect = lambda h: None
    key = middleware.key_func(request)
    assert key == "127.0.0.1"

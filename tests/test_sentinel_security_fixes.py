from unittest.mock import Mock

import pytest

from xyra.middleware.cors import CorsMiddleware
from xyra.middleware.csrf import CSRFMiddleware
from xyra.middleware.rate_limiter import RateLimiter


def test_ratelimiter_lru_eviction():
    # Test that RateLimiter respects max_entries and evicts oldest
    max_entries = 10
    limiter = RateLimiter(requests=10, window=60, max_entries=max_entries)

    # Fill up
    for i in range(max_entries):
        limiter.is_allowed(f"user_{i}")

    assert len(limiter._requests) == max_entries
    assert "user_0" in limiter._requests

    # Add one more
    limiter.is_allowed("new_user")

    assert len(limiter._requests) == max_entries
    assert "user_0" not in limiter._requests  # Oldest should be gone
    assert "new_user" in limiter._requests


def test_ratelimiter_no_creation_on_read():
    # Test that reading state doesn't create new entries
    limiter = RateLimiter(requests=10, window=60)

    limiter.get_reset_time("non_existent")
    assert "non_existent" not in limiter._requests

    limiter.get_remaining_requests("non_existent")
    assert "non_existent" not in limiter._requests


@pytest.mark.asyncio
async def test_csrf_token_masking_different_each_time():
    # Test that CSRF tokens are different even for same base token
    middleware = CSRFMiddleware(secret_key="test_secret")

    request = Mock()
    request.method = "GET"
    request.get_header.return_value = None
    response = Mock()

    await middleware(request, response)
    token1 = request.csrf_token

    # Use the same cookie for second request
    args, _ = response.set_cookie.call_args
    cookie_value = args[1]

    request2 = Mock()
    request2.method = "GET"
    request2.get_header.side_effect = (
        lambda h: f"{middleware.cookie_name}={cookie_value}"
        if h.lower() == "cookie"
        else None
    )

    await middleware(request2, response)
    token2 = request2.csrf_token

    assert token1 != token2
    assert middleware._unmask_token(token1) == middleware._unmask_token(token2)


@pytest.mark.asyncio
async def test_csrf_host_prefix_enforcement():
    # Test that __Host- prefix is used when secure=True
    middleware = CSRFMiddleware(cookie_name="my_token", secure=True)
    assert middleware.cookie_name == "__Host-my_token"

    request = Mock()
    request.method = "GET"
    request.get_header.return_value = None
    response = Mock()

    await middleware(request, response)

    args, _ = response.set_cookie.call_args
    assert args[0] == "__Host-my_token"


def test_cors_no_reflection_on_wildcard():
    # Test that Origin is not reflected when "*" is allowed
    middleware = CorsMiddleware(allowed_origins=["*"], allow_credentials=False)

    request = Mock()
    request.method = "GET"
    request.get_header.side_effect = (
        lambda h: "https://attacker.com" if h.lower() == "origin" else None
    )
    response = Mock()
    headers = {}
    response.header.side_effect = lambda k, v: headers.__setitem__(k, v)

    middleware(request, response)

    assert headers["Access-Control-Allow-Origin"] == "*"

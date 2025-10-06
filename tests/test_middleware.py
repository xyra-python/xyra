from unittest.mock import AsyncMock, Mock

import pytest

from xyra.middleware.cors import CorsMiddleware, cors
from xyra.middleware.gzip import GzipMiddleware, gzip_middleware
from xyra.middleware.httpsredirect import (
    HTTPSRedirectMiddleware,
    https_redirect_middleware,
)
from xyra.middleware.trustedhost import TrustedHostMiddleware, trusted_host_middleware


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


@pytest.mark.asyncio
async def test_cors_middleware_call():
    middleware = CorsMiddleware(allowed_origins=["https://example.com"])
    request = Mock()
    request.get_header.return_value = "https://example.com"
    request.method = "GET"
    response = Mock()
    next_handler = AsyncMock()

    await middleware(request, response, next_handler)

    response.header.assert_any_call(
        "Access-Control-Allow-Origin", "https://example.com"
    )
    next_handler.assert_called_once()


@pytest.mark.asyncio
async def test_cors_middleware_options():
    middleware = CorsMiddleware()
    request = Mock()
    request.method = "OPTIONS"
    response = Mock()
    next_handler = AsyncMock()

    await middleware(request, response, next_handler)

    response.status.assert_called_once_with(204)
    response.send.assert_called_once_with("")
    next_handler.assert_not_called()


def test_cors_function():
    middleware = cors(allowed_origins=["https://test.com"])
    assert isinstance(middleware, CorsMiddleware)
    assert middleware.allowed_origins == ["https://test.com"]


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


# HTTPS Redirect Tests
def test_https_redirect_middleware_init():
    middleware = HTTPSRedirectMiddleware()
    assert middleware.redirect_status_code == 301


def test_https_redirect_function():
    middleware = https_redirect_middleware(redirect_status_code=302)
    assert isinstance(middleware, HTTPSRedirectMiddleware)
    assert middleware.redirect_status_code == 302


# Trusted Host Tests
def test_trusted_host_middleware_init():
    middleware = TrustedHostMiddleware(allowed_hosts=["example.com"])
    assert middleware.allowed_hosts == ["example.com"]


def test_trusted_host_function():
    middleware = trusted_host_middleware(["test.com", "api.test.com"])
    assert isinstance(middleware, TrustedHostMiddleware)
    assert middleware.allowed_hosts == ["test.com", "api.test.com"]

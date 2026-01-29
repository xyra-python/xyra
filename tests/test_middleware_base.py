import pytest
from unittest.mock import Mock
from xyra.middleware.base import BaseHTTPMiddleware
from xyra.request import Request
from xyra.response import Response

@pytest.mark.asyncio
async def test_base_middleware_dispatch_not_implemented():
    middleware = BaseHTTPMiddleware()
    mock_req = Mock(spec=Request)
    async def call_next(req):
        return Mock(spec=Response)

    with pytest.raises(NotImplementedError):
        await middleware(mock_req, call_next)

@pytest.mark.asyncio
async def test_base_middleware_dispatch_override():
    class MyMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            return await call_next(request)

    middleware = MyMiddleware()
    mock_req = Mock(spec=Request)
    expected_res = Mock(spec=Response)

    async def call_next(req):
        return expected_res

    res = await middleware(mock_req, call_next)
    assert res is expected_res

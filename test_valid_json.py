import sys
import json
sys.modules['orjson'] = json
from unittest.mock import Mock, AsyncMock
sys.modules['xyra.libxyra'] = Mock()

from xyra.request import Request
from xyra.response import Response
import asyncio

async def test():
    native_res = Mock()
    res = Response(native_res)
    req = Request(Mock(), res)

    # Test valid application/json with parameters
    req.get_header = lambda name, default=None: {
        "content-type": "application/json; charset=utf-8",
    }.get(name.lower(), default)

    req._res = Mock()
    req._res.get_data = AsyncMock(return_value=b'{"admin": true}')

    try:
        data = await req.json()
        print("Success for application/json:", data)
    except ValueError as e:
        print("Failed for application/json:", e)

    # Test valid vnd.api+json
    req._json_cache = None
    req._body_cache = None
    req.get_header = lambda name, default=None: {
        "content-type": "application/vnd.api+json",
    }.get(name.lower(), default)

    try:
        data = await req.json()
        print("Success for +json:", data)
    except ValueError as e:
        print("Failed for +json:", e)

asyncio.run(test())

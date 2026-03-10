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

    # Simulate attacker sending a simple request with text/plain (no preflight)
    # but sneaking in +json to bypass the MIME check.
    req.get_header = lambda name, default=None: {
        "content-type": "text/plain; boundary=+json",
    }.get(name.lower(), default)

    req._res = Mock()
    req._res.get_data = AsyncMock(return_value=b'{"admin": true}')

    try:
        data = await req.json()
        print("VULNERABLE! Parsed data:", data)
    except ValueError as e:
        print("SECURE! Rejected:", e)

asyncio.run(test())

import sys
import json
sys.modules['orjson'] = json
from unittest.mock import Mock
sys.modules['xyra.libxyra'] = Mock()

from xyra.middleware.proxy_headers import ProxyHeadersMiddleware
from xyra.request import Request
from xyra.response import Response

def test_proxy():
    # If the proxy setup is 1 trusted proxy:
    mw = ProxyHeadersMiddleware(trusted_proxies=["10.0.0.1"])

    native_res = Mock()
    res = Response(native_res)
    req = Request(Mock(), res)

    req._remote_addr_cache = "10.0.0.1"

    req.get_header = lambda name, default=None: {
        "x-forwarded-for": "1.2.3.4, 5.6.7.8",
        # What if proxy didn't append to XFP?
        "x-forwarded-proto": "https"
    }.get(name.lower(), default)

    mw(req, res)
    print("RES IP:", req.remote_addr)
    print("RES SCHEME:", req.scheme)

test_proxy()


import time
from unittest.mock import Mock

from xyra.middleware.proxy_headers import ProxyHeadersMiddleware
from xyra.request import Request


def test_large_xff_dos():
    req = Mock()
    res = Mock()

    # 10MB XFF header with no commas
    large_xff = "A" * (10 * 1024 * 1024)

    headers = {"x-forwarded-for": large_xff}
    req.get_header.side_effect = lambda k, default=None: headers.get(k, default)
    res.get_remote_address_bytes.return_value = b"\x0a\x00\x00\x01" # 10.0.0.1

    request = Request(req, res)
    mw = ProxyHeadersMiddleware(["10.0.0.1"])

    start = time.time()
    mw(request, res)
    end = time.time()

    print(f"Time taken for 10MB XFF: {end - start:.4f}s")

if __name__ == "__main__":
    test_large_xff_dos()

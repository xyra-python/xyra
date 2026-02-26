import unittest
import time
from unittest.mock import MagicMock
from xyra.request import Request
from xyra.response import Response
from xyra.middleware.proxy_headers import ProxyHeadersMiddleware

print("Loading test...")

class MockRequest(Request):
    def __init__(self, remote_addr, xff):
        self._remote_addr_cache = remote_addr
        self.headers_mock = {
            "x-forwarded-for": xff,
            "host": "example.com"
        }
        # Request object expects a native req object
        self._req = MagicMock()
        self._req.get_header = lambda name: self.headers_mock.get(name.lower())
        self._req.get_headers = lambda: self.headers_mock
        self._req.get_url = lambda: "/api/test"
        self._req.get_query = lambda: ""
        self._req.get_method = lambda: "GET"

        self._res = MagicMock()
        self._res.get_remote_address_bytes = lambda: b'\x7f\x00\x00\x01' # 127.0.0.1

        # Initialize parent
        super().__init__(self._req, self._res)

class TestProxyDos(unittest.TestCase):
    def test_proxy_header_dos_mitigation(self):
        print("Starting DoS mitigation test...")
        # Create a massive X-Forwarded-For header with 50,000 IPs
        xff = ", ".join(["1.1.1.1"] * 50000)

        req = MockRequest("127.0.0.1", xff)
        res = Response(MagicMock())

        # Trust all IPv4 addresses via CIDR.
        middleware = ProxyHeadersMiddleware(trusted_proxies=["0.0.0.0/0"])

        start_time = time.time()
        middleware(req, res)
        end_time = time.time()

        duration = end_time - start_time
        print(f"Time taken to process 50,000 IPs (limited): {duration:.4f}s")

        # Should be fast (< 0.05s usually, 0.1s safe margin)
        self.assertLess(duration, 0.1)

        # Should fail safe (set remote_addr to unknown instead of trusted proxy IP)
        self.assertEqual(req.remote_addr, "unknown")

    def test_proxy_header_valid_short_chain(self):
        print("Starting valid chain test...")
        # Chain: Client -> Proxy1 -> Proxy2
        # We trust Proxy2 (remote_addr) and Proxy1.
        # XFF: Client, Proxy1
        xff = "10.0.0.1, 10.0.0.2"
        req = MockRequest("127.0.0.1", xff)
        res = Response(MagicMock())

        # Trust 127.0.0.1 and 10.0.0.2
        middleware = ProxyHeadersMiddleware(trusted_proxies=["127.0.0.1", "10.0.0.2"])

        middleware(req, res)

        # Should resolve to 10.0.0.1 (Client)
        self.assertEqual(req.remote_addr, "10.0.0.1")

if __name__ == "__main__":
    unittest.main()

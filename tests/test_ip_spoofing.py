import socket
import unittest
from unittest.mock import MagicMock

from xyra.middleware.rate_limiter import RateLimiter, RateLimitMiddleware, rate_limiter
from xyra.request import Request


class TestIpSpoofing(unittest.TestCase):
    def setUp(self):
        self.mock_req = MagicMock()
        self.mock_res = MagicMock()
        self.request = Request(self.mock_req, self.mock_res)

    def test_remote_addr_ipv4(self):
        # Mock IPv4: 127.0.0.1 -> b'\x7f\x00\x00\x01'
        self.mock_res.get_remote_address_bytes.return_value = b"\x7f\x00\x00\x01"
        # Clear cache if any
        self.request._remote_addr_cache = None

        self.assertEqual(self.request.remote_addr, "127.0.0.1")
        self.mock_res.get_remote_address_bytes.assert_called_once()

    def test_remote_addr_ipv6(self):
        # Mock IPv6: ::1 -> 15 nulls + 1
        ipv6_bytes = b"\x00" * 15 + b"\x01"
        self.mock_res.get_remote_address_bytes.return_value = ipv6_bytes
        self.request._remote_addr_cache = None

        self.assertEqual(self.request.remote_addr, "::1")

    def test_rate_limiter_trust_proxy_false(self):
        # Setup: Real IP is 1.2.3.4, Header says 5.6.7.8
        self.mock_res.get_remote_address_bytes.return_value = socket.inet_pton(
            socket.AF_INET, "1.2.3.4"
        )
        self.request._remote_addr_cache = None

        # Mock headers
        headers = {"x-forwarded-for": "5.6.7.8"}
        self.request.get_header = lambda name, default=None: headers.get(
            name.lower(), default
        )

        limiter = RateLimiter()
        middleware = RateLimitMiddleware(limiter, trust_proxy=False)

        # Should use remote_addr (1.2.3.4)
        key = middleware._default_key_func(self.request)
        self.assertEqual(key, "1.2.3.4")

    def test_rate_limiter_trust_proxy_true(self):
        # Setup: Real IP is 1.2.3.4, Header says 5.6.7.8
        self.mock_res.get_remote_address_bytes.return_value = socket.inet_pton(
            socket.AF_INET, "1.2.3.4"
        )
        self.request._remote_addr_cache = None

        # Mock headers
        headers = {"x-forwarded-for": "5.6.7.8"}
        self.request.get_header = lambda name, default=None: headers.get(
            name.lower(), default
        )

        limiter = RateLimiter()
        middleware = RateLimitMiddleware(limiter, trust_proxy=True)

        # Should use header (5.6.7.8)
        key = middleware._default_key_func(self.request)
        self.assertEqual(key, "5.6.7.8")

    def test_rate_limiter_spoofing_attempt(self):
        # Setup: Real IP is 1.2.3.4 (not used when proxy trusted)
        # Proxy IP is 10.0.0.1
        # Attacker injects "8.8.8.8" into X-Forwarded-For
        # Proxy appends real client IP "1.2.3.4"
        self.mock_res.get_remote_address_bytes.return_value = socket.inet_pton(
            socket.AF_INET, "10.0.0.1"
        )
        self.request._remote_addr_cache = None

        headers = {"x-forwarded-for": "8.8.8.8, 1.2.3.4"}
        self.request.get_header = lambda name, default=None: headers.get(
            name.lower(), default
        )

        limiter = RateLimiter()
        # Default trusted_proxy_count=1
        middleware = RateLimitMiddleware(limiter, trust_proxy=True)

        # Should use the LAST IP (1.2.3.4), ignoring the spoofed "8.8.8.8"
        key = middleware._default_key_func(self.request)
        self.assertEqual(key, "1.2.3.4")

    def test_rate_limiter_multi_proxy(self):
        # Setup: Chain is Client (1.2.3.4) -> Proxy1 (10.0.0.1) -> Proxy2 (10.0.0.2)
        # Header: "1.2.3.4, 10.0.0.1" (as seen by Proxy2/App)
        self.mock_res.get_remote_address_bytes.return_value = socket.inet_pton(
            socket.AF_INET, "10.0.0.2"
        )
        self.request._remote_addr_cache = None

        headers = {"x-forwarded-for": "1.2.3.4, 10.0.0.1"}
        self.request.get_header = lambda name, default=None: headers.get(
            name.lower(), default
        )

        limiter = RateLimiter()
        # Trust 2 proxies
        middleware = RateLimitMiddleware(
            limiter, trust_proxy=True, trusted_proxy_count=2
        )

        # Should take the 2nd from right (1.2.3.4)
        key = middleware._default_key_func(self.request)
        self.assertEqual(key, "1.2.3.4")

    def test_rate_limiter_helper_function(self):
        mw = rate_limiter(trust_proxy=True)
        self.assertTrue(mw.trust_proxy)
        self.assertEqual(mw.trusted_proxy_count, 1)

        mw = rate_limiter(trust_proxy=True, trusted_proxy_count=2)
        self.assertEqual(mw.trusted_proxy_count, 2)

        mw = rate_limiter(trust_proxy=False)
        self.assertFalse(mw.trust_proxy)


if __name__ == "__main__":
    unittest.main()

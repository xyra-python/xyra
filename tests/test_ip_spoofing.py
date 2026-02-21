import socket
import unittest
from unittest.mock import MagicMock

from xyra.middleware.proxy_headers import ProxyHeadersMiddleware
from xyra.middleware.rate_limiter import RateLimiter, RateLimitMiddleware
from xyra.request import Request


class TestIpSpoofing(unittest.TestCase):
    def setUp(self):
        self.mock_req = MagicMock()
        self.mock_res = MagicMock()
        self.request = Request(self.mock_req, self.mock_res)

    def test_remote_addr_ipv4(self):
        # Mock IPv4: 127.0.0.1 -> b'\x7f\x00\x00\x01'
        self.mock_res.get_remote_address_bytes.return_value = b"\x7f\x00\x00\x01"
        self.request._remote_addr_cache = None
        self.assertEqual(self.request.remote_addr, "127.0.0.1")

    def test_remote_addr_ipv6(self):
        # Mock IPv6: ::1 -> 15 nulls + 1
        ipv6_bytes = b"\x00" * 15 + b"\x01"
        self.mock_res.get_remote_address_bytes.return_value = ipv6_bytes
        self.request._remote_addr_cache = None
        self.assertEqual(self.request.remote_addr, "::1")

    def test_rate_limiter_uses_remote_addr(self):
        # Setup: Real IP is 1.2.3.4
        self.mock_res.get_remote_address_bytes.return_value = socket.inet_pton(
            socket.AF_INET, "1.2.3.4"
        )
        self.request._remote_addr_cache = None

        limiter = RateLimiter()
        middleware = RateLimitMiddleware(limiter)  # No trust_proxy needed

        # Should use remote_addr (1.2.3.4)
        key = middleware._default_key_func(self.request)
        self.assertEqual(key, "1.2.3.4")

    def test_rate_limiter_with_proxy_headers(self):
        # Setup: Real IP is 1.2.3.4, Header says 5.6.7.8 (Spoofed by client?)
        # Or Proxy sends it.
        # If we trust proxy, we resolve.

        self.mock_res.get_remote_address_bytes.return_value = socket.inet_pton(
            socket.AF_INET,
            "1.2.3.4",  # Proxy IP
        )
        self.request._remote_addr_cache = None

        headers = {"x-forwarded-for": "5.6.7.8"}
        self.request.get_header = lambda name, default=None: headers.get(
            name.lower(), default
        )

        # Use ProxyHeadersMiddleware to resolve IP
        proxy_mw = ProxyHeadersMiddleware(trusted_proxies=["1.2.3.4"])
        proxy_mw(self.request, self.mock_res)

        # Should now be 5.6.7.8
        self.assertEqual(self.request.remote_addr, "5.6.7.8")

        # Rate Limiter uses resolved IP
        limiter = RateLimiter()
        rl_mw = RateLimitMiddleware(limiter)
        key = rl_mw._default_key_func(self.request)
        self.assertEqual(key, "5.6.7.8")

    def test_rate_limiter_spoofing_prevention(self):
        # Setup: Proxy IP 10.0.0.1 (Trusted).
        # Attacker injects "8.8.8.8".
        # Proxy appends Real IP "1.2.3.4".
        # Header: "8.8.8.8, 1.2.3.4".

        self.mock_res.get_remote_address_bytes.return_value = socket.inet_pton(
            socket.AF_INET, "10.0.0.1"
        )
        self.request._remote_addr_cache = None

        headers = {"x-forwarded-for": "8.8.8.8, 1.2.3.4"}
        self.request.get_header = lambda name, default=None: headers.get(
            name.lower(), default
        )

        # Use ProxyHeadersMiddleware
        proxy_mw = ProxyHeadersMiddleware(trusted_proxies=["10.0.0.1"])
        proxy_mw(self.request, self.mock_res)

        # Should resolve to 1.2.3.4
        self.assertEqual(self.request.remote_addr, "1.2.3.4")

        # Rate Limiter
        limiter = RateLimiter()
        rl_mw = RateLimitMiddleware(limiter)
        key = rl_mw._default_key_func(self.request)
        self.assertEqual(key, "1.2.3.4")


if __name__ == "__main__":
    unittest.main()

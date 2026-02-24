import socket
from unittest.mock import Mock

from xyra.middleware.proxy_headers import ProxyHeadersMiddleware, proxy_headers
from xyra.request import Request


def create_request(remote_addr, headers=None):
    req = Mock()
    res = Mock()

    # Mock remote_addr
    # Request uses res.get_remote_address_bytes()
    try:
        if ":" in remote_addr:
            addr_bytes = socket.inet_pton(socket.AF_INET6, remote_addr)
        else:
            addr_bytes = socket.inet_pton(socket.AF_INET, remote_addr)
    except OSError:
        addr_bytes = b""

    res.get_remote_address_bytes.return_value = addr_bytes

    # Mock headers - normalize to lowercase keys as Request expects
    headers = {k.lower(): v for k, v in (headers or {}).items()}
    req.get_header.side_effect = lambda k, default=None: headers.get(k, default)

    # Create Request
    request = Request(req, res)
    return request, res


def test_proxy_headers_basic():
    # Trusted proxy 10.0.0.1, Client 1.2.3.4
    request, response = create_request("10.0.0.1", {"X-Forwarded-For": "1.2.3.4"})

    mw = proxy_headers(["10.0.0.1"])
    mw(request, response)

    assert request.remote_addr == "1.2.3.4"


def test_proxy_headers_untrusted_source():
    # Untrusted source 8.8.8.8 sends XFF
    request, response = create_request("8.8.8.8", {"X-Forwarded-For": "1.2.3.4"})

    mw = ProxyHeadersMiddleware(["10.0.0.1"])
    mw(request, response)

    # Should ignore XFF because source is not trusted
    assert request.remote_addr == "8.8.8.8"


def test_proxy_headers_cidr():
    # Trusted CIDR 10.0.0.0/8
    request, response = create_request("10.0.0.5", {"X-Forwarded-For": "1.2.3.4"})

    mw = ProxyHeadersMiddleware(["10.0.0.0/8"])
    mw(request, response)

    assert request.remote_addr == "1.2.3.4"


def test_proxy_headers_chain():
    # Chain: Client (1.1.1.1) -> Proxy1 (2.2.2.2) -> Proxy2 (10.0.0.1) -> App
    # App trusts 10.0.0.1. Proxy2 sets XFF: 1.1.1.1, 2.2.2.2

    request, response = create_request(
        "10.0.0.1", {"X-Forwarded-For": "1.1.1.1, 2.2.2.2"}
    )

    mw = ProxyHeadersMiddleware(["10.0.0.1"])
    mw(request, response)

    # Logic:
    # Remote: 10.0.0.1 (Trusted)
    # Check 2.2.2.2 (Last in XFF). Trusted? No.
    # Result: 2.2.2.2

    assert request.remote_addr == "2.2.2.2"


def test_proxy_headers_chain_recursive_trust():
    # Chain: Client (1.1.1.1) -> Proxy1 (10.0.0.2) -> Proxy2 (10.0.0.1) -> App
    # App trusts 10.0.0.0/8.

    request, response = create_request(
        "10.0.0.1", {"X-Forwarded-For": "1.1.1.1, 10.0.0.2"}
    )

    mw = ProxyHeadersMiddleware(["10.0.0.0/8"])
    mw(request, response)

    # Logic:
    # Remote: 10.0.0.1 (Trusted)
    # Check 10.0.0.2. Trusted? Yes.
    # Check 1.1.1.1. Trusted? No.
    # Result: 1.1.1.1

    assert request.remote_addr == "1.1.1.1"


def test_proxy_headers_trust_all():
    # Trust all proxies (*)
    # Default count is 1.
    # Remote: 8.8.8.8 (Trusted).
    # XFF: 1.2.3.4.
    # Check 1.2.3.4. Count=1. Max hops=0.
    # Hops=0. 0 < 0 False.
    # Result: 1.2.3.4.

    request, response = create_request("8.8.8.8", {"X-Forwarded-For": "1.2.3.4"})

    mw = ProxyHeadersMiddleware(["*"])
    mw(request, response)

    assert request.remote_addr == "1.2.3.4"


def test_proxy_headers_invalid_xff():
    request, response = create_request(
        "10.0.0.1", {"X-Forwarded-For": "invalid, 1.2.3.4"}
    )
    mw = ProxyHeadersMiddleware(["10.0.0.1"])
    mw(request, response)

    # "1.2.3.4" is valid, but "invalid" is not.
    # Logic:
    # Check 1.2.3.4. Trusted? No.
    # Result: 1.2.3.4

    assert request.remote_addr == "1.2.3.4"


def test_proxy_headers_fully_invalid_xff():
    request, response = create_request("10.0.0.1", {"X-Forwarded-For": "invalid"})
    mw = ProxyHeadersMiddleware(["10.0.0.1"])
    mw(request, response)
    assert request.remote_addr == "10.0.0.1"


def test_proxy_headers_spoofing_attempt():
    # Attacker (1.2.3.4) sends XFF: 8.8.8.8
    # 1.2.3.4 is NOT trusted.
    request, response = create_request("1.2.3.4", {"X-Forwarded-For": "8.8.8.8"})

    mw = ProxyHeadersMiddleware(["10.0.0.1"])
    mw(request, response)

    assert request.remote_addr == "1.2.3.4"


def test_proxy_headers_ipv6():
    # IPv6 Trusted
    request, response = create_request("::1", {"X-Forwarded-For": "2001:db8::1"})

    mw = ProxyHeadersMiddleware(["::1"])
    mw(request, response)

    assert request.remote_addr == "2001:db8::1"


def test_proxy_headers_mixed_ipv4_ipv6():
    # Remote: ::1 (trusted)
    # XFF: 1.2.3.4, 2001:db8::2 (trusted)
    request, response = create_request(
        "::1", {"X-Forwarded-For": "1.2.3.4, 2001:db8::2"}
    )

    # Trust ::1 and 2001:db8::/32
    mw = ProxyHeadersMiddleware(["::1", "2001:db8::/32"])
    mw(request, response)

    # Logic:
    # Check 2001:db8::2 (Trusted)
    # Check 1.2.3.4 (Untrusted)
    # Result: 1.2.3.4

    assert request.remote_addr == "1.2.3.4"


def test_proxy_headers_internal_client():
    # Remote: 10.0.0.1 (Trusted)
    # XFF: 10.0.0.2 (Trusted)
    # All trusted. Should pick the first one (originator)
    request, response = create_request("10.0.0.1", {"X-Forwarded-For": "10.0.0.2"})

    mw = ProxyHeadersMiddleware(["10.0.0.0/8"])
    mw(request, response)

    assert request.remote_addr == "10.0.0.2"


def test_proxy_headers_garbage_remote_addr():
    # Remote addr is unknown/garbage
    request, response = create_request("unknown", {"X-Forwarded-For": "1.2.3.4"})

    mw = ProxyHeadersMiddleware(["10.0.0.0/8"])
    mw(request, response)

    assert request.remote_addr == "unknown"


def test_proxy_headers_trust_all_with_spoofing():
    # Scenario: LB (Trusted) receives request from Attacker.
    # Attacker sends XFF: Spoofed.
    # LB appends AttackerIP.
    # XFF: Spoofed, AttackerIP.
    # trust_all=True ("*").
    # Default trusted_proxy_count=1 (trusts LB).
    # Expected: AttackerIP.

    request, response = create_request(
        "10.0.0.1", {"X-Forwarded-For": "1.2.3.4, 5.6.7.8"}
    )

    # 10.0.0.1 is LB.
    # 5.6.7.8 is Attacker (Real).
    # 1.2.3.4 is Spoofed.

    mw = ProxyHeadersMiddleware(["*"])  # Default count=1
    mw(request, response)

    # Should stop at 5.6.7.8
    assert request.remote_addr == "5.6.7.8"


def test_proxy_headers_trust_all_with_count():
    # Scenario: LB -> Proxy1 -> Client.
    # App sees LB.
    # XFF: Client, Proxy1.
    # trust_all=True. trusted_proxy_count=2.

    request, response = create_request(
        "10.0.0.1", {"X-Forwarded-For": "1.1.1.1, 2.2.2.2"}
    )

    mw = ProxyHeadersMiddleware(["*"], trusted_proxy_count=2)
    mw(request, response)

    # 1. Trust LB (implicit).
    # 2. Trust Proxy1 (2.2.2.2) (count=2 means 1 additional hop).
    # Result: Client (1.1.1.1).

    assert request.remote_addr == "1.1.1.1"


def test_proxy_headers_trust_all_count_exceeded():
    # Scenario: LB -> Client.
    # XFF: Client.
    # trusted_proxy_count=5.

    request, response = create_request("10.0.0.1", {"X-Forwarded-For": "1.1.1.1"})

    mw = ProxyHeadersMiddleware(["*"], trusted_proxy_count=5)
    mw(request, response)

    # Should fall back to first IP (Client)
    assert request.remote_addr == "1.1.1.1"


def test_proxy_headers_host_poisoning():
    # Trusted proxies: 3 (Trust P3, P2, P1)
    # Remote Addr is P3 (10.0.0.3). XFF: Client, P1, P2.
    # XFH: Evil. (len 1).
    # peeled_count = 2 (P1, P2 peeled from XFF).
    # target_index = 1 - 1 - 2 = -2.
    # Should be None (ignored).

    request, response = create_request(
        "10.0.0.3",
        {
            "X-Forwarded-For": "1.2.3.4, 10.0.0.1, 10.0.0.2",
            "X-Forwarded-Host": "evil.com",
            "Host": "internal-service",
        },
    )

    mw = ProxyHeadersMiddleware(["*"], trusted_proxy_count=3)
    mw(request, response)

    assert request._host_cache is None


def test_proxy_headers_valid_minus_one_case():
    # Case where target_index is -1 (valid).
    # XFF: Client, P1. (peeled_count=1).
    # XFH: ClientHost. (len 1).
    # target_index = 1 - 1 - 1 = -1.
    # Should return ClientHost.

    request, response = create_request(
        "10.0.0.2",
        {
            "X-Forwarded-For": "1.2.3.4, 10.0.0.1",
            "X-Forwarded-Host": "client.com",
            "Host": "internal-service",
        },
    )

    mw = ProxyHeadersMiddleware(["*"], trusted_proxy_count=2)
    mw(request, response)

    assert request._host_cache == "client.com"

def test_proxy_headers_valid_chain_resolution():
    request, response = create_request(
        "10.0.0.2",
        {
            "X-Forwarded-For": "1.2.3.4, 10.0.0.1",
            "X-Forwarded-Host": "client.com, proxy1.com",
            "Host": "internal-service",
        },
    )

    mw = ProxyHeadersMiddleware(["*"], trusted_proxy_count=2)
    mw(request, response)

    assert request._host_cache == "client.com"

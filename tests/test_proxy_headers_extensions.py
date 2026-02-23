import socket
from unittest.mock import Mock

from xyra.middleware.proxy_headers import ProxyHeadersMiddleware, proxy_headers
from xyra.request import Request


def create_request(remote_addr, headers=None):
    req = Mock()
    res = Mock()

    try:
        if ":" in remote_addr:
            addr_bytes = socket.inet_pton(socket.AF_INET6, remote_addr)
        else:
            addr_bytes = socket.inet_pton(socket.AF_INET, remote_addr)
    except OSError:
        addr_bytes = b""

    res.get_remote_address_bytes.return_value = addr_bytes

    headers = {k.lower(): v for k, v in (headers or {}).items()}
    req.get_header.side_effect = lambda k, default=None: headers.get(k, default)
    # Mock get_headers for Request.headers property
    req.get_headers.return_value = headers

    request = Request(req, res)
    return request, res


def test_proxy_headers_scheme_host_port():
    # Client (1.2.3.4) -> Nginx (10.0.0.1) -> App
    # Remote Addr: 10.0.0.1
    # XFF: 1.2.3.4
    # XFP: https
    # XFH: example.com
    # XFPort: 443

    request, response = create_request(
        "10.0.0.1",
        {
            "x-forwarded-for": "1.2.3.4",
            "x-forwarded-proto": "https",
            "x-forwarded-host": "example.com",
            "x-forwarded-port": "443",
            "host": "internal-lb:8080",
        },
    )

    mw = proxy_headers(["10.0.0.1"])
    mw(request, response)

    assert request.remote_addr == "1.2.3.4"
    assert request.scheme == "https"
    assert request.host == "example.com"
    assert request.port == 443


def test_proxy_headers_chain_scheme():
    # Chain: Client (1.1.1.1) -> Proxy1 (10.0.0.2) -> Proxy2 (10.0.0.1) -> App
    # Trusted: Proxy2, Proxy1.
    # XFF: 1.1.1.1, 10.0.0.2
    # XFP: http, https
    # Proxy2 sets remote_addr=10.0.0.1.

    request, response = create_request(
        "10.0.0.1",
        {
            "x-forwarded-for": "1.1.1.1, 10.0.0.2",
            "x-forwarded-proto": "http, https",
            "host": "internal-lb:8080",
        },
    )

    # Trust both proxies
    mw = proxy_headers(["10.0.0.1", "10.0.0.2"])
    mw(request, response)

    # Should resolve to 1.1.1.1
    # Should resolve scheme to "http" (first one)
    assert request.remote_addr == "1.1.1.1"
    assert request.scheme == "http"


def test_proxy_headers_malformed_proto():
    # XFP is malformed or missing
    request, response = create_request(
        "10.0.0.1",
        {
            "x-forwarded-for": "1.2.3.4",
            "host": "localhost:8000",
        },
    )

    mw = proxy_headers(["10.0.0.1"])
    mw(request, response)

    # Should default to http
    assert request.scheme == "http"


def test_proxy_headers_trust_all_scheme():
    # Trust all (*)
    # Remote: 10.0.0.1 (Trusted)
    # XFF: 1.2.3.4
    # XFP: https

    request, response = create_request(
        "10.0.0.1",
        {
            "x-forwarded-for": "1.2.3.4",
            "x-forwarded-proto": "https",
        },
    )

    mw = proxy_headers(["*"])
    mw(request, response)

    assert request.scheme == "https"

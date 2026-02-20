"""
Proxy Headers Middleware for Xyra Framework

Safely resolves the client IP address when running behind trusted proxies.
"""

from ipaddress import ip_address, ip_network

from ..logger import get_logger
from ..request import Request
from ..response import Response


class ProxyHeadersMiddleware:
    """
    Middleware for correctly resolving client IP addresses when behind trusted proxies.

    This middleware inspects the X-Forwarded-For header to determine the real client IP,
    but only if the request comes from a trusted proxy. This prevents IP spoofing attacks.
    """

    def __init__(self, trusted_proxies: list[str], trusted_proxy_count: int | None = None):
        """
        Initialize proxy headers middleware.

        Args:
            trusted_proxies: List of trusted proxy IPs or CIDR networks.
                             Examples: ["127.0.0.1", "10.0.0.0/8", "::1"]
                             Use "*" to trust all proxies (NOT RECOMMENDED for production unless
                             the server is only reachable via a trusted load balancer).
            trusted_proxy_count: Number of trusted proxies in the chain.
                                 Required if using "*" in trusted_proxies to prevent IP spoofing.
                                 Defaults to 1 if "*" is used and count is not provided.
        """
        self.trust_all = "*" in trusted_proxies
        self.trusted_networks = []
        self.trusted_proxy_count = trusted_proxy_count

        if self.trust_all:
            if self.trusted_proxy_count is None:
                logger = get_logger("xyra")
                logger.warning(
                    "🚨 Security Warning: ProxyHeadersMiddleware configured with '*' but "
                    "no 'trusted_proxy_count'. Defaulting to 1 (only the immediate proxy is trusted). "
                    "To trust more proxies, set 'trusted_proxy_count' explicitly."
                )
                self.trusted_proxy_count = 1

            # Ensure count is at least 1
            if self.trusted_proxy_count < 1:
                self.trusted_proxy_count = 1
        else:
            for proxy in trusted_proxies:
                try:
                    # Support both single IPs and CIDR networks
                    # strict=False allows host bits to be set (e.g., 192.168.1.1/24)
                    # and also handles single IPs correctly (e.g., 127.0.0.1 -> /32)
                    network = ip_network(proxy, strict=False)
                    self.trusted_networks.append(network)
                except ValueError:
                    # Invalid IP/CIDR, skip it
                    continue

    def _is_trusted(self, ip_str: str) -> bool:
        """Check if an IP address is trusted."""
        if self.trust_all:
            return True

        try:
            ip = ip_address(ip_str)
            for network in self.trusted_networks:
                if ip in network:
                    return True
            return False
        except ValueError:
            return False

    def __call__(self, req: Request, res: Response) -> None:
        """
        Resolve the real client IP from X-Forwarded-For headers.

        Logic:
        1. Start with the connecting IP (remote_addr).
        2. If trusted, inspect X-Forwarded-For header.
        3. Parse the list of IPs in X-Forwarded-For (Client, Proxy1, Proxy2...).
        4. Iterate backwards from the last proxy.
        5. If an IP is trusted, move to the previous one.
        6. The first untrusted IP found (from right to left) is the real client IP.
        """
        remote_addr = req.remote_addr

        # If the immediate connection is not trusted, do nothing
        if not self._is_trusted(remote_addr):
            return

        xff = req.get_header("x-forwarded-for")
        if not xff:
            return

        # Parse XFF list
        try:
            # Split by comma and strip whitespace
            # XFF format: client, proxy1, proxy2
            ips = [ip.strip() for ip in xff.split(",")]
        except Exception:
            return

        if not ips:
            return

        # Walk backwards through the chain
        # We start by assuming the last IP in the list is the one that connected to us
        # (if trusted). If trusted, we check the one before it.
        # The first untrusted IP we encounter is the client IP.

        client_ip = remote_addr  # Default fallback if logic fails or all trusted

        if self.trust_all:
            # SECURITY: If trusting all, we rely on trusted_proxy_count to limit recursion.
            # Without this, we would trust every IP in the chain, allowing spoofing.
            # We trust 'remote_addr' (the immediate proxy) plus (trusted_proxy_count - 1) proxies in the header.
            hops = 0
            # trusted_proxy_count is at least 1.
            # max_hops = trusted_proxy_count - 1
            max_hops = self.trusted_proxy_count - 1  # type: ignore

            for ip in reversed(ips):
                if hops < max_hops:
                    hops += 1
                    continue
                else:
                    client_ip = ip
                    break
            else:
                # If we exhausted the list without finding an untrusted IP (within count limits),
                # it means the chain is shorter than expected or fully trusted.
                # We default to the first IP (originator).
                if ips:
                    client_ip = ips[0]
        else:
            # Standard logic using IP whitelist
            # Iterate right to left
            for ip in reversed(ips):
                if self._is_trusted(ip):
                    continue
                else:
                    client_ip = ip
                    break
            else:
                # All IPs in XFF are trusted (and remote_addr is trusted).
                # This implies the client itself is a trusted entity (e.g. internal service)
                # or the chain is fully trusted.
                # In this case, the "client" is the first IP in the list (the originator).
                if ips:
                    client_ip = ips[0]

        # Update the request's remote_addr cache
        # Validate that the resolved IP is a valid IP string
        try:
            # Ensure it's a valid IP address
            ip_address(client_ip)
            # Set the cache directly
            req._remote_addr_cache = client_ip
        except ValueError:
            pass


def proxy_headers(
    trusted_proxies: list[str], trusted_proxy_count: int | None = None
) -> ProxyHeadersMiddleware:
    """
    Create a proxy headers middleware instance.

    Args:
        trusted_proxies: List of trusted proxy IPs or CIDR networks.
        trusted_proxy_count: Number of trusted proxies (required if using "*").
    """
    return ProxyHeadersMiddleware(trusted_proxies, trusted_proxy_count)

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

    def __init__(
        self, trusted_proxies: list[str], trusted_proxy_count: int | None = None
    ):
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
            # SECURITY: Limit the number of IPs processed to prevent DoS via CPU/Memory exhaustion.
            # We only care about the last few IPs (the trusted chain).
            # 20 hops is more than enough for any reasonable architecture.
            raw_ips = xff.rsplit(",", 20)
            ips = [ip.strip() for ip in raw_ips]
        except Exception:
            return

        if not ips:
            return

        # Walk backwards through the chain
        # We start by assuming the last IP in the list is the one that connected to us
        # (if trusted). If trusted, we check the one before it.
        # The first untrusted IP we encounter is the client IP.

        client_ip = remote_addr  # Default fallback if logic fails or all trusted
        client_index = -1  # Index in the `ips` list (from left) that corresponds to the client

        if self.trust_all:
            # SECURITY: If trusting all, we rely on trusted_proxy_count to limit recursion.
            # Without this, we would trust every IP in the chain, allowing spoofing.
            # We trust 'remote_addr' (the immediate proxy) plus (trusted_proxy_count - 1) proxies in the header.
            hops = 0
            # trusted_proxy_count is at least 1.
            # max_hops = trusted_proxy_count - 1
            max_hops = self.trusted_proxy_count - 1  # type: ignore

            for i in range(len(ips) - 1, -1, -1):
                if hops < max_hops:
                    hops += 1
                    continue
                else:
                    client_ip = ips[i]
                    client_index = i
                    break
            else:
                # If we exhausted the list without finding an untrusted IP (within count limits),
                # it means the chain is shorter than expected or fully trusted.
                # We default to the first IP (originator).
                if ips:
                    client_ip = ips[0]
                    client_index = 0
        else:
            # Standard logic using IP whitelist
            # Iterate right to left
            for i in range(len(ips) - 1, -1, -1):
                if self._is_trusted(ips[i]):
                    continue
                else:
                    client_ip = ips[i]
                    client_index = i
                    break
            else:
                # All IPs in XFF are trusted (and remote_addr is trusted).
                # This implies the client itself is a trusted entity (e.g. internal service)
                # or the chain is fully trusted.
                # In this case, the "client" is the first IP in the list (the originator).
                if ips:
                    client_ip = ips[0]
                    client_index = 0

        # Update the request's remote_addr cache
        # Validate that the resolved IP is a valid IP string
        try:
            # Ensure it's a valid IP address
            ip_address(client_ip)
            # Set the cache directly
            req._remote_addr_cache = client_ip
        except ValueError:
            # SECURITY: If IP is invalid, we MUST NOT leave remote_addr as the trusted proxy IP.
            # This would allow attackers to bypass IP-based rate limits or blocklists by
            # making their requests appear to come from the trusted proxy itself.
            # We set it to "unknown" so they share a single rate limit bucket (or get blocked).
            logger = get_logger("xyra")
            logger.warning(
                f"Security Warning: Resolved client IP '{client_ip}' from trusted proxy is invalid. "
                "Setting remote_addr to 'unknown' to prevent IP spoofing/DoS attribution to proxy."
            )
            req._remote_addr_cache = "unknown"
            return

        # Handle X-Forwarded-Proto, X-Forwarded-Host, X-Forwarded-Port
        # We assume that the proxy chain is consistent for these headers.
        # We use the same 'depth' (peeled proxies) to find the correct value.

        # Number of proxies stripped from the end of the list
        # ips = [Client, Proxy1] (len=2). client_index=0. peeled = 2 - 1 - 0 = 1.
        peeled_count = len(ips) - 1 - client_index

        def get_forwarded_value(header_name: str) -> str | None:
            header_val = req.get_header(header_name)
            if not header_val:
                return None
            try:
                # Split by comma, limit similar to XFF
                values = [v.strip() for v in header_val.rsplit(",", 20)]
                if not values:
                    return None

                # Calculate index from the right
                # target_index = len(values) - 1 - peeled_count
                target_index = len(values) - 1 - peeled_count

                if target_index < 0:
                    # SECURITY: List is shorter than expected based on trusted proxy count.
                    # If target_index == -1, it means the list length matches the peeled count.
                    # This is valid: the first value (values[0]) was added by the furthest trusted proxy we peeled.
                    if target_index == -1:
                        return values[0]

                    # If target_index < -1, it implies multiple trusted proxies did not append to the header.
                    # Returning the first value (values[0]) is unsafe as it might be attacker-controlled
                    # and was not overwritten/appended by the trusted proxies we peeled off.
                    # We return None to ignore this header and fallback to the connection's properties.
                    return None
                return values[target_index]
            except Exception:
                return None

        # Update Scheme
        proto = get_forwarded_value("x-forwarded-proto")
        if proto:
            req._scheme_cache = proto.lower()

        # Update Host
        host = get_forwarded_value("x-forwarded-host")
        if host:
            req._host_cache = host

        # Update Port
        port_str = get_forwarded_value("x-forwarded-port")
        if port_str:
            try:
                req._port_cache = int(port_str)
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

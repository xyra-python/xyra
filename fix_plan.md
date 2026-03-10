Oh! IPv4-mapped IPv6 addresses bypass `ip in network` checks if the `trusted_networks` are IPv4!
Wait, but `ProxyHeadersMiddleware` uses this to determine if the IP is a TRUSTED PROXY.
If an attacker sends an IPv4-mapped IPv6 address from an UNTRUSTED IP... wait, the TCP connection's remote IP is what `request.remote_addr` is.
If the proxy connects using an IPv4-mapped IPv6 address (because the host OS is dual-stack), and the user configured `192.168.1.1` as a trusted proxy, `_is_trusted` will return `False`!
This means the proxy won't be trusted, and its `X-Forwarded-For` won't be parsed! This is a fail-secure bug, not a bypass.

What about `trustedhost.py`?
```python
    def __init__(self, allowed_hosts: list[str]):
        """
        Initialize trusted host middleware.
        """
        # SECURITY: Lowercase allowed hosts to ensure case-insensitive matching
        self.allowed_hosts = [host.lower() for host in allowed_hosts]
        self.allow_all = "*" in self.allowed_hosts

    def _parse_host(self, host: str) -> tuple[str, str | None]:
        # ...
        if host.startswith("["):
            end_index = host.find("]")
            if end_index != -1:
                hostname = host[: end_index + 1]
                port = host[end_index + 2 :] if len(host) > end_index + 2 else None
                if port and port.startswith(":"):
                    port = port[1:]
                return hostname, port
        ...
```
What if `host` is `"[::1]"`? `hostname = "[::1]"`. Does `allowed_hosts` contain `[::1]`? If the user configured it, yes.

What about `cors.py`?
```python
        origin = request.get_header("origin")
        # ...
        if origin and self._is_origin_allowed(origin):
            response.header("Access-Control-Allow-Origin", origin)
```
If an attacker sends an invalid Origin, it won't match, so no CORS headers.
What if `origin` contains CRLF? e.g. `Origin: http://example.com\r\nInjected: Header`
`request.get_header("origin")` reads from `uWebSockets`. `uWebSockets` parses HTTP headers strictly. Wait, what if the origin is explicitly allowed and contains a CRLF? If the origin is in `self.allowed_origins`, it must match exactly. A user won't configure an allowed origin with CRLF.

What if we look at `request.py` `query_params`?
```python
                        self._query_params_cache = parse_qs(
                            query_string, keep_blank_values=True, max_num_fields=1000
                        )
```
In `xyra/request.py`, `Request.json()`
```python
        # SECURITY: Strictly validate Content-Type before parsing JSON
        content_type = self.get_header("content-type", "")
        content_type_lower = content_type.lower()
        if not content_type_lower or not (
            content_type_lower.startswith("application/json") or
            "+json" in content_type_lower
        ):
            raise ValueError(
                f"Invalid Content-Type for JSON parsing: '{content_type}'. "
                f"Expected 'application/json' or similar '+json' media type. "
                f"This prevents MIME confusion attacks."
            )
```
Wait! What if `content_type` is `text/plain; +json`?
`+json` is in `text/plain; +json`, so it passes!
Is `text/plain; +json` a valid JSON content type?
No! `text/plain` triggers simple cross-origin requests without a preflight (CORS bypass)!
If an attacker sends a POST request with `Content-Type: text/plain; +json` to a sensitive API endpoint, the browser WILL SEND IT without a preflight!
Then `request.json()` sees `+json` in `content_type_lower`, bypasses the check, and parses the JSON!
This completely bypasses CORS preflight protections for JSON endpoints!
This is a HIGH severity CSRF/CORS vulnerability!

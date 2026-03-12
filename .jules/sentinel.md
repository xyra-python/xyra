
## 2023-10-27 - [TOCTOU in Static File Handler]
**Vulnerability:** A Time-of-Check to Time-of-Use (TOCTOU) vulnerability existed in `xyra/application.py` where `os.path.exists()`, `os.path.isfile()`, and `os.path.getsize()` were checked sequentially before the file was opened with `open(..., "rb")`. An attacker could potentially swap a benign file for a malicious symlink between the check and the open.
**Learning:** Checking file properties and then opening it creates a race condition window.
**Prevention:** Open the file first, then use `os.fstat(f.fileno())` to check its properties (size, type) using the file descriptor. This ensures the properties checked belong to the exact file being read.

## 2023-10-29 - [Host Header Injection Bypass in TrustedHostMiddleware]
**Vulnerability:** `TrustedHostMiddleware` was reading the raw `Host` header via `req.get_header("host")` instead of the validated `req.host` / `req.port` attributes populated by `ProxyHeadersMiddleware`. When behind a reverse proxy, an attacker could bypass the allowlist by injecting a malicious `X-Forwarded-Host` while the middleware validated the proxy's internal `Host` header.
**Learning:** Relying on raw HTTP headers when framework abstractions securely resolve proxy state creates architectural disjoints that lead to security bypasses.
**Prevention:** Middleware that validates derived request state (like host, IP, or scheme) must exclusively rely on the framework's internal securely-resolved properties (`req.host`, `req.port`, `req.scheme`, `req.remote_addr`) rather than fetching raw header strings.
# Sentinel Security Journal

## 2025-02-04 - CSRF Origin Check Bypass on HTTPS
**Vulnerability pattern:** `CSRFMiddleware` skipped Origin/Referer verification on HTTPS if `secure=False` was configured (default), relying solely on token check.
**Learned constraint:** Always auto-detect HTTPS context (via `request.scheme`) to enforce strict Origin checks, regardless of user configuration.
**Prevention:** Use `is_https = self.secure or request.scheme == "https"` to determine secure context dynamically. Also ensure `request.host` and `request.port` (which respect `ProxyHeadersMiddleware`) are used for constructing expected Origin, rather than raw `Host` header.

## 2025-02-04 - Default CSP in Security Headers
**Vulnerability pattern:** `SecurityHeadersMiddleware` defaulted to no CSP, leaving applications vulnerable to XSS/Injection by default.
**Learned constraint:** Framework helper methods (like `enable_security_headers`) should provide safe defaults (e.g., `object-src 'none'; base-uri 'self'`) rather than empty policies.
**Prevention:** Set `content_security_policy` default in `App.enable_security_headers` if not provided.

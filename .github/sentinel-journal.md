# Sentinel Security Journal

## 2025-05-23 – Manual cookie string concatenation caused attribute injection
**Vulnerability pattern:** `set_cookie` constructed headers via f-string `"{name}={value}"`, allowing injection of attributes like `; HttpOnly` via `value`.
**Learned constraint:** Always use `http.cookies.SimpleCookie` for cookie serialization, even if manual concatenation seems faster.
**Prevention:** `SimpleCookie` handles escaping and quoting correctly.

## 2025-05-23 – Header Injection (CRLF) in `Response.header`
**Vulnerability pattern:** `Response.header` blindly accepted keys/values containing `\r\n`, allowing response splitting.
**Learned constraint:** Explicitly reject `\r` and `\n` in header setters.
**Prevention:** Added validation in `Response.header`.

## 2025-05-23 – IP Spoofing in Rate Limit Middleware via X-Forwarded-For
**Vulnerability pattern:** `trust_proxy=True` trusted the left-most IP in `X-Forwarded-For` (`split(",")[0]`), which is attacker-controlled when proxies append.
**Learned constraint:** Always pick the IP from the right side (n-th from right) when parsing `X-Forwarded-For` behind proxies that append headers.
**Prevention:** Introduced `trusted_proxy_count` to safely select the correct client IP.

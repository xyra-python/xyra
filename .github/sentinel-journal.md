## 2025-05-18 – Python SimpleCookie Attribute Injection
**Vulnerability pattern:** `http.cookies.SimpleCookie` does not validate or quote `path` and `domain` attributes, allowing injection of other cookie flags (e.g. overwriting `HttpOnly`).
**Learned constraint:** Always validate `path` and `domain` for `;` and control characters before passing to `SimpleCookie`.
**Prevention:** Enforce strict allow-list or deny-list on cookie attribute values.

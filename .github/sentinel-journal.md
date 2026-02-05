## 2025-05-23 – SimpleCookie attribute injection risk
**Vulnerability pattern:** `http.cookies.SimpleCookie` does not validate attribute values (Path, Domain) against `;`, allowing attribute injection.
**Learned constraint:** Always validate user-controlled Path/Domain inputs before passing them to `set_cookie` or `SimpleCookie`.
**Prevention:** Explicit validation for `;`, `\r`, `\n` in sensitive cookie attributes.

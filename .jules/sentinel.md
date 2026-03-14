
## 2025-02-04 - Insecure CORS Wildcard with Credentials
**Vulnerability:** `Response.cors()` permitted setting `Access-Control-Allow-Origin: *` while simultaneously setting `Access-Control-Allow-Credentials: true`. This exposes applications to severe CORS misconfiguration where any origin can make authenticated cross-origin requests.
**Learning:** Even utility methods for HTTP responses must validate the security constraints of the headers they emit, not just middleware.
**Prevention:** Hardcoded validation in `Response.cors` to check if `origin == "*"` and `credentials == True`. If so, it logs a warning and disables credentials (`credentials = False`).

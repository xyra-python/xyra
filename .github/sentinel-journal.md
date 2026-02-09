# Sentinel Journal

## 2025-02-18 – Middleware Bypass on 404 Handlers
**Vulnerability pattern:** Registering a catch-all (404) handler directly with the underlying native app bypasses the framework's middleware stack.
**Learned constraint:** All route handlers, including error handlers and catch-alls, must be wrapped using `_create_final_handler` or equivalent middleware application logic.
**Prevention:** Ensure `not_found_handler` is treated as a standard route handler in `xyra/application.py`.

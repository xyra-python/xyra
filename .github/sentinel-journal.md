# Sentinel Security Journal

## 2025-05-23 – Global Middleware Bypass on 404/Not Found Handler
**Vulnerability pattern:** Framework-internal error handlers (like 404/500) defined outside the standard route registration pipeline bypass global middleware.
**Learned constraint:** Error handlers must be explicitly wrapped with the application's middleware stack (`_create_final_handler`) to ensure security controls (Rate Limit, CORS, Security Headers) apply to error responses.
**Prevention:** Audit all `app.any` or manual route registrations to ensure they go through the middleware wrapping logic.

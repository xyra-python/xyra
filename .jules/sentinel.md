## 2026-04-08 - Escape HTML in Inline Scripts
**Vulnerability:** XSS vulnerability in Swagger UI caused by injecting user-controlled paths into inline script blocks using `json.dumps()`.
**Learning:** `json.dumps()` securely escapes quotes, but it does not encode HTML tags like `<` or `>`. When rendering a script tag (`<script>`), if an attacker controls input mapped to JSON, they can inject `</script><script>alert(1)</script>`. The browser parses the `</script>` tag and terminates the script context immediately, falling back to HTML context which then executes the payload.
**Prevention:** When embedding JSON content within an inline `<script>` tag in HTML templates, replace `<` with `\u003c` or use a dedicated HTML-safe JSON encoder.

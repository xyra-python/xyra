
import json

from xyra import App
from xyra.middleware.cors import CorsMiddleware
from xyra.middleware.security_headers import SecurityHeadersMiddleware


# Mock classes
class MockRequest:
    def __init__(self, headers=None, method="GET"):
        self.headers = headers or {}
        self.method = method

    def get_header(self, name):
        return self.headers.get(name.lower())

class MockResponse:
    def __init__(self):
        self._headers = {}
        self._status_code = 200
        self._body = None
        self._ended = False
        self.templates = None

    def header(self, key, value):
        self._headers[key] = value

    def status(self, code):
        self._status_code = code
        return self

    def send(self, body):
        self._body = body
        self._ended = True

    def json(self, data):
        self._body = json.dumps(data)
        self._ended = True

    def html(self, content):
        self._body = content
        self._ended = True

# --- Tests ---

def test_cors_secure_wildcard():
    """Test that CORS does NOT reflect origin when wildcard is used with credentials."""
    middleware = CorsMiddleware(allowed_origins=["*"], allow_credentials=True)
    req = MockRequest({"origin": "http://evil.com"})
    res = MockResponse()

    middleware(req, res)

    assert "Access-Control-Allow-Origin" not in res._headers
    assert res._headers.get("Access-Control-Allow-Credentials") == "true"

def test_cors_allowed_origin():
    """Test that CORS reflects origin when explicitly allowed."""
    middleware = CorsMiddleware(allowed_origins=["http://good.com"], allow_credentials=True)
    req = MockRequest({"origin": "http://good.com"})
    res = MockResponse()

    middleware(req, res)

    assert res._headers.get("Access-Control-Allow-Origin") == "http://good.com"
    assert res._headers.get("Access-Control-Allow-Credentials") == "true"

def test_cors_wildcard_no_creds():
    """Test that CORS allows wildcard when credentials are NOT allowed."""
    middleware = CorsMiddleware(allowed_origins=["*"], allow_credentials=False)
    req = MockRequest({"origin": "http://any.com"})
    res = MockResponse()

    middleware(req, res)

    # Behavior depends on implementation: either reflect origin or send *
    # The code says:
    # if origin in allowed: return origin
    # elif "*" in allowed: return "*"

    # Since "http://any.com" is not in allowed list (only "*"), it hits the elif.
    # Actually, the implementation prefers reflecting the origin if it is allowed.
    # So it might return the origin itself.
    allowed_origin = res._headers.get("Access-Control-Allow-Origin")
    assert allowed_origin == "http://any.com" or allowed_origin == "*"

def test_security_headers_default():
    """Test default security headers."""
    middleware = SecurityHeadersMiddleware()
    req = MockRequest()
    res = MockResponse()

    middleware(req, res)

    assert res._headers.get("X-Content-Type-Options") == "nosniff"
    assert res._headers.get("X-Frame-Options") == "SAMEORIGIN"
    assert res._headers.get("X-XSS-Protection") == "1; mode=block"
    assert res._headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"

def test_security_headers_hsts():
    """Test HSTS headers."""
    middleware = SecurityHeadersMiddleware(hsts_seconds=31536000, hsts_include_subdomains=True, hsts_preload=True)
    req = MockRequest()
    res = MockResponse()

    middleware(req, res)

    assert res._headers.get("Strict-Transport-Security") == "max-age=31536000; includeSubDomains; preload"

def test_swagger_xss_protection():
    """Test that Swagger UI path is properly escaped."""
    # We use a weird path that would cause XSS if not escaped
    dangerous_path = '"; alert(1); "'
    app = App(swagger_options={"swagger_json_path": dangerous_path, "swagger_ui_path": "/docs"})
    app.enable_swagger()

    # Find the route handler for /docs
    handler = None
    for route in app.router.routes:
        if route["path"] == "/docs":
            handler = route["handler"]
            break

    assert handler is not None

    req = MockRequest()
    res = MockResponse()

    # Run the handler
    handler(req, res)

    assert res._body is not None
    html_content = res._body

    # Check that it contains the JSON encoded version
    expected = json.dumps(dangerous_path)
    assert f"url: {expected}" in html_content
    # Check that it does NOT contain the raw injection
    assert f'url: "{dangerous_path}"' not in html_content

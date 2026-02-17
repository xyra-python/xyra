import logging

from xyra.middleware.cors import CorsMiddleware


class MockRequest:
    def __init__(self, headers):
        self._headers = headers
        self.method = "GET"

    def get_header(self, name):
        return self._headers.get(name.lower())


from multidict import CIMultiDict


class MockResponse:
    def __init__(self):
        self.headers_dict = {}
        self.headers = CIMultiDict()
        self._ended = False

    def header(self, name, value):
        self.headers_dict[name] = value
        self.headers[name] = value

    def status(self, code):
        pass

    def send(self, body):
        pass


def test_cors_wildcard_reflection_with_credentials_blocked(caplog):
    # Vulnerable config: allow_credentials=True + allowed_origins="*"
    # Should now trigger warning and block wildcard matching

    with caplog.at_level(logging.WARNING, logger="xyra"):
        middleware = CorsMiddleware(allowed_origins=["*"], allow_credentials=True)

    # Check if warning was logged
    assert "Security Warning" in caplog.text
    assert "Wildcard origin is ignored" in caplog.text

    req = MockRequest(headers={"origin": "http://evil.com"})
    res = MockResponse()

    # Cast to behave like real types
    middleware(req, res)

    # Check if origin was reflected
    # It should NOT be reflected now.
    assert res.headers_dict.get("Access-Control-Allow-Origin") is None

    # Credentials header should NOT be set if origin is not allowed (Defense in Depth).
    assert res.headers_dict.get("Access-Control-Allow-Credentials") is None


def test_cors_explicit_origin_with_credentials():
    # Safe config: explicit origin
    middleware = CorsMiddleware(
        allowed_origins=["http://good.com"], allow_credentials=True
    )

    req = MockRequest(headers={"origin": "http://good.com"})
    res = MockResponse()

    middleware(req, res)

    assert res.headers_dict.get("Access-Control-Allow-Origin") == "http://good.com"
    assert res.headers_dict.get("Access-Control-Allow-Credentials") == "true"


def test_cors_wildcard_without_credentials():
    # Safe config: allow_credentials=False + allowed_origins="*"
    middleware = CorsMiddleware(allowed_origins=["*"], allow_credentials=False)

    req = MockRequest(headers={"origin": "http://any.com"})
    res = MockResponse()

    middleware(req, res)

    # SECURITY: Updated implementation uses '*' directly when wildcard is allowed
    # without credentials, instead of reflecting the origin. This is safer.

    assert res.headers_dict.get("Access-Control-Allow-Origin") == "*"
    # Credentials should not be true (default is False, but we didn't check header presence)
    assert res.headers_dict.get("Access-Control-Allow-Credentials") is None

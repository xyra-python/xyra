import pytest

from xyra.middleware.security_headers import SecurityHeadersMiddleware
from xyra.response import Response


class MockSocketifyResponse:
    def __init__(self):
        self.headers = {}
        self.status_code = 200

    def write_header(self, key, value):
        self.headers[key] = value

    def write_status(self, status):
        self.status_code = int(status)

    def end(self, data):
        pass


def test_permissions_policy_unsafe_value_rejected():
    """
    Test that Permissions-Policy values with unsafe characters (like unquoted closing parenthesis)
    are rejected to prevent header injection.
    """
    # Unsafe value: contains unquoted `)` which could break syntax.
    unsafe_value = "self), camera=(*"

    with pytest.raises(ValueError) as excinfo:
        SecurityHeadersMiddleware(
            permissions_policy={"geolocation": unsafe_value}
        )

    assert "Invalid Permissions-Policy value" in str(excinfo.value)
    assert "unsafe characters" in str(excinfo.value)


def test_permissions_policy_unsafe_list_rejected():
    """
    Test that Permissions-Policy list values with unsafe characters are also rejected.
    """
    unsafe_value = ["self), camera=(*"]

    with pytest.raises(ValueError) as excinfo:
        SecurityHeadersMiddleware(
            permissions_policy={"geolocation": unsafe_value}
        )

    assert "Invalid Permissions-Policy value" in str(excinfo.value)


def test_permissions_policy_safe_values():
    """
    Test that safe values are still accepted.
    """
    # 1. Simple value
    middleware = SecurityHeadersMiddleware(permissions_policy={"geolocation": "self"})
    mock_res_native = MockSocketifyResponse()
    res = Response(mock_res_native)
    middleware(None, res)
    assert "geolocation=(self)" in res.headers["Permissions-Policy"]

    # 2. Wrapped value (backward compat)
    middleware = SecurityHeadersMiddleware(permissions_policy={"geolocation": "(self)"})
    mock_res_native = MockSocketifyResponse()
    res = Response(mock_res_native)
    middleware(None, res)
    assert "geolocation=(self)" in res.headers["Permissions-Policy"]

    # 3. List value (handled by different branch, but good to check)
    middleware = SecurityHeadersMiddleware(permissions_policy={"geolocation": ["self"]})
    mock_res_native = MockSocketifyResponse()
    res = Response(mock_res_native)
    middleware(None, res)
    assert "geolocation=(self)" in res.headers["Permissions-Policy"]

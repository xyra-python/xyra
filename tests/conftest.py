
import sys
from unittest.mock import MagicMock

# Mock libxyra before any test imports xyra
if "xyra.libxyra" not in sys.modules:
    mock_libxyra = MagicMock()
    # Mock parse_path to return valid tuple (native_path, param_names)
    def mock_parse_path(path):
        return path, []

    # Mock format_cookie to behave realistically for unit tests
    def mock_format_cookie(name, value, max_age=None, expires=None, path="/", domain=None, secure=False, http_only=True, same_site="Lax"):
        # Validation
        def has_control(s):
            if not s: return False
            for c in s:
                if (0 <= ord(c) <= 8) or (10 <= ord(c) <= 31) or ord(c) == 127:
                    return True
            return False

        if not name or ";" in name or "=" in name or has_control(name):
             raise ValueError("Invalid cookie name")

        # Value validation: check for control chars first
        if has_control(value):
             # Specific message for control chars in value matches C++ binding
             raise ValueError("Invalid characters in cookie")

        if ";" in value:
            raise ValueError("Cookie value cannot contain ';'")

        # Quoting logic: if contains space, comma, semi-colon (already checked), backslash, double quote
        if any(c in value for c in ' ",;\\'):
             # Escape \ and "
             escaped = value.replace("\\", "\\\\").replace("\"", "\\\"")
             value = f'"{escaped}"'

        if path and (";" in path or has_control(path)):
             raise ValueError("Invalid characters in Path attribute")

        if domain and (";" in domain or has_control(domain)):
             raise ValueError("Invalid characters in Domain attribute")

        parts = [f"{name}={value}"]
        if max_age is not None:
            parts.append(f"Max-Age={max_age}")
        if expires:
            parts.append(f"Expires={expires}")
        if path:
            parts.append(f"Path={path}")
        if domain:
            parts.append(f"Domain={domain}")
        if secure:
            parts.append("Secure")
        if http_only:
            parts.append("HttpOnly")
        if same_site:
            s = str(same_site)
            if s.lower() == "none" and not secure:
                raise ValueError("SameSite=None requires Secure=True")
            if ";" in s or has_control(s):
                 raise ValueError("Invalid characters in SameSite attribute")
            parts.append(f"SameSite={s}")

        return "; ".join(parts)

    mock_libxyra.parse_path.side_effect = mock_parse_path
    mock_libxyra.format_cookie.side_effect = mock_format_cookie

    # Also ensure Request/Response classes are mocks
    sys.modules["xyra.libxyra"] = mock_libxyra

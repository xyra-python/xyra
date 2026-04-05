import sys
from unittest.mock import MagicMock

# Try to import the real native extension; if it fails, mock it.
try:
    import xyra._libxyra  # noqa: F401
    import xyra.libxyra  # noqa: F401
except ImportError:
    mock_libxyra = MagicMock()
    mock__libxyra = MagicMock()

    mock_lib = MagicMock()
    mock_ffi = MagicMock()
    mock__libxyra.lib = mock_lib
    mock__libxyra.ffi = mock_ffi

    # Mock parse_path to return valid tuple (native_path, param_names)
    def mock_parse_path(path):
        return path, []

    # Mock format_cookie to behave realistically for unit tests
    def mock_format_cookie(
        c_name,
        c_value,
        has_max_age,
        max_age,
        c_expires,
        c_path,
        c_domain,
        secure,
        http_only,
        c_samesite,
        out_buf,
        out_len
    ):
        # handle byte strings coming straight from python wrapper
        name = c_name.decode('utf-8') if isinstance(c_name, bytes) else mock_ffi.string(c_name).decode('utf-8')
        value = c_value.decode('utf-8') if isinstance(c_value, bytes) else mock_ffi.string(c_value).decode('utf-8')

        expires = None
        if c_expires != mock_ffi.NULL and c_expires is not None:
             expires = c_expires.decode('utf-8') if isinstance(c_expires, bytes) else mock_ffi.string(c_expires).decode('utf-8')

        path = "/"
        if c_path != mock_ffi.NULL and c_path is not None:
             path = c_path.decode('utf-8') if isinstance(c_path, bytes) else mock_ffi.string(c_path).decode('utf-8')

        domain = None
        if c_domain != mock_ffi.NULL and c_domain is not None:
             domain = c_domain.decode('utf-8') if isinstance(c_domain, bytes) else mock_ffi.string(c_domain).decode('utf-8')

        same_site = "Lax"
        if c_samesite != mock_ffi.NULL and c_samesite is not None:
             same_site = c_samesite.decode('utf-8') if isinstance(c_samesite, bytes) else mock_ffi.string(c_samesite).decode('utf-8')

        # Validation
        def has_control(s):
            if not s:
                return False
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
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            value = f'"{escaped}"'

        if path and (";" in path or has_control(path)):
            raise ValueError("Invalid characters in Path attribute")

        if domain and (";" in domain or has_control(domain)):
            raise ValueError("Invalid characters in Domain attribute")

        # Emulate the quoting from the original mock test
        if any(c in value for c in ' ",;\\'):
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            value = f'"{escaped}"'

        parts = [f"{name}={value}"]
        if has_max_age:
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

        res = "; ".join(parts).encode('utf-8')

        if isinstance(out_len, list):
            out_len[0] = len(res)

        if hasattr(out_buf, '__setitem__'):
            if isinstance(out_buf, bytearray):
                out_buf[:len(res)] = res
            elif isinstance(out_buf, list):
                for i, b in enumerate(res):
                    if i < len(out_buf):
                        out_buf[i] = b

        mock_ffi._last_cookie = res
        return res.decode('utf-8')

    def mock_xyra_format_cookie(c_name, c_value, has_max_age, max_age, c_expires, c_path, c_domain, secure, http_only, c_samesite, out_buf, out_len):
        try:
            mock_format_cookie(c_name, c_value, has_max_age, max_age, c_expires, c_path, c_domain, secure, http_only, c_samesite, out_buf, out_len)
        except ValueError as e:
            if "Invalid characters in header" in str(e):
                out_len[0] = 0
            elif "cannot contain ';'" in str(e):
                out_len[0] = -1
            elif "Invalid characters in Path" in str(e) or "Domain" in str(e) or "SameSite" in str(e):
                out_len[0] = -2
            elif "Invalid characters in cookie" in str(e) or "Invalid cookie name" in str(e):
                out_len[0] = 0

    # Ensure CFFI array sizes work
    def mock_new(cdecl, init=None):
        if cdecl == "size_t*":
            return [1024]
        if cdecl == "char[]":
            return bytearray(1024)
        return b""
    mock_ffi.new.side_effect = mock_new

    mock_ffi.cast.side_effect = lambda t, v: v

    mock_libxyra.parse_path.side_effect = mock_parse_path
    mock_lib.xyra_format_cookie.side_effect = mock_xyra_format_cookie

    def custom_ffi_string(buf, length):
        if isinstance(buf, bytearray):
            return bytes(buf[:length])
        if isinstance(buf, list):
            byte_list = []
            for b in buf[:length]:
                if isinstance(b, bytes):
                    byte_list.append(b)
                elif isinstance(b, int):
                    byte_list.append(bytes([b]))
            return b"".join(byte_list)
        if isinstance(buf, bytes):
            return buf[:length]
        if hasattr(mock_ffi, "_last_cookie"):
            return mock_ffi._last_cookie[:length]
        return b""
    mock_ffi.string.side_effect = custom_ffi_string

    # Also ensure Request/Response classes are mocks
    sys.modules["xyra.libxyra"] = mock_libxyra
    sys.modules["xyra._libxyra"] = mock__libxyra

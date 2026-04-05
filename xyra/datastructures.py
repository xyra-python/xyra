import re

try:
    from multidict import CIMultiDict
except ImportError:
    # Used only during cffi build before requirements are available
    class CIMultiDict(dict):
        pass

try:
    from . import _libxyra
    from ._libxyra import lib
    def has_control_chars(s: str) -> bool:
        b = s.encode('utf-8')
        return lib.xyra_has_control_chars(b, len(b))
except ImportError:
    def has_control_chars(s: str) -> bool:
        # Fallback for tests if CFFI fails to load
        if not s:
            return False
        for c in s:
            if (0 <= ord(c) <= 8) or (10 <= ord(c) <= 31) or ord(c) == 127:
                return True
        return False

# SECURITY: Regex to match control characters except HTAB (\t)
# Matches 0x00-0x08, 0x0A-0x1F, 0x7F
_CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0a-\x1f\x7f]")

# SECURITY: Regex to match control characters except HTAB (\t)
# Matches 0x00-0x08, 0x0A-0x1F, 0x7F
_CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0a-\x1f\x7f]")

class Headers(CIMultiDict):
    """
    A case-insensitive dictionary for HTTP headers.
    It intercepts mutation methods to validate keys and values
    against control characters, preventing HTTP response splitting.
    """

    def _validate(self, key, value):
        if has_control_chars(str(key)) or has_control_chars(str(value)):
            raise ValueError("Invalid characters in header (injection attempt)")

    def __setitem__(self, key, value):
        self._validate(key, value)
        super().__setitem__(key, value)

    def add(self, key, value):
        self._validate(key, value)
        super().add(key, value)

    def setdefault(self, key, default=None):
        self._validate(key, default)
        return super().setdefault(key, default)

    def update(self, *args, **kwargs):
        temp = CIMultiDict(*args, **kwargs)
        for key, value in temp.items():
            self._validate(key, value)
        super().update(temp)

    def extend(self, *args, **kwargs):
        temp = CIMultiDict(*args, **kwargs)
        for key, value in temp.items():
            self._validate(key, value)
        super().extend(temp)

    def __init__(self, *args, **kwargs):
        super().__init__()
        if args or kwargs:
            self.extend(*args, **kwargs)


class QueryParams(CIMultiDict):
    pass

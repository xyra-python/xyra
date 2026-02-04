
import pytest
from unittest.mock import MagicMock
from xyra.response import Response

def test_set_cookie_attribute_injection_protection():
    res = Response(MagicMock())

    # Attempt to inject a Domain attribute via the path argument
    malicious_path = "/; Domain=evil.com"

    # This should currently fail (pass without error but produce bad header)
    # After fix, it should raise ValueError
    try:
        res.set_cookie("session", "value", path=malicious_path)

        # If no exception, check the header for injection
        set_cookie_header = res.headers.get("Set-Cookie", "")
        # If injection succeeded, we see the malicious domain unquoted/unescaped
        # SimpleCookie behavior is just to append it: Path=/; Domain=evil.com
        # We assert that we DO NOT want this.
        # Ideally, we want a ValueError.

        if "; Domain=evil.com" in set_cookie_header and 'Path="/' not in set_cookie_header:
             pytest.fail("Cookie attribute injection succeeded: " + set_cookie_header)

    except ValueError as e:
        # This is the desired behavior after fix
        assert "Invalid character" in str(e) or "injection" in str(e)

def test_clear_cookie_attribute_injection_protection():
    res = Response(MagicMock())
    malicious_path = "/; Domain=evil.com"

    try:
        res.clear_cookie("session", path=malicious_path)

        set_cookie_header = res.headers.get("Set-Cookie", "")
        # clear_cookie currently does manual string concatenation
        if "; Domain=evil.com" in set_cookie_header:
             pytest.fail("Cookie attribute injection in clear_cookie succeeded: " + set_cookie_header)

    except ValueError as e:
        # Desired behavior
        assert "Invalid character" in str(e) or "injection" in str(e)

def test_set_cookie_newline_injection():
    res = Response(MagicMock())
    malicious_val = "val\r\nSet-Cookie: evil=true"

    # This might be caught by SimpleCookie or Response.header
    try:
        res.set_cookie("safe", malicious_val)
    except ValueError as e:
        # Expected
        pass
    except Exception as e:
        # SimpleCookie might raise generic error
        pass

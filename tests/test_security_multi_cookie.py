from unittest.mock import Mock

import pytest

from xyra.response import Response


def test_multiple_cookies():
    mock_res = Mock()
    mock_res.write_header = Mock()

    res = Response(mock_res)
    res.set_cookie("cookie1", "val1")
    res.set_cookie("cookie2", "val2")

    # Check that headers object has both
    # CIMultiDict.getall() returns all values for a key
    cookies = res.headers.getall("Set-Cookie")
    assert len(cookies) == 2
    assert any("cookie1=val1" in c for c in cookies)
    assert any("cookie2=val2" in c for c in cookies)

    # Check that _write_headers calls native write_header twice for Set-Cookie
    res._write_headers()

    # write_header should be called for each cookie
    calls = [call.args for call in mock_res.write_header.call_args_list if call.args[0] == "Set-Cookie"]
    assert len(calls) == 2
    assert any("cookie1=val1" in c[1] for c in calls)
    assert any("cookie2=val2" in c[1] for c in calls)

def test_header_injection_control_chars():
    mock_res = Mock()
    res = Response(mock_res)

    # Test Null Byte
    with pytest.raises(ValueError, match="Invalid characters in header"):
        res.header("X-Header", "value\x00evil")

    # Test other control chars
    with pytest.raises(ValueError, match="Invalid characters in header"):
        res.header("X-Header", "value\x01")

    # Test TAB (should be allowed in values, but Xyra's current regex blocks it)
    # Wait, my regex was [\x00-\x08\x0a-\x1f\x7f]. HTAB is \x09. So HTAB is allowed!
    res.header("X-Header", "value\twith-tab")
    assert res.headers["X-Header"] == "value\twith-tab"

def test_cookie_injection_control_chars():
    mock_res = Mock()
    res = Response(mock_res)

    # Test Null Byte in cookie
    with pytest.raises(ValueError, match="Invalid characters in cookie"):
        res.set_cookie("name", "value\x00evil")

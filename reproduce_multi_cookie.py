from unittest.mock import Mock
import sys

# Mock xyra.libxyra before importing anything from xyra
sys.modules['xyra.libxyra'] = Mock()

from xyra.response import Response

def test_multi_cookie():
    mock_res = Mock()
    mock_res.write_header = Mock()

    res = Response(mock_res)
    res.set_cookie("cookie1", "val1")
    res.set_cookie("cookie2", "val2")

    print(f"Headers after setting 2 cookies: {res.headers}")

    res._write_headers()

    calls = mock_res.write_header.call_args_list
    print(f"Native write_header calls: {calls}")

if __name__ == "__main__":
    test_multi_cookie()

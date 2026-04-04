import sys
try:
    from xyra.libxyra import has_control_chars, parse_form
    print("has_control_chars('hello'):", has_control_chars('hello'))
    print("has_control_chars('hello\\x00'):", has_control_chars('hello\x00'))
    print("parse_form('a=1&b=2'):", parse_form('a=1&b=2'))
except ImportError as e:
    print("Error:", e)

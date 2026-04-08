import timeit
import re

_QUOTE_RE = re.compile(r'["\s,;]')

def quote_any(v):
    if any(c in v for c in ' ",;\t\n\r\x0b\x0c'):
        v = v.replace('"', '\\"')
        return f'"{v}"'
    return v

def quote_re(v):
    if _QUOTE_RE.search(v):
        v = v.replace('"', '\\"')
        return f'"{v}"'
    return v

v_short_no = "helloworld"
v_short_yes = "hello world"
v_long_no = "helloworld" * 10
v_long_yes = "helloworld" * 10 + " "

for name, func in [("baseline", quote_any), ("regex", quote_re)]:
    for v_name, v in [("v_short_no", v_short_no), ("v_short_yes", v_short_yes), ("v_long_no", v_long_no), ("v_long_yes", v_long_yes)]:
        t = timeit.timeit(lambda: func(v), number=1000000)
        print(f"{name:10} {v_name:20}: {t:.3f}")

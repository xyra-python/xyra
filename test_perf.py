import re
import time

_CONTROL_CHARS_PATTERN = re.compile(r"[\x00-\x08\x0a-\x1f\x7f]")

def check_re(s):
    return _CONTROL_CHARS_PATTERN.search(s)

s = "Valid-Header-Name: Valid-Value"
start = time.time()
for _ in range(1000000):
    check_re(s)
print("re:", time.time() - start)

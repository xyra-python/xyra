import re
import time
from xyra.libxyra import has_control_chars

s = "Valid-Header-Name: Valid-Value"
start = time.time()
for _ in range(1000000):
    has_control_chars(s)
print("cpp:", time.time() - start)

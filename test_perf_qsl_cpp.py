import time
from xyra.libxyra import parse_qsl

data = "a=1&b=2&c=3&d=4&e=5&f=6"
start = time.time()
for _ in range(100000):
    parse_qsl(data)
print("cpp parse_qsl:", time.time() - start)

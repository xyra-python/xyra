import time
from xyra.datastructures import Headers

start = time.time()
for _ in range(100000):
    h = Headers()
    h["A"] = "B"
print("cpp headers:", time.time() - start)

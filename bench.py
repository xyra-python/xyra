import timeit

setup = """
class MockIPNetwork:
    def __contains__(self, item):
        return True

class ProxyHeadersMiddleware:
    def __init__(self):
        self.trusted_networks = [MockIPNetwork()]
        self.trust_all = False
    def _is_trusted(self, ip_str: str) -> bool:
        if self.trust_all: return True
        return ip_str == "127.0.0.1"

self = ProxyHeadersMiddleware()
ips = ["1.1.1.1", "127.0.0.1", "127.0.0.1", "127.0.0.1"]
"""

code1 = """
client_ip = ips[0]
client_index = 0
for i in range(len(ips) - 1, -1, -1):
    if self._is_trusted(ips[i]):
        continue
    else:
        client_ip = ips[i]
        client_index = i
        break
"""

code2 = """
client_ip = ips[0]
client_index = 0
for i in reversed(range(len(ips))):
    if not self._is_trusted(ips[i]):
        client_ip = ips[i]
        client_index = i
        break
"""

print("whitelist original loop:", timeit.timeit(code1, setup=setup, number=1000000))
print("whitelist reversed(range):", timeit.timeit(code2, setup=setup, number=1000000))

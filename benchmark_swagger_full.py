import time
import sys
from unittest.mock import Mock

sys.modules['xyra.libxyra'] = Mock()

from xyra.application import App
from xyra.swagger import generate_swagger

def benchmark():
    app = App()

    # Generate 1000 routes with different methods
    def my_handler(req, res):
        """A simple handler."""
        pass

    for i in range(1000):
        path = f"/api/v1/resource_{i}/{{id}}"
        app.get(path, my_handler)
        app.post(path, my_handler)
        app.put(path, my_handler)
        app.delete(path, my_handler)

    start = time.time()
    for _ in range(10):
        generate_swagger(app)
    end = time.time()
    print(f"Time taken for 10 calls: {end - start:.4f} seconds")

if __name__ == "__main__":
    benchmark()

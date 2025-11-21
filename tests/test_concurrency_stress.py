
import asyncio
import unittest
from xyra.application import App
from xyra.request import Request
from xyra.response import Response

# Mocking socketify internals
class MockSocketifyRequest:
    def __init__(self, url, method="GET", params=None):
        self._url = url
        self._method = method
        self._params = params or {}
        self._headers = {}

    def get_method(self): return self._method
    def get_url(self): return self._url
    def for_each_header(self, callback): pass
    def get_parameter(self, idx): return list(self._params.values())[idx] if idx < len(self._params) else None

class MockSocketifyResponse:
    def __init__(self):
        self.ended = False
        self.status = 200
        self.body = None
        self.headers = {}

    def write_header(self, key, val):
        self.headers[key] = val

    def write_status(self, status):
        self.status = int(status)

    def end(self, data):
        self.ended = True
        self.body = data

class TestConcurrencyStress(unittest.TestCase):
    def test_simultaneous_requests(self):
        """
        Test that multiple simultaneous requests do not share state.
        """
        app = App()

        # A route that sleeps to simulate work and increase chance of overlap
        async def handler(req, res):
            req_id = req.get_parameter(0)
            # Store something in request to verify it doesn't leak
            req.my_id = req_id
            await asyncio.sleep(0.01)

            # Verify it's still our ID
            if req.my_id != req_id:
                res.status(500).send("RACE_CONDITION")
            else:
                res.send(req_id)

        final_handler = app._create_final_handler(
            handler, ["id"], [], "/test/{id}"
        )

        async def run_req(i):
            mock_req = MockSocketifyRequest(f"/test/{i}", params={"id": str(i)})
            mock_res = MockSocketifyResponse()
            await final_handler(mock_res, mock_req)
            return mock_res.body

        async def main():
            tasks = [run_req(i) for i in range(100)]
            results = await asyncio.gather(*tasks)
            return results

        results = asyncio.run(main())

        # Verify every request got its own ID back
        for i, res_body in enumerate(results):
            self.assertEqual(res_body, str(i))

if __name__ == "__main__":
    unittest.main()

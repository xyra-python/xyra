import unittest
from unittest.mock import MagicMock
from xyra.request import Request
from xyra.response import Response

class TestRequestUtils(unittest.TestCase):
    def test_full_path(self):
        # Mock native request
        req_mock = MagicMock()
        req_mock.get_url.return_value = "/api/test"
        req_mock.get_query.return_value = "id=123&sort=asc"
        req_mock.get_method.return_value = "GET"

        # Instantiate Request
        req = Request(req_mock, MagicMock())

        # Verify full_path
        self.assertEqual(req.full_path, "/api/test?id=123&sort=asc")

        # Verify caching
        req_mock.get_url.assert_called_once()
        # Request.query calls get_query() once
        # Request.full_path calls self.query once

    def test_full_path_empty_query(self):
        req_mock = MagicMock()
        req_mock.get_url.return_value = "/api/test"
        req_mock.get_query.return_value = ""
        req_mock.get_method.return_value = "GET"

        req = Request(req_mock, MagicMock())

        self.assertEqual(req.full_path, "/api/test")

if __name__ == "__main__":
    unittest.main()

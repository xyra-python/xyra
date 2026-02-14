import os
import sys
import tempfile
import asyncio
import pytest
from unittest.mock import MagicMock

# Ensure libxyra is mocked
if "xyra.libxyra" not in sys.modules:
    sys.modules["xyra.libxyra"] = MagicMock()

from xyra import App, Request, Response

@pytest.mark.asyncio
async def test_static_files_security():
    # Setup temporary directory structure
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create files
        os.makedirs(os.path.join(temp_dir, "public"), exist_ok=True)
        with open(os.path.join(temp_dir, "public", "style.css"), "w") as f:
            f.write("body { color: red; }")

        # Hidden file
        with open(os.path.join(temp_dir, "public", ".env"), "w") as f:
            f.write("SECRET_KEY=123")

        # Hidden directory
        os.makedirs(os.path.join(temp_dir, "public", ".git"), exist_ok=True)
        with open(os.path.join(temp_dir, "public", ".git", "config"), "w") as f:
            f.write("[core]")

        # .well-known (should be allowed)
        os.makedirs(os.path.join(temp_dir, "public", ".well-known"), exist_ok=True)
        with open(os.path.join(temp_dir, "public", ".well-known", "assetlinks.json"), "w") as f:
            f.write("{}")

        app = App()
        app.static_files("/static", os.path.join(temp_dir, "public"))

        # Find handler
        route = next(r for r in app._router.routes if "/static" in r["path"])
        handler = route["handler"]

        # Helper to simulate request
        async def simulate_request(path):
            mock_req = MagicMock(spec=Request)
            # The handler expects get_parameter(0) to return the relative path
            mock_req.get_parameter.return_value = path

            mock_res = MagicMock(spec=Response)
            # Mock header method to store headers
            headers = {}
            def set_header(k, v):
                headers[k] = v
                return mock_res
            mock_res.header.side_effect = set_header
            # Also mock headers.add for vary logic if needed, but static_files uses res.header

            # Mock status
            mock_res.status_code = 200
            def set_status(c):
                mock_res.status_code = c
                return mock_res
            mock_res.status.side_effect = set_status

            await handler(mock_req, mock_res)
            return mock_res, headers

        # Test 1: Normal file
        res, headers = await simulate_request("style.css")
        assert res.status_code == 200, "Normal file should be 200"

        # Check security headers (this assertion will fail until implemented)
        # We comment it out or mark expected failure if we want to check partial progress?
        # No, let's keep it to verify failure.
        assert "X-Content-Type-Options" in headers, "Missing X-Content-Type-Options"
        assert headers["X-Content-Type-Options"] == "nosniff"

        # Test 2: Hidden file (.env) -> Should fail 403 (will be 200 until fixed)
        res, headers = await simulate_request(".env")
        assert res.status_code == 403, "Hidden file should be 403"

        # Test 3: File in hidden directory (.git/config) -> Should fail 403
        res, headers = await simulate_request(".git/config")
        assert res.status_code == 403, "File in hidden dir should be 403"

        # Test 4: .well-known file -> Should succeed 200
        res, headers = await simulate_request(".well-known/assetlinks.json")
        assert res.status_code == 200, ".well-known should be allowed"

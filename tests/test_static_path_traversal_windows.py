import os
import shutil
import tempfile
from unittest.mock import Mock

import pytest

from xyra import App, Request, Response


@pytest.mark.asyncio
async def test_path_traversal_windows_absolute_path_blocked():
    """Test that Windows absolute path traversal attempts are blocked in static file serving."""
    # Setup directories
    temp_dir = tempfile.mkdtemp()
    try:
        static_dir = os.path.join(temp_dir, "static")
        os.makedirs(static_dir)

        # Create safe file
        with open(os.path.join(static_dir, "index.html"), "w") as f:
            f.write("SAFE")

        # Create secret file outside static directory
        secret_path = os.path.join(temp_dir, "secret.txt")
        with open(secret_path, "w") as f:
            f.write("SECRET")

        app = App()
        app.static_files("/static", static_dir)

        # Find the route handler
        route = None
        for r in app.router.routes:
            if r["path"].endswith("*"):
                route = r
                break

        assert route is not None, "Static file route not found"
        handler = route["handler"]

        # Mock Native Request with a Windows absolute path pointing to the secret file
        mock_native_req = Mock()
        mock_native_req.get_method.return_value = "GET"
        mock_native_req.get_url.return_value = f"/static/C:{secret_path}"
        # The wildcard parameter would get C:\temp\secret.txt or similar
        mock_native_req.get_parameter.return_value = f"C:{secret_path}"
        mock_native_req.for_each_header = Mock(side_effect=lambda func: None)

        # Mock Native Response
        mock_native_res = Mock()
        mock_native_res.write_status = Mock()
        mock_native_res.write_header = Mock()
        mock_native_res.end = Mock()

        # Create Xyra Response wrapper
        res = Response(mock_native_res)
        # Create Request using the wrapper as _res (to match current implementation)
        req = Request(mock_native_req, res)

        # Run handler
        await handler(req, res)

        # Check what was sent
        args = mock_native_res.end.call_args
        sent_data = b""
        if args:
            sent_data = args[0][0]
            if isinstance(sent_data, str):
                sent_data = sent_data.encode()

        # Expectation: Should NOT return "SECRET". Should return 404 or similar.
        assert b"SECRET" not in sent_data, (
            "Path Traversal Vulnerability: Secret file content leaked!"
        )

        # Verify status code is 404 or 403
        status_args = mock_native_res.write_status.call_args
        assert status_args is not None, "write_status was never called"
        status = status_args[0][0]
        assert status in ["404", "403"], f"Expected 404/403, got {status}"

    finally:
        shutil.rmtree(temp_dir)

@pytest.mark.asyncio
async def test_path_traversal_windows_drive_relative_path_blocked():
    """Test that Windows drive-relative path traversal attempts are blocked in static file serving."""
    # Setup directories
    temp_dir = tempfile.mkdtemp()
    try:
        static_dir = os.path.join(temp_dir, "static")
        os.makedirs(static_dir)

        # Create safe file
        with open(os.path.join(static_dir, "index.html"), "w") as f:
            f.write("SAFE")

        # Create secret file outside static directory
        secret_path = os.path.join(temp_dir, "secret.txt")
        with open(secret_path, "w") as f:
            f.write("SECRET")

        app = App()
        app.static_files("/static", static_dir)

        # Find the route handler
        route = None
        for r in app.router.routes:
            if r["path"].endswith("*"):
                route = r
                break

        assert route is not None, "Static file route not found"
        handler = route["handler"]

        # Mock Native Request with a Windows absolute path pointing to the secret file
        mock_native_req = Mock()
        mock_native_req.get_method.return_value = "GET"
        mock_native_req.get_url.return_value = "/static/C:../secret.txt"
        # The wildcard parameter would get C:\temp\secret.txt or similar
        mock_native_req.get_parameter.return_value = "C:../secret.txt"
        mock_native_req.for_each_header = Mock(side_effect=lambda func: None)

        # Mock Native Response
        mock_native_res = Mock()
        mock_native_res.write_status = Mock()
        mock_native_res.write_header = Mock()
        mock_native_res.end = Mock()

        # Create Xyra Response wrapper
        res = Response(mock_native_res)
        # Create Request using the wrapper as _res (to match current implementation)
        req = Request(mock_native_req, res)

        # Run handler
        await handler(req, res)

        # Check what was sent
        args = mock_native_res.end.call_args
        sent_data = b""
        if args:
            sent_data = args[0][0]
            if isinstance(sent_data, str):
                sent_data = sent_data.encode()

        # Expectation: Should NOT return "SECRET". Should return 404 or similar.
        assert b"SECRET" not in sent_data, (
            "Path Traversal Vulnerability: Secret file content leaked!"
        )

        # Verify status code is 404 or 403
        status_args = mock_native_res.write_status.call_args
        assert status_args is not None, "write_status was never called"
        status = status_args[0][0]
        assert status in ["404", "403"], f"Expected 404/403, got {status}"

    finally:
        shutil.rmtree(temp_dir)

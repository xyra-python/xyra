import os
import shutil
import tempfile
import asyncio
from unittest.mock import Mock, AsyncMock
from xyra import App, Request, Response
import pytest

@pytest.mark.asyncio
async def test_path_traversal_blocked():
    """Test that path traversal attempts are blocked in static file serving."""
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
            if "filename" in r["param_names"]:
                route = r
                break

        assert route is not None, "Static file route not found"
        handler = route["handler"]

        # Mock Request
        mock_req = Mock()
        mock_req.get_method.return_value = "GET"
        mock_req.get_url.return_value = "/static/../secret.txt"
        mock_req.for_each_header = Mock(side_effect=lambda func: None)

        # Mock Native Response
        mock_native_res = Mock()
        mock_native_res.write_status = Mock()
        mock_native_res.write_header = Mock()
        mock_native_res.end = Mock()

        # Create Request with malicious filename
        # Simulate accessing ../secret.txt
        req = Request(mock_req, mock_native_res, params={"filename": "../secret.txt"})
        res = Response(mock_native_res)

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
        # Currently, it returns "SECRET" because of vulnerability.

        # For the purpose of confirming the fix later, we assert that "SECRET" is NOT in the response.
        # But initially (before fix), this assertion will fail.
        # Since I'm creating the test now, I will assert failure if I want to confirm vulnerability.
        # But usually test files should pass after fix.
        # So I will write the test assuming the fix is applied (assert "SECRET" not in sent_data).
        # When run now, it should fail.

        assert b"SECRET" not in sent_data, "Path Traversal Vulnerability: Secret file content leaked!"

        # Verify status code is 404 or 403
        # mock_native_res.write_status might have been called
        status_args = mock_native_res.write_status.call_args
        if status_args:
            status = status_args[0][0]
            # It could be "404" or "403"
            assert status in ["404", "403"], f"Expected 404/403, got {status}"
        else:
             # If status wasn't written, it defaults to 200 in Response object but native might need explicit write?
             # Response.send calls write_status.
             pass

    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_symlink_traversal_blocked():
    """Test that symlinks pointing outside the static directory are blocked."""
    # Setup directories
    temp_dir = tempfile.mkdtemp()
    try:
        static_dir = os.path.join(temp_dir, "static")
        os.makedirs(static_dir)

        # Create secret file outside static directory
        secret_path = os.path.join(temp_dir, "secret.txt")
        with open(secret_path, "w") as f:
            f.write("SECRET_LEAK")

        # Create symlink inside static dir pointing to secret
        symlink_path = os.path.join(static_dir, "leak")
        try:
            os.symlink(secret_path, symlink_path)
        except OSError:
            pytest.skip("Symlinks not supported on this platform")

        app = App()
        app.static_files("/static", static_dir)

        # Find handler
        route = next(r for r in app.router.routes if "filename" in r["param_names"])
        handler = route["handler"]

        # Mock Request for symlink
        mock_req = Mock()
        mock_req.get_method.return_value = "GET"
        mock_req.get_url.return_value = "/static/leak"
        mock_req.for_each_header = Mock(side_effect=lambda func: None)

        mock_native_res = Mock()
        mock_native_res.write_status = Mock()
        mock_native_res.end = Mock()

        req = Request(mock_req, mock_native_res, params={"filename": "leak"})
        res = Response(mock_native_res)

        await handler(req, res)

        # Verify response
        args = mock_native_res.end.call_args
        sent_data = b""
        if args:
            sent_data = args[0][0]
            if isinstance(sent_data, str):
                sent_data = sent_data.encode()

        # Vulnerability check: If vulnerable, it returns "SECRET_LEAK"
        # We assert that it does NOT leak.
        assert b"SECRET_LEAK" not in sent_data, "Symlink Traversal Vulnerability: Secret file content leaked!"

        # Verify status code is 403 Forbidden
        status_args = mock_native_res.write_status.call_args
        if status_args:
            status = status_args[0][0]
            assert status == "403", f"Expected 403 Forbidden, got {status}"

    finally:
        shutil.rmtree(temp_dir)

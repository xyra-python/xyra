import os
import subprocess
import sys


def test_response_uaf():
    # Run the reproduction script in a subprocess
    # This bypasses conftest.py's mocking of libxyra
    # and allows us to test the real native extension.
    # The reproduction script attempts to crash the server.

    script_path = os.path.join(os.path.dirname(__file__), "reproduce_uaf_script.py")

    # Run with timeout (30 seconds should be enough)
    try:
        proc = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Check return code
        if proc.returncode != 0:
            print(f"Subprocess failed with return code {proc.returncode}")
            print("STDOUT:", proc.stdout)
            print("STDERR:", proc.stderr)
            assert False, "Reproduction script failed (likely crashed)"

        # Check for expected output
        assert "Success: No crash" in proc.stdout

    except subprocess.TimeoutExpired:
        assert False, "Subprocess timed out (server hung?)"

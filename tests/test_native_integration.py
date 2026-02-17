import os
import subprocess
import sys

import pytest

# Ensure libxyra.so is found
if not os.path.exists("xyra/libxyra.so") and not any(f.startswith("libxyra") for f in os.listdir("xyra")):
    pytest.skip("Native extension not built", allow_module_level=True)

@pytest.mark.integration
def test_native_bindings_subprocess():
    """Run native bindings test in a subprocess to bypass mocks in conftest.py."""
    script = """
import sys
import os

# Add current directory to path
sys.path.insert(0, os.getcwd())

print(f"Python executable: {sys.executable}")
print(f"Sys path: {sys.path}")

try:
    import orjson
    print(f"orjson imported: {orjson}")
except ImportError as e:
    print(f"Failed to import orjson: {e}")

try:
    import xyra.libxyra
except ImportError as e:
    print(f"Failed to import xyra.libxyra: {e}")
    # Print traceback
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test parse_path
native, params = xyra.libxyra.parse_path("/users/{id}")
if native != "/users/:id":
    print(f"parse_path native path mismatch: {native} != /users/:id")
    sys.exit(1)
if params != ["id"]:
    print(f"parse_path params mismatch: {params} != ['id']")
    sys.exit(1)

# Test parse_path (root)
native, params = xyra.libxyra.parse_path("/")
if native != "/":
    print(f"parse_path root mismatch: {native}")
    sys.exit(1)

# Test format_cookie
try:
    c = xyra.libxyra.format_cookie("test", "val", max_age=3600, path="/")
    if "test=val" not in c or "Max-Age=3600" not in c or "Path=/" not in c:
        print(f"format_cookie output unexpected: {c}")
        sys.exit(1)

    # Test cookie validation (should raise)
    try:
        xyra.libxyra.format_cookie("invalid name", "val")
        print("format_cookie failed to raise on invalid name")
        sys.exit(1)
    except ValueError:
        pass

    try:
        xyra.libxyra.format_cookie("test", "val;injection")
        print("format_cookie failed to raise on value injection")
        sys.exit(1)
    except ValueError:
        pass

except Exception as e:
    print(f"format_cookie raised unexpected exception: {e}")
    sys.exit(1)

# Test Request.get_queries method existence
if not hasattr(xyra.libxyra.Request, "get_queries"):
    print("Request.get_queries missing")
    sys.exit(1)

print("Native bindings OK")
"""
    result = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True, cwd=os.getcwd())
    if result.returncode != 0:
        pytest.fail(f"Native bindings test failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")

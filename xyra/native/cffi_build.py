import glob
import os
import platform
import sys

from cffi import FFI

ffi = FFI()

# Read the C header file
with open(os.path.join(os.path.dirname(__file__), "c_api.h")) as f:
    cdef_str = f.read()

# Filter out preprocessor directives like #ifndef, #include, etc for cffi
lines = cdef_str.split("\n")
filtered_lines = []
for line in lines:
    if line.strip().startswith("#"):
        continue
    if "extern \"C\"" in line:
        continue
    # we need to remove '}' from the end of extern "C" block
    if line.strip() == "}":
        continue
    filtered_lines.append(line)

ffi.cdef("\n".join(filtered_lines))

# Use CMake's built static library
# (This ensures all USOCKETS definitions and system libs are properly handled)

extra_libs = ["z"]
if platform.system() == "Windows":
    extra_libs.append("libuv")

# Ensure CFFI finds the library wherever setuptools decides to put it, or fall back
version = f"{sys.version_info.major}{sys.version_info.minor}"
build_temp_dirs = glob.glob(os.path.abspath("build/temp.*"))
library_dirs = [os.path.abspath("xyra"), os.path.abspath("xyra/native")] + build_temp_dirs

cffi_libs = ["xyra", "xyra_native"]
if platform.system() != "Windows":
    cffi_libs.append("stdc++")

ffi.set_source(
    "xyra._libxyra",
    '#include "c_api.h"',
    include_dirs=[
        os.path.abspath("xyra/native")
    ],
    library_dirs=library_dirs,
    libraries=cffi_libs + extra_libs
)

def build_cffi(output_path):
    ffi.compile(tmpdir=os.path.dirname(output_path))

if __name__ == "__main__":
    build_cffi("xyra_cffi.c")

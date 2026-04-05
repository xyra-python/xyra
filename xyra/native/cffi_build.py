import os

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
import platform
extra_libs = ["z"]
if platform.system() == "Windows":
    extra_libs.append("libuv")

ffi.set_source(
    "xyra._libxyra",
    '#include "c_api.h"',
    include_dirs=[
        os.path.abspath("xyra/native")
    ],
    library_dirs=[os.path.abspath("xyra")],
    libraries=["xyra"] + extra_libs
)

def build_cffi(output_path):
    ffi.compile(tmpdir=os.path.dirname(output_path))

if __name__ == "__main__":
    build_cffi("xyra_cffi.c")

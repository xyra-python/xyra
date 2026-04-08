import os
import platform
import re
import subprocess
import sys

from setuptools import Extension, setup
from setuptools.command.build_ext import build_ext


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=""):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(["cmake", "--version"])
        except OSError as e:
            raise RuntimeError(
                "CMake must be installed to build the following extensions: "
                + ", ".join(e.name for e in self.extensions)
            ) from e

        if platform.system() == "Windows":
            match = re.search(r"version\s*([\d.]+)", out.decode())
            if match:
                cmake_version_str = match.group(1)
                cmake_version = tuple(
                    int(x) for x in cmake_version_str.split(".") if x.isdigit()
                )
                if cmake_version < (3, 1, 0):
                    raise RuntimeError("CMake >= 3.1.0 is required on Windows")

        # Initialize the compiler for CFFI
        from setuptools.command.build_ext import build_ext as _build_ext
        _build_ext.run(self)

        # for ext in self.extensions:
        #     self.build_extension(ext)

    def build_extension(self, ext):
        if not hasattr(ext, "sourcedir"):
            # We are inside CMakeBuild but trying to build a CFFI extension.
            # setuptools build_ext hasn't initialized the compiler correctly yet
            # because we override run(). We need to explicitly call super().run()
            # for the CFFI extension. To do that, we'll let the standard build_ext
            # handle it by calling the parent class implementation.
            from setuptools.command.build_ext import build_ext as _build_ext
            _build_ext.build_extension(self, ext)
            return

        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))

        # Ensure output directory exists
        if not os.path.exists(extdir):
            os.makedirs(extdir)

        cmake_args = [
            "-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=" + extdir,
            "-DPYTHON_EXECUTABLE=" + sys.executable,
        ]

        if "CMAKE_TOOLCHAIN_FILE" in os.environ:
            cmake_args += [
                "-DCMAKE_TOOLCHAIN_FILE=" + os.environ["CMAKE_TOOLCHAIN_FILE"]
            ]

        cfg = "Debug" if self.debug else "Release"
        build_args = ["--config", cfg]

        if platform.system() == "Windows":
            cmake_args += [f"-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{cfg.upper()}={extdir}"]
            if sys.maxsize > 2**32:
                cmake_args += ["-A", "x64"]
            build_args += ["--", "/m"]
        else:
            cmake_args += ["-DCMAKE_BUILD_TYPE=" + cfg]
            build_args += ["--", "-j2"]

        env = os.environ.copy()
        env["CXXFLAGS"] = '{} -DVERSION_INFO=\\"{}\\"'.format(
            env.get("CXXFLAGS", ""), self.distribution.get_version()
        )

        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)

        subprocess.check_call(
            ["cmake", ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env
        )
        subprocess.check_call(
            ["cmake", "--build", "."] + build_args, cwd=self.build_temp
        )

        # In xyra/native/CMakeLists.txt it might build libxyra.a
        import shutil

        for libname in ("libxyra.a", "xyra.lib", "xyra.a"):
            lib_path = os.path.join(self.build_temp, libname)
            if os.path.exists(lib_path):
                shutil.copy(lib_path, "xyra/")
                # also copy to ext.sourcedir just in case cffi needs it
                shutil.copy(lib_path, ext.sourcedir)

                # Copy with different names to be completely safe during CFFI linking
                if libname == "libxyra.a":
                    shutil.copy(lib_path, "xyra/libxyra_native.a")
                    shutil.copy(lib_path, os.path.join(ext.sourcedir, "libxyra_native.a"))

                print(f"Copied {lib_path} to xyra/ and {ext.sourcedir}")

        # Generate CFFI C code
        sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
        import xyra.native.cffi_build
        xyra.native.cffi_build.build_cffi(os.path.join(ext.sourcedir, "xyra_cffi.c"))


setup(
    name="xyra",
    version="0.2.6",
    author="Xyra Team",
    author_email="team@xyra.dev",
    description="High Performance Frameworks, Easy to learn and Ready for Production",
    long_description="",
    ext_modules=[CMakeExtension("xyra._libxyra", sourcedir="xyra/native")],
    cffi_modules=["xyra/native/cffi_build.py:ffi"],
    cmdclass={"build_ext": CMakeBuild},
    include_package_data=True,
    zip_safe=False,
)

import os
import re
import sys
import platform
import subprocess

from setuptools import setup, Extension
from setuptools.command.build_ext import build_ext
from distutils.version import LooseVersion


class CMakeExtension(Extension):
    def __init__(self, name, sourcedir=''):
        Extension.__init__(self, name, sources=[])
        self.sourcedir = os.path.abspath(sourcedir)


class CMakeBuild(build_ext):
    def run(self):
        try:
            out = subprocess.check_output(['cmake', '--version'])
        except OSError:
            raise RuntimeError("CMake must be installed to build the following extensions: " +
                               ", ".join(e.name for e in self.extensions))

        if platform.system() == "Windows":
            cmake_version = LooseVersion(re.search(r'version\s*([\d.]+)', out.decode()).group(1))
            if cmake_version < '3.1.0':
                raise RuntimeError("CMake >= 3.1.0 is required on Windows")

        for ext in self.extensions:
            self.build_extension(ext)

    def build_extension(self, ext):
        extdir = os.path.abspath(os.path.dirname(self.get_ext_fullpath(ext.name)))
        cmake_args = ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY=' + extdir,
                      '-DPYTHON_EXECUTABLE=' + sys.executable]

        cfg = 'Debug' if self.debug else 'Release'
        build_args = ['--config', cfg]

        if platform.system() == "Windows":
            cmake_args += ['-DCMAKE_LIBRARY_OUTPUT_DIRECTORY_{}={}'.format(cfg.upper(), extdir)]
            if sys.maxsize > 2**32:
                cmake_args += ['-A', 'x64']
            build_args += ['--', '/m']
        else:
            cmake_args += ['-DCMAKE_BUILD_TYPE=' + cfg]
            build_args += ['--', '-j2']

        env = os.environ.copy()
        env['CXXFLAGS'] = '{} -DVERSION_INFO=\\"{}\\"'.format(
            env.get('CXXFLAGS', ''),
            self.distribution.get_version()
        )
        if not os.path.exists(self.build_temp):
            os.makedirs(self.build_temp)
        print(['cmake', ext.sourcedir] + cmake_args)
        subprocess.check_call(['cmake', ext.sourcedir] + cmake_args, cwd=self.build_temp, env=env)
        subprocess.check_call(['cmake', '--build', '.'] + build_args, cwd=self.build_temp)

setup(
    name='homography_est',
    version='0.0.0',
    author='Viktor Larsson, Iago Suarez, Rémi Pautrat',
    author_email='remi.pautrat@inf.ethz.ch',
    description='Point-Line homography estimation bindings',
    long_description='',
    ext_modules=[CMakeExtension('homography_est')],
    cmdclass=dict(build_ext=CMakeBuild),
    zip_safe=False,
)

# from setuptools import setup
# from glob import glob

# # Available at setup time due to pyproject.toml
# from pybind11.setup_helpers import Pybind11Extension, build_ext
# # from pybind11 import get_cmake_dir

# __version__ = "0.0.0"

# The main interface is through Pybind11Extension.
# * You can add cxx_std=11/14/17, and then build_ext can be removed.
# * You can set include_pybind11=false to add the include directory yourself,
#   say from a submodule.
#
# Note:
#   Sort input source files if you glob sources to ensure bit-for-bit
#   reproducible builds (https://github.com/pybind/python_example/pull/53)

# ext_modules = [
#     Pybind11Extension("homography_est",
#         sorted(glob("./*.cc")),
#         # ["python_interface.cc"],
#         # Example: passing in the version to the compiled code
#         define_macros = [('VERSION_INFO', __version__)],
#         ),
# ]

# setup(
#     name="homography_est",
#     version=__version__,
#     author="Viktor Larsson, Rémi Pautrat",
#     author_email="remi.pautrat@inf.ethz.ch",
#     description="Line homography estimation bindings",
#     long_description="",
#     ext_modules=ext_modules,
#     # extras_require={"test": "pytest"},
#     # Currently, build_ext only provides an optional "highest supported C++
#     # level" feature, but in the future it may provide more features.
#     cmdclass={"build_ext": build_ext},
#     zip_safe=False,
# )
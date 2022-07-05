#from setuptools import setup
import setuptools # I think this is needed for the following
from numpy.distutils.core import Extension,setup
from distutils.spawn import find_executable
import os

ext_modules = []

# {{{ compile_SpinCore_pp implies that these are set in bashrc -- I don't know
#     how they get set in the first place
arg_list = []
if "conda_headers" not in os.environ.keys():
    raise ValueError("I don't see the environment variables that I expect -- please edit environment.sh so it describes your system, and then run it w/ `source environment.sh`")
for j in ["conda_headers","spincore","numpy"]:
    arg_list.append('-I'+os.environ[j])
for j in ["conda_libs","spincore"]:
    arg_list.append('-L'+os.environ[j])
# }}}
ext_modules.append(Extension(name='SpinCore_pp._SpinCore_pp',
    sources = ["SpinCore_pp/SpinCore_pp.i", "SpinCore_pp/SpinCore_pp.c"],
    define_macros = [('ADD_UNDERSCORE',None)],
    # flags from compile_SpinCore_pp.sh
    extra_compile_args = [
        "-shared",
        "-DMS_WIN64",
        ] + arg_list,# debug flags
    library_dirs = ['.'],
    libraries = ['mrispinapi64'],
    swig_opts=['-threads'],
    ))
exec(compile(open('SpinCore_pp/version.py', "rb").read(), 'SpinCore_pp/version.py', 'exec'))

setup(
    name='SpinCore_pp',
    author='Beaton,Franck,Guinness',
    version=__version__,
    packages=setuptools.find_packages(),
    license='LICENSE.md',
    author_email='jmfranck@notgiven.com',
    url='http://github.com/jmfrancklab/spincore_apps',
    description='custom pulse programming language',
    long_description="Pulse programming language for SpinCore RadioProcessor G",
    install_requires=[
        "numpy",
        "h5py",
        "pyserial>=3.0",
        ],
    ext_modules = ext_modules,
)

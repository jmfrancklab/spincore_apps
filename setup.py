#from setuptools import setup
import setuptools # I think this is needed for the following
from numpy.distutils.core import Extension,setup
from distutils.spawn import find_executable

ext_modules = []
ext_modules.append(Extension(name='SpinCore_pp/_SpinCore_pp',
        sources = ["SpinCore_pp/SpinCore_pp.i"],
        define_macros = [('ADD_UNDERSCORE',None)],
        # flags from compile_SpinCore_pp.sh
        extra_compile_args = [
            "-shared",
            "-DMS_WIN64",
            "-lmrispinapi64",
            ],# debug flags
        ))
execfile('SpinCore_pp/version.py')

setup(
    name='SpinCore_pp',
    author='Beaton,Franck',
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
    entry_points={gds_for_tune=SpinCore_pp.gds_for_tune:__main__},
)

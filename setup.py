#from setuptools import setup
import setuptools # I think this is needed for the following
from numpy.distutils.core import Extension,setup
from distutils.spawn import find_executable

ext_modules = []
execfile('SpinCore_pp/version.py')

setup(
    name='francklab_SpinCore_apps',
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
    entry_points={},
)

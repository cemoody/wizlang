#!/usr/bin/env python

from distutils.core import setup
from distutils.extension import Extension
from Cython.Build import cythonize
from Cython.Distutils import build_ext

import numpy


setup(
    cmdclass = {'build_ext': build_ext},
    ext_modules = [Extension("shortdot",
                         sources=["shortdot.pyx"],
                         include_dirs=[numpy.get_include()])],
)

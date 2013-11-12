#!/usr/bin/env python
"""
simple test of the shortdot.pyx code
"""

import numpy as np
import shortdot
import time

rows = 100
dims = 1000
A = np.random.normal(size=(rows, dims)).astype('f4')
B = np.random.normal(size=(dims)).astype('f4')
C = np.zeros(dims)

n = 500
start = time.time()
for i in range(n):
    skipped = shortdot.shortdot(A, B, C, -1.0)
stop = time.time()
print "finished cython, skipped %i"  % skipped
cy = (stop - start) * 1.0 / n * 1e9

start = time.time()
for i in range(n):
    np.dot(A, B)
stop = time.time()
py = (stop - start) * 1.0 / n * 1e9

print "cython: %1.3ens" % cy
print "python: %1.3ens" % py

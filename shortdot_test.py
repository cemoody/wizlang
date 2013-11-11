#!/usr/bin/env python
"""
simple test of the shortdot.pyx code
"""

import numpy as np
import shortdot
import time

rows = 100
dims = 10
A = np.random.random((rows, dims)).astype('f4')
B = np.random.random((dims)).astype('f4')
C = np.zeros(dims).astype('f8')

n = 500
start = time.time()
for i in range(n):
    shortdot.shortdot(A, B, C)
stop = time.time()
cy = (stop - start) * 1000.0 / n

start = time.time()
for i in range(n):
    np.dot(A, B)
stop = time.time()
py = (stop - start) * 1000.0 / n

print "cython: %1.3fms" % cy
print "python: %1.3fms" % py

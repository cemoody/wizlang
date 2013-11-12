#!/usr/bin/env python
"""
simple test of the shortdot.pyx code
"""

import numpy as np
import shortdot
import time

test_rand = False

if test_rand:
    rows = int(1e5)
    dims = 1000
    A = np.random.normal(size=(rows, dims)).astype('f4')
    B = np.random.normal(size=(dims)).astype('f4')
    C = np.zeros(dims)
    thresh = -1.0
    print "created matrix"
else:
    A = np.load("/nobackupp5/cmoody3/data/ids/trained/vectors.fullwiki.1000.s50.num.npy")
    A = A.astype('f4')
    B = A[A.shape[0]/2]
    C = np.zeros(A.shape[0]).astype('f8')
    thresh = 0.1
    rows = A.shape[0]
    dims = A.shape[1]
C = C.astype('f4')
n = 20
start = time.time()
for i in range(n):
    C = np.zeros(rows).astype('f4')
    skipped = shortdot.shortdot(A, B, C, 50, thresh)
stop = time.time()
frac = skipped * 1.0 / (rows * dims)
print "finished cython, skipped %i, %1.1f%%"  % (skipped, frac * 100.0)
cy = (stop - start) * 1.0 / n * 1e6
print 'cython top 5:', np.sort(C)[-5:], np.argsort(C)[-5:]

start = time.time()
for i in range(n):
    x = np.zeros(rows).astype('f4')
    D = np.dot(A, B)
stop = time.time()
py = (stop - start) * 1.0 / n * 1e6
print 'numpy  top 5:', np.sort(D)[-5:], np.argsort(D)[-5:]
comp = np.where(np.argsort(D)[::-1] != np.argsort(C)[::-1])[0]
print "first inequal indices", comp[:10]

print "cython: %1.3ems" % cy
print "python: %1.3ems" % py
print "cython speed up %1.1f " % (py / cy)

cimport cython
import numpy as np
cimport numpy as np

@cython.boundscheck(False)
@cython.wraparound(False)
cdef np.ndarray[double, ndim=1] shortdot(
    np.ndarray[float, ndim=2] A,
    np.ndarray[float, ndim=1] B,
    float threshold = -3.0):
    '''
    Matrix-vector multiplication.
    We stop row multiplication if the cosine distance
    is below the threshold. The sum is a double for better
    accuracy
    '''
    cdef: 
        int i, j
        int A_n = A.shape[0]
        int A_m = A.shape[1]
        int B_n = B.shape[0]
        double tot = 0.0
        np.ndarray[double, ndim=1] C
    
    # Initialize the results matrix.
    C = np.zeros(A_n)
    for i in xrange(A_n):
        for j in xrange(A_m):
            tot += A[i, j] * B[j]
            if j > 10 and tot < threshold:
                break
        C[i] = tot
    return C

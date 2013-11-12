cimport cython
import numpy as np
cimport numpy as np

@cython.boundscheck(False)
@cython.wraparound(False)
def shortdot(
    np.ndarray[float, ndim=2] A,
    np.ndarray[float, ndim=1] B,
    np.ndarray[float, ndim=1] C,
    int jmax = 50,
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
        int C_n = C.shape[0]
        float tot = 0.0
        int skipped = 0

    assert A_m == B_n
    assert C_n == A_n
    
    # Initialize the results matrix.
    for i in xrange(A_n):
        tot = 0.0
        for j in xrange(A_m):
            #tot += <double> (A[i, j] * B[j])
            tot += (A[i, j] * B[j])
            #if j % 10 == 0:
            #    z = abs(tot - 1.0) /  (0.3) * j / jmax
            #    if z < threshold:
            #        skipped += B_n - j
            #        break
            if j > jmax and tot < threshold:
            #if tot < threshold:
                skipped += B_n - j
                break
        C[i] = tot
    #print i,j, A_n, A_m, B_n, C_n
    return skipped

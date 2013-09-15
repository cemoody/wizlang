import time
import sys
from multiprocessing import Process, Pipe
from itertools import izip

# Courtesy of 
#http://stackoverflow.com/questions/3288595/multiprocessing-using-pool-map-on-a
#-function-defined-in-a-class
def spawn(f):
    def fun(pipe,x):
        pipe.send(f(x))
        pipe.close()
    return fun

def parmap(f,X):
    pipe=[Pipe() for x in X]
    proc=[Process(target=spawn(f),args=(c,x)) for x,(p,c) in izip(X,pipe)]
    [p.start() for p in proc]
    [p.join() for p in proc]
    return [p.recv() for (p,c) in pipe]


def timer(func):
    def wrapped(*args, **kwargs):
        start = time.time()
        rv = func(*args, **kwargs)
        print "%02.1fs in %s" % (time.time() - start, func.__name__)
        return rv
    return wrapped

def fail_print(func):
    def wrapped(*args, **kwargs):
        try:
            rv = func(*args, **kwargs)
        except:
            print sys.exc_info()[0]
            rv = None
        return rv
    return wrapped

class dummy_async():
    """This is faking an async result for debugging purposes"""
    def __init__(self, val):
        self.val = val
    def get(self):
        return self.val

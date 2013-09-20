import time
import sys
from multiprocessing import Process, Pipe
from itertools import izip
import os.path
import json

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

def persist_to_file(original_func):
    """ Each query gets written out to a page
        Obviously, this is much slower than the save key-values
        to Redis. But it's quick and doesn't break too much"""
    n = 100
    def decorator(*args, **kwargs):
        file_name = "./cache/"
        file_name += original_func.__name__
        for arg in args:
            file_name += str(arg)[:n]
        keys = sorted(kwargs.keys())
        for k in keys:

            v = kwargs[k]
            v = str(v)[:n]
            file_name += "%s_%s-" %(k, v)
        file_name = file_name.replace("'","")
        file_name = file_name.replace('"',"")
        file_name = file_name.replace('/',"")
        try:
            ret = json.load(open(file_name, 'r'))
        except (IOError, ValueError):
            ret = None
        if ret is None:
            ret = original_func(*args,**kwargs)
            json.dump(ret, open(file_name, 'w'))
        return ret
    return decorator

def json_exception(original_func):
    def wrapper(*args, **kwargs):
        try:
            rv = original_func(*args, **kwargs)
        except:
            print "ERROR"
            dv = dict(error=str(sys.exc_info()))
            rv = json.dumps(dv)
        return rv
    return wrapper

class dummy_async():
    """This is faking an async result for debugging purposes"""
    def __init__(self, val):
        self.val = val
    def get(self):
        return self.val

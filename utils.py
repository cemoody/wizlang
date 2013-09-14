import time
import sys

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
    def __init__(val):
        self.val = val
    def get():
        return self.val

import time

def timer(func):
    def wrapped(*args, **kwargs):
        start = time.time()
        rv = func(*args, **kwargs)
        print "%02.1fs in %s" % (time.time() - start, func.__name__)
        return rv
    return wrapped


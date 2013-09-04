from difflib import get_close_matches
import pandas as pd
import numpy as np
import os.path
import string
import difflib
from sets import Set

""" A library to lookup word vectors, reduce the vector list to a subset and
calculate the nearest word given a vector"""

fnw = '%s/vectors.bin.008.words' % '.'
fnv = '%s/vectors.bin.008.num' % '.'
fnc = 'data/movies_canonical'
def distance(v1, v2, axis=None):
    if type(v1) is str:
        v1 = lookup_vector(v1)
    if type(v2) is str:
        v2 = lookup_vector(v2)
    if len(v1.shape[0]) > 1:
        axis = 1
    i = (v1.astype(np.float64) - v2.astype(np.float64))**2.0
    d = np.sqrt(np.sum(i, axis=axis, dtype=np.float128))
    return d

def reshape(v1):
    if len(v1.shape) == 1:
        shape = [1, v1.shape[0]]
        v1 = np.reshape(v1, shape)
    return v1

def mag(x):
    return np.sqrt(np.sum(x**2.0, axis=1))

def chunks(l, n):
    """ Yield successive n-sized chunks from l.
    """
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def sim(v, v2, dtype=np.float64, chunksize=1e4):
    vs = []
    for v1 in chunks(v, long(chunksize)):
        i = (v1.astype(dtype) * v2.astype(dtype))
        d = (mag(v1.astype(dtype)) * mag(v2.astype(dtype)))
        d = np.reshape(d, [d.shape[0], 1])
        i /= d
        vs.append(i)
        del d, i
    i = np.vstack(vs)
    return i

def dot(v1, v2, axis=1):
    if type(v1) is str:
        v1 = lookup_vector(v1)
    if type(v2) is str:
        v2 = lookup_vector(v2)
    v1 = reshape(v1)
    v2 = reshape(v2)
    print v1.shape, v2.shape
    try: 
        dtype = np.float16
        i = sim(v1, v2, dtype)
    except MemoryError:
        dtype = np.float8
        i = sim(v1, v2, dtype)
    print i.shape
    similarity = np.sum(i, axis=axis, dtype=np.float128)
    print similarity.shape
    return similarity

def nearest_word(vector, vector_lib, index2word):
    if type(vector) is str:
        vector = lookup_vector(vector)
    d = dot(vector_lib, vector)
    idx =  np.argsort(d)[2] #First two entries always the input keys
    return index2word[idx]

def lookup_vector(word, vector_lib, w2i, fuzzy=True):
    keys = w2i.keys()
    key, = get_close_matches(word, keys, 1)
    return vector_lib[w2i[key]]

def read_canon_text(fn):
    canon = Set()
    with open(fn) as fh:
        text = fh.read()
        text = text.replace('\r', ' ')
        text = text.replace('\t', ' ')
        text = text.translate(None, string.digits)
        for line in text.split('\n'):
            canon.add(line.strip().strip('_'))
    return canon, text 

def get_canon_rep(fn):
    c2f, f2c = {}, {}
    with open(fn) as fh:
        for line in fh.readlines():
            f, c = line.rsplit(',', 1)
            f, c = f.strip(), c.strip()
            c2f[c] = f
            f2c[f] = c
    return c2f, f2c

def canonize(phrase, c2f):
    phrase = phrase.strip().lower()
    phrase = phrase.replace('\n','').replace('\t','').replace('\r','')
    phrase = phrase.translate(string.digits)
    phrase = phrase.translate(string.punctuation)
    for i in range(5):
        phrase = phrase.replace('  ', ' ')
    phrase = phrase.replace(' ', '_')
    phrase, = difflib.get_close_matches(phrase, c2f.keys(), 1)
    return phrase

def reduce_vectorlib(vector_lib, word2index, canon):
    indices = []
    w2i, i2w = {}, {}
    for name, index in word2index.iteritems():
        if name in canon:
            indices.append(index)
            w2i[name] = index
            i2w[index] = name
    rvl = vector_lib[indices]
    return rvl, w2i, i2w

def get_names(fn=fnc):
    names = [x.replace('\n', '').strip() for x in fh.readlines()]
    text = ''.join(names)
    text = text.replace('\n', '')
    return text

def get_words(fn=fnw):
    words = pd.read_csv(fn, skiprows=3, dtype='str', na_filter=False,
                        usecols=[0], squeeze=True)
    word2index = {}
    index2word = {}
    for k, v in words.iteritems():
        index2word[k] = v
        word2index[v] = k
    return word2index, index2word

def get_vector_lib(fn=fnv):
    fnvn = fn.replace('.npy', '')
    if not os.path.exists(fn) and os.path.exists(fnvn):
        data = pd.read_csv('./data/vectors.bin.007.num', sep=' ',
                           dtype='f4', na_filter=False)
        data = np.array(data, dtype=np.float32)
        np.save(fn, data)
        return data
    else:
        vectors = np.load(fn)
        return vectors

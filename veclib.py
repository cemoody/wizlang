from difflib import get_close_matches
import pandas as pd
import numpy as np
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
    shape = [1, 1]
    for i, val in enumerate(v1.shape):
        shape[i] = val
    v1 = np.reshape(v1, shape)
    return v1

def mag(x):
    return np.sqrt(np.sum(x**2.0, axis=1))

def dot(v1, v2, axis=1):
    if type(v1) is str:
        v1 = lookup_vector(v1)
    if type(v2) is str:
        v2 = lookup_vector(v2)
    v1 = reshape(v1)
    v2 = reshape(v2)
    i  = (v1.astype(np.float64) * v2.astype(np.float64))
    i /= (mag(v1) * mag(v2))
    similarity = np.sum(i, axis=axis, dtype=np.float128)
    return similarity

def nearest_word(vector, index2word, vector_lib):
    if type(v1) is str:
        vector = lookup_vector(vector)
    d = similarity(vector_lib, vector)
    idx =  np.argmin(d)
    return index2word(idx)

def lookup_vector(word, vector_lib, fuzzy=True):
    keys = vector_lib.keys()
    key = get_close_matches(word, keys, 1)
    return vector_lib[key]

def read_canon_text(fn):
    canon = Set()
    with open(fn) as fh:
        text = fh.read()
        text = text.replace('\r', ' ')
        text = text.replace('\t', ' ')
        text = text.translate(None, string.digits)
        for line in text.split('\n'):
            canon.add(line)
    return canon, text 

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
    fnvn = fnv.replace('.npy', '')
    if not os.path.exists(fnv) and os.path.exists(fnvn):
        data = pd.read_csv('vectors.bin.007.num', sep=' ',
                           dtype='f4', na_filter=False)
        data = np.array(data, dtype=np.float32)
        np.save(fnv, data)
        return data
    else:
        vectors = np.load(fnv)
        return vectors

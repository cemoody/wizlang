from difflib import get_close_matches
import pandas as pd
import numpy as np
import os.path
import string
import difflib
from sets import Set 

""" A library to lookup word vectors, reduce the vector list to a subset and
calculate the nearest word given a vector"""

trained = "/u/cmoody3/data2/ids/trained"
fnw = '%s/vectors.bin.008.words' % trained
fnv = '%s/vectors.bin.008.num' % trained
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

mag2 = lambda x: np.sqrt(np.sum(x**2.0, axis=1))
mag1 = lambda x: np.sqrt(np.sum(x**2.0, axis=0))
def similarity(svec, total):
    smv = np.reshape(total, (1, total.shape[0]))
    top = svec * smv
    denom = mag2(svec) * mag1(total)
    denom = np.reshape(denom, (denom.shape[0], 1))
    sim = np.sum(top / denom, axis=1)
    return sim

def chunks(l, n):
    for i in xrange(0, len(l), n):
        yield l[i:i+n]

def in_between(vectora, vectorb, vector_lib, index2word, n=10):
    #Measure rough dispersion in each dimension
    dispersion = np.abs(vectorb - vectora)
    vectora = np.reshape(vectora, (1, vectora.shape[0]))
    vectorb = np.reshape(vectorb, (1, vectorb.shape[0]))
    dist = np.minimum(np.abs(vector_lib - vectora),
                      np.abs(vector_lib - vectorb))
    idx = np.argsort(dist)
    words = [index2word[idx[i]] for i in range(n)]
    return dist / dispersion

def nearest_word(vector, vector_lib, index2word, n=5, skip=0, 
                 chunk_size=100000):
    words = []
    sims = []
    for vl in chunks(vector_lib, chunk_size):
        d = similarity(vl, vector)
        da = np.argsort(d)[::-1]
        for i in range(n):
            idx = da[i]
            words.append(index2word[idx])
            sims.append(d[idx])
    idx = np.argsort(sims)[::-1]
    words = [words[i] for i in idx[:n]]
    return words

def lookup_vector(word, vector_lib, w2i, fuzzy=True):
    keys = w2i.keys()
    key, = get_close_matches(word, keys, 1)
    print 'Lookup: %s -> %s' % (word, key)
    return vector_lib[w2i[key]]

def get_canon_rep(fn):
    c2f, f2c = {}, {}
    with open(fn) as fh:
        for line in fh.readlines():
            line = line.strip()
            line = line.replace('  ', ' ')
            f, c = line.rsplit(',', 1)
            f, c = f.strip(), c.strip()
            c2f[c] = f
            f2c[f] = c
    return c2f, f2c

def canonize(phrase, c2f, match=False):
    phrase = phrase.strip().lower()
    phrase = phrase.replace('\n','').replace('\t','').replace('\r','')
    phrase = phrase.translate(string.digits)
    phrase = phrase.translate(string.punctuation)
    for i in range(5):
        phrase = phrase.replace('  ', ' ')
    phrase = phrase.replace(' ', '_')
    if match:
        phrase, = difflib.get_close_matches(phrase, c2f, 1)
    return phrase

def reduce_vectorlib(vector_lib, word2index, canon):
    indices = []
    w2i, i2w = {}, {}
    outindex = 0
    words = Set(word2index.keys())
    common = Set(canon).intersection(words)
    for name in common:
        index = word2index[name]
        indices.append(index)
        w2i[name] = outindex
        i2w[outindex] = name
        outindex += 1
    indices = np.array(indices)
    rvl = vector_lib[indices]
    return rvl, w2i, i2w

def get_names(fn=fnc):
    names = [x.replace('\n', '').strip() for x in fh.readlines()]
    text = ''.join(names)
    text = text.replace('\n', '')
    return text

def get_words(fn=fnw, subsample=None):
    words = open(fn).readlines()
    word2index = {}
    index2word = {}
    for v, k in enumerate(words):
        k = k.strip().replace('\n', '')
        if subsample:
            if v > subsample - 1:
                break
        index2word[v] = k
        word2index[k] = v
    return word2index, index2word

def get_english(fn):
    words = []
    with open(fn) as fh:
        for line in fh.readlines():
            words.append(line.strip())
    return words

def get_vector_lib(fn=fnv):
    fnvn = fn.replace('.npy', '')
    if not os.path.exists(fn) and os.path.exists(fnvn):
        data = pd.read_csv(fn, sep=' ',
                           dtype='f4', na_filter=False)
        data = np.array(data, dtype=np.float32)
        np.save(fn, data)
        return data
    else:
        vectors = np.load(fn)
        return vectors

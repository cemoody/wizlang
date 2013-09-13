import urllib2
import json
import string
import re
import httplib
import urlparse
import sets
import cPickle
import os.path
import time
import sharedmem
import multiprocessing
from multiprocessing import Manager
from sets import Set
import numexpr as ne
from wiki import *
from utils import *
import veclib

def eval_sign(query):
    """ This is a dumb parser that assign + or - to every character
        in an expression. We can then use this to lookup the sign of
        every token in the expression"""
    out = ""
    sign = '+' # defailt is positive
    for c in query:
        if c == '-': 
            sign = '-'
        elif c == '+':
            sign = '+'
        out += sign
    return out

class Actor(object):
    """ This encapsulates all of the actions associated with a results 
        page. We test multiple Actor objects until validate(query) is True
        and then parse and evaluate the query, which is usually called 
        through run"""
    name = 'Actor'
    pool = None

    def validate(self, query):
        """Is the given query suitable for this Action"""
        return False

    def parse(self, query):
        """ Reduce the query into arguments for evaluate"""
        return 

    def evaluate(self, arg, **kwargs):
        """Evaluate the query and return a results object
           that gets plugged into the Jinja code in results.html.
           Defaults to a pass-through to OMDB"""
        return {}

    @timer
    def run(self, query):
        if self.pool is None:
            self.pool = multiprocessing.Pool()
        start = time.time()
        try:
            args, kwargs = self.parse(query)
            reps = self.evaluate(*args, **kwargs)
        except:
            reps = {}
        reps['actor'] = self.name
        stop = time.time()
        reps['query_time'] = "%1.1f" %(stop - start)
        return reps

class Passthrough(Actor):
    name = "Passthrough"

    def validate(self, query):
        return True

    def parse(self, query, kwargs=None):
        if kwargs is None:
            kwargs = {'query':query}
        args = query.replace('+','|').replace('-','|')
        args = args.split('|')
        return [args[0]], kwargs

    def evaluate(self, arg, **kwargs):
        #result = get_omdb(arg)
        result = process_wiki(arg)
        if result is None:
            return {}
        query_text = kwargs['query']
        print result.keys()
        reps = dict(query_text=query_text, results=[result])
        return reps

class Expression(Actor):
    name = "Expression"

    @timer
    def __init__(self, preloaded_actor=None, subsampling=False, 
                 fast=False, test=True):
        """We need to load and preprocess all of the vectors into the 
           memory and persist them to cut down on IO costs"""
        if not preloaded_actor:
            # a= 'all'
            # w='wikipedia'
            trained = "/u/cmoody3/data2/ids/trained" 
            trained = "/home/ubuntu/data" 
            if fast:
                fnv = '%s/vectors.bin.005.num.npy' % trained
                fnw = '%s/vectors.bin.005.words' % trained
            else:
                fnv = '%s/vectors.wiki.1000.num.npy' % trained
                fnw = '%s/vectors.wiki.1000.words' % trained
                fnv = '%s/vectors.fullwiki.1000.s50.num.npy' % trained
                fnw = '%s/vectors.fullwiki.1000.s50.words' % trained
            wc2t = '%s/c2t' % './data'
            wt2c = '%s/t2c' % './data'
            # all word vecotor lib VL
            self.wc2t = cPickle.load(open(wc2t))
            self.wt2c = cPickle.load(open(wt2c))
            ks, vs  = [], []
            for k, v in self.wc2t.iteritems():
                k = veclib.canonize(k, {}, match=False)
                ks.append(k)
                vs.append(v)
            for k, v in zip(ks, vs):
                self.wc2t[k] = v
            avl = veclib.get_vector_lib(fnv)
            # all words, word to index mappings w2i
            if os.path.exists(fnw + '.pickle'):
                self.aw2i , self.ai2w = cPickle.load(open(fnw + '.pickle'))
            else:
                self.aw2i , self.ai2w = veclib.get_words(fnw)
                cPickle.dump([self.aw2i, self.ai2w], open(fnw + '.pickle','w'))
            if subsampling:
                n = long(1e6) # keep top one million words
                print "subsampling %1.1e elements" % n
                wl = sets.Set(self.wc2t.keys())
                avl, self.aw2i, self.ai2w = veclib.subsample(avl, self.aw2i, 
                                                             self.ai2w, wl, n)
                assert max(self.ai2w.keys()) == len(wl) + 1
            self.avl = veclib.normalize(avl)
            del avl
            # # of words better be the same in both the vectors
            # and the list of words
            rets = veclib.reduce_vectorlib(self.avl, self.aw2i, 
                                           sets.Set(self.wc2t.keys()))
            self.wvl, self.ww2i, self.wi2w = rets
            self.wvl = self.wvl.astype('f4')
            assert self.avl.shape[0] == len(self.ai2w.keys())
                
            # now let's test loading a word and finding its index
            if test:
                import numpy as np
                idx = self.ww2i.values()[0]
                vec = self.wvl[idx]
                idx2 = np.argmin(np.sum(np.abs(self.wvl - \
                                np.reshape(vec, (1, vec.shape[0]))), axis=1))
                assert idx2 == idx
            print "%1.1e vectors, %1.1e articles and %1.1e common" % \
                    (len(self.avl), len(self.wc2t.keys()), 
                     len(self.wvl))
        else:
            # Wikipedia articles and their canonical transformations
            self.wc2t = preloaded_actor.wc2t #Wiki dump article titles
            self.wt2c = preloaded_actor.wt2c
            # All vectors from word2vec
            self.avl  = preloaded_actor.avl #All word2vec
            self.aw2i = preloaded_actor.aw2i
            self.ai2w = preloaded_actor.ai2w
            # Just wikipedia vectors, indices
            self.wvl  = preloaded_actor.wvl # Intersection of word2vec
            self.ww2i = preloaded_actor.ww2i # and wikipedia dump
            self.wi2w = preloaded_actor.wi2w

    def validate(self, query):
        return '+' in query or '-' in query

    @timer
    def parse(self, query, kwargs=None):
        print "Query: ", query
        words = query.replace('+', '|').replace('-', '|')
        sign  = eval_sign(query)
        print "Sign : ", sign
        signs = ['+',]
        signs.extend([sign[match.start() + 1] \
                  for match in re.finditer('\|', words)])
        signs = [1.0 if s=='+' else -1.0 for s in signs]
        words = words.split('|')
        prewords  = words
        fwords = words
        ptitle = get_wiki_name(words[0])
        if len(ptitle) > 0:
            print "Wiki lookup %s -> %s" %(words[0], ptitle)
            title = [veclib.canonize(ptitle, self.ww2i, match=False)]
        else:
            title = [veclib.canonize(words[0], self.aw2i)]
        words = [veclib.canonize(a, self.aw2i) for a in words[1:]]
        words = title + words
        print 'Words: ',
        for a, b in zip(prewords, words):
            print a.strip(), ': ',
            print b.strip(),
        print ' '
        base = [self.wvl[self.ww2i[title[0]]]]
        vecs = [self.avl[self.aw2i[w]] for w in words[1:]]
        return [signs, base + vecs], {'query':query, 'words':words,
                    'fwords':fwords, 'ptitle':ptitle}
    
    @timer
    def evaluate(self, *args, **kwargs):
        signs, vecs = args
        words  = kwargs['words']
        fwords = kwargs['fwords']
        total = signs[0] * vecs[0]
        translated = ''
        for s, v, w in zip(signs, vecs, words):
            if s > 0:
                sign = '+'
                total += s * v
            else:
                sign = '-'
                total += s * v
            translated += ' %s %s' % (sign, w)
        start = time.time()
        manager = Manager()
        rv = manager.dict()
        expr_ncanon = veclib.nearest_word(total, self.wvl, self.wi2w, n=20)
        #root_ncanon = veclib.nearest_word(vecs[0], self.wvl, self.wi2w, n=10)
        #root_nwords = veclib.nearest_word(vecs[0], self.avl, self.ai2w, n=50)
        root_notable, root_types = get_freebase_types(fwords[0])
        #expr_nwords = veclib.nearest_word(total, self.avl, self.ai2w, n=50)
        results = []
        titles = [self.wc2t[c].strip() for c in expr_ncanon]
        pwfs = []
        gfts = []
        for title in titles:
            nwfs.append(self.pool.apply_async(get_wiki_name, [title]))
            pwfs.append(self.pool.apply_async(process_wiki, [title]))
            gfts.append(self.pool.apply_async(get_freebase_types, [title]))
        wiki_titles = []
        for title, pwf, gft, nft in zip(titles, pwfs, gfts, nfts):
            if title == kwargs['ptitle']:
                print "Skipping :", title
            wiki_title = nft.get()
            if title in words:
                print "Skipping :", title
            result = pwf.get()
            if result is not None and result['title'] not in wiki_titles:
                wiki_titles.append(result['title'])
            else:
                print "Repeat ", result['title']
                continue
            if reject_result(result):
                print "Rejected ", result['title']
                continue
            result_notable, result_types = gft.get()
            #if result_notable is not None and len(result_notable) > 5:
            #    result['description'] = result_notable
            result_types = sets.Set(result_types)
            root_types = sets.Set(root_types)
            both_types = result_types & root_types 
            if len(both_types) < 1:
                continue
                print "Skipping because not similar"
            print ("Freebase types to %s: " % title), result_types
            themes = [str(t) for t in both_types]
            themes = sorted(themes, key=lambda x: len(x))
            result['themes'] = themes[-2:]
            results.append(result)
        print "Finished at +%1.1s" % (time.time() - start)
        if len(results) ==0 :
            return {}
        self.pool.terminate()
        del self.pool
        self.pool = None
        query_text = kwargs['query']
        reps = dict(query_text=query_text, results=results, 
                    translated=translated)
        return reps

class Nearest(Expression):
    name = "Nearest"
    def validate(self, query):
        return '+' not in query and '-' not in query

    def parse(self, query, kwargs=None):
        words = query.replace('+', '|').replace('-', '|')
        word = words.split('|')[0]
        ptitle = get_wiki_name(word)
        if len(ptitle) > 0:
            print "Wiki lookup %s -> %s" %(word, ptitle)
            title = [veclib.canonize(ptitle, self.ww2i, match=False)]
        else:
            title = [veclib.canonize(words[0], self.aw2i)]
        canon = veclib.canonize(title[0], self.wc2t)
        return [canon], {'query':query, 'words':words}
    
    def evaluate(self, *args, **kwargs):
        canon, = args
        vector = veclib.lookup_vector(canon, self.wvl, self.ww2i)
        canons = veclib.nearest_word(vector, self.wvl, self.wi2w, n=50)
        print "Nearest: ", canons
        full_words = [self.wc2t[c] for c in canons]
        presults = self.pool.map(process_wiki, full_words)
        results = []
        for full_word, result in zip(full_words, presults):
            if result is not None:
                results.append(result)
                if len(results) > 4: break
        if len(results)==0:
            return {}
        query_text = kwargs['query']
        reps = dict(query_text=query_text, results=results)
        return reps

near = Nearest()
criteria = [Nearest(near), Expression(near), Passthrough()]
#criteria = [Passthrough()]

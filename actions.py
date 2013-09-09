import urllib2
import json
import veclib
import string
import re
import httplib
import urlparse
import sets
from sets import Set

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

    def run(self, query):
        args, kwargs = self.parse(query)
        reps = self.evaluate(*args, **kwargs)
        reps['actor'] = self.name
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
        result = get_omdb(arg)
        if result is None:
            return {}
        query_text = kwargs['query']
        reps = dict(query_text=query_text, results=[result])
        return reps

class Expression(Actor):
    name = "Expression"
    def __init__(self, preloaded_actor=None, subsample=False):
        """We need to load and preprocess all of the vectors into the 
           memory and persist them to cut down on IO costs"""
        if not preloaded_actor:
            trained = "/u/cmoody3/data2/ids/trained" 
            fnv = '%s/vectors.wiki.1000.num.npy' % trained
            fnw = '%s/vectors.wiki.1000.words' % trained
            fnr = '%s/articles.dict' % './data'
            fne = '%s/english' % './data'
            self.vl = veclib.get_vector_lib(fnv)
            self.vw2i , self.vi2w = veclib.get_words(fnw)
            assert self.vl.shape[0] == len(self.vw2i.keys())
            self.rc2f, self.rf2c = veclib.get_canon_rep(fnr)
            if subsample:
                english = sets.Set(veclib.get_english(fne))
                english = english.union(sets.Set(self.rc2f.keys()))
                rets = veclib.reduce_vectorlib(self.vl, self.vw2i, 
                                               english)
                self.vl, self.vw2i, self.vi2w = rets
                print "SUBSAMPLING! to %i words out of %i english words" \
                        % (len(self.vl), len(english))
            rets = veclib.reduce_vectorlib(self.vl, self.vw2i, 
                                           sets.Set(self.rc2f.keys()))
            self.cvl, self.cw2i, self.ci2w = rets
            # All movies at this point should exist in the 
            # canon set and in the vector set
            self.vset = sets.Set(self.vw2i.keys()) #from vector libs, is lowered
            self.rset = sets.Set(self.rc2f.keys()) #from reps, only canonical form
            self.cset = sets.Set(self.cw2i.keys()) #common word list
            assert len(self.cset) == len(self.cset.intersection(self.vset))
            assert len(self.cset) == len(self.cset.intersection(self.rset))
            print "Loaded in vector libs"
            import gc; gc.collect()
        else:
            self.vl   = preloaded_actor.vl
            self.vw2i = preloaded_actor.vw2i
            self.vi2w = preloaded_actor.vi2w
            self.rc2f = preloaded_actor.rc2f
            self.rf2c = preloaded_actor.rf2c
            self.cvl  = preloaded_actor.cvl
            self.cw2i = preloaded_actor.cw2i
            self.ci2w = preloaded_actor.ci2w
            self.cset = preloaded_actor.cset
            self.vset = preloaded_actor.vset
            self.rset = preloaded_actor.rset

    def validate(self, query):
        return '+' in query or '-' in query

    def parse(self, query, kwargs=None):
        print "Query: ", query
        words = query.replace('+', '|').replace('-', '|')
        sign  = eval_sign(query)
        print "Sign : ", sign
        signs = ['+',]
        signs.extend([sign[match.start() + 1] \
                  for match in re.finditer('\|', words)])
        signs = [1.0 if s=='+' else -1.0 for s in signs]
        print 'Words (pre) : ', words
        print 'Signs : ', signs
        words = words.split('|')
        movie = [veclib.canonize(words[0], self.cset)]
        nonmovie = [veclib.canonize(a, self.vset) for a in words[1:]]
        words = movie + nonmovie
        print 'Words (post): ', words
        base = [self.cvl[self.cw2i[words[0]]]]
        vecs = [self.vl[self.vw2i[w]] for w in words[1:]]
        return [signs, base + vecs], {'query':query, 'words':words}
    
    def evaluate(self, *args, **kwargs):
        signs, vecs = args
        words = kwargs['words']
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
        similar = veclib.nearest_word(vecs[0], self.cvl, self.ci2w, n=1)
        swords = veclib.nearest_word(vecs[0], self.vl, self.vi2w, n=100)
        movies = veclib.nearest_word(total, self.cvl, self.ci2w, n=50)
        print "Nearby words: ", swords, len(swords)
        print "Similar: ", similar
        print "Expression: ", movies
        swords = Set(swords)
        results = []
        full_movies = []
        for movie in movies:
            if len(results) >= 3: break
            if movie in similar:
                print "Skipping similar %s" % movie
                continue
            full_movie = self.rc2f[movie]
            result = get_omdb(full_movie)
            vec = self.cvl[self.cw2i[movie]]
            nwords = veclib.nearest_word(vec, self.vl, self.vi2w, n=100)
            themes = Set(nwords).intersection(swords).difference(Set(movies))
            print "In common %s:" % movie, themes
            result['themes'] = [t.replace('_',' ') for t in list(themes)]
            #import pdb; pdb.set_trace()
            #print "In between:", veclib.in_between(vecs[0], vec, self.vl, 
            #                                       self.vi2w)
            if result is not None:
                results.append(result)
            full_movies.append(full_movie)
        print "Non-Canonical: ", full_movies
        if len(results) ==0 :
            return {}
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
        movie = veclib.canonize(word, self.cset)
        print "Query: ", query, word, movie
        return [movie], {'query':query, 'words':words}
    
    def evaluate(self, *args, **kwargs):
        movie, = args
        vector = veclib.lookup_vector(movie, self.cvl, self.cw2i)
        movies = veclib.nearest_word(vector, self.cvl, self.ci2w, n=50)
        print "Result: ", movies
        results = []
        for movie in movies:
            full_word = self.rc2f[movie]
            result = get_omdb(full_word)
            if result is not None:
                results.append(result)
                if len(results) > 4: break
        print " "
        if len(results)==0:
            return {}
        query_text = kwargs['query']
        reps = dict(query_text=query_text, results=results)
        return reps

near = Nearest()
criteria = [Nearest(near), Expression(near), Passthrough()]

import urllib2
import json
import veclib
import string
import re

def get_omdb(name, google_images=False):
    """Search for the most relevant movie name on OMDB,
    then using that IMDB ID lookup get the rest of the
    information: description, actors, etc. Optionally 
    search Google Images for the poster image and hotlink
    it"""
    url = r"http://www.omdbapi.com/?t=%s" % urllib2.quote(name)
    response = urllib2.urlopen(url)
    odata = json.load(response)
    if 'Error' in odata.keys():
        print 'OMDB Error: %s' % name
        return None
    data = {k.lower():v for k, v in odata.iteritems()}
    return data

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
    def __init__(self):
        """We need to load and preprocess all of the vectors into the 
           memory and persist them to cut down on IO costs"""
        fnv = './data/vectors.bin.005.num.npy'
        fnw = './data/vectors.bin.005.words'
        fnc = './data/movies_canonical'
        fnr = './data/movies_rep'
        self.vl = veclib.get_vector_lib(fnv)
        self.w2i , self.i2w = veclib.get_words(fnw)
        self.c2f, self.f2c = veclib.get_canon_rep(fnr)
        self.movies, self.movie_text = veclib.read_canon_text(fnc)
        rv = veclib.reduce_vectorlib(self.vl, self.w2i, self.movies)
        self.mvl, self.mw2i, self.mi2w = rv
        print "Loaded in vector libs"

    def validate(self, query):
        return '+' in query and '-' in query

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
        words = words.split('|')
        movie = [veclib.canonize(words[0], self.c2f)]
        nonmovie = [veclib.canonize(a, self.w2i) for a in words[1:]]
        words = movie + nonmovie
        print 'Words (post): ', words
        base = veclib.lookup_vector(words[0], self.vl, self.w2i)
        vecs = [veclib.lookup_vector(w, self.vl, self.w2i) for w in words[1:]]
        return [signs, vecs], {'query':query}
    
    def evaluate(self, *args, **kwargs):
        signs, vecs = args
        total = signs[0] * vecs[0]
        for s, v in zip(signs, vecs):
            total += s * v
        word = veclib.nearest_word(total, self.mvl, self.mi2w)
        full_word = self.c2f[word]
        result = get_omdb(full_word)
        if result is None:
            return {}
        query_text = kwargs['query']
        reps = dict(query_text=query_text, results=[result])
        return reps

criteria = [Expression(), Passthrough()]

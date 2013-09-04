import urllib2
import json
import veclib
import string

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
        fnc = './data/movies_canonical"
        self.vl = veclib.get_vector_lib(fnv)
        self.w2i , self.i2w = veclib.get_words(fnw)
        self.movies, self.movie_text = read_canon_text(fnc)
        rv = veclib.reduce_vectorlib(self.vl, self.w2i, self.movies)
        self.mvl, self.mw2i, self.mi2w = rv

    def validate(self, query):
        return '+' in query and '-' in query

    def parse(self, query, kwargs=None):
        args = query.replace('+', '|').replace('-', '|')
        args = [a.strip() for a in args]
        return args
    
    def evaluate(self, *args, **kwargs):
        pass
criteria = [Passthrough()]

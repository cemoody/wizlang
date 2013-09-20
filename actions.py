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
import traceback
from multiprocessing import Manager
from sets import Set
import numexpr as ne
from wiki import *
from utils import *
import veclib

backend_url = r'http://localhost:5005/nearest/'

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
        start = time.time()
        if False:
            try:
                args, kwargs = self.parse(query)
                reps = self.evaluate(*args, **kwargs)
            except:
                traceback.print_exc()
                reps = {}
        else:
            args = self.parse(query)
            reps = self.evaluate(*args)
        reps['actor'] = self.name
        stop = time.time()
        reps['query_time'] = "%1.1f" %(stop - start)
        return reps

def result_chain(canonical, c2t):
    """Chain the decanonization, wiki lookup,
       wiki article lookup, and freebase all together"""
    title = canonical.replace('_', ' ')
    try:
        wikiname, article = pick_wiki(canonical)
    except:
        print "Error in ", canonical
        wikiname, article = None, None
    notable, types = None, []
    for search in (wikiname, title):
        try:
            notable, types = get_freebase_types(search)
            break
        except:
            pass
    return dict(wikiname=wikiname, article=article, notable=notable,
                types=types)
img = r"http://upload.wikimedia.org/wikipedia/commons/thumb/5/51/"
img += r"Warren_Buffett_KU_Visit.jpg/220px-Warren_Buffett_KU_Visit.jpg"
text =  "Warren Edward Buffett (August 30, 1930) is an American "
text += "business magnate, investor, and philanthropist. He is widely considered "
text += "the most successful investor of... the 20th century."
fake_results = [dict(info=dict(wikiname='Warren Buffet', 
                article=dict(description=text),
                types=['type1a', 'typ1b']), 
                themes=['type 1', 'type 2'], 
                url="http://en.wikipedia.org/wiki/Warren_buffet", 
                title="Warren Buffet",
                description=text,
                notable="Wealthy Person",
                img=img,
                similarity=0.56)]
fake_other   = dict(query='query', translated='translated query',
                    wikinames=[])

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
            trained = "data" 
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
            # all words, word to index mappings w2i
            if os.path.exists(fnw + '.pickle'):
                self.aw2i , self.ai2w = cPickle.load(open(fnw + '.pickle'))
            else:
                self.aw2i , self.ai2w = veclib.get_words(fnw)
                cPickle.dump([self.aw2i, self.ai2w], open(fnw + '.pickle','w'))
        else:
            # Wikipedia articles and their canonical transformations
            self.wc2t = preloaded_actor.wc2t #Wiki dump article titles
            self.wt2c = preloaded_actor.wt2c
            # All vectors from word2vec
            self.aw2i = preloaded_actor.aw2i
            self.ai2w = preloaded_actor.ai2w

    def validate(self, query):
        return len(query) > 3

    @timer
    @persist_to_file
    def parse(self, query, parallel=True, kwargs=None):
        """Debug with parallel=False, production use
        switch to multiprocessing"""
        # Split the query and find the signs of every word
        if query == 'None':
            return fake_results, fake_other
        words = query.replace('+', '|').replace('-', '|').replace(',', '|')
        sign  = eval_sign(query)
        signs = ['+',]
        signs.extend([sign[match.start() + 1] \
                  for match in re.finditer('\|', words)])
        signs = [1.0 if s=='+' else -1.0 for s in signs]
        words = words.split('|')
        # Get the canonical names for the query
        canon = self.aw2i.keys()
        if parallel:
            wc = lambda x: wiki_canonize(x, canon, use_wiki=False)
            rets  = [wiki_canonize(words[0], canon, use_wiki=True)]
            rets += parmap(wc, words[1:])
        else:
            rets  = [wiki_canonize(words[0], canon, use_wiki=True)]
            rets += [wiki_canonize(w, canon, use_wiki=False) for w in words[1:]]
        canonizeds, wikinames = zip(*rets)
        if wikinames[0] is None:
            return [], {}
        wikinames = [w if len(w)>0 else c for c, w in zip(canonizeds, wikinames)]
        # Make the translated query string
        translated = ""
        for sign, canonized in zip(signs, canonizeds):
            translated += "%+1.0f %s " %(sign, canonized)
        print 'translated: ', translated
        # Format the vector lib request
        args = []
        for sign, word, canonical in zip(signs, words, canonizeds):
            args.append([sign, canonical])
        send = json.dumps(dict(args=args))
        url = backend_url + urllib2.quote(send)
        response = json.load(urllib2.urlopen(url))
        response['query'] = query
        print response['result']
        # Decanonize the results and get freebase, article info
        if parallel:
            rc = lambda x: result_chain(x, self.wc2t)
            rv = parmap(rc, response['result'])
        else:
            n = 3
            rv = [result_chain(x, self.wc2t) for x in response['result']]
        args = (response['result'], response['similarity'], 
                response['root_similarity'], rv)
        args = sorted(zip(*args), key=lambda x:x[1])[::-1]
        results = []
        print args[:2]
        for c, s, r, v in args:
            print '%s %1.2f %s' % (s, r, v['wikiname'])
            if r > 0.75:
                continue
            if v['wikiname'] is None:
                continue
            results.append(dict(canonical=c, similarity=s, info=v))
        other = dict(query=query, translated=translated, wikinames=wikinames,
                     query_text=query)
        return results, other
    
    @timer
    def evaluate(self, dresults, other, max=2):
        previous_titles = []
        results = []
        max = results.get('max', max)
        for dresult in dresults:
            if len(results) > max: break
            wikiname = dresult['info']['wikiname']
            article  = dresult['info']['article']
            if wikiname in other['wikinames']:
                print 'Skipping direct in query', wikiname
                continue
            if wikiname in previous_titles: 
                print 'Skipping previous', wikiname
                continue
            result = {}
            result.update(article)
            result.update(dresult['info'])
            result['themes'] = dresult['info']['types'][:3]
            if len(result['themes']) == 0:
                print 'Skipping zero themes'
                continue
            result.update(dresult)
            result['similarity'] = "%1.2f" % result['similarity']
            results.append(result)
            previous_titles.append(wikiname)
        if len(results) == 0:
            return {}
        else:
            reps = dict(results=results)
            reps.update(other)
            return reps

from flask import *
from werkzeug.contrib.profiler import ProfilerMiddleware
from collections import defaultdict
import json
import sys
import cPickle
import os.path
import numpy as np

import veclib
from utils import *
 
app = Flask(__name__,  static_folder='static', 
            static_url_path='', template_folder='templates')

trained = "/home/ubuntu/data" 
fnv = '%s/vectors.fullwiki.1000.s50.5k.num.npy' % trained
fnw = '%s/vectors.fullwiki.1000.s50.5k.words' % trained
ffb = '%s/freebase_types_and_fullwiki.1000.s50.words' % trained
avl = veclib.get_vector_lib(fnv)
#avl = veclib.normalize(avl)
avl = veclib.split(veclib.normalize, avl)
if os.path.exists(fnw + '.pickle'):
    aw2i, ai2w = cPickle.load(open(fnw + '.pickle'))
else:
    aw2i, ai2w = veclib.get_words(fnw)
    cPickle.dump([aw2i, ai2w], open(fnw + '.pickle','w'))
frac = None
if frac:
    end = int(avl.shape[0] * frac)
    avl = avl[:end]
    for i in range(end, avl.shape):
        del aw2i[ai2w[i].pop()]

@app.route('/farthest/<raw_query>')
#@json_exception
def farthest(raw_query='{"args":["iphone", "ipad", "ipod", "walkman"]}'):
    """Given a list of arguments, calculate all the N^2 distance matrix
    and return the item farthest away. The total distance is just the 
    distance from a node to all other nodes seperately."""
    print 'QUERY'
    print raw_query
    query = json.loads(raw_query.strip("'"))
    nargs = len(query['args'])
    words = query['args']
    N2, N1, vectors = veclib.build_n2(words, avl, aw2i)
    inner, left, right = veclib.common_words(words, vectors, avl, aw2i, ai2w,
                                             N2, N1, blacklist=words)
    fb_words = [word.strip() for word in open(ffb).readlines()]
    fw2i = {w:i for i, w in enumerate(fb_words)}
    fi2w = {i:w for i, w in enumerate(fb_words)}
    idx = [aw2i[word] for word in fb_words]
    inner_fb, left_fb, right_fb = veclib.common_words(words, vectors, avl[idx], fw2i, fi2w,
                                             N2, N1, blacklist=words, n=1000)
    resp = {}
    resp['N1'] = [float(x) for x in N1]
    resp['args'] = words
    resp['inner'] = inner
    resp['inner_freebase'] = inner_fb[:50]
    resp['left'] = left
    resp['left_freebase'] = left_fb[:50]
    resp['right'] = right
    resp['right_freebase'] = right_fb[:50]
    resp['right_word'] = words[N1.argmin()]
    text = json.dumps(resp)
    return text

@app.route('/nearest/<raw_query>')
@timer
def nearest(raw_query='{"args": [[1.0, "jurassic_park"]]}'):
    """Given the expression, find the appropriate vectors, and evaluate it"""
    print 'QUERY'
    print raw_query
    try:
        query = json.loads(raw_query.strip("'"))
        total = None
        resp = defaultdict(lambda : list)
        resp['args'] = query['args']
        args_neighbors = []
        root_vectors = []
        for sign, word in query['args']:
            vector = avl[aw2i[word]]
            root_vectors.append(vector)
            if False:
                canon, vectors, sim = veclib.nearest_word(vector, avl, ai2w, n=20)
                args_neighbors.append(canon)
            else:
                args_neighbors.append([None])
            if total is None:
                total = vector * sign
            else:
                total += vector * sign
        total /= np.sum(total**2.0)
        canon, vectors, sim = veclib.nearest_word(total, avl, ai2w, n=20)
        root_sims = []
        for canonical, vector in zip(canon, vectors):
            sims = []
            for (sign, word), root_vector in zip(query['args'], root_vectors):
                total = (root_vector * vector).astype(np.float128)
                #total /= np.sqrt(np.sum(total ** 2.0))
                root_sim = np.sum(total,dtype=np.float128)
                sims.append(root_sim)
                print canonical, word, root_sim
            root_sims.append(np.max(sims))
            print canonical, max(sims)
        resp['result'] = canon
        resp['similarity'] = [float(s) for s in sim]
        resp['args_neighbors'] = args_neighbors
        resp['root_similarity'] = [float(s) for s in root_sims]
        send = {}
        send.update(resp)
        print resp
        text = json.dumps(send)
        print "RESPONSE"
        #print json.dumps(send, sort_keys=True,indent=4, separators=(',', ': '))
    except:
        print "ERROR"
        text = dict(error=str(sys.exc_info()))
        text = json.dumps(text)
        print text
    return text

if __name__ == '__main__':
    port = 5005
    try:
        port = int(sys.argv[-1])
        print "Serving port %i" % port
    except:
        pass
    use_flask = False
    if use_flask:
        app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    else:
        from twisted.internet import reactor
        from twisted.web.server import Site
        from twisted.web.wsgi import WSGIResource

        resource = WSGIResource(reactor, reactor.getThreadPool(), app)
        site = Site(resource)
        reactor.listenTCP(port, site, interface="0.0.0.0")
        reactor.run()
        print "Running"

    #app.run(host='0.0.0.0', port=port)

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
fnv = '%s/vectors.fullwiki.1000.s50.num.npy' % trained
fnw = '%s/vectors.fullwiki.1000.s50.words' % trained
avl = veclib.get_vector_lib(fnv)
avl = veclib.normalize(avl)
if os.path.exists(fnw + '.pickle'):
    aw2i, ai2w = cPickle.load(open(fnw + '.pickle'))
else:
    aw2i, ai2w = veclib.get_words(fnw)
    cPickle.dump([aw2i, ai2w], open(fnw + '.pickle','w'))

@app.route('/farthest/<raw_query>')
def similarity(raw_query='{"args":["iphone", "ipad", "ipod", "walkman"]}'):
    """Given a list of arguments, calculate all the N^2 distance matrix
    and return the item farthest away. The total distance is just the 
    distance from a node to all other nodes seperately."""
    print 'QUERY'
    print raw_query
    query = json.loads(raw_query.strip("'"))
    nargs = len(query['args'])
    N2 = np.zeros((nargs, nargs))
    resp = {}
    words = query['args']
    vectors = {word:avl[aw2i[word]] for word in words}
    for i, worda in enumerate(words):
        vectora = vectors[worda]
        for j, wordb in enumerate(words):
            if j == i: continue
            vectorb = vectors[wordb]
            dist = (vectora * vectorb).sum(dtype=np.float128)
            N2[i, j] = dist
            print worda, wordb, dist
    print N2
    N1 = np.sum(N2, axis=0)
    f = words[np.argmin(N1)]
    resp['N1'] = [float(x) for x in N1]
    resp['words'] = words
    resp['similarity'] = (f, float(N1.min()))
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
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)
    #app.run(host='0.0.0.0', port=port)

from flask import *
from werkzeug.contrib.profiler import ProfilerMiddleware
from collections import defaultdict
import json
import sys
import cPickle
import os.path

import veclib
from utils import *
 
app = Flask(__name__,  static_folder='static', 
            static_url_path='', template_folder='templates')

trained = "/home/ubuntu/data" 
fnv = '%s/vectors.fullwiki.1000.s50.num.npy' % trained
fnw = '%s/vectors.fullwiki.1000.s50.words' % trained
avl = veclib.get_vector_lib(fnv)
if os.path.exists(fnw + '.pickle'):
    aw2i, ai2w = cPickle.load(open(fnw + '.pickle'))
else:
    aw2i, ai2w = veclib.get_words(fnw)
    cPickle.dump([aw2i, ai2w], open(fnw + '.pickle','w'))

@app.route('/nearest/<raw_query>')
@timer
def nearest(raw_query='{"args": [[1.0, "jurassic_park"]]}'):
    """Given the expression, find the appropriate vectors, and evaluate it"""
    print 'QUERY'
    print raw_query
    query = json.loads(raw_query.strip("'"))
    total = None
    resp = defaultdict(lambda : list)
    resp['args'] = query['args']
    args_neighbors = []
    for sign, word in query['args']:
        vector = avl[aw2i[word]]
        canon, vectors = veclib.nearest_word(vector, avl, ai2w, n=20)
        args_neighbors.append(canon)
        if total is None:
            total = vectors[0]
        else:
            total += vectors[0]
    canon, vectors = veclib.nearest_word(vector, avl, ai2w, n=20)
    resp['result'] = canon
    resp['args_neighbors'] = args_neighbors
    text = json.dumps(resp)
    print "RESPONSE"
    print json.dumps(resp, sort_keys=True,indent=4, separators=(',', ': '))
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

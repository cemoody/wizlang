#!/usr/bin/env python
from flask import *
from actions import *
from werkzeug.contrib.profiler import ProfilerMiddleware
import sys
 
app = Flask(__name__,  static_folder='static', 
            static_url_path='', template_folder='templates')
expr = Expression()
criteria = [expr, Fraud(expr)]
@app.route('/results.html', methods=['GET', 'POST'])
@app.route('/search/<query>', methods=['GET', 'POST'])
def results(query="Jurassic Park"):
    if request.method == 'POST':
        query = request.form['query']
        quote = str(urllib2.quote(query))
        url = "/search/%s" % quote
        return redirect(url)
    else:
        reps = {}
        for actor in criteria:
            if actor.validate(query):
                print "Using Actor %s" % actor.name
                reps = actor.run(query)
                break
        return render_template('results.html', **reps)

@app.route('/wait/<query>')
def wait(query='', **kwargs):
    """ Throw up a wait page and immediately 
        redirect to query page
    """
    return render_template('wait.html', **reps)

@app.route('/', methods=['GET', 'POST'])
@app.route('/index.html', methods=['GET', 'POST'])
def index(query="Jurassic Park"):
    if request.method == 'POST':
        query = request.form['query']
        quote = str(urllib2.quote(query))
        url = "/search/%s" % quote
        return redirect(url)
    else:
        return render_template('index.html')

if __name__ == '__main__':
    #app.config['PROFILE'] = True
    #app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions = [30])
    twisted = False
    if twisted:
        from twisted.internet import reactor
        from twisted.web.server import Site
        from twisted.web.wsgi import WSGIResource

        resource = WSGIResource(reactor, reactor.getThreadPool(), app)
        site = Site(resource)
        reactor.listenTCP(8080, site, interface="0.0.0.0")
        reactor.run()
        print "Running"

    else:
        port = 5000
        try:
            port = int(sys.argv[-1])
            print "Serving port %i" % port
        except:
            pass
        app.run(host='0.0.0.0', port=port, use_reloader=False)

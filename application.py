from flask import *
from actions import *
from werkzeug.contrib.profiler import ProfilerMiddleware
 
app = Flask(__name__,  static_folder='static', 
            static_url_path='', template_folder='templates')

@app.route('/results.html', methods=['GET', 'POST'])
@app.route('/search/<query>', methods=['GET', 'POST'])
def results(query="Jurassic Park"):
    if request.method == 'POST':
        query = request.form['query']
        quote = str(urllib2.quote(query))
        url = "/search/%s" % quote
        return redirect(url)
    else:
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

@app.route('/index.html', methods=['GET', 'POST'])
def index():
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
    app.run(host='0.0.0.0', port=5001, debug=True, use_reloader=False)

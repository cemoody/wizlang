from flask import *
import re
import urllib2
import json
 
app = Flask(__name__,  static_folder='static', 
            static_url_path='', template_folder='templates')

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

def movie_passthrough(name, *args, **kwargs):
    """ This will lookup the movie name
    on OMDB, ignore the other arguments
    and return a 'result' of the same 
    movie """
    result = get_omdb(name)
    if result is None:
        return {}
    result['original'] = name
    query_text = name + ' '.join(args)
    reps = dict(query_text=query_text, results=[result])
    return reps

def parse(query):
    action = movie_passthrough
    args = query.replace('-', '|').replace('+', '|')
    args = args.split('|')
    reps = action(*args)
    kwargs = {}
    return action, args, kwargs

@app.route('/results.html', methods=['GET', 'POST'])
@app.route('/search/<query>', methods=['GET', 'POST'])
def results(query="Jurassic Park"):
    if request.method == 'POST':
        query = request.form['query']
        quote = str(urllib2.quote(query))
        url = "/search/%s" % quote
        return redirect(url)
    action, args, kwargs = parse(query)
    reps = action(*args, **kwargs)
    return render_template('results.html', **reps)

@app.route('/index.html', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        query = request.form['query']
        quote = str(urllib2.quote(query))
        url = "/search/%s" % quote
        return redirect(url)
    return render_template('index.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

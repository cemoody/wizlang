from flask import render_template, Flask, escape
import re
import urllib2
import json
 
app = Flask(__name__,  static_folder='static', 
            static_url_path='', template_folder='templates')

@app.route('/index.html')
def main():
    return render_template('index.html')

def get_omdb(name, google_images=False):
    """Search for the most relevant movie name on OMDB,
    then using that IMDB ID lookup get the rest of the
    information: description, actors, etc. Optionally 
    search Google Images for the poster image and hotlink
    it"""
    url = r"http://www.omdbapi.com/?t=%s" % urllib2.quote(name)
    response = urllib2.urlopen(url)
    odata = json.load(response)
    data = {k.lower():v for k, v in odata.iteritems()}
    return data

def movie_passthrough(name, *args, **kwargs):
    """ This will lookup the movie name
    on OMDB, ignore the other arguments
    and return a 'result' of the same 
    movie """
    result = get_omdb(name)
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

@app.route('/search/<query>')
def results(query):
    action, args, kwargs = parse(query)
    reps = action(*args, **kwargs)
    return render_template('results.html', **reps)

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

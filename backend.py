from flask import *
from actions import *
from werkzeug.contrib.profiler import ProfilerMiddleware
import sys
 
app = Flask(__name__,  static_folder='static', 
            static_url_path='', template_folder='templates')

near = veclib.Nearest()
criteria = [Nearest(near), Expression(near), Passthrough()]

@app.route('/json/<query>')
def results(query="jurassic_park"):
    canon = veclib.nearest_word(query, self.wvl, self.wi2w, n=20)
    return render_template('results.html', **reps)

if __name__ == '__main__':
    port = 5005
    try:
        port = int(sys.argv[-1])
        print "Serving port %i" % port
    except:
        pass
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)

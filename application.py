from flask import render_template
 
app = flask.Flask(__name__,  static_folder='static', 
                  template_folder='templates')

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/search/<search>')
def results():
    return render_template('results.html')

if __name__ == '__main__':
    application.run(host='0.0.0.0')

from flask import render_template, Flask
 
app = Flask(__name__,  static_folder='static', 
            static_url_path='', template_folder='templates')

@app.route('/index.html')
def main():
    return render_template('index.html')

@app.route('/search/<search>')
def results(search):
    return render_template('results.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)

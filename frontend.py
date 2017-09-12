from flask import Flask
from flask import render_template

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/player')
def player():
    return render_template('player.html')


if __name__ == '__main__':
    app.run()

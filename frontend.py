from flask import Flask
from flask import render_template
import requests
import json

app = Flask(__name__)


@app.route('/')
def index():
    r = requests.get("http://127.0.0.1:5000/playlist")
    playlist = json.loads(r.text)
    return render_template('index.html', playlist=playlist)


@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/player')
def player():
    return render_template('player.html')


if __name__ == '__main__':
    app.run(port=5001)

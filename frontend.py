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


@app.route('/search/<name>')
def search(name):
    params = {
        "render": "json",
        "locale": "fr-FR",
        "call": name,
        "query": name,
        "c": "stations"
    }
    r = requests.get("https://opml.radiotime.com/Search.ashx", params=params)
    return r.text

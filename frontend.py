from flask import Flask, render_template, request
import requests
import json


# some config
backend_url = "http://127.0.0.1:5000"
tunein_url  = "https://opml.radiotime.com"

# Flask app
app = Flask(__name__)

#
# Helpers
#

# parse search result from tunein
def parse_search(data):
    # print(data)
    qr_name = data['head']['title']
    search_result = []
    search_error = {}
    if data['head']['status'] == "200":
        for r in data['body']:
            if 'type' in r:
                if r['type'] == 'audio':
                    search_result.append({
                        'text': r['text'],
                        'img': r['image'],
                        'url': r['URL']
                    })
            elif 'children' in r:
                search_error = {'text': 'No result'}
            else:
                search_error = {'text': r['text']}
    else:
        search_error = {'code': data['head']['status']}
    return qr_name, search_result, search_error


#
# Routes
#
@app.route('/')
def index():
    r = requests.get("%s/playlist" % backend_url)
    playlist = json.loads(r.text)
    return render_template('index.html', playlist=playlist)


@app.route('/player')
def player():
    return render_template('player.html')


@app.route('/search', methods=['POST', 'GET'])
def search():
    qrn = "" # query
    sr  = [] # results
    se  = {} # error
    if request.method == 'POST':
        params = {
            "render": "json",
            "locale": "en-US",
            "call": request.form['name'],
            "query": request.form['name'],
            "c": "stations"
        }
        r = requests.get("%s/Search.ashx" % tunein_url, params=params)
        qrn, sr, se = parse_search(json.loads(r.text))
    # test only
    else:
        qrn, sr, se = parse_search(json.load(open('tunein_res.json')))

    return render_template('search.html', sr=sr, se=se, name=qrn)

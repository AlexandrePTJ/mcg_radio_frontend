# coding: utf-8

from sqlite3 import dbapi2 as sqlite3
from flask import Flask, render_template, request, g, redirect
import requests
import json
import os


# Flask app
app = Flask(__name__)
app.config.from_object(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, '../mcg_radio.db'),
    BACKEND_URL="http://127.0.0.1:5000",
    TUNEIN_URL="https://opml.radiotime.com"
))


#
# Helpers
#
def connect_db():
    """Connects to the specific database."""
    rv = sqlite3.connect(app.config['DATABASE'])
    rv.row_factory = sqlite3.Row
    return rv


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


def get_next_position(db):
    """ Find hole in positions """
    cur = db.execute("SELECT MAX(position) FROM stations ORDER BY position ASC")
    r = cur.fetchone()
    return 1 if r[0] is None else r[0] + 1


def get_positions(db):
    """ Return current positions occupied """
    cur = db.execute("SELECT position FROM stations ORDER BY position ASC")
    return [r[0] for r in cur]


def insert_station(db, name, position, stream_url, image_url, volume=80):
    """ Create a new station entry """
    db.execute(
        "INSERT INTO stations(name,position,stream_url,image_url,volume) VALUES (?,?,?,?,?)",
        (name, position, stream_url, image_url, volume)
    )
    db.commit()


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()


def parse_search(data):
    """ parse search result from tunein """
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


def extract_stream_url(ashx_url):
    """ Extract real stream url from tunein stream url """
    r = requests.get(ashx_url)
    for l in r.text.splitlines():
        if len(l) != 0:
            return l


#
# Routes
#
@app.route('/')
def index():
    db = get_db()
    cur = db.execute("SELECT * FROM stations ORDER BY position ASC")
    stations = cur.fetchall()
    return render_template('index.html', stations=stations)


@app.route('/handle_station', methods=['POST'])
def handle_station():
    real_stream_url = extract_stream_url(request.form['stream_url'])
    if request.form.get('add'):
        db = get_db()
        insert_station(db, request.form['name'], get_next_position(db), real_stream_url, request.form['image_url'])
    elif request.form.get('play'):
        params = {"url": real_stream_url}
        requests.get("%s/play" % app.config['BACKEND_URL'], params=params)
    return redirect('/')


@app.route('/new', methods=['POST', 'GET'])
def new_station():
    db = get_db()

    if request.method == 'POST':
        insert_station(db,
                       request.form['name'],
                       request.form['position'],
                       request.form['stream_url'],
                       request.form['image_url'],
                       request.form['volume'])
        return redirect('/')

    positions = get_positions(db)
    return render_template('edit.html', station={}, positions=positions)


@app.route('/edit/<station_id>', methods=['POST', 'GET'])
def edit_station(station_id):
    db = get_db()

    if request.method == 'POST':
        db.execute(
            "UPDATE stations SET name=?,position=?,stream_url=?,image_url=?,volume=? WHERE id=?",
            (
                request.form['name'],
                request.form['position'],
                request.form['stream_url'],
                request.form['image_url'],
                request.form['volume'],
                station_id
            )
        )
        db.commit()
        return redirect('/')

    cur = db.execute("SELECT * FROM stations WHERE id=?", (station_id,))
    station = cur.fetchone()
    positions = get_positions(db)
    positions.remove(station['position'])
    return render_template('edit.html', station=station, positions=positions)


@app.route('/remove/<station_id>')
def remove_station(station_id):
    db = get_db()
    db.execute("DELETE FROM stations WHERE id=?", (station_id,))
    db.commit()
    return redirect('/')


@app.route('/search', methods=['POST', 'GET'])
def search():
    qrn = "" # query
    sr  = [] # results
    se  = {} # error
    if request.method == 'POST':
        params = {
            "render": "json",
            "call": request.form['name'],
            "query": request.form['name'],
            "c": "stations"
        }
        r = requests.get("%s/Search.ashx" % app.config['TUNEIN_URL'], params=params)
        qrn, sr, se = parse_search(json.loads(r.text))

    return render_template('search.html', sr=sr, se=se, name=qrn)


@app.route('/play/<station_id>')
def play_station(station_id):
    params = { "id": station_id }
    requests.get("%s/play" % app.config['BACKEND_URL'], params=params)
    return redirect('/')


@app.route('/shutdown')
def shutdown():
    requests.get("%s/shutdown" % app.config['BACKEND_URL'])
    return redirect('/')

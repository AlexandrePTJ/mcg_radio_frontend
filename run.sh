#!/bin/sh

export FLASK_DEBUG=1
export FLASK_APP=frontend.py

flask run --port=5001

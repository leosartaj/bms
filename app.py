import atexit
import flask
from flask import request, jsonify, Flask, session
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import os
import pandas as pd

from bms import Scrapper, Notifier, HISTORY_DEFAULT


# Check Configuration section for more details
# setup
WATCHING_PATH = 'data/movies.txt'
THEATERS_PATH = 'data/theaters.txt'
EMAILS_PATH = 'data/emails.txt'
HISTORY_PATH = 'data/{}'.format(HISTORY_DEFAULT)
LISTINGS_PATH = '{}_listings.json'.format(HISTORY_PATH)
UPDATED_PATH = '{}_updated.txt'.format(HISTORY_PATH)
BMS_USER = os.environ['BMS_USER']
BMS_PASS = os.environ['BMS_PASS']
SCRAPPER = Scrapper(WATCHING_PATH, THEATERS_PATH, HISTORY_PATH)
NOTIFIER = Notifier(EMAILS_PATH, BMS_PASS, BMS_USER)


app = Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    return "BMS notification service. (Version: Alpha)"


@app.route('/movies', methods=['GET'])
def get_movies():
    watching = SCRAPPER.watching
    return jsonify(watching)


@app.route('/theaters', methods=['GET'])
def get_theaters():
    theaters = SCRAPPER.theaters
    return jsonify(theaters)


import json
@app.route('/listings', methods=['GET'])
def listings():
    with open(LISTINGS_PATH) as f:
        ls = f.read()
        ls = json.loads(ls)
    with open(UPDATED_PATH) as f:
        updated = f.read()
        ls['updated'] = updated
    result = '{}'.format(ls)
    return jsonify(result)


def scrape_notify():
    listing_dates = SCRAPPER.get_listing_dates()
    movies = SCRAPPER.scrape(listing_dates, verbose=True, update=True)

    if len(movies):
        SCRAPPER.save_history()
        #NOTIFIER.notify(movies)



# schedule scraping operation
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape_notify, trigger="interval", seconds=10)
scheduler.start()
# cleanup at app stop time
atexit.register(lambda: scheduler.shutdown())

app.run()

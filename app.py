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
BMS_USER = os.environ['BMS_USER']
BMS_PASS = os.environ['BMS_PASS']


app = Flask(__name__)
app.config["DEBUG"] = True


@app.route('/', methods=['GET'])
def home():
    return "BMS notification service. (Version: Alpha)"


@app.route('/emails', methods=['GET'])
def get_emails():
    emails = notifier.emails
    return jsonify(emails)


@app.route('/movies', methods=['GET'])
def get_movies():
    watching = scrapper.watching
    return jsonify(watching)


@app.route('/theaters', methods=['GET'])
def get_theaters():
    theaters = scrapper.theaters
    return jsonify(theaters)


@app.route('/listings', methods=['GET'])
def listings():
    with open('data/.bms_history.csv_listings.json') as f:
        ls = f.read()
    with open('data/.bms_history.csv_updated.txt') as f:
        updated = f.read()
    result = '{}\n\n{}'.format(ls, updated)
    return jsonify(result)


def scrape_notify(scrapper, notifier):
    listing_dates = scrapper.get_listing_dates()
    movies = scrapper.scrape(listing_dates, verbose=True, update=True)

    if len(movies):
        scrapper.save_history()
        #notifier.notify(movies)


if __name__ == '__main__':
    scrapper = Scrapper(WATCHING_PATH, THEATERS_PATH, HISTORY_PATH)
    notifier = Notifier(EMAILS_PATH, BMS_PASS, BMS_USER)

    # schedule scraping operation
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=scrape_notify, args=(scrapper, notifier),
                      trigger="interval", seconds=10)
    scheduler.start()
    # cleanup at app stop time
    atexit.register(lambda: scheduler.shutdown())

    app.secret_key = 'A0Zr98j/3yX R~XHH!jmN]LWX/,?RT'
    app.run()

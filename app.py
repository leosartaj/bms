import atexit
import flask
from flask import request, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import os
import pandas as pd

from bms import Scrapper, Notifier, HISTORY_DEFAULT

# setup
WATCHING_PATH = 'data/movies.txt'
THEATERS_PATH = 'data/theaters.txt'
EMAILS_PATH = 'data/emails.txt'
HISTORY_PATH = 'data/{}'.format(HISTORY_DEFAULT)
BMS_USER = os.environ['BMS_USER']
BMS_PASS = os.environ['BMS_PASS']


app = flask.Flask(__name__)
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


def scrape():
    print('Test Scrape')


scrapper = Scrapper(WATCHING_PATH, THEATERS_PATH, HISTORY_PATH)
notifier = Notifier(EMAILS_PATH, BMS_PASS, BMS_USER)

# schedule scraping operation
scheduler = BackgroundScheduler()
scheduler.add_job(func=scrape, trigger="interval", minutes=1)
scheduler.start()
atexit.register(lambda: scheduler.shutdown())

app.run()

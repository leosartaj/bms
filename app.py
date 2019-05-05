import flask
from flask import request, jsonify
from bms import load_data
import pandas as pd


WATCHING_PATH = 'data/movies.txt'
THEATERS_PATH = 'data/theaters.txt'
EMAILS_PATH = 'data/emails.txt'


app = flask.Flask(__name__)
app.config["DEBUG"] = True


def load():
    watching, theaters, emails = load_data(WATCHING_PATH, THEATERS_PATH,
                                           EMAILS_PATH)
    return watching, theaters, emails


@app.route('/', methods=['GET'])
def home():
    return "BMS notification service. (Version: Alpha)"


@app.route('/emails', methods=['GET'])
def get_emails():
    _, _, emails = load()
    return jsonify(emails)


@app.route('/addemail', methods=['GET'])
def add_email():
    result = 'Error: No email registered. Please specify email.'
    if 'email' in request.args:
        email = request.args['email']
        with open(EMAILS_PATH, 'a') as f:
            f.write('{}\n'.format(email))
        result = '{} successsfully registered'.format(email)
    return jsonify(result)


@app.route('/rmemail', methods=['GET'])
def rm_emails():
    result = 'Error: No email de-registered. Please specify email.'
    if 'email' in request.args:
        email = request.args['email']
        emails = pd.read_csv(EMAILS_PATH, header=None)
        reg_num = emails.shape[0]
        emails = emails.loc[emails[0] != email, :]
        if (reg_num - emails.shape[0]) == 1:
            result = '{} successsfully de-registered.'.format(email)
            emails.to_csv(EMAILS_PATH, index=False, header=None)
        else:
            result = 'Error: {} not registered'.format(email)

    return jsonify(result)


@app.route('/movies', methods=['GET'])
def get_movies():
    watching, _, _ = load()
    return jsonify(watching)


@app.route('/theaters', methods=['GET'])
def get_theaters():
    _, theaters, _ = load()
    return jsonify(theaters)


app.run()

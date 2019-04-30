import os
import time
from collections import defaultdict
import datetime

import smtplib
from email.message import EmailMessage
import requests

from bs4 import BeautifulSoup
import pandas as pd


def load_data(movies_list, theaters_list, email_list):
    with open(movies_list) as f:
        watching = f.read().strip('\n').split('\n')

    theaters = {}
    with open(theaters_list) as f:
        for line in f:
            theater, url = line.split(',')
            theaters[theater.strip(' ')] = url.strip('\n').strip(' ')

    for theater, url in theaters.items():
        url = '{}/'.format(url.rstrip('/'))
        theaters[theater] = url

    with open('data/email_list.txt', 'r') as f:
        emails = f.read().strip('\n').split('\n')

    return watching, theaters, emails


def get_date(date, offset=None):
    if offset:
        offset_days = datetime.timedelta(days=offset)
        date = date + offset_days
    year = date.year
    day = date.day
    month = date.month
    date = '{:04d}{:02d}{:02d}'.format(year, month, day)
    return date


def get_listing_dates(check_days=7):
    now = datetime.datetime.now()
    listing_dates = [get_date(now, offset=i) for i in range(check_days)]
    return listing_dates


def load_history(history_file):
    if os.path.isfile(history_file):
        history = pd.read_csv(history_file)
    else:
        history = pd.DataFrame([], columns=['date', 'movie', 'dest'])

    return history



def connect_server(user, psw):
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(user, psw)
    except:
        raise ValueError('Something went wrong while connecting to gmail...')

    return server


def notify(emails, movies):
    server = connect_server(BMS_USER, BMS_PASS)

    movie_names = ','.join(movies.keys())
    subject = 'New Listings for {}'.format(movie_names)

    body = ''
    for movie_name in movies.keys():
        body += '{}\n'.format(movie_name)
        for date, dest, times in movies[movie_name]:
            times = ' '.join(times)
            day = pd.to_datetime(date).day_name()
            body += '{}, {}, {} => {}\n\n'.format(dest, day, date, times)
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = BMS_USER
    msg['To'] = emails

    server.send_message(msg)


def bms_scrapper(watching, destinations, listing_dates, history, is_notify=False):
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11'
            '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
        'Accept-Encoding': 'none',
        'Accept-Language': 'en-US,en;q=0.8',
        'Connection': 'keep-alive'}

    movies = defaultdict(list)
    for date in listing_dates:
        frm_date = '{}-{}-{}'.format(date[-2:], date[4:6], date[:4])
        for movie_name in watching:
            for dest, dest_url in destinations.items():
                logged = history.loc[(history['date'] == int(date))&(history['movie'] == movie_name)&(history['dest'] == dest), :]
                if logged.shape[0] != 0:
                    print('Already Notified for {}, {}'.format(frm_date, movie_name))
                    continue
                movie_date_url = '{}{}'.format(dest_url, date)
                time.sleep(1)
                movie_date_info = requests.get(movie_date_url, params=headers)
                if date not in movie_date_info.url:
                    print('{} not listed for {}'.format(movie_name, frm_date))
                    break
                movie_date_html = BeautifulSoup(movie_date_info.text, features='lxml')
                containers = movie_date_html.find_all('div', attrs={'class': 'container'})
                container = containers[2]
                available_times = []
                for movie in container.find_all('li', attrs={'class': 'list'}):
                    try:
                        curr_movie_name = movie.find('strong').text
                    except AttributeError:
                        try:
                            curr_movie_name = movie.find('span',
                                                     attrs={'class': '__name'}).text
                        except AttributeError:
                            continue
                    curr_movie_name = curr_movie_name.strip('\n').strip(' ')
                    if movie_name not in curr_movie_name:
                        continue
                    body = movie.find('div', attrs={'class': 'body'})
                    listings = body.find_all('div')
                    available = filter(lambda listing: listing['data-oline'] == 'Y', listings)
                    available_times.extend(list(map(lambda listing: listing.text, available)))
                history = history.append([{'movie': movie_name, 'date': int(date), 'dest': dest}])
                if len(available_times):

                    available_times = map(lambda x: x[:x.find('M')+1], available_times)
                    available_times = map(lambda x: x.replace('\t', '').strip('\n'),
                                          available_times)
                    available_times = list(available_times)
                    movies[movie_name].append((frm_date, dest, available_times))
    if len(movies) and is_notify:
        notify(emails, movies)

    return history


if __name__ == '__main__':
    is_notify = False
    BMS_USER = os.environ['BMS_USER']
    BMS_PASS = os.environ['BMS_PASS']

    movies_list = 'data/movies.txt'
    theaters_list = 'data/theaters.txt'
    emails_list = 'data/emails_list.txt'
    watching, theaters, emails = load_data(movies_list, theaters_list, emails_list)

    history_file = 'data/.bms_scrapper.csv'
    history = load_history(history_file)

    listing_dates = get_listing_dates()

    history = bms_scrapper(watching, theaters, listing_dates, history, is_notify=is_notify)

    history.to_csv(history_file, index=False)

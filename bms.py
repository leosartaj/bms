import argparse
import os
import time
from collections import defaultdict
import datetime

import smtplib
from email.message import EmailMessage
import requests

from bs4 import BeautifulSoup
import pandas as pd


def get_date(date, offset=None):
    if offset:
        offset_days = datetime.timedelta(days=offset)
        date = date + offset_days
    year = date.year
    day = date.day
    month = date.month
    date = '{:04d}{:02d}{:02d}'.format(year, month, day)
    return date


class Scrapper(object):
    def __init__(self, movies_list, theaters_list, history_file):
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

        self.movies_list = movies_list
        self.theaters_list = theaters_list
        self.load_lists()

        self.history_file = history_file
        self.load_history()


    def load_lists(self):
        movies_list = self.movies_list
        theaters_list = self.theaters_list

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

        self.watching = watching
        self.theaters = theaters


    def get_listing_dates(self, check_days=7):
        now = datetime.datetime.now()
        listing_dates = [get_date(now, offset=i) for i in range(check_days)]
        return listing_dates


    def load_history(self):
        history_file = self.history_file
        if os.path.isfile(history_file):
            history = pd.read_csv(history_file)
        else:
            history = pd.DataFrame([], columns=['date', 'movie', 'dest', 'time'])

        self.history = history

        return history


    def save_history(self):
        self.history.to_csv(self.history_file, index=False)


    def scrape(self, listing_dates, verbose=False, wait=1):
        watching = self.watching
        destinations = self.theaters
        history = self.history

        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11'
                '(KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.3',
            'Accept-Encoding': 'none',
            'Accept-Language': 'en-US,en;q=0.8',
            'Connection': 'keep-alive'}

        movies = defaultdict(list)
        completed = False
        for date in listing_dates:
            frm_date = '{}-{}-{}'.format(date[-2:], date[4:6], date[:4])
            for movie_name in watching:
                for dest, dest_url in destinations.items():
                    logged = history.loc[(history['date'] == int(date))&(history['movie'] == movie_name)&(history['dest'] == dest), :]
                    if logged.shape[0] != 0:
                        if verbose:
                            print('Already Notified for {}, {}'.format(frm_date,
                                                                    movie_name))
                        continue
                    movie_date_url = '{}{}'.format(dest_url, date)
                    time.sleep(wait)
                    movie_date_info = requests.get(movie_date_url, params=headers)
                    if date not in movie_date_info.url:
                        if verbose:
                            print('{} not listed for {}'.format(movie_name, frm_date))
                        completed = True
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
                    history = history.append([{'movie': movie_name, 'date': int(date),
                                            'dest': dest, 'times':available_times}])
                    if len(available_times):

                        available_times = map(lambda x: x[:x.find('M')+1], available_times)
                        available_times = map(lambda x: x.replace('\t', '').strip('\n'),
                                            available_times)
                        available_times = list(available_times)
                        movies[movie_name].append((frm_date, dest, available_times))
            else:
                if completed:
                    break

        # update history
        self.history = history

        return movies


class Notifier(object):
    def __init__(self, emails_list, user, psw):
        self.emails_list = emails_list
        self.user = user
        self.psw = psw
        self.load_emails()


    def load_emails(self):
        emails_list = self.emails_list
        with open(emails_list) as f:
            emails = f.read().strip('\n').split('\n')

        self.emails = emails


    def connect_server(self):
        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.ehlo()
            server.login(self.user, self.psw)
        except:
            raise ValueError('Something went wrong while connecting to gmail...')

        self.server = server

        return server


    def notify(self, movies):
        server = self.connect_server()

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
        msg['From'] = self.user
        msg['To'] = self.emails

        server.send_message(msg)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='BookMyShow movie listing'
                                     ' notifier.')

    parser.add_argument('movies_list', help='List of movies to watch for')
    parser.add_argument('theaters_list', help='Theaters to check for listings')

    parser.add_argument('-e', '--emails_list', help='List of emails to notify',
                        default=False)
    parser.add_argument('-u', '--user', help='Account to use for sending emails',
                        default=False)
    parser.add_argument('-p', '--psw', help='password of account to use for '
                        'sending emails',
                        default=False)

    parser.add_argument('-c', '--cache', help='History file to use',
                        default='.bms_history.csv')

    parser.add_argument('-d', '--days', help='Number of days to check for'
                        ' (default is today i.e 1)', type=int, default=1)

    parser.add_argument('--debug', action="store_true",
                        help='verbose mode')
    args = parser.parse_args()

    movies_list = args.movies_list
    theaters_list = args.theaters_list

    is_notify = False
    if args.emails_list:
        is_notify = True
        if args.user:
            BMS_USER = args.user
        else:
            BMS_USER = os.environ['BMS_USER']
        if args.psw:
            BMS_PASS = args.psw
        else:
            BMS_PASS = os.environ['BMS_PASS']
        emails_list = args.emails_list

        notifier = Notifier(emails_list, BMS_USER, BMS_PASS)
    else:
        emails_list = None
        notifier = None

    history_file = args.cache
    scraper = Scrapper(movies_list, theaters_list, history_file)

    listing_dates = scraper.get_listing_dates(check_days=args.days)

    movies = scraper.scrape(listing_dates, verbose=args.debug)

    scraper.save_history()

    if emails_list and len(movies):
        notifier.notify(movies)

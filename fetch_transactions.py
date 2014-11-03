#!/usr/bin/env python

import os
import sys
import datetime
import pprint
import requests
import ConfigParser
from urlparse import urljoin
from bs4 import BeautifulSoup

class Session(object):
    def __init__(self, account):
        self.account = account
        self._load_config()
        self.last_url = None
        self.cookies = {}

    def _load_config(self):
        self.Config = ConfigParser.ConfigParser()
        dirname, filename = os.path.split(os.path.realpath(__file__))
        file_base, file_ext = os.path.splitext(filename)
        ini_file = os.path.join(dirname, '%s.ini' % file_base)
        assert os.path.exists(ini_file), 'There is no config file %r.' % ini_file
        assert os.access(ini_file, os.R_OK), 'Config file is not readable.'
        assert oct(os.stat(ini_file).st_mode & 0777).endswith('00'), 'Config file permissions are too open. Do:\nchmod 0600 %s' % ini_file
        self.Config.read(ini_file)
        accounts = self.Config.sections()
        assert accounts, 'There are no accounts configured'
        assert self.account in accounts, 'There is no section for account %s in config file.' % self.account

    def conf(self, param):
        return self.Config.get(self.account, param)

    def get(self, location, post=False, post_data=None, track_last_url=True):
        url = urljoin(self.last_url, location)
        kwargs = {}
        #kwargs['headers'] = {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)'}

        if self.cookies:
            kwargs['cookies'] = self.cookies

        if post:
            r = requests.post(url, data=post_data, **kwargs)
        else:
            r = requests.get(url, **kwargs)

        assert r.ok

        for h in r.history or () + (r,):
            if h.cookies:
                self.cookies.update(h.cookies.get_dict())

        if track_last_url:
            self.last_url = r.request.url

        return r.text.encode('utf8')

    def logout(self, content):
        try:
            soup = BeautifulSoup(content)
            logout = soup.find('li', class_='logout').find('a').get('href')
        except AttributeError:
            assert False, 'Could not find logout link. Maybe we are not logged in.'

        content = self.get(logout)
        save('log/logged_out.html', content)

def get_cwd():
    return os.path.dirname(os.path.realpath(__file__))

def save(file_name, content):
    cwd = get_cwd()
    subdir = os.path.join(cwd, os.path.dirname(file_name))
    if not os.path.isdir(subdir):
        os.makedirs(subdir)
    file_path = os.path.join(cwd, file_name)
    f = open(file_path, 'w')
    f.write(content)
    f.close()

def read(file_name):
    cwd = get_cwd()
    file_path = os.path.join(cwd, file_name)
    f = open(file_path, 'r')
    content = f.read()
    f.close()

    return content

def main(account):
    sess = Session(account)
    content = sess.get('https://banking.postbank.de')
    save('log/login.html', content)
    #content = read('log/login.html')
    soup = BeautifulSoup(content)
    login_form = soup.find('form', class_='form-cn')
    login_data = {}
    for inp in login_form.find_all(['input', 'button']):
        login_data[inp.get('name')] = inp.get('value')

    login_data['nutzername'] = sess.conf('user')
    login_data['kennwort'] = sess.conf('pass')

    # login
    content = sess.get(login_form.get('action'), post=True, post_data=login_data)
    save('log/logged_in.html', content)
    #content = read('log/logged_in.html')
    soup = BeautifulSoup(content)
    transactions = soup.find('li', class_='ng-transactions').find('a').get('href')

    # get transactions
    content = sess.get(transactions)
    save('log/transcations.html', content)
    #content = read('log/transcations.html')
    soup = BeautifulSoup(content)
    trans_form = soup.find('form')
    trans_data = {}
    for sel in trans_form.find_all('select'):
        for opt in sel.find_all('option'):
            if not sel.get('value', 1) or opt.get('selected'):
                sel['value'] = opt.get('value', '')

    today = datetime.date.today()
    date_format = '%d.%m.%Y'
    trans_form.find('div', class_='fld-date-bis').find('input')['value'] = today.strftime(date_format)
    trans_form.find('div', class_='fld-date-von').find('input')['value'] = (today - datetime.timedelta(95)).strftime(date_format)

    for el in trans_form.find_all(['input', 'select', 'button']):
        trans_data[el.get('name')] = el.get('value')

    content = sess.get(trans_form.get('action'), post=True, post_data=trans_data)
    soup = BeautifulSoup(content)
    csv_link = soup.find('a', class_='action-pdf').get('href')
    csv_content = sess.get(csv_link)
    save('data/%s/trans/%s_%s.csv' % (today.year,
                                      account,
                                      today.strftime('%Y_%m_%d')), csv_content)

    sess.logout(content)

if '__main__' == __name__:
    if len(sys.argv) < 2 or not sys.argv[1]:
        print 'usage: %s account_name' % __file__
        sys.exit()

    main(sys.argv[1])

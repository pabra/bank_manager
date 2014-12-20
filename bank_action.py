#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import time
import csv
import sqlite3
import locale
import datetime
import pprint
import requests
import ConfigParser
from urlparse import urljoin
from bs4 import BeautifulSoup

DB_CONNECTION = False

locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

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

    def get(self, location, post=False, post_data=None, track_last_url=True, binary=False):
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

        if not binary:
            cnt = r.text.encode('utf8')
            if not cnt:
                pprint.pprint(r.headers)
                pprint.pprint(r.history)
            return cnt

        return r.content

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

def save(file_name, content, binary=False):
    cwd = get_cwd()
    subdir = os.path.join(cwd, os.path.dirname(file_name))
    if not os.path.isdir(subdir):
        os.makedirs(subdir)
    file_path = os.path.join(cwd, file_name)
    mode = 'w' if not binary else 'wb'
    f = open(file_path, mode)
    f.write(content)
    f.close()

def read(file_name):
    cwd = get_cwd()
    file_path = os.path.join(cwd, file_name)
    f = open(file_path, 'r')
    content = f.read()
    f.close()

    return content

def get_files(account=None, min_date=None):
    start_dir = os.path.join(get_cwd(), 'data')
    find_files = [os.path.join(path, f)
                  for path, dirs, files in os.walk(start_dir)
                  for f in files
                  if (path.endswith('trans')
                      and (f.startswith(account) if account else True)
                      and (datetime.datetime.strptime(re.match(r'^.*?_(\d{4}_\d{2}_\d{2})\.csv$', f).group(1), '%Y_%m_%d').date() >= min_date if min_date else True))]

    return find_files

def cleanup_csv(date_format):
    files = get_files()
    today = datetime.date.today()
    for f in files:
        match = re.match(r'^.*?_(\d{4}_\d{2}_\d{2})\.csv$', f)
        if match:
            f_date = datetime.datetime.strptime(match.group(1), date_format).date()
            if not f_date.day in (1, 10, 20, 30) and f_date != today:
                os.unlink(f)

def db_connect():
    global DB_CONNECTION

    if not DB_CONNECTION:
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        DB_CONNECTION = sqlite3.connect(os.path.join(curr_dir, 'bank.sqlite3'), detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        con = DB_CONNECTION
        con.text_factory = str
        cur = con.cursor()

        cur.execute('SELECT * FROM sqlite_master')
        sqlite_master = cur.fetchall()
        tables = [x[1] for x in sqlite_master if x[0] == 'table']
        indices = [x[1] for x in sqlite_master if x[0] == 'index']

        if not 'accounts' in tables:
            cur.execute('''
                CREATE TABLE accounts (
                    number INTERGER PRIMARY KEY NOT NULL,
                    name TEXT,
                    init_saldo INTERGER,
                    last_update TIMESTAMP
                )
            ''')

        if not 'transactions' in tables:
            cur.execute('''
                CREATE TABLE transactions (
                    account INTERGER NOT NULL,
                    date DATE,
                    valuta DATE,
                    type TEXT,
                    subject TEXT,
                    transfer_from TEXT,
                    transfer_to TEXT,
                    value INTERGER,
                    FOREIGN KEY (account) REFERENCES accounts (number)
                )
            ''')

        if not 'debit_warn' in tables:
            cur.execute('''
                CREATE TABLE debit_warn (
                    name TEXT PRIMARY KEY NOT NULL,
                    date DATE NOT NULL
                )
            ''')

    else:
        con = DB_CONNECTION
        cur = con.cursor()

    return con, cur

def db_close(commit=True):
    if DB_CONNECTION:
        if commit:
            try:
                DB_CONNECTION.commit()
            except sqlite3.ProgrammingError:
                # connection was already closed
                pass

        DB_CONNECTION.close()

def check_account_existence(acc_name, acc_no):
    con, cur = db_connect()
    q = '''
        SELECT 1
        FROM accounts
        WHERE number = ?
    '''
    cur.execute(q, (acc_no,))
    res = cur.fetchone()

    if not res:
        q = '''
            INSERT INTO accounts
            (number, name)
            VALUES
            (?, ?)
        '''
        cur.execute(q, (acc_no, acc_name))

def parse_amount(v):
    return int(re.sub(r'[^0-9-]', '', v).replace(',','.'))

def format_amount(v):
    return locale.currency(v / 100.0, symbol=True, grouping=True)

def parse_date(date_str):
    return datetime.datetime.strptime(date_str, '%d.%m.%Y').date()

def get_csv_from_file(file_name):
    with open(file_name, 'r') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';', quotechar='"')
        csv_list = [row for i, row in enumerate(csv_reader) if i > 8]
        csv_list.reverse()

    return csv_list

def get_parsed_csv_row(row):
    return (parse_date(row[0]),     # 0 - date
            parse_date(row[1]),     # 1 - valDate
            row[2].strip(),         # 2 - type
            row[3].strip(),         # 3 - subj
            row[4].strip(),         # 4 - from
            row[5].strip(),         # 5 - to
            parse_amount(row[6]),   # 6 - value
            parse_amount(row[7]))   # 7 - sum

def handle_init_transaction(account, first_row_values):
    con, cur = db_connect()
    init_int = first_row_values[7] - first_row_values[6]
    q = '''
        UPDATE accounts
        SET init_saldo = ?,
            last_update = ?
        WHERE number = ?
    '''
    cur.execute(q, (init_int, datetime.datetime.now(), account))
    return init_int

def check_lastschrift():
    con, cur = db_connect()
    today = datetime.date.today()
    year_ago = today - datetime.timedelta(365)
    # first clean up
    q = '''
        DELETE FROM debit_warn
        WHERE date < ?
    '''
    cur.execute(q, (year_ago,))

    # then update
    q = '''
        UPDATE debit_warn
        SET date = (SELECT _.date
                    FROM transactions _
                    WHERE _.transfer_to = name
                    ORDER BY _.date DESC
                    LIMIT 1)
    '''

    # finally fetch, report and add new ones
    q = '''
        SELECT account, date, type, subject, value, transfer_to
        FROM transactions
        WHERE date >= ?
              AND (LOWER(type) = "lastschrift"
                   OR (LOWER(type) = "kartenverfügung"
                       AND transfer_to <> ""))
              AND transfer_to NOT IN (SELECT _.name
                                      FROM debit_warn _)
        GROUP BY transfer_to
        ORDER BY date DESC
    '''
    cur.execute(q, (year_ago,))
    res = cur.fetchall()
    for x in res:
        if x[1] >= year_ago:
            print '\n'.join(['On %s',
                             '%r balanced of your account %s',
                             'by %s using %r',
                             'with subject %r.']) % (x[1].strftime('%a, %d %b %Y'), x[5], x[0], format_amount(x[4]), x[2], x[3])
            q = '''
                INSERT INTO debit_warn
                (name, date)
                VALUES
                (?, ?)
            '''
            cur.execute(q, (x[5], x[1]))

def db_import_file(file_name, account_no):
    con, cur = db_connect()
    csv_list = get_csv_from_file(file_name)
    csv_from = get_parsed_csv_row(csv_list[:1][0])[0]
    csv_to = get_parsed_csv_row(csv_list[-1:][0])[0]
    last_date = get_last_entry_date(account_no)

    if last_date and csv_from <= last_date and csv_to >= last_date:
        drop_entries_for_date(account_no, last_date)

    current_saldo = get_saldo(account_no)

    if current_saldo is None:
        current_saldo = handle_init_transaction(account_no,
                                                get_parsed_csv_row(csv_list[0]))
    inserts = []
    for row in csv_list:
        # date, valDate, type, subj, from, to, value, saldo
        values = get_parsed_csv_row(row)
        # do not touch old entries
        if last_date and values[0] < last_date:
            continue
        trans_values = (account_no,) + values[:7]

        current_saldo += values[6]
        assert current_saldo == values[7], '\n'.join(['%s != %s' % (current_saldo, values[7]),
                                                      'values: %s' % pprint.pformat(trans_values),
                                                      'file: %s' % file_name])
        inserts.append(trans_values)

    update_timestamp = bool(inserts)
    while inserts:
        insters_slice = inserts[0:400]
        del inserts[0:400]
        q = '''
            INSERT INTO transactions
            (account, date, valuta, type, subject, transfer_from, transfer_to, value)
            VALUES
            %s
        ''' % ','.join(('(?,?,?,?,?,?,?,?)',)*len(insters_slice))
        cur.execute(q, [y for x in insters_slice for y in x])

    if update_timestamp:
        q = '''
            UPDATE accounts
            SET last_update = ?
            WHERE number = ?
        '''
        cur.execute(q, (datetime.datetime.now(), account_no))
        check_lastschrift()

def get_saldo(account):
    con, cur = db_connect()
    q = '''
        SELECT
            a.init_saldo
            +
            IFNULL(SUM(t.value), 0)
        FROM accounts a
        LEFT JOIN transactions t ON t.account = a.number
        WHERE a.number = ?
    '''
    cur.execute(q, (account,))
    res = cur.fetchone()
    if not res:
        return None

    return res[0]

def get_last_entry_date(account):
    con, cur = db_connect()
    q = '''
        SELECT MAX(date) AS "max [DATE]"
        FROM transactions
        WHERE account = ?
    '''
    cur.execute(q, (account,))
    res = cur.fetchone()
    if not res:
        return None

    return res[0]

def drop_entries_for_date(account, last_date):
    if last_date:
        con, cur = db_connect()
        q = '''
            DELETE FROM transactions
            WHERE account = ?
              AND date = ?
        '''
        cur.execute(q, (account, last_date))

def update_db(account):
    sess = Session(account)
    acc_no = sess.conf('user')
    check_account_existence(account, acc_no)
    last_date = get_last_entry_date(acc_no)
    files = get_files(account=account, min_date=last_date)
    files.sort()
    for f in files:
        db_import_file(f, acc_no)

    db_close()

def fetch(account):
    date_format = '%d.%m.%Y'
    date_save_format = '%Y_%m_%d'

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
    trans_form.find('div', class_='fld-date-bis').find('input')['value'] = today.strftime(date_format)
    trans_form.find('div', class_='fld-date-von').find('input')['value'] = (today - datetime.timedelta(95)).strftime(date_format)

    for el in trans_form.find_all(['input', 'select', 'button']):
        trans_data[el.get('name')] = el.get('value')

    time.sleep(3)
    content = sess.get(trans_form.get('action'), post=True, post_data=trans_data)
    save('log/transcations-95.html', content)
    #content = read('log/transcations-95.html')
    if not content:
        print 'post transaction data again with 3 sec timeout'
        time.sleep(3)
        content = sess.get(trans_form.get('action'), post=True, post_data=trans_data)
        save('log/transcations-95_2.html', content)
    soup = BeautifulSoup(content)
    csv_link = soup.find('a', class_='action-pdf').get('href')
    csv_content = sess.get(csv_link, track_last_url=False)
    save('data/%s/trans/%s_%s.csv' % (today.year,
                                      account,
                                      today.strftime(date_save_format)), csv_content)

    statements_overview = soup.find('a', class_='action-more').get('href')

    content = sess.get(statements_overview)
    save('log/statements_overview.html', content)
    #content = read('log/statements_overview.html')
    soup = BeautifulSoup(content)
    pdf_links = []
    for row in soup.find_all('tr', class_='state-unmarked'):
        pdf_date = datetime.datetime.strptime(row.find('td', class_='headers-date').get_text(strip=True), date_format).date()
        pdf_link = row.find('a', 'action-icon-download').get('href')
        pdf_links.append((pdf_date, pdf_link))

    if pdf_links:
        for x in pdf_links:
            pdf_content = sess.get(x[1], track_last_url=False, binary=True)
            save('data/%s/pdf/%s_%s.pdf' % (x[0].year,
                                            account,
                                            x[0].strftime(date_save_format)),
                 pdf_content,
                 binary=True)

    sess.logout(content)

    cleanup_csv(date_save_format)

def usage():
    print 'usage: %s fetch <account_name>' % __file__
    print '       %s update <account_name>' % __file__
    sys.exit()

if '__main__' == __name__:
    sys.argv.extend(['']*2)

    if 'update' == sys.argv[1] and sys.argv[2]:
        update_db(sys.argv[2])

    elif 'fetch' == sys.argv[1] and sys.argv[2]:
        fetch(sys.argv[2])

    else:
        usage()

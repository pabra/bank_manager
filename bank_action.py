#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import csv
import sqlite3
import locale
import datetime
import pprint
import ConfigParser
import mechanize
import smtplib
from email.mime.text import MIMEText

DB_CONNECTION = False

locale.setlocale(locale.LC_MONETARY, locale.getdefaultlocale())

class Config(object):
    def __init__(self, account):
        self.account = account
        self._load_config()

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
        assert 'config' != self.account, '%r is no valid account name.' % self.account
        assert 'config' in accounts, 'Missing [config] section in config file.'
        assert self.account in accounts, 'There is no section for account %r in config file.' % self.account

    def conf(self, param):
        return self.Config.get(self.account, param)

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

def fetchall_dicts(cur):
    columns = [x[0] for x in cur.description]
    return [dict(zip(columns, x)) for x in cur.fetchall()]

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
                    last_happend DATE NOT NULL,
                    reported DATE NOT NULL
                )
            ''')

    else:
        con = DB_CONNECTION
        cur = con.cursor()

    return con, cur

def db_close(commit=True):
    global DB_CONNECTION

    if DB_CONNECTION:
        if commit:
            try:
                DB_CONNECTION.commit()
            except sqlite3.ProgrammingError:
                # connection was already closed
                pass

        DB_CONNECTION.close()
        DB_CONNECTION = False

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

def send_message(msg=[], subject='Debit Warning', mail_from='patrick.braune@gmail.com', rcpt_to='patrick.braune@gmail.com', host='localhost'):
    if not msg:
        return

    text_to_send = '\n\n'.join(msg)
    try:
        smtp_msg = MIMEText(text_to_send)
        smtp_msg.set_charset('utf-8')
        smtp_msg['Subject'] = subject
        smtp_msg['From'] = mail_from
        smtp_msg['To'] = rcpt_to
        s = smtplib.SMTP(host)
        s.sendmail(mail_from, [rcpt_to], smtp_msg.as_string())
    except:
        print text_to_send

def check_lastschrift(sess):
    con, cur = db_connect()
    today = datetime.date.today()
    year_ago = today - datetime.timedelta(365)
    # first clean up
    q = '''
        DELETE FROM debit_warn
        WHERE last_happend < ?
    '''
    cur.execute(q, (year_ago,))

    # then update
    q = '''
        UPDATE debit_warn
        SET last_happend = (SELECT _.date
                            FROM transactions _
                            WHERE _.transfer_to = name
                            ORDER BY _.date DESC
                            LIMIT 1)
    '''
    cur.execute(q)

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
    msg = []
    for x in res:
        if x[1] >= year_ago:
            msg.append('\n'.join(['On %s',
                                  '"%s" adjusted your account %s',
                                  'by %s using "%s"',
                                  'with subject "%s".']) % (x[1].strftime('%a, %d %b %Y'),
                                                            x[5],
                                                            x[0],
                                                            format_amount(x[4]),
                                                            x[2],
                                                            x[3]))
            q = '''
                INSERT INTO debit_warn
                (name, last_happend, reported)
                VALUES
                (?, ?, ?)
            '''
            cur.execute(q, (x[5], x[1], today))

    if msg:
        msg.append('see \n%s/debit' % (sess.Config.get('config', 'bank_server') or 'http://127.0.0.1/'))
        send_message(msg)

def db_import_file(file_name, account_no, sess):
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

    inserted = bool(inserts)
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

    if inserted:
        q = '''
            UPDATE accounts
            SET last_update = ?
            WHERE number = ?
        '''
        cur.execute(q, (datetime.datetime.now(), account_no))
        check_lastschrift(sess)

def get_accounts():
    con, cur = db_connect()
    q = '''
        SELECT number, name, last_update
        FROM accounts
        ORDER BY number ASC
    '''
    cur.execute(q)
    return fetchall_dicts(cur)

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
    config = Config(account)
    acc_no = config.conf('user')
    check_account_existence(account, acc_no)
    last_date = get_last_entry_date(acc_no)
    files = get_files(account=account, min_date=last_date)
    files.sort()
    for f in files:
        db_import_file(f, acc_no, config)

    db_close()

def fetch(account):
    date_format = '%d.%m.%Y'
    date_save_format = '%Y_%m_%d'

    config = Config(account)
    br = mechanize.Browser()
    br.set_handle_robots(False)
    br.set_handle_refresh(False)
    br.addheaders = [('User-Agent', 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:31.0) Gecko/20130401 Firefox/31.0')]
    br.open('https://banking.postbank.de')

    save('log/login.html', br.response().read())
    #content = read('log/login.html')
    if 0 == len(list(br.forms())):
        headings = re.findall(r'<h1[^>]*>([\s\S]*?)</\s*h1>',
                              br.response().read())
        print 'no login form'
        print '\n'.join(headings)
        br.close()
        sys.exit(0)
    br.form = filter(lambda f: f.attrs.get('class') == 'form-cn', br.forms())[0]
    br['nutzername'] = config.conf('user')
    br['kennwort'] = config.conf('pass')
    br.submit()

    save('log/logged_in.html', br.response().read())
    #content = read('log/logged_in.html')
    link = filter(lambda l: l.text == 'Umsätze', br.links())[0]
    br.follow_link(link)

    save('log/transcations.html', br.response().read())
    #content = read('log/transcations.html')
    today = datetime.date.today()
    br.form = list(br.forms())[0]
    ctrl = filter(lambda c: c.type == 'text' and re.match(r'^.*?bisDatum$', c.name),  br.form.controls)[0]
    ctrl.value = today.strftime(date_format)
    ctrl = filter(lambda c: c.type == 'text' and re.match(r'^.*?vonDatum$', c.name),  br.form.controls)[0]
    ctrl.value = (today - datetime.timedelta(95)).strftime(date_format)
    br.submit()

    save('log/transcations-95.html', br.response().read())
    #content = read('log/transcations-95.html')
    link = filter(lambda l: l.text == 'CSV herunterladen', br.links())[0]
    link2 = filter(lambda l: l.text == 'Zu den Kontoauszügen', br.links())[0]
    br.follow_link(link)

    csv_cnt = br.response().read()
    csv_cnt = csv_cnt.decode('1252')
    csv_cnt = csv_cnt.encode('utf-8')
    save('data/%s/trans/%s_%s.csv' % (today.year,
                                      account,
                                      today.strftime(date_save_format)),
         csv_cnt)

    br.open(link2.absolute_url)

    save('log/statements_overview.html', br.response().read())
    #content = read('log/statements_overview.html')

    logout_link = filter(lambda l: l.text == 'Banking beenden', br.links())[0]
    pdf_links = []
    for link in br.links():
        attrs = {a[0]: a[1] for a in link.attrs}
        if (attrs.get('title') == 'Kontoauszug als PDF öffnen'
                and attrs.get('onclick')):

            pdf_links.append(link)

    for l in pdf_links:
        br.follow_link(l)
        pdf_disp = br.response().info().getheader('content-disposition')
        pdf_date_match = re.search(r'[0-9_]+?(\d{2}-\d{2}-\d{4})[0-9_]+\.pdf', pdf_disp)
        if pdf_date_match:
            pdf_date = datetime.datetime.strptime(pdf_date_match.group(1), '%d-%m-%Y')
            save('data/%s/pdf/%s_%s.pdf' % (pdf_date.year,
                                            account,
                                            pdf_date.strftime(date_save_format)),
                 br.response().read())
        else:
            print 'not saving PDF - no matching date in content-disposition\n', pdf_disp, '\nof link\n', l

    br.open(logout_link.absolute_url)
    save('log/logged_out.html', br.response().read())

    br.close()

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

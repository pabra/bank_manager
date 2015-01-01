#!/usr/bin/env python
import os
import bottle
import datetime
import re
import pprint
from bank_action import db_connect, db_close, get_accounts, fetchall_dicts

app = application = bottle.Bottle()

def handle_account_selection():
    accounts = get_accounts()
    account = bottle.request.GET.get('account')
    if not account in map(str, (x['number'] for x in accounts)):
        account = str(accounts[0]['number'])

    return account, accounts

def prepare_json(obj, as_locale=False):
    def str_date(d):
        if isinstance(d, datetime.datetime):
            return d.strftime('%d.%m.%Y %H:%M:%S') if as_locale else d.isoformat()

        if isinstance(d, datetime.date):
            return d.strftime('%d.%m.%Y') if as_locale else d.isoformat()

        return d

    if isinstance(obj, dict):
        return {x: str_date(obj[x]) for x in obj}

    elif isinstance(obj, list):
        return [prepare_json(x, as_locale=as_locale)
                if isinstance(x, dict)
                else str_date(x)
                for x in obj]

    elif isinstance(obj, tuple):
        return (str_date(x) for x in obj)

def str_to_date(date_str):
    if date_str in ('yearAgo', 'year_ago'):
        date_str = (datetime.date.today() - datetime.timedelta(365)).isoformat()
    try:
        return datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
    except:
        return None

def parse_value_compare(s):
    if not s:
        return None, None
    match = re.match(r'^((?:g|l)te?)(\d+)$', s)
    sign_dict = {'lt':  '<',
                 'lte': '<=',
                 'gt':  '>',
                 'gte': '>='}
    if match:
         sign, value = match.groups()
         return sign_dict[sign], int(value)

    return None, None

@app.route('/static/<filename>')
def serve_static(filename):
    root = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static')
    return bottle.static_file(filename, root=root)

@app.route('/')
@app.route('/summary')
@bottle.view('summary')
def show_index():
    con, cur = db_connect()
    account, accounts = handle_account_selection()
    db_close()
    return {'account': account,
            'accounts': prepare_json(accounts, as_locale=True)}

@app.route('/transactions')
@bottle.view('transactions')
def show_transactions():
    con, cur = db_connect()
    account, accounts = handle_account_selection()
    db_close()
    return {'account': account,
            'accounts': prepare_json(accounts, as_locale=True)}

@app.route('/debit')
@bottle.view('debit')
def show_debit():
    con, cur = db_connect()
    account, accounts = handle_account_selection()
    db_close()
    return {'account': account,
            'accounts': prepare_json(accounts, as_locale=True)}

@app.route('/api/<action>/<account:int>', method='GET')
def api(action, account):
    assert action in ('debit', 'transactions', 'summary')
    con, cur = db_connect()
    if 'summary' == action:
        rq_get = bottle.request.GET.get
        year = rq_get('year')

        if year:
            period_format = '%Y-%m'
        else:
            period_format = '%Y'

        q = '''
            SELECT
                STRFTIME(?, t.date)             AS period,
                SUM(CASE WHEN t.value >= 0
                    THEN t.value ELSE 0 END)    AS plus_sum,
                COUNT(CASE WHEN t.value >= 0
                      THEN 1 ELSE NULL END)     AS plus_count,
                SUM(CASE WHEN t.value < 0
                    THEN t.value ELSE 0 END)    AS minus_sum,
                COUNT(CASE WHEN t.value < 0
                      THEN 1 ELSE NULL END)     AS minus_count,
                SUM(t.value)                    AS sum_sum,
                COUNT(t.value)                  AS sum_count,
                (SELECT _.init_saldo
                 FROM accounts _
                 WHERE _.number = t.account) +
                (SELECT SUM(_.value)
                 FROM transactions _
                 WHERE _.account = t.account
                   AND _.date <= t.date)        AS saldo
            FROM transactions t
            WHERE account = ?
              %s
            GROUP BY period
            ORDER BY period ASC
        '''
        q_args = (period_format, account)
        if year:
            q %= 'AND STRFTIME("%Y", t.date) = ?'
            q_args += (year,)
        else:
            q %= ''

        cur.execute(q, q_args)
        data = prepare_json(fetchall_dicts(cur))
        db_close()
        return {'data': data}

    if 'debit' == action:
        today = datetime.date.today()
        year_ago = today - datetime.timedelta(365)
        q = '''
            SELECT
                d.name,
                d.last_happend,
                d.reported,
                (SELECT COUNT(_.account)
                 FROM transactions _
                 WHERE _.account = ?
                   AND _.transfer_to = d.name) AS occur_total,
                (SELECT COUNT(_.account)
                 FROM transactions _
                 WHERE _.account = ?
                   AND _.transfer_to = d.name
                   AND _.date >= ?) AS occur_last_year
            FROM debit_warn d
        '''
        cur.execute(q, (account,
                        account,
                        year_ago))
        data = prepare_json(fetchall_dicts(cur))
        db_close()
        return {'data': data}

    if 'transactions' == action:
        rq_get = bottle.request.GET.get

        date_from = str_to_date(rq_get('date_from'))
        date_to = str_to_date(rq_get('date_to'))
        transfer_from = rq_get('transfer_from')
        transfer_from_like = rq_get('transfer_from_like')
        transfer_to = rq_get('transfer_to')
        transfer_to_like = rq_get('transfer_to_like')
        value_compare_sign, value_compare_value = parse_value_compare(rq_get('value_compare'))

        q = '''
            SELECT
                date,
                valuta,
                type,
                subject,
                transfer_from,
                transfer_to,
                value
            FROM transactions
            WHERE account = ?
        '''
        q_args = (account,)

        if date_from:
            q += '''
                AND date >= ?
            '''
            q_args += (date_from,)

        if date_to:
            q += '''
                AND date <= ?
            '''
            q_args += (date_to,)

        if transfer_from:
            q += '''
                AND transfer_from = ?
            '''
            q_args += (transfer_from,)

        if transfer_from_like:
            q += '''
                AND transfer_from LIKE ?
            '''
            q_args += ('%%%s%%' % transfer_from_like,)

        if transfer_to:
            q += '''
                AND transfer_to = ?
            '''
            q_args += (transfer_to,)

        if transfer_to_like:
            q += '''
                AND transfer_to LIKE ?
            '''
            q_args += ('%%%s%%' % transfer_to_like,)
        if value_compare_sign:
            q += '''
                AND value %s ?
            ''' % value_compare_sign
            q_args += (value_compare_value,)

        cur.execute(q, q_args)
        data = prepare_json(fetchall_dicts(cur))
        db_close()
        return {'data': data}

if '__main__' == __name__:
    bottle.run(app=app,
               host='127.0.0.1',
               port=3001,
               reloader=True,
               debug=True)

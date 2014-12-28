#!/usr/bin/env python
import os
import bottle
import datetime
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

    q = '''
        SELECT *
        FROM debit_warn
    '''
    cur.execute(q)
    res = cur.fetchall()
    db_close()
    return {'account': account,
            'accounts': accounts,
            'res': pprint.pformat(res)}

@app.route('/transactions')
@bottle.view('transactions')
def show_transactions():
    con, cur = db_connect()
    account, accounts = handle_account_selection()
    db_close()
    return {'account': account,
            'accounts': accounts}

@app.route('/debit')
@bottle.view('debit')
def show_debit():
    con, cur = db_connect()
    account, accounts = handle_account_selection()

    db_close()
    return {'account': account,
            'accounts': accounts}

@app.route('/api/<action>/<account:int>', method='GET')
def api(action, account):
    assert action in ('debit', 'transactions')
    con, cur = db_connect()
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
        return {'data': prepare_json(fetchall_dicts(cur))}

    if 'transactions' == action:
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
        cur.execute(q, (account,))
        return {'data': prepare_json(fetchall_dicts(cur))}

    db_close()
    return {'a': ['1',2,datetime.date.today().isoformat(), action]}

if '__main__' == __name__:
    bottle.run(app=app,
               host='127.0.0.1',
               port=3001,
               reloader=True,
               debug=True)

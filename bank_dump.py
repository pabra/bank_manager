#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import re
import csv
import locale
import sqlite3
import locale
import datetime
import pprint

locale.setlocale(locale.LC_ALL, locale.getdefaultlocale())

def main():
    con = sqlite3.connect('bank_sqlite3.db')
    cur = con.cursor()
    kto = '929708901'
    #kto = '396208853'
    q = '''
        SELECT *
        FROM konto_%s
        ORDER BY Datum DESC
    ''' % kto
    cur.execute(q)
    trans_sum = None
    for row in cur.fetchall():
        datum = datetime.datetime.fromtimestamp(row[0]).date()
        datum_str = datum.strftime('%d.%m.%Y')
        wertst = datetime.datetime.fromtimestamp(row[1]).date()
        wertst_str = wertst.strftime('%d.%m.%Y')
        if datum.year in (2010, 2011, 2012):
            trans_type = row[2].encode('utf-8')
            if not isinstance(row[3], basestring):
                subj = str(row[3])
            else:
                subj = row[3]
            subj = subj.encode('utf-8')
            trans_from = row[4].encode('utf-8')
            trans_to = row[5].encode('utf-8')
            amount = row[6]
            amount_str = locale.currency(amount, symbol=True, grouping=True)
            if trans_sum is None:
                print 'Backup 2010, 2011, 2012'
                print 'Konto %s' % kto
                print 3
                print 4
                print 5
                print 6
                print 7
                print 8
                print '"Buchungstag";"Wertstellung";"Umsatzart";"Buchungsdetails";"Auftraggeber";"Empfänger";"Betrag (€)";"Saldo (€)"'
                trans_sum = row[7]
                trans_sum = -18.00 # lpz
                #trans_sum = -611.02 # nbg

            trans_sum_str = locale.currency(trans_sum, symbol=True, grouping=True)

            #print row
            #print datum_str
            #print wertst_str
            #print trans_type
            #print subj
            #print trans_from
            #print trans_to
            #print amount_str
            #print trans_sum_str
            #print '"%s";"%s";"%s";"%s";"%s";"%s";"%s";"%s"' % (datum_str, wertst_str, trans_type, subj, trans_from, trans_to, amount_str, trans_sum_str)
            out = ''
            out += '"%s";' % datum_str
            out += '"%s";' % wertst_str
            out += '"%s";' % trans_type
            out += '"%s";' % subj
            out += '"%s";' % trans_from
            out += '"%s";' % trans_to
            out += '"%s";' % amount_str
            out += '"%s"' % trans_sum_str
            print out
            trans_sum -= amount

            #rows.append((datum_str, wertst_str, trans_type, subj, trans_from, trans_to, amount_str))

    con.close()

if '__main__' == __name__:
    main()

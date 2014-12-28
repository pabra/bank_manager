/*global ko, account, routeName */
'use strict';
var WebFontConfig, strToDate, dateToStr, formatMoney, getLocationSearch,
    BankDebit, BankTransactions, debug_ooo;

WebFontConfig = {google:{families:['Ubuntu+Mono::latin', 'Ubuntu:400,700:latin']}};

strToDate = function strToDateFn(dStr) {
    var parsed = dStr.match(/(\d{4})-(\d{2})-(\d{2})/),
        y, m, d, dObj;
    if(!parsed){
        return false;
    }
    y = parseInt(parsed[1], 10);
    m = parseInt(parsed[2], 10) -1;
    d = parseInt(parsed[3], 10);
    dObj = new Date(0);
    dObj.setUTCFullYear(y);
    dObj.setUTCMonth(m);
    dObj.setUTCDate(d);
    if(dObj.getUTCFullYear() !== y
            || dObj.getUTCMonth() !== m
            || dObj.getUTCDate() !== d){
        return false;
    }
    return dObj;
};

dateToStr = function dateToStrFn(dObj, fmt) {
    var Y = dObj.getUTCFullYear(),
        m = dObj.getUTCMonth() +1,
        d = dObj.getUTCDate(),
        lPad = function(s) {
            var n = '0'+s;
            return n.substr(n.length -2);
        };
    fmt = fmt || '%Y-%m-%d';
    return fmt.replace(/%d/g, lPad(d))
              .replace(/%m/g, lPad(m))
              .replace(/%Y/g, Y);
};

formatMoney = function formatMoneyFn(value) {
    return String((value / 100).toFixed(2)).replace('.', ',').replace(/(\d)(\d{3}),/, '$1.$2,')+' €';
};

getLocationSearch = function getLocationSearchFn() {
    var dict = {};
    if (!location.search) {
        return dict;
    }
    $.each(location.search.replace(/^\?/, '').split('&'), function() {
        var kv = this.split('=');
        dict[kv[0]] = decodeURIComponent(kv[1].replace(/\+/g, ' '));
    });
    return dict;
};

BankDebit = function BankDebitFn() {
    var _self = this,
        Model, model, init;

    Model = function ModelFn() {
        var self = this;

        self.sortList = function orderListFn(column, direction) {
            self.debitList.sort(function(a, b) {
                var valA = 'string' === typeof a[column] ? a[column].toLowerCase() : a[column],
                    valB = 'string' === typeof b[column] ? b[column].toLowerCase() : b[column];
                if (valA > valB) {
                    return 'asc' === direction ? 1 : -1;
                }
                if (a[column] < b[column]) {
                    return 'asc' === direction ? -1 : 1;
                }
                return 0;
            });
            self.sortColumn(column);
            self.sortDirection(direction);
        };

        self.clickSort = function clickSortFn(mod, ev) {
            var col = $(ev.target).attr('data-column'),
                dir = mod.sortColumn() === col && mod.sortDirection() === 'asc' ? 'desc' : 'asc';

            mod.sortList(col, dir);
        };

        self.sortColumn = ko.observable();
        self.sortDirection = ko.observable();
        self.debitList = ko.observableArray();
    };

    init = function initFn() {
        model = new Model();
        _self.ooo = model;
        ko.applyBindings(model);
        $.getJSON('api/debit/'+account, function(data) {
            var list = data.data;
            ko.utils.arrayForEach(list, function(x){
                x.reported_loc = dateToStr(strToDate(x.reported), '%d.%m.%Y');
                x.last_happend_loc = dateToStr(strToDate(x.last_happend), '%d.%m.%Y');
            });
            model.debitList(list);
            model.sortList('name', 'asc');
        });
    };

    init();
};

BankTransactions = function BankTransactionsFn() {
    var init;

    init = function initFn() {
        console.log('init BankTransactions');
    };

    init();
};

$(function(){
    var bankDebit, bankTransactions,
        wf, s;

    wf = document.createElement('script');
    wf.src = ('https:' === document.location.protocol ? 'https' : 'http') + '://ajax.googleapis.com/ajax/libs/webfont/1/webfont.js';
    wf.type = 'text/javascript';
    wf.async = 'true';
    s = document.getElementsByTagName('script')[0];
    s.parentNode.insertBefore(wf, s);

    $('#header_links a').each(function(){
        var el = $(this);
        if (el.attr('href').split('?')[0] === routeName) {
            el.addClass('active');
        }
    });
    if ('debit' === routeName) {
        bankDebit = new BankDebit();
        debug_ooo = bankDebit;
    } else if ('transactions' === routeName) {
        bankTransactions = new BankTransactions();
        debug_ooo = bankTransactions;
    }
});

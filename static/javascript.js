/*global ko, account, routeName */
'use strict';
var WebFontConfig, strToDate, dateToStr, lastOfMonth, formatMoney, getLocationSearch,
    BankDebit, BankTransactions, BankSummary, debug_ooo;

WebFontConfig = {google:{families:['Ubuntu+Mono:400,700:latin', 'Ubuntu:400,700:latin']}};

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

lastOfMonth = function lastOfMonthFn(dStr) {
    var dMatch = dStr.match(/^(\d{4})-(\d{2})-\d{2}$/),
        y, m;
    if (!dMatch) {
        return false;
    }
    y = parseInt(dMatch[1], 10);
    m = parseInt(dMatch[2], 10) -1;
    return dateToStr(new Date(y, (m +1), 0, 3, 3, 3));
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

        self.sortList = function sortListFn(column, direction) {
            var getVal = function getValFn(val) {
                return 'string' === typeof val ? val.toLowerCase() : val;
            };
            self.debitList.sort(function(a, b) {
                var valA = getVal(a[column]),
                    valB = getVal(b[column]);
                if (valA > valB) {
                    return 'asc' === direction ? 1 : -1;
                }
                if (valA < valB) {
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

        self.gotoHref = function gotoHrefFn(mod, ev) {
            var params = {account: account},
                el = $(ev.target),
                col = el.attr('data-column'),
                myEl;
            if ('name' === col) {
                params.transferTo = el.text();
            }
            if ('occur_total' === col) {
                myEl = el.parent().find('td[data-column=name]');
                params.transferTo = myEl.text();
            }
            if ('occur_last_year' === col) {
                myEl = el.parent().find('td[data-column=name]');
                params.transferTo = myEl.text();
                params.dateFrom = 'yearAgo';
            }
            location.href = 'transactions?' + $.param(params);
        };

        self.sortColumn = ko.observable();
        self.sortDirection = ko.observable();
        self.debitList = ko.observableArray();
        self.caption = ko.pureComputed(function(){
            return self.debitList().length + ' rows';
        });
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
    var _self = this,
        Model, model, init;

    Model = function ModelFn() {
        var self = this;

        self.transactionList = ko.observableArray();
        self.sumList = ko.observableArray();
        self.sumListSumValue = ko.pureComputed(function() {
            var sum = 0;
            ko.utils.arrayForEach(self.sumList(), function(x) {
                sum += x.value;
            });
            return sum;
        });
        self.sumListSumValueLoc = ko.pureComputed(function() {
            return formatMoney(self.sumListSumValue());
        });
        self.readyForGet = ko.observable(false);
        self.lastUri = ko.observable();
        self.sortColumn = ko.observable();
        self.sortDirection = ko.observable();
        self.dateFrom = ko.observable();
        self.dateTo = ko.observable();
        self.valueCompare = ko.observable();
        self.transferFrom = ko.observable();
        self.transferFromLike = ko.observable();
        self.transferTo = ko.observable();
        self.transferToLike = ko.observable();
        self.caption = ko.pureComputed(function(){
            var sum = 0;
            $.each(self.transactionList(), function(){
                sum += this.value;
            });
            return (self.transactionList().length
                    + ' rows - in sum <span class="money '
                    + (sum >= 0 ? 'pos' : 'neg')+'">'
                    + formatMoney(sum) + '</span>');
        });
        self.getTransactions = ko.computed(function() {
            if (!self.readyForGet()) {
                return;
            }
            self.readyForGet(false);
            var params = {},
                uri;
            if (self.dateFrom()) {
                params.date_from = self.dateFrom();
            }
            if (self.dateTo()) {
                params.date_to = self.dateTo();
            }
            if (self.transferFrom()) {
                params.transfer_from = self.transferFrom();
            }
            if (self.transferFromLike()) {
                params.transfer_from_like = self.transferFromLike();
            }
            if (self.transferTo()) {
                params.transfer_to = self.transferTo();
            }
            if (self.transferToLike()) {
                params.transfer_to_like = self.transferToLike();
            }
            if (self.valueCompare()) {
                params.value_compare = self.valueCompare();
            }
            uri = 'api/transactions/'+account+'?'+$.param(params);
            if (uri === self.lastUri())  {
                return;
            }
            self.lastUri(uri);
            $.getJSON(uri, function(data) {
                var list = data.data;
                ko.utils.arrayForEach(list, function(x){
                    x.date_loc = dateToStr(strToDate(x.date), '%d.%m.%Y');
                    x.valuta_loc = dateToStr(strToDate(x.valuta), '%d.%m.%Y');
                    x.value_loc = formatMoney(x.value);
                });
                model.transactionList(list);
                model.sortList(self.sortColumn(), self.sortDirection());
                self.readyForGet(true);
            });
        });

        self.clickForSum = function clickForSumFn(transaction) {
            var idx = self.sumList.indexOf(transaction);
            if (-1 === idx) {
                self.sumList.push(transaction);
            } else {
                self.sumList.splice(idx, 1);
            }
        };

        self.sortList = function sortListFn(column, direction) {
            var getVal = function getValFn(val) {
                return 'string' === typeof val ? val.toLowerCase() : val;
            };
            self.transactionList.sort(function(a, b) {
                var valA = getVal(a[column]),
                    valB = getVal(b[column]);
                if (valA > valB) {
                    return 'asc' === direction ? 1 : -1;
                }
                if (valA < valB) {
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
    };

    init = function initFn() {
        model = new Model();
        _self.ooo = model;
        $.each(getLocationSearch(), function(k,v) {
            if (v
                && ko.isObservable(model[k])
                && -1 !== $.inArray(k, ['transferFrom',
                                        'transferFromLike',
                                        'transferTo',
                                        'transferToLike',
                                        'valueCompare',
                                        'dateFrom',
                                        'dateTo'])) {
                model[k](v);
            }
        });
        ko.applyBindings(model);
        model.sortList('date', 'desc');
        model.readyForGet(true);
    };

    init();
};

BankSummary = function BankSummaryFn() {
    var _self = this,
        extendSummaryList,
        Model, model, init;

    extendSummaryList = function extentSummaryListFn(list) {
        ko.utils.arrayForEach(list, function(x){
            x.plus_loc = formatMoney(x.plus_sum);
            x.minus_loc = formatMoney(x.minus_sum);
            x.sum_loc = formatMoney(x.sum_sum);
            x.saldo_loc = formatMoney(x.saldo);
        });

        return list;
    };

    Model = function ModelFn() {
        var self = this;

        self.summaryList = ko.observableArray();
        self.sort = function sortFn() {
            var getVal = function getValFn(val) {
                return self.isClickable(val) ? val+'-z' : val;
            };
            self.summaryList.sort(function(a, b) {
                var valA = getVal(a.period),
                    valB = getVal(b.period);
                if (valA > valB) {
                    return 1;
                }
                if (valA < valB) {
                    return -1;
                }
                return 0;
            });
        };

        self.cleanSummaryList = function cleanSummaryListFn() {
            var findDetailRow, detailRow;

            findDetailRow = function findDetailRowFn() {
                var i = -1;
                ko.utils.arrayForEach(self.summaryList(), function(v, k) {
                    if (-1 === i && !self.isClickable(v.period)) {
                        i = k;
                    }
                });
                return i;
            };

            for(detailRow = findDetailRow(); -1 !== detailRow; detailRow = findDetailRow()) {
                self.summaryList.splice(detailRow, 1);
            }
        };

        self.gotoTransactions = function gotoTransactionsFn(row, ev) {
            var params = {account: account},
                el = $(ev.target),
                periodMatch = row.period.match(/^(\d{4})(?:-(\d{2}))?$/);

            if (el.hasClass('values_plus')) {
                params.valueCompare = 'gte0';
            } else if (el.hasClass('values_minus')) {
                params.valueCompare = 'lt0';
            }
            if (periodMatch[2]) {   // month row
                params.dateFrom = periodMatch[1]+'-'+periodMatch[2]+'-01';
                params.dateTo = lastOfMonth(params.dateFrom);
            } else {                // year row
                params.dateFrom = periodMatch[1]+'-01-01';
                params.dateTo = periodMatch[1]+'-12-31';
            }

            location.href = 'transactions?' + $.param(params);
        };

        self.isClickable = function isClickableFn(period) {
            //console.log('isClickable');
            //console.log(period);
            return period.match(/^\d{4}$/) ? true : false;
        };

        self.getSummaryYear = function getSummaryYearFn(row) {
            if (!self.isClickable(row.period)) {
                return;
            }
            var params = {year: row.period},
                scrollPosTop = $(window).scrollTop();
            self.cleanSummaryList();
            $.getJSON('api/summary/'+account+'?'+$.param(params), function(data) {
                var list = extendSummaryList(data.data);
                ko.utils.arrayForEach(list, function(x) {
                    model.summaryList.push(x);
                });
                self.sort();
                $(window).scrollTop(scrollPosTop);
            });
        };
    };

    init = function initFn() {
        model = new Model();
        _self.ooo = model;
        ko.applyBindings(model);
        $.getJSON('api/summary/'+account, function(data) {
            var list = extendSummaryList(data.data);
            model.summaryList(list);
            model.getSummaryYear({period: list[list.length -1].period});
        });
    };

    init();
};

$(function(){
    var bankDebit, bankTransactions, bankSummary,
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
    } else if ('summary' === routeName) {
        bankSummary = new BankSummary();
        debug_ooo = bankSummary;
    }
});

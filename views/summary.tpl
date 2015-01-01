% include('_header.tpl')
<h1>Summary</h1>
<table>
    <thead>
        <th>period</th>
        <th colspan="2">+</th>
        <th colspan="2">-</th>
        <th colspan="2">&sum;</th>
        <th>saldo</th>
    </thead>
    <tbody data-bind="foreach: {data: summaryList}">
        <tr data-bind="css: {odd: $index()%2,
                             even: !($index()%2),
                             month_row: !$parent.isClickable(period),
                             year_row: $parent.isClickable(period)}">
            <td data-bind="text: period, click: $parent.getSummaryYear, css: {clickable: $parent.isClickable(period)}"></td>
            <td data-bind="text: plus_count, css: 'money'"></td>
            <td data-bind="text: plus_loc,
                           css: {money: 1,
                                 pos: plus_sum >= 0,
                                 neg: plus_sum < 0,
                                 values_plus: 1,
                                 clickable: 1},
                           click: $parent.gotoTransactions"></td>
            <td data-bind="text: minus_count, css: 'money'"></td>
            <td data-bind="text: minus_loc,
                           css: {money: 1,
                                 pos: minus_sum >= 0,
                                 neg: minus_sum < 0,
                                 values_minus: 1,
                                 clickable: 1},
                           click: $parent.gotoTransactions"></td>
            <td data-bind="text: sum_count, css: 'money'"></td>
            <td data-bind="text: sum_loc,
                           css: {money: 1,
                                 pos: sum_sum >= 0,
                                 neg: sum_sum < 0,
                                 clickable: 1},
                           click: $parent.gotoTransactions"></td>
            <td data-bind="text: saldo_loc, css: {money: 1, pos: saldo >= 0, neg: saldo < 0}"></td>
        </tr>
    </tbody>
</table>
% include('_footer.tpl')

% include('_header.tpl')
<h1>Summary</h1>
<table>
    <thead>
        <tr>
            <th>period</th>
            <th colspan="2">+</th>
            <th colspan="2">-</th>
            <th colspan="2">&sum;</th>
            <th>saldo</th>
        </tr>
    </thead>
    <tbody data-bind="foreach: {data: summaryList}">
        <tr data-bind="css: {odd: $index()%2,
                             even: !($index()%2),
                             month_row: !$parent.isClickable(period),
                             year_row: $parent.isClickable(period)}">
            <td class="bold mono more_pedding_left more_pedding_right"
                data-bind="text: period, click: $parent.getSummaryYear, css: {clickable: $parent.isClickable(period)}"></td>
            <td class="money more_pedding_left less_padding_right" data-bind="text: plus_count"></td>
            <td class="money values_plus clickable less_padding_left"
                data-bind="text: plus_loc,
                           css: {pos: plus_sum >= 0,
                                 neg: plus_sum < 0},
                           click: $parent.gotoTransactions"></td>
            <td class="money more_pedding_left less_padding_right" data-bind="text: minus_count"></td>
            <td class="money values_minus clickable less_padding_left"
                data-bind="text: minus_loc,
                           css: {pos: minus_sum >= 0,
                                 neg: minus_sum < 0},
                           click: $parent.gotoTransactions"></td>
            <td class="money more_pedding_left less_padding_right" data-bind="text: sum_count"></td>
            <td class="money clickable less_padding_left"
                data-bind="text: sum_loc,
                           css: {pos: sum_sum >= 0,
                                 neg: sum_sum < 0},
                           click: $parent.gotoTransactions"></td>
            <td class="money bold more_pedding_left more_pedding_right"
                data-bind="text: saldo_loc, css: {pos: saldo >= 0, neg: saldo < 0}"></td>
        </tr>
    </tbody>
</table>
% include('_footer.tpl')

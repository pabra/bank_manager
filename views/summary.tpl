% include('_header.tpl')
<h1>Summary</h1>
<table>
    <thead>
        <th>period</th>
        <th>+</th>
        <th>-</th>
        <th>&sum;</th>
        <th>saldo</th>
    </thead>
    <tbody data-bind="foreach: {data: summaryList}">
        <tr data-bind="css: $index() % 2 ? 'odd' : 'even'">
            <td data-bind="text: period"></td>
            <td data-bind="text: plus_loc, css: {money: true, pos: plus >= 0, neg: plus < 0}"></td>
            <td data-bind="text: minus_loc, css: {money: true, pos: minus >= 0, neg: minus < 0}"></td>
            <td data-bind="text: sum_loc, css: {money: true, pos: sum >= 0, neg: sum < 0}"></td>
            <td data-bind="text: saldo_loc, css: {money: true, pos: saldo >= 0, neg: saldo < 0}"></td>
        </tr>
    </tbody>
</table>
% include('_footer.tpl')

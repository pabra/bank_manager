% include('_header.tpl')
<h1>Transactions</h1>
<table>
    <caption data-bind="text: caption"></caption>
    <thead>
        <th>date</th>
        <th>valuta</th>
        <th>type</th>
        <th>subject</th>
        <th>from</th>
        <th>to</th>
        <th>value</th>
    </thead>
    <tbody data-bind="foreach: {data: transactionList}">
        <tr data-bind="css: $index() % 2 ? 'odd' : 'even'">
            <td data-bind="text: date_loc"></td>
            <td data-bind="text: valuta_loc"></td>
            <td data-bind="text: type"></td>
            <td data-bind="text: subject"></td>
            <td data-bind="text: transfer_from"></td>
            <td data-bind="text: transfer_to"></td>
            <td data-bind="text: value_loc"></td>
        </tr>
    </tbody>
</table>
% include('_footer.tpl')

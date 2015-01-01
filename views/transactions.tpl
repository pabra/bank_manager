% include('_header.tpl')
<h1>Transactions</h1>
<div id="sum_box" data-bind="visible: sumList().length">
    <div data-bind="foreach: {data: sumList}">
            <div data-bind="text: value_loc,
                            css: {money: 1,
                                  pos: value >= 0,
                                  neg: value < 0}"></div>
    </div>
    <div class="money sum_line"
         data-bind="text: sumListSumValueLoc,
                    css: {pos: sumListSumValue() >= 0,
                          neg: sumListSumValue() < 0}"></div>
</div>
<table>
    <caption data-bind="html: caption"></caption>
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
            <td class="mono" data-bind="text: date_loc"></td>
            <td class="mono" data-bind="text: valuta_loc"></td>
            <td class="mono" data-bind="text: type"></td>
            <td class="mono" data-bind="text: subject"></td>
            <td class="mono" data-bind="text: transfer_from"></td>
            <td class="mono" data-bind="text: transfer_to"></td>
            <td data-bind="text: value_loc,
                           css: {money: 1,
                                 pos: value >= 0,
                                 neg: value < 0,
                                 clickable: 1},
                           click: $parent.clickForSum"></td>
        </tr>
    </tbody>
</table>
% include('_footer.tpl')

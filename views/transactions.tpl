% include('_header.tpl')
<h1>Transactions</h1>
<div id="sum_box" data-bind="visible: sumList().length">
    <div data-bind="foreach: {data: sumList}">
            <div data-bind="text: value_loc,
                            event: {mouseenter: $parent.mouseenter, mouseleave: $parent.mouseleave},
                            css: {money: 1,
                                  pos: value >= 0,
                                  neg: value < 0,
                                  highlight: hover}"></div>
    </div>
    <div class="money sum_line"
         data-bind="text: sumListSumValueLoc,
                    css: {pos: sumListSumValue() >= 0,
                          neg: sumListSumValue() < 0}"></div>
</div>
<table>
    <caption data-bind="html: caption"></caption>
    <thead>
        <th class="clickable" data-column="date" data-bind="click: clickSort, css: 'date'===sortColumn()?sortDirection():''">date</th>
        <th class="clickable" data-column="valuta" data-bind="click: clickSort, css: 'valuta'===sortColumn()?sortDirection():''">valuta</th>
        <th class="clickable" data-column="type" data-bind="click: clickSort, css: 'type'===sortColumn()?sortDirection():''">type</th>
        <th class="clickable" data-column="subject" data-bind="click: clickSort, css: 'subject'===sortColumn()?sortDirection():''">subject</th>
        <th class="clickable" data-column="transfer_from" data-bind="click: clickSort, css: 'transfer_from'===sortColumn()?sortDirection():''">from</th>
        <th class="clickable" data-column="transfer_to" data-bind="click: clickSort, css: 'transfer_to'===sortColumn()?sortDirection():''">to</th>
        <th class="clickable" data-column="value" data-bind="click: clickSort, css: 'value'===sortColumn()?sortDirection():''">value</th>
    </thead>
    <tbody data-bind="foreach: {data: transactionList}">
        <tr data-bind="event: {mouseenter: $parent.mouseenter, mouseleave: $parent.mouseleave},
                       css: {odd: $index() % 2,
                             even: !$index() % 2,
                             highlight: hover}">
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

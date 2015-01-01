% include('_header.tpl')
<h1>Direct Debit</h1>
<table>
    <caption data-bind="text: caption"></caption>
    <thead>
        <tr>
            <th class="clickable" data-column="name" data-bind="click: clickSort, css: 'name'===sortColumn()?sortDirection():''">Name</th>
            <th class="clickable" data-column="reported" data-bind="click: clickSort, css: 'reported'===sortColumn()?sortDirection():''">reported</th>
            <th class="clickable" data-column="last_happend" data-bind="click: clickSort, css: 'last_happend'===sortColumn()?sortDirection():''">last happend</th>
            <th class="clickable" data-column="occur_total" data-bind="click: clickSort, css: 'occur_total'===sortColumn()?sortDirection():''">total</th>
            <th class="clickable" data-column="occur_last_year" data-bind="click: clickSort, css: 'occur_last_year'===sortColumn()?sortDirection():''">within year ago</th>
        </tr>
    </thead>
    <tbody data-bind="foreach: {data: debitList}">
        <tr data-bind="css: $index() % 2 ? 'odd' : 'even'">
            <td data-column="name" data-bind="text: name, click: $root.gotoHref" class="clickable mono"></td>
            <td data-column="reported" data-bind="text: reported_loc" class="mono"></td>
            <td data-column="last_happend" data-bind="text: last_happend_loc" class="mono"></td>
            <td data-column="occur_total" data-bind="text: occur_total, click: $root.gotoHref" class="clickable money more_right_padding"></td>
            <td data-column="occur_last_year" data-bind="text: occur_last_year, click: $root.gotoHref" class="clickable money more_right_padding"></td>
        </tr>
    </tbody>
</table>
% include('_footer.tpl')

% include('_header.tpl')
<h1>Direct Debit</h1>
<table>
    <thead>
        <tr>
            <th class="clickable" data-column="name" data-bind="click: clickSort, css: 'name'===sortColumn()?sortDirection():''">Name</th>
            <th class="clickable" data-column="reported" data-bind="click: clickSort, css: 'reported'===sortColumn()?sortDirection():''">reported</th>
            <th class="clickable" data-column="last_happend" data-bind="click: clickSort, css: 'last_happend'===sortColumn()?sortDirection():''">last happend</th>
            <th class="clickable" data-column="occur_total" data-bind="click: clickSort, css: 'occur_total'===sortColumn()?sortDirection():''">happend total</th>
            <th class="clickable" data-column="occur_last_year" data-bind="click: clickSort, css: 'occur_last_year'===sortColumn()?sortDirection():''">happend last year</th>
        </tr>
    </thead>
    <tbody data-bind="foreach: {data: debitList}">
        <tr data-bind="css: $index() % 2 ? 'odd' : 'even'">
            <td data-column="name" data-bind="text: name, click: $root.gotoHref" class="clickable"></td>
            <td data-column="reported" data-bind="text: reported_loc"></td>
            <td data-column="last_happend" data-bind="text: last_happend_loc"></td>
            <td data-column="occur_total" data-bind="text: occur_total, click: $root.gotoHref" class="clickable"></td>
            <td data-column="occur_last_year" data-bind="text: occur_last_year, click: $root.gotoHref" class="clickable"></td>
        </tr>
    </tbody>
</table>
% include('_footer.tpl')

<!DOCTYPE html>
<head>
<title>Bank</title>
<link rel="stylesheet" type="text/css" href="static/style.css" />
<script type="text/javascript" src="static/jquery.js"></script>
<script type="text/javascript" src="static/knockout.js"></script>
<script type="text/javascript" src="static/javascript.js"></script>
<script type="text/javascript">
//<![CDATA[
var account = "{{account}}",
    routeName = "{{route_name}}";
//]]>
</script>
</head>
<body>
<div id="header">
    <div id="header_links">
        <a href="summary?account={{account}}">Summary</a>
        <a href="transactions?account={{account}}&dateFrom=yearAgo">Transactions</a>
        <a href="debit?account={{account}}">Direct Debit</a>
    </div>
    <div id="header_accounts">
% for x in accounts:
        <a href="?account={{x['number']}}" class="{{'active' if str(x['number']) == account else ''}}" title="last updated: {{x['last_update']}}">{{x['number']}}</a>
% end
    </div>
</div>

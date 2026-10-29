#!/usr/bin/env bash
# Runs the WSDL/SOAP examples of docs/python/25-wsdl-soap.md and docs/php/25-wsdl-soap.md, plus the
# python src/app.py entry blocks of 13-events §10 and 27-service-runner §10, against stock tina4-python /
# tina4-php through the real server. Blocks are taken verbatim; a block with no path is written where
# its prose says, else (classes with no route) mounted by a harness route at /h/<Class>. The docs' own
# curl blocks run with only the port changed. Every adaptation is named in the check's line.
# Pages: PY25= PY13= PY27= PHP25= <file>, or DOCS=<tina4-documentation tree>, or BOOK=<tina4-book tree>;
# default tina4-documentation origin/main. Usage: prove-py-php.sh [py|php] (default both).
# Frameworks: TINA4_PY (tree with .venv), TINA4_PHP (tree with vendor/); SOAP_INI (dir with soap.ini, for
# PHP's SoapClient). Ports PY_PORT (7600) PHP_PORT (7601).
cd "$(dirname "$0")"; H=$PWD; . ./portguard.sh
W=$HOME/.cache/tina4-worktrees
PY=${TINA4_PY:-$W/dapi01-py-efa826a3}; PH=${TINA4_PHP:-$W/dapi01-php-b321c1fc}; SOAP_INI=${SOAP_INI:-$W/php84-soap-ext/ini}
YP=${PY_PORT:-7600}; HP=${PHP_PORT:-7601}; SEC=0123456789abcdef0123456789abcdef0123456789abcdef
T=$(mktemp -d); trap '[ -n "$PID" ] && kill $PID 2>/dev/null; wait 2>/dev/null; rm -rf "$T"' EXIT
page(){ if [ -n "$1" ]; then cp "$1" $T/p; elif [ -n "$DOCS" ]; then cp "$DOCS/docs/$2" $T/p; elif [ -n "$BOOK" ]; then cp "$BOOK/$3" $T/p
  else git -C /var/home/work/gitdir/tinaforks/tina4-documentation show origin/main:docs/$2 > $T/p; fi; cat $T/p; }
page "$PY25" python/25-wsdl-soap.md book-1-python/chapters/25-wsdl-soap.md > $T/py25.md
page "$PY13" python/13-events.md book-1-python/chapters/13-events.md > $T/py13.md
page "$PY27" python/27-service-runner.md book-1-python/chapters/27-service-runner.md > $T/py27.md
page "$PHP25" php/25-wsdl-soap.md book-2-php/chapters/25-wsdl-soap.md > $T/php25.md
ok=0; bad=0
pass(){ echo "  PASS $1"; ok=$((ok+1)); }; fail(){ echo "  FAIL $1"; bad=$((bad+1)); }
has(){ grep -qF -- "$2" <<<"$1"; }
one(){ tr -d '\n' <<<"$1" | sed 's/>\s*</></g' | cut -c1-${2:-220}; }
# blk <md> <heading> <lang> [n]: the section's blocks (all, concatenated, or the n-th), verbatim
blk(){ local d=$T/blk.$RANDOM; python3 blocks.py "$1" "$2" "$3" $d | cut -f1 > $d.l; if [ -n "$4" ]; then cat "$(sed -n "${4}p" $d.l)"; else xargs cat < $d.l; fi; rm -rf $d $d.l; }
# curlblock <md> <heading> <docport> <port> [extra header]: run the section's bash blocks, port changed; appends HTTP <code>
curlblock(){ blk "$1" "$2" bash | sed -e "s/localhost:$3/127.0.0.1:$4/g" -e "s/^curl /curl -s -w '\\\\nHTTP %{http_code}\\\\n' ${5:+-H \"$5\" }/" | bash 2>&1; }
# xmlcmp <doc xml> <got>: every tag and text the doc shows (comments, decl and "..." dropped) must be in the output
xmlcmp(){ python3 - "$1" "$2" <<'EOF'
import re, sys
tok = lambda s: [re.sub(r"\s+", " ", t).strip() for t in re.findall(r"<[^>]+>|[^<]+", re.sub(r"<!--.*?-->", "", s, flags=re.S)) if t.strip() and not t.startswith("<?")]
want, got = tok(sys.argv[1]), set(tok(sys.argv[2]))
miss = [t for t in want if t not in got]
print("MATCH" if not miss else "MISSING %d/%d: %s" % (len(miss), len(want), " | ".join(miss[:5])))
EOF
}
env_run(){ env HOME=$(mktemp -d "$T/home.XXXX") TINA4_NO_BROWSER=true TINA4_OVERRIDE_CLIENT=true TINA4_SECRET=$SEC "$@"; }

# ---------- python ----------
py_app(){ A=$(mktemp -d "$T/py.XXXX"); mkdir -p $A/src/routes; printf '%s\n' '"""Tina4 Application."""' 'from tina4_python.core import run' '' 'if __name__ == "__main__":' '    run()' > $A/app.py; }
py_up(){ port_busy $YP && { echo "  PORT $YP BUSY before start"; return 1; }
  ( cd $A && exec env HOME=$(mktemp -d "$T/home.XXXX") TINA4_NO_BROWSER=true TINA4_OVERRIDE_CLIENT=true TINA4_SECRET=$SEC PYTHONUNBUFFERED=1 TINA4_DEBUG=${1:-false} TINA4_PORT=$YP "$PY/.venv/bin/python" app.py >server.log 2>&1 ) & PID=$!
  for i in $(seq 80); do curl -s -o /dev/null http://127.0.0.1:$YP/ && return 0; kill -0 $PID 2>/dev/null || break; sleep 0.25; done
  echo "  server did not start: $(tail -c 300 $A/server.log | tr '\n' ' ')"; return 1; }
py_down(){ kill $PID 2>/dev/null; wait $PID 2>/dev/null; PID=; wait_port_free $YP; }
# py_mount <file> <Class...>: harness route (public, GET+POST) for classes the doc gives no route
py_mount(){ local f=$1; shift; echo 'from tina4_python.core.router import get as _hg, post as _hp, noauth as _hn' >> $f
  for c in "$@"; do printf '%s\n' "@_hg(\"/h/$c\")" "@_hp(\"/h/$c\")" '@_hn()' "async def _h_$c(request, response):" "    return response($c(request).handle())" >> $f; done; }
ysoap(){ curl -s -X POST "http://127.0.0.1:$YP$1" -H 'Content-Type: text/xml' ${3:+-H "$3"} -d "<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"><soap:Body>$2</soap:Body></soap:Envelope>"; }
pytoken(){ ( cd $T && env_run "$PY/.venv/bin/python" -c 'from tina4_python.auth import Auth; print(Auth().get_token({"sub": "harness"}))' 2>/dev/null | tail -1 ); }
run_py(){
  echo "python (tina4-python $(git -C "$PY" log -1 --format=%h))"
  TOK=$(pytoken); [ -n "$TOK" ] || echo "  (no token minted)"
  # Y1-Y2 + gotcha 1: section 2 service + route, section 4 and 5 curl blocks, verbatim
  py_app; blk $T/py25.md "2. Your First SOAP Service" python > $A/src/routes/calculator.py
  if py_up; then
    w=$(curlblock $T/py25.md "4. Auto WSDL Generation at ?wsdl" 7146 $YP)
    s=$(curlblock $T/py25.md "5. Calling the Service" 7146 $YP)
    sa=$(curlblock $T/py25.md "5. Calling the Service" 7146 $YP "Authorization: Bearer $TOK")
    c=$(ysoap /api/soap/calculator '<Add><a>15</a><b>27</b></Add>' "Authorization: Bearer $TOK")
    g=$(curl -s -X POST http://127.0.0.1:$YP/api/soap/calculator -H 'Content-Type: text/xml' -H "Authorization: Bearer $TOK" -d '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><Add><a>15</a><b>27</b></Add></soap:Body></soap:Envelope>')
    g2=$(ysoap /api/soap/calculator '<Add xmlns="http://elsewhere.example/ns"><a>15</a><b>27</b></Add>' "Authorization: Bearer $TOK")
    py_down
    r=$(xmlcmp "$(blk $T/py25.md "4. Auto WSDL Generation at ?wsdl" xml)" "$w")
    [ "$r" = MATCH ] && pass "Y1 25/4 ?wsdl matches doc" || fail "Y1 25/4 ?wsdl vs doc: $r"
    r=$(xmlcmp "$(blk $T/py25.md "5. Calling the Service" xml)" "$s")
    [ "$r" = MATCH ] && pass "Y2 25/5 curl as written" || fail "Y2 25/5 curl as written: $(one "$s" 160) -- vs doc: $r"
    r=$(xmlcmp "$(blk $T/py25.md "5. Calling the Service" xml)" "$sa")
    [ "$r" = MATCH ] && pass "Y2b 25/5 curl + bearer token" || fail "Y2b 25/5 curl + bearer token: $(one "$sa" 300)"
    has "$c" '<Result>42</Result>' && pass "Y2c control: <Add> (not <tns:AddRequest>) + token -> $(grep -o '<Result>[^<]*</Result>' <<<"$c")" || fail "Y2c control: $(one "$c")"
    has "$g" 'Fault' && pass "G1 25/11 gotcha 1: no SOAPAction -> fault" || fail "G1 25/11 gotcha 1 says no SOAPAction -> 'operation was not found' fault; got $(grep -o '<Result>[^<]*</Result>' <<<"$g")"
    has "$g2" 'Fault' && pass "G2 25/11 gotcha 2: foreign namespace -> not matched" || fail "G2 25/11 gotcha 2 says a namespace mismatch is not matched; foreign ns got $(grep -o '<Result>[^<]*</Result>' <<<"$g2")"
  else py_down; fail "Y1-2 25/2 app did not boot"; fi
  # Y3: section 3 PriceService (no route in doc; harness mount)
  py_app; f=$A/src/routes/price.py; { echo 'from tina4_python.wsdl import WSDL, wsdl_operation'; blk $T/py25.md "3. The @wsdl_operation Decorator" python; } > $f; py_mount $f PriceService
  if py_up; then w=$(curl -s "http://127.0.0.1:$YP/h/PriceService?wsdl"); s=$(ysoap /h/PriceService '<GetProductPrice><product_id>KB-001</product_id><currency>EUR</currency></GetProductPrice>'); py_down
    has "$w" 'name="product_id" type="xsd:string"' && has "$s" '<Price>73.99</Price>' && has "$s" '<Currency>EUR</Currency>' && pass "Y3 25/3 PriceService (import line added): Price 73.99 EUR" || fail "Y3 25/3: $(one "$s")"
  else py_down; fail "Y3 25/3 did not boot"; fi
  # Y4: section 6 hooks
  py_app; f=$A/src/routes/order.py; blk $T/py25.md "6. Lifecycle Hooks: on_request and on_result" python > $f; py_mount $f OrderService
  if py_up; then s=$(ysoap /h/OrderService '<CreateOrder><customer_id>c1</customer_id><product_id>p1</product_id><quantity>2</quantity></CreateOrder>'); sleep 0.5; py_down
    if has "$s" '<OrderId>ORD-c1-p1</OrderId>' && grep -q 'SOAP request received' $A/server.log $A/logs/* 2>/dev/null && grep -q 'SOAP operation completed' $A/server.log $A/logs/* 2>/dev/null; then pass "Y4 25/6 hooks: OrderId ORD-c1-p1, both hook lines logged"
    else fail "Y4 25/6 hooks: $(one "$s" 160) log: $(grep -h -o -m2 -E 'SOAP (request received|operation completed)|Error[^"]{0,100}' $A/server.log $A/logs/* 2>/dev/null | tr '\n' ' ')"; fi
  else py_down; fail "Y4 25/6 did not boot"; fi
  # Y5: section 7 complex types and lists
  py_app; f=$A/src/routes/product.py; blk $T/py25.md "7. Complex Types and Lists" python > $f; py_mount $f ProductService
  if py_up; then w=$(curl -s "http://127.0.0.1:$YP/h/ProductService?wsdl"); p=$(ysoap /h/ProductService '<GetProduct><product_id>KB-001</product_id></GetProduct>')
    l=$(ysoap /h/ProductService '<SumList><Numbers>1</Numbers><Numbers>2</Numbers><Numbers>3</Numbers></SumList>'); l2=$(ysoap /h/ProductService '<SumList><Numbers>1,2,3</Numbers></SumList>'); py_down
    has "$p" '<Name>Wireless Keyboard</Name>' && pass "Y5a 25/7 GetProduct KB-001: $(grep -o -E '<(Name|InStock|Error)[^>]*>[^<]*' <<<"$p" | tr '\n' ' ')" || fail "Y5a 25/7 GetProduct: $(one "$p")"
    has "$l" '<Total>6</Total>' && pass "Y5b 25/7 SumList repeated <Numbers>: Total 6" || fail "Y5b 25/7 SumList repeated <Numbers> 1,2,3 (WSDL: $(grep -o '<xsd:element name="Numbers"[^>]*>' <<<"$w")): got $(grep -o -E '<(Total|Average)>[^<]*' <<<"$l" | tr '\n' ' '); comma form <Numbers>1,2,3</Numbers> got $(grep -o -E '<Total>[^<]*' <<<"$l2")"
  else py_down; fail "Y5 25/7 did not boot"; fi
  # Y6: section 8 fault (production, then debug)
  py_app; f=$A/src/routes/order.py; { echo 'from tina4_python.wsdl import WSDL, wsdl_operation'; blk $T/py25.md "8. Error Handling" python; } > $f; py_mount $f OrderService
  q='<CreateOrder><customer_id>c</customer_id><product_id>p</product_id><quantity>0</quantity></CreateOrder>'
  if py_up false; then a=$(ysoap /h/OrderService "$q"); py_down; py_up true && { b=$(ysoap /h/OrderService "$q"); py_down; }
    r=$(xmlcmp "$(blk $T/py25.md "8. Error Handling" xml)" "$a")
    [ "$r" = MATCH ] && pass "Y6 25/8 fault as shown (import line added)" || fail "Y6 25/8 fault: doc shows $(one "$(blk $T/py25.md "8. Error Handling" xml)" 200); production got $(grep -o '<faultcode>.*</faultstring>' <<<"$a"); TINA4_DEBUG=true got $(grep -o '<faultcode>.*</faultstring>' <<<"$b")"
  else py_down; fail "Y6 25/8 did not boot"; fi
  # Y7: section 10 solution at src/routes/currency_soap.py, section 9 test curls
  py_app; blk $T/py25.md "10. Solution" python > $A/src/routes/currency_soap.py
  if py_up; then s=$(curlblock $T/py25.md "9. Exercise: Build a Currency Conversion SOAP Service" 7146 $YP); sa=$(curlblock $T/py25.md "9. Exercise: Build a Currency Conversion SOAP Service" 7146 $YP "Authorization: Bearer $TOK"); py_down
    if has "$s" '<Amount>92.0</Amount>'; then pass "Y7 25/9-10 Convert 100 USD->EUR = 92.0"
    else fail "Y7 25/9-10 test curls: wsdl $(grep -c 'name="Convert' <<<"$s") hits; as written: $(grep -o -E 'HTTP [0-9]+' <<<"$s" | tr '\n' ' '); + token: $(grep -o -E '<faultstring>[^<]*|<Amount>[^<]*' <<<"$sa")"; fi
  else py_down; fail "Y7 25/10 did not boot"; fi
  # Y8: 13 section 10, src/routes/user_events.py + src/app.py entry block
  py_app; blk $T/py13.md "10. Solution" python 1 > $A/src/routes/user_events.py; blk $T/py13.md "10. Solution" python 2 > $A/src/app.py
  if py_up; then sleep 0.5; py_down; grep -q 'Application ready.' $A/server.log && pass "Y8 13/10 src/app.py emit reaches @once app.ready handler" || fail "Y8 13/10 src/app.py: 'Application ready.' never printed; log: $(grep -m2 -iE 'error|app.py' $A/server.log | cut -c1-160 | tr '\n' ' ')"
  else py_down; fail "Y8 13/10 did not boot"; fi
  # Y8c control: the same two files, src/app.py renamed so it sorts after src/routes/ (server.py:467 imports in sorted order)
  mv $A/src/app.py $A/src/zz_app.py; : > $A/server.log
  if py_up; then sleep 0.5; py_down; grep -q 'Application ready.' $A/server.log && pass "Y8c control: as src/zz_app.py the handler fires" || fail "Y8c control: still not printed"; else py_down; fail "Y8c did not boot"; fi
  # Y9: 27 section 10, three blocks at their path comments, src/app.py starts the runner
  py_app; for n in 1 2 3; do blk $T/py27.md "10. Solution" python $n > $T/b; p=$(head -1 $T/b | sed -E 's/^# (src\/[^ ]+\.py).*/\1/'); mkdir -p $A/$(dirname $p); cp $T/b $A/$p; done
  if py_up; then r=; for i in $(seq 12); do r=$(curl -s http://127.0.0.1:$YP/api/products/featured); has "$r" '"count": 20' && break; has "$r" '"count":20' && break; sleep 0.5; done; py_down
    has "$r" '"count"' && pass "Y9 27/10 src/app.py runner warms cache: $(grep -o '"count": *[0-9]*' <<<"$r")" || fail "Y9 27/10 featured endpoint: $(one "$r" 120); log: $(grep -m1 -iE 'error|exception|typeerror' $A/server.log | cut -c1-160)"
  else py_down; fail "Y9 27/10 did not boot: $(grep -m1 -iE 'error' $A/server.log | cut -c1-160)"; fi; }

# ---------- php ----------
php_app(){ A=$(mktemp -d "$T/php.XXXX"); mkdir -p $A/src/routes $A/src/app $A/vendor
  for e in "$PH"/vendor/*; do [ "$(basename $e)" = autoload.php ] || ln -s "$e" $A/vendor/; done
  # the project's composer autoloader: the framework's, plus the psr-4 '' => src/app/ that `tina4php init` writes
  printf '%s\n' '<?php' "\$l = require '$PH/vendor/autoload.php';" "\$l->addPsr4('', __DIR__ . '/../src/app/');" 'return $l;' > $A/vendor/autoload.php
  printf '%s\n' '<?php' 'require_once "./vendor/autoload.php";' '' '$app = new \Tina4\App(basePath: __DIR__);' '$app->handle();' > $A/index.php; }
php_env(){ env_run PHP_INI_SCAN_DIR=":$SOAP_INI" "$@"; }
php_up(){ port_busy $HP && { echo "  PORT $HP BUSY before start"; return 1; }
  ( cd $A && exec env HOME=$(mktemp -d "$T/home.XXXX") TINA4_NO_BROWSER=true TINA4_OVERRIDE_CLIENT=true TINA4_SECRET=$SEC PHP_INI_SCAN_DIR=":$SOAP_INI" TINA4_DEBUG=${1:-false} php "$PH/bin/tina4php" serve 127.0.0.1:$HP >server.log 2>&1 ) & PID=$!
  for i in $(seq 80); do curl -s -o /dev/null http://127.0.0.1:$HP/ && return 0; kill -0 $PID 2>/dev/null || break; sleep 0.25; done
  echo "  server did not start: $(tail -c 300 $A/server.log | tr '\n' ' ')"; return 1; }
php_down(){ pkill -P $PID 2>/dev/null; kill $PID 2>/dev/null; wait $PID 2>/dev/null; PID=; wait_port_free $HP; }
# client <file>: run a doc client script; each `echo X; // V` gets a newline so outputs line up with the comments
# with TOK set, the SoapClient also gets a stream_context carrying "Authorization: Bearer $TOK" (the only change);
# KA=1 adds keep_alive => false (a second request on a kept-alive connection fails with "Error Fetching http headers")
client(){ sed -E 's#^(\s*echo [^;]+);(\s*//)#\1, "\\n";\2#' "$1" | sed "s/localhost:7145/127.0.0.1:$HP/g" > $A/client.php
  [ -n "$TOK" ] && python3 -c 'import re,sys; f,t,k=sys.argv[1:]; o=("\x27keep_alive\x27 => false, " if k else "") + "\x27stream_context\x27 => stream_context_create([\x27http\x27 => [\x27header\x27 => \x27Authorization: Bearer %s\x27]])" % t; s=open(f).read(); s=re.sub(r"(new SoapClient\(\x27[^\x27]+\x27)(, \[|\))", lambda m: m.group(1) + (", [" + o + ", " if m.group(2) != ")" else ", [" + o + "])"), s); open(f,"w").write(s)' $A/client.php "$TOK" "$KA"
  ( cd $A && php_env timeout 30 php -d display_errors=stderr -d log_errors=0 client.php 2>$A/client.err; echo __ERR__; cat $A/client.err ); }
# expect <script> <output>: compare each echo line with the value in its // comment (numerically when numeric)
expect(){ python3 - "$1" "$2" <<'EOF'
import re, sys
want = [m.group(1).strip() for m in re.finditer(r"echo [^;]+;\s*//\s*(.*)", open(sys.argv[1]).read())]
out, err = open(sys.argv[2]).read().split("__ERR__\n", 1)
got = out.split("\n")
errs = [l for l in err.split("\n") if re.match(r"(PHP )?(Warning|Fatal|Uncaught)", l.strip())]
bad = []
for i, w in enumerate(want):
    g = got[i] if i < len(got) else "<none>"
    try: same = abs(float(w.rstrip(".")) - float(g)) < 1e-3 if w.endswith("...") else float(w) == float(g)
    except ValueError: same = g.strip() == w
    if not same: bad.append("doc %r got %r" % (w, g))
print("MATCH" if not bad else "%d/%d differ: %s%s" % (len(bad), len(want), "; ".join(bad[:5]), (" | " + " / ".join(sorted(set(re.sub(r" in /\S+", "", e.strip())[:110] for e in errs)))) if errs else ""))
EOF
}
hsoap(){ curl -s -X POST "http://127.0.0.1:$HP$1" -H 'Content-Type: text/xml' -d "<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"><soap:Body>$2</soap:Body></soap:Envelope>"; }
run_php(){
  echo "php (tina4-php $(git -C "$PH" log -1 --format=%h); SoapClient $(PHP_INI_SCAN_DIR=":$SOAP_INI" php -r 'echo class_exists("SoapClient") ? "loaded" : "MISSING";'))"
  # H1-H3,H5: section 2 class in src/app, section 3 route in src/routes; 4 and 9 curl blocks; 5 SoapClient script
  php_app; blk $T/php25.md "2. Creating a SOAP Service" php > $A/src/app/CalculatorService.php; blk $T/php25.md "3. Registering the Service" php > $A/src/routes/calculator.php
  blk $T/php25.md "6. A Real-World Service: Currency Conversion" php 1 > $A/src/app/CurrencyService.php
  { printf '%s\n' '<?php' 'use Tina4\Router;' 'use Tina4\Request;' 'use Tina4\Response;'; blk $T/php25.md "6. A Real-World Service: Currency Conversion" php 2; } > $A/src/routes/currency.php
  printf '%s\n' '<?php' 'use Tina4\WSDL;' 'use Tina4\WSDLOperation;' 'class UserService extends WSDL {' > $A/src/app/UserService.php; blk $T/php25.md "8. SOAP Faults" php >> $A/src/app/UserService.php; echo '}' >> $A/src/app/UserService.php
  # control for H3: the same class with `use Tina4\WSDLOperation;` added (the doc's block omits it), renamed
  blk $T/php25.md "6. A Real-World Service: Currency Conversion" php 1 | sed -e 's/^use Tina4\\WSDL;/use Tina4\\WSDL;\nuse Tina4\\WSDLOperation;/' -e 's/class CurrencyService /class CurrencyServiceUse /' > $A/src/app/CurrencyServiceUse.php
  # harness route: get + post()->noAuth(), because any()->noAuth() opens only GET (Router.php:269-271)
  printf '%s\n' '<?php' '$h = fn($request, $response) => (new UserService($request))->handle();' 'Tina4\Router::get("/h/UserService", $h);' 'Tina4\Router::get("/h/CurrencyServiceUse", fn($request, $response) => (new CurrencyServiceUse($request))->handle());' 'Tina4\Router::post("/h/UserService", $h)->noAuth();' > $A/src/routes/zz_harness.php
  TOK=$(cd $T && php -r "require '$PH/vendor/autoload.php'; echo \Tina4\Auth::getToken(['sub' => 'harness'], '$SEC', 3600);" 2>/dev/null | tail -1); [ -n "$TOK" ] || echo "  (no token minted)"
  if php_up; then
    w=$(curlblock $T/php25.md "4. Accessing the Auto-Generated WSDL" 7145 $HP)
    s=$(curlblock $T/php25.md "9. Testing with curl" 7145 $HP); st=$(curlblock $T/php25.md "9. Testing with curl" 7145 $HP "Authorization: Bearer $TOK")
    blk $T/php25.md "5. Calling the Service with PHP SoapClient" php > $T/c5.php; K=$TOK; TOK= client $T/c5.php > $T/o5; TOK=$K client $T/c5.php > $T/o5t; TOK=$K KA=1 client $T/c5.php > $T/o5k
    { echo '<?php'; blk $T/php25.md "6. A Real-World Service: Currency Conversion" php 3; } > $T/c6.php; TOK=$K client $T/c6.php > $T/o6
    cw=$(curl -s "http://127.0.0.1:$HP/currency?wsdl"); cu=$(curl -s "http://127.0.0.1:$HP/h/CurrencyServiceUse?wsdl")
    u=$(hsoap /h/UserService '<GetUserEmail><userId>0</userId></GetUserEmail>')
    php_down
    if php_up true; then blk $T/php25.md "5. Calling the Service with PHP SoapClient" php > $T/c5.php; TOK=$K KA=1 client $T/c5.php > $T/o5d; ud=$(hsoap /h/UserService '<GetUserEmail><userId>0</userId></GetUserEmail>'); php_down; fi
    r=$(xmlcmp "$(blk $T/php25.md "4. Accessing the Auto-Generated WSDL" xml)" "$w")
    [ "$r" = MATCH ] && pass "H1 25/4 ?wsdl matches doc" || fail "H1 25/4 ?wsdl vs doc: $r"
    r=$(expect $T/c5.php $T/o5); [ "$r" = MATCH ] && pass "H2 25/5 SoapClient outputs match comments" || fail "H2 25/5 SoapClient (production): $r"
    r=$(expect $T/c5.php $T/o5t); [ "$r" = MATCH ] && pass "H2t 25/5 SoapClient + bearer token" || fail "H2t 25/5 SoapClient + bearer token (production): $r"
    r=$(expect $T/c5.php $T/o5k); [ "$r" = MATCH ] && pass "H2k 25/5 + token, keep_alive off" || fail "H2k 25/5 SoapClient + token + keep_alive off (production): $r"
    r=$(expect $T/c5.php $T/o5d); [ "$r" = MATCH ] && pass "H2d 25/5 + token, keep_alive off, TINA4_DEBUG=true" || fail "H2d 25/5 SoapClient + token + keep_alive off (TINA4_DEBUG=true): $r"
    r=$(expect $T/c6.php $T/o6); [ "$r" = MATCH ] && pass "H3 25/6 Currency (<?php + use lines added to fragments, + token)" || fail "H3 25/6 Currency: $r; ?wsdl operations: $(grep -c '<operation name=' <<<"$cw"), with the use line added: $(grep -c '<operation name=' <<<"$cu")"
    has "$u" '<faultcode>Client</faultcode>' && has "$u" 'User ID must be a positive integer' && pass "H4 25/8 SoapFault('Client') reaches client" || fail "H4 25/8 SoapFault('Client',...): production got $(grep -o '<faultcode>.*</faultstring>' <<<"$u"); debug got $(grep -o '<faultcode>.*</faultstring>' <<<"$ud") (method wrapped in a class, harness route)"
    r=$(xmlcmp "$(blk $T/php25.md "9. Testing with curl" xml)" "$s")
    [ "$r" = MATCH ] && pass "H5 25/9 curl matches doc" || fail "H5 25/9 curl as written: $(one "$s" 200) -- vs doc: $r"
    r=$(xmlcmp "$(blk $T/php25.md "9. Testing with curl" xml)" "$st")
    [ "$r" = MATCH ] && pass "H5t 25/9 curl + bearer token matches doc" || fail "H5t 25/9 curl + bearer token: $(one "$st" 300) -- vs doc: $r"
  else php_down; fail "H1-5 25/2-9 app did not boot"; fi; }

case "${1:-all}" in py) run_py;; php) run_php;; *) run_py; run_php;; esac
echo "VERDICT ok=$ok bad=$bad"; [ $bad = 0 ]

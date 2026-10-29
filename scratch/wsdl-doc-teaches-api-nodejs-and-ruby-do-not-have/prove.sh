#!/usr/bin/env bash
# Runs the WSDL/SOAP examples of docs/nodejs/25-wsdl-soap.md, docs/ruby/25-wsdl-soap.md and the app.ts
# entry blocks of docs/nodejs/13-events.md, verbatim, against stock tina4-nodejs / tina4-ruby, through the real
# server. Code blocks are written where their first-line path comment says (else into src/app|src/services
# and loaded by the harness); the docs' own curl blocks are run with only the port changed.
# Pages: ND25= ND13= RB25= <file>, or DOCS=<tina4-documentation tree>, or BOOK=<tina4-book tree>;
# default tina4-documentation origin/main. Usage: prove.sh [nd|rb] (default both).
cd "$(dirname "$0")"; H=$PWD; . ./portguard.sh
ND=${TINA4_ND:-$HOME/.cache/tina4-worktrees/docfix-stock-nodejs}; RB=${TINA4_RB:-$HOME/.cache/tina4-worktrees/docfix-stock-ruby}
NP=${ND_PORT:-7341}; RP=${RB_PORT:-7342}; SEC=0123456789abcdef0123456789abcdef0123456789abcdef
T=$(mktemp -d); trap '[ -n "$PID" ] && kill $PID 2>/dev/null; rm -rf "$T"' EXIT
page(){ # page <var-value> <docs path> <book path>
  if [ -n "$1" ]; then cp "$1" $T/p; elif [ -n "$DOCS" ]; then cp "$DOCS/docs/$2" $T/p; elif [ -n "$BOOK" ]; then cp "$BOOK/$3" $T/p
  else git -C /var/home/work/gitdir/tinaforks/tina4-documentation show origin/main:docs/$2 > $T/p; fi; cat $T/p; }
page "$ND25" nodejs/25-wsdl-soap.md book-4-nodejs/chapters/25-wsdl-soap.md > $T/nd25.md
page "$ND13" nodejs/13-events.md book-4-nodejs/chapters/13-events.md > $T/nd13.md
page "$RB25" ruby/25-wsdl-soap.md book-3-ruby/chapters/25-wsdl-soap.md > $T/rb25.md
ok=0; bad=0; skip=0
pass(){ echo "  PASS $1"; ok=$((ok+1)); }; fail(){ echo "  FAIL $1"; bad=$((bad+1)); }
has(){ grep -qF -- "$2" <<<"$1"; }
# net <output>: the remote service, not the code, failed (outage, reset, timeout, 5xx)
net(){ grep -qE 'fetch failed|ECONNRESET|ETIMEDOUT|ENOTFOUND|EAI_AGAIN|ECONNREFUSED|UND_ERR|SOAP HTTP 5[0-9]{2}|status(Code)?:? ?5[0-9]{2}' <<<"$1"; }
why(){ local l; l=$(grep -a -m1 -E 'ERROR: |SyntaxError|does not provide|Cannot find' "$1" || grep -a -m1 -E 'Error' "$1"); echo "${l:0:180}"; }
# place <md> <heading> <lang> <appdir> <fallback dir>: writes the section's blocks, prints the unpathed ones
place(){ local n=0; python3 blocks.py "$1" "$2" "$3" "$T/b$$" 2>/dev/null | while IFS=$'\t' read -r f p; do
    n=$((n+1)); if [ "$p" = - ]; then case $f in *.ruby) x=rb;; *) x=ts;; esac; p="$5/block_${2%%.*}_$n.$x"; echo "$p"; fi
    mkdir -p "$4/$(dirname "$p")"; cp "$f" "$4/$p"; done; rm -rf "$T/b$$"; }
curlblock(){ python3 blocks.py "$1" "$2" bash "$T/c" | cut -f1 | while read -r f; do sed "s/localhost:$3/127.0.0.1:$4/g" "$f" | bash 2>/dev/null; echo; done; rm -rf "$T/c"; }
shown(){ python3 blocks.py "$1" "$2" xml "$T/x" | cut -f1 | xargs cat; rm -rf "$T/x"; }

# ---------- nodejs ----------
nd_app(){ A=$(mktemp -d "$T/nd.XXXX"); mkdir -p $A/node_modules $A/src/routes; echo '{ "type": "module" }' > $A/package.json; ln -s "$ND" $A/node_modules/tina4-nodejs; }
nd_up(){ port_busy $NP && { echo "PORT $NP BUSY before start"; return 1; }
  ( cd $A && HOME=$(mktemp -d "$T/home.XXXX") TINA4_DEBUG=false TINA4_SECRET=$SEC TINA4_PORT=$NP exec "$ND/node_modules/.bin/tsx" "${1:-app.ts}" >server.log 2>&1 ) & PID=$!
  for i in $(seq 60); do curl -s -o /dev/null http://127.0.0.1:$NP/ && return 0; kill -0 $PID 2>/dev/null || break; sleep 0.25; done
  echo "  server did not start: $(why $A/server.log)"; return 1; }
nd_down(){ kill $PID 2>/dev/null; wait $PID 2>/dev/null; wait_port_free $NP; }
nd_harness_app(){ { sed 's#^src/\(.*\)\.ts$#import "./src/\1";#' "$1"; echo 'import { startServer } from "tina4-nodejs";'
  echo 'await startServer({ port: Number(process.env.TINA4_PORT), basePath: process.cwd(), noBrowser: true });'; } > $A/app.ts; }
probe_route(){ mkdir -p $A/src/routes/__probe; printf '%s\n' 'import { Events } from "tina4-nodejs";' 'export default async (req, res) => res.json({ n: Events.listeners("order.placed").length });' > $A/src/routes/__probe/get.ts; }
run_nd(){
  echo "nodejs (tina4-nodejs $(git -C "$ND" log -1 --format=%h))"
  # N1: 25 section 2, consuming a remote service (needs the network; skipped when the service is down)
  if curl -s -m 10 -o /dev/null https://www.dataaccess.com/webservicesserver/NumberConversion.wso; then
    nd_app; python3 blocks.py $T/nd25.md "2. Consuming an External SOAP Service" typescript $T/n1 | cut -f1 | xargs cat > $A/client.mts; rm -rf $T/n1
    for try in 1 2 3; do out=$(cd $A && HOME=$(mktemp -d "$T/home.XXXX") timeout 60 "$ND/node_modules/.bin/tsx" client.mts 2>&1); rc=$?; net "$out" || break; sleep 3; done
    if [ $rc = 0 ] && has "$out" "forty two"; then pass "N1 25/2 client: $(head -1 <<<"$out")"
    elif net "$out"; then echo "  SKIP N1 25/2 client: network error after 3 tries: $(grep -m1 -o -E 'fetch failed|E[A-Z_]{4,}|UND_ERR[A-Z_]*|HTTP [0-9]{3}' <<<"$out")"; skip=$((skip+1))
    else fail "N1 25/2 client rc=$rc: $(why <(printf '%s' "$out"))"; fi
  else echo "  SKIP N1 25/2 client: dataaccess.com unreachable"; skip=$((skip+1)); fi
  # N2: 25 section 3, the decorator block loads and publishes its operation
  nd_app; place $T/nd25.md "3. The @WSDLOperation Decorator" typescript $A src/app > $T/u; [ -s $T/u ] || place $T/nd25.md "3. wsdl_operation Decorator" typescript $A src/app > $T/u
  printf '%s\n' 'import { WSDLService } from "tina4-nodejs";' "const m = await import(\"./$(head -1 $T/u)\");" \
    'for (const v of Object.values(m)) if (typeof v === "function" && v.prototype instanceof WSDLService) console.log(new (v as any)().generateWSDL());' > $A/n2.mts
  out=$(cd $A && HOME=$(mktemp -d "$T/home.XXXX") timeout 60 "$ND/node_modules/.bin/tsx" n2.mts 2>&1)
  has "$out" '<xsd:element name="GetProductPrice">' && has "$out" 'name="productId" type="xsd:string"' && pass "N2 25/3 decorator publishes GetProductPrice" || fail "N2 25/3 decorator: $(why <(printf '%s' "$out"))"
  # N3: 25 sections 4+5, publish CurrencyService, the doc's own curl blocks
  nd_app; place $T/nd25.md "4. Publishing a SOAP Service" typescript $A src/app > $T/u; nd_harness_app $T/u
  if nd_up; then w=$(curlblock $T/nd25.md "4. Publishing a SOAP Service" 7148 $NP); s=$(curlblock $T/nd25.md "5. Calling Your Published Service" 7148 $NP); nd_down
    d=$(shown $T/nd25.md "5. Calling Your Published Service" | grep -o '<result>[^<]*</result>')
    if has "$w" '<xsd:element name="ConvertCurrency">' && has "$s" '<result>92</result>' && has "$s" '<rate>0.92</rate>' && has "$s" "$d"; then pass "N3 25/4-5 publish+call: $(grep -o '<result>[^<]*</result>' <<<"$s"), doc shows $d"
    else fail "N3 25/4-5 publish+call: wsdl $(grep -c ConvertCurrency <<<"$w") hits, response $(tr -d '\n' <<<"$s" | cut -c1-160), doc shows $d"; fi
  else nd_down; fail "N3 25/4-5 publish+call: app did not boot"; fi
  # N4: 25 section 7 solution, the section 6 test curls plus ListProducts
  nd_app; place $T/nd25.md "7. Solution" typescript $A src/app > $T/u; nd_harness_app $T/u
  if nd_up; then s=$(curlblock $T/nd25.md "6. Exercise: Expose a Product Catalogue as a SOAP Service" 7148 $NP)
    l=$(curl -s -X POST http://127.0.0.1:$NP/soap/products -H 'Content-Type: text/xml' -d '<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/"><soap:Body><ListProducts><category>Electronics</category></ListProducts></soap:Body></soap:Envelope>'); nd_down
    if has "$s" '<xsd:element name="GetProduct">' && has "$s" '<name>Wireless Keyboard</name>' && [ "$(grep -o '<productIds>[^<]*</productIds>' <<<"$l" | tr -d '\n')" = '<productIds>1</productIds><productIds>4</productIds>' ]; then pass "N4 25/7 solution: GetProduct + ListProducts(Electronics)=1,4"
    else fail "N4 25/7 solution: $(tr -d '\n' <<<"$s$l" | grep -o -E 'faultstring>[^<]*|<name>[^<]*|<productIds>[^<]*|<h1>[^<]*' | head -3 | tr '\n' ' ')"; fi
  else nd_down; fail "N4 25/7 solution: app did not boot"; fi
  # N5: 13 sections 9 and 11, the app.ts entry blocks verbatim (the events files they import: 11's own, a stub for 9's)
  for sec in "9. Organising Events in a Real Application" "11. Solution"; do
    nd_app; python3 blocks.py $T/nd13.md "$sec" typescript $T/e > $T/u; f=$(tail -1 $T/u | cut -f1)
    # the entry file is where the section's prose says (stock: src/index.ts, fixed: app.ts)
    E=app.ts; sed -n "/^## ${sec%%.*}\./,/^## [0-9]/p" $T/nd13.md | grep -q '`src/index.ts`' && E=src/index.ts; mkdir -p $A/src; cp "$f" $A/$E
    if [ "${sec%%.*}" = 11 ]; then mkdir -p $A/src/events; cp "$(head -1 $T/u | cut -f1)" $A/src/events/orders.ts
    else mkdir -p $A/src/events; printf '%s\n' 'import { Events } from "tina4-nodejs";' 'Events.on("order.placed", () => {});' > $A/src/events/index.ts; fi; rm -rf $T/e; probe_route
    want=$([ "${sec%%.*}" = 11 ] && echo 3 || echo 1)
    if nd_up $E; then n=$(curl -s http://127.0.0.1:$NP/__probe); nd_down
      [ "$n" = "{\"n\":$want}" ] && pass "N5 13/${sec%%.*} app.ts boots, $want listener(s) registered" || fail "N5 13/${sec%%.*} app.ts: probe said $n"
    else nd_down; fail "N5 13/${sec%%.*} $E did not boot"; fi
  done; }

# ---------- ruby ----------
rb_app(){ A=$(mktemp -d "$T/rb.XXXX"); mkdir -p $A/src/routes $A/src/services; printf '%s\n' 'require "tina4"' 'Tina4.run!(port: ENV.fetch("PORT").to_i, no_browser: true)' > $A/app.rb; }
rb_up(){ port_busy $RP && { echo "PORT $RP BUSY before start"; return 1; }
  ( cd $A && HOME=$(mktemp -d "$T/home.XXXX") TINA4_OVERRIDE_CLIENT=true TINA4_DEBUG=${1:-false} TINA4_SECRET=$SEC PORT=$RP exec ruby -I "$RB/lib" app.rb >server.log 2>&1 ) & PID=$!
  for i in $(seq 60); do curl -s -o /dev/null http://127.0.0.1:$RP/ && return 0; kill -0 $PID 2>/dev/null || break; sleep 0.25; done; echo "  server did not start"; return 1; }
rb_down(){ kill $PID 2>/dev/null; wait $PID 2>/dev/null; wait_port_free $RP; }
rb_errs(){ grep -a -o -m1 -E "(Failed to load|500 Internal Server Error)[^\"]{0,140}" $A/server.log; }
# harness route: mounts every Tina4::WSDL subclass the blocks define at /h/<ClassName>
rb_mount(){ { sed 's|^src/services/\(.*\)$|begin; require_relative "../services/\1"; rescue Exception => e; Tina4::Log.error("Failed to load \1: #{e.class}: #{e.message}"); end|' "$1"
  echo 'Tina4::WSDL.subclasses.each { |k| Tina4::Router.post("/h/#{k.name}") { |request, response| response.xml(k.new(request).handle) }.no_auth }'; } > $A/src/routes/zz_harness.rb; }
soap(){ curl -s -X POST "http://127.0.0.1:$RP/h/$1" -H 'Content-Type: text/xml' -d "<soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\"><soap:Body>$2</soap:Body></soap:Envelope>"; }
run_rb(){
  echo "ruby (tina4-ruby $(git -C "$RB" log -1 --format=%h))"
  # R1: 25 sections 3-6, define + mount CalculatorService, the doc's own curl blocks
  rb_app; place $T/rb25.md "3. Defining a WSDL Service" ruby $A src/services > /dev/null; place $T/rb25.md "4. Mounting the Service" ruby $A src/routes > /dev/null
  if rb_up; then w=$(curlblock $T/rb25.md "5. Auto-Generated WSDL" 7147 $RP); s=$(curlblock $T/rb25.md "6. Calling the SOAP Service" 7147 $RP); e=$(rb_errs); rb_down
    d=$(shown $T/rb25.md "6. Calling the SOAP Service" | grep -o '<result>[^<]*</result>')
    if has "$w" '<xsd:element name="add">' && has "$s" '<result>42</result>' && has "$s" "$d"; then pass "R1 25/3-6 define+mount+call: <result>42</result>, doc shows $d"
    else fail "R1 25/3-6: wsdl '$(head -c 60 <<<"$w" | tr -d '\n')' response '$(tr -d '\n' <<<"$s" | cut -c1-80)' log: $e"; fi
  else rb_down; fail "R1 25/3-6: app did not boot"; fi
  # R2: 25 section 8, several fields and lists
  rb_app; place $T/rb25.md "$(grep -m1 -o -E '^## 8\. .*' $T/rb25.md | sed 's/^## //')" ruby $A src/services > $T/u
  ls $A/src/services/*.rb 2>/dev/null | sed "s#^$A/##" > $T/u; rb_mount $T/u
  if rb_up; then o=$(soap OrderService '<place_order><customer_email>a@b.c</customer_email><city>Cape Town</city><total>9.5</total></place_order>'); k=$(soap OrderService '<list_skus><category>x</category></list_skus>'); e=$(rb_errs); rb_down
    if has "$o" '<status>pending</status>' && has "$o" '<total>9.5</total>' && [ "$(grep -c '<sku>' <<<"$k")" = 2 ]; then pass "R2 25/8 fields+list: place_order total 9.5, list_skus 2 items"
    else fail "R2 25/8: $(tr -d '\n' <<<"$o" | cut -c1-80) log: $e"; fi
  else rb_down; fail "R2 25/8: app did not boot"; fi
  # R3: 25 section 9, a raised exception becomes the fault the doc shows (production), and its message under debug
  rb_app; place $T/rb25.md "9. Error Handling in Operations" ruby $A src/services > /dev/null
  ls $A/src/services/*.rb | sed "s#^$A/##" > $T/u; rb_mount $T/u; d=$(shown $T/rb25.md "9. Error Handling in Operations" | grep -o '<faultstring>[^<]*</faultstring>')
  if rb_up false; then p=$(soap SafeCalculatorService '<divide><a>1</a><b>0</b></divide>'); e=$(rb_errs); rb_down
    if rb_up true; then q=$(soap SafeCalculatorService '<divide><a>1</a><b>0</b></divide>'); rb_down; fi
    if has "$p" "$d" && has "$p" '<faultcode>Server</faultcode>' && has "$q" '<faultstring>Divisor cannot be zero</faultstring>'; then pass "R3 25/9 fault: production '$d' as shown, debug shows the message"
    else fail "R3 25/9: doc shows $d, got '$(grep -o '<faultstring>[^<]*' <<<"$p")' / debug '$(grep -o '<faultstring>[^<]*' <<<"$q")' log: $e"; fi
  else rb_down; fail "R3 25/9: app did not boot"; fi; }

case "${1:-all}" in nd) run_nd;; rb) run_rb;; *) run_nd; run_rb;; esac
echo "VERDICT ok=$ok bad=$bad skip=$skip"; [ $bad = 0 ]

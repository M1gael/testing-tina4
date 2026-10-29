#!/usr/bin/env bash
# f-api-12: does a second php SoapClient call fail on a kept-alive connection to a tina4-php WSDL service?
# SERVER=serve (tina4php serve, default) or SERVER=php-S; NOFORK=1 disables pcntl_fork (request served in the parent). Three calls in one SoapClient, keep_alive default (true) vs false. usage: soap-keepalive.sh [tina4-php tree]  port 7691
P=${1:-$HOME/.cache/tina4-worktrees/dapi01-php-b321c1fc}; SOAP_INI=${SOAP_INI:-$HOME/.cache/tina4-worktrees/php84-soap-ext/ini}; PORT=7691
ss -ltn | grep -q ":$PORT " && { echo "port $PORT busy"; exit 2; }
A=$(mktemp -d); mkdir -p $A/src/routes
cat > $A/src/routes/calc.php <<'PHP'
<?php
use Tina4\Router; use Tina4\WSDL; use Tina4\WSDLOperation;
class Calculator extends WSDL {
    #[WSDLOperation(['Result' => 'int'])]
    public function Add(int $a, int $b): array { return ['Result' => $a + $b]; }
}
Router::get('/calculator', fn($req, $res) => (new Calculator($req))->handle())->noAuth();
Router::post('/calculator', fn($req, $res) => (new Calculator($req))->handle())->noAuth();
Router::get('/hello', fn($req, $res) => $res->json(['hello' => 'world']));
PHP
printf '<?php\nrequire "%s/vendor/autoload.php";\n$app = new \\Tina4\\App(basePath: __DIR__);\n$app->handle();\n' "$P" > $A/index.php
SECRET=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d " \n")
if [ "${SERVER:-serve}" = serve ]; then cd $A; HOME=$(mktemp -d) TINA4_NO_BROWSER=true TINA4_OVERRIDE_CLIENT=true TINA4_SECRET=$SECRET php ${NOFORK:+-d disable_functions=pcntl_fork} $P/bin/tina4php serve 127.0.0.1:$PORT > $A/server.log 2>&1 & SP=$!
else cd $A; HOME=$(mktemp -d) TINA4_SECRET=$SECRET php -S 127.0.0.1:$PORT -t $A $A/index.php > $A/server.log 2>&1 & SP=$!; fi
echo "server: ${SERVER:-serve}${NOFORK:+ (pcntl_fork disabled)}"
for i in $(seq 100); do curl -s -o /dev/null "127.0.0.1:$PORT/calculator?wsdl" && break; sleep 0.2; done; curl -s -o /dev/null "127.0.0.1:$PORT/calculator?wsdl" || { echo "server did not start"; tail -5 $A/server.log; }
cat > $A/client.php <<'PHP'
<?php
[$_, $port, $ka] = $argv;
$opts = ['cache_wsdl' => WSDL_CACHE_NONE, 'exceptions' => true];
if ($ka === 'off') $opts['keep_alive'] = false;
$c = new SoapClient("http://127.0.0.1:$port/calculator?wsdl", $opts);
foreach ([1, 2, 3] as $n) {
    try { $r = $c->Add(['a' => $n, 'b' => 10]); echo "call $n: ", json_encode($r), "\n"; }
    catch (Throwable $e) { echo "call $n: ERROR ", $e->getMessage(), "\n"; }
}
PHP
[ -n "$RAW" ] && for k in get soap; do echo "-- raw $k"; python3 $(dirname $0)/raw-keepalive.py $PORT /calculator $k 2>&1 | grep -E "^req|Error"; done; echo "-- raw get /hello"; python3 $(dirname $0)/raw-keepalive.py $PORT /hello get 2>&1 | grep -E "^req|Error"
for ka in default off; do echo "-- keep_alive $ka"; PHP_INI_SCAN_DIR=$SOAP_INI php $A/client.php $PORT $ka; done
kill $SP; wait $SP 2>/dev/null; pkill -f "tina4php serve 127.0.0.1:$PORT" 2>/dev/null; for i in $(seq 25); do ss -ltn | grep -q ":$PORT " || break; sleep 0.2; done; [ -n "$KEEP" ] && grep -v 'Accepted\|Closing' $A/server.log | tail -8; rm -rf $A

#!/usr/bin/env bash
# f-rt-24: php Router::any(...)->noAuth() — which methods does noAuth() actually open?
# usage: any-noauth.sh [tina4-php tree with vendor/]   port 7690
P=${1:-$HOME/.cache/tina4-worktrees/dapi01-php-b321c1fc}; PORT=7690
ss -ltn | grep -q ":$PORT " && { echo "port $PORT busy"; exit 2; }
A=$(mktemp -d); mkdir -p $A/src/routes
cat > $A/src/routes/r.php <<'PHP'
<?php
use Tina4\Router;
Router::any('/any-open', function ($request, $response) { return $response->json(['ok' => true]); })->noAuth();
Router::post('/post-open', function ($request, $response) { return $response->json(['ok' => true]); })->noAuth();
PHP
cat > $A/index.php <<PHP
<?php
require '$P/vendor/autoload.php';
\$app = new \Tina4\App(basePath: __DIR__);
\$app->handle();
PHP
cd $A; HOME=$(mktemp -d) TINA4_DEBUG=true php -S 127.0.0.1:$PORT -t $A $A/index.php > $A/server.log 2>&1 & SP=$!
for i in $(seq 50); do curl -s -o /dev/null 127.0.0.1:$PORT/any-open && break; sleep 0.2; done
curl -s -X POST 127.0.0.1:$PORT/post-open | head -c 600; echo
for m in GET POST PUT PATCH DELETE; do echo "any()->noAuth() $m: $(curl -s -o /dev/null -w '%{http_code}' -X $m 127.0.0.1:$PORT/any-open)"; done
echo "control post()->noAuth() POST: $(curl -s -o /dev/null -w '%{http_code}' -X POST 127.0.0.1:$PORT/post-open)"
kill $SP; wait $SP 2>/dev/null; [ -n "$KEEP" ] && { tail -15 $A/server.log; curl -s 127.0.0.1:$PORT/x >/dev/null; }; rm -rf $A

#!/usr/bin/env bash
# Runs every response.file() example in ruby and nodejs chapter 3 through a real server and checks the
# page's prose. Usage: DOCS=<tina4-documentation tree> BOOK=<tina4-book tree> ./prove.sh   (either may be omitted)
# Frameworks: RB=<tina4-ruby tree> ND=<tina4-nodejs tree with packages/core/dist built> (defaults: stock copies).
# Ports 7781 (ruby) and 7782 (nodejs); refused if busy, freed after. HOME is a temp dir for every server.
# Exit 0 all PASS, 1 any FAIL, 2 ERROR (missing tool/tree, server did not start, nothing extracted).
set -u; HERE=$(cd "$(dirname "$0")" && pwd)
D=/var/home/work/.cache/tina4-worktrees/grind-1102/drt08
RB=${RB:-$D/stock-tina4-ruby} ND=${ND:-$D/stock-tina4-nodejs}
RUN=$(mktemp -d); trap 'rm -rf "$RUN"' EXIT
err(){ echo "ERROR $*"; exit 2; }
command -v ruby >/dev/null || err "ruby missing"; command -v node >/dev/null || err "node missing"
[ -f "$RB/lib/tina4.rb" ] || err "no ruby tree at $RB"; [ -f "$ND/packages/core/dist/index.js" ] || err "no built nodejs tree at $ND"
[ -n "${KEEPLOG:-}" ] && trap "cp $RUN/log.* $KEEPLOG/ 2>/dev/null; rm -rf $RUN" EXIT
[ -n "${DOCS:-}${BOOK:-}" ] || err "set DOCS= and/or BOOK="
echo "frameworks: rb $(cd $RB && ruby -I lib -e 'require "tina4/version"; print Tina4::VERSION' 2>/dev/null) ($RB) nd $(node -p "require('$ND/packages/core/package.json').version") ($ND)"

port_busy(){ ss -ltn 2>/dev/null | grep -q "[:.]$1 " || curl -s -o /dev/null --max-time 1 "http://127.0.0.1:$1/"; }
killtree(){ local c; for c in $(pgrep -P $1); do killtree $c; done; kill $1 2>/dev/null; }
start(){ local dir=$1 p=$2; shift 2; port_busy $p && err "port $p busy before start"
  ( cd "$dir" && exec env HOME=$RUN/home PORT=$p TINA4_PORT=$p TINA4_DEBUG=false TINA4_SECRET=0123456789abcdef0123456789abcdef0123456789abcdef REPORT=$REPORT ND_TREE=$ND "$@" ) >$RUN/log.$p 2>&1 & PID=$!
  for i in $(seq 120); do curl -s -o /dev/null --max-time 1 http://127.0.0.1:$p/ping && return 0; kill -0 $PID 2>/dev/null || break; sleep 0.25; done
  tail -5 $RUN/log.$p; stop $p; err "server in $dir did not start on $p"; }
stop(){ killtree $PID; wait $PID 2>/dev/null; for i in $(seq 60); do port_busy $1 || return 0; sleep 0.25; done; err "port $1 still busy after stop"; }

mkdir -p $RUN/home; REPORT=$RUN/report.pdf; printf '%%PDF-1.4 probe\n' > $REPORT
TOTAL_FAIL=0
check_page(){ # check_page <label> <page> <ruby|nodejs>
  local label=$1 page=$2 port=$3 lang; [ -f "$page" ] || err "missing page $page"
  local A=$RUN/app-$label; rm -rf $A; mkdir -p $A/data/reports $A/src/routes $A/src/public/uploads; cp $REPORT $A/data/reports/q1.pdf; cp $REPORT $A/src/public/uploads/q1.pdf
  [ $port = ruby ] && lang=ruby || lang=typescript
  python3 -I $HERE/extract.py "$page" $lang $A > $A/manifest || err "extract failed on $page"
  local n=$(wc -l < $A/manifest); [ "$n" -ge 4 ] || err "$label: only $n file() examples extracted from $page"
  if [ $port = ruby ]; then
    { echo 'require "tina4"'; echo 'REPORT = ENV.fetch("REPORT")'; echo 'Tina4::Router.get("/ping") { |request, response| response.json({ pong: true }) }'
      while read i kind args path; do
        if [ $kind = route ]; then cp $A/b$i.txt $A/src/routes/b$i.rb   # auto-discovered, as the chapter intends
        else echo "Tina4::Router.get(\"/b$i\") do |request, response|"; echo '  filepath = REPORT'; sed 's#"/path/to/report.pdf"#REPORT#' $A/b$i.txt; echo end; fi
      done < $A/manifest
      echo 'Tina4.run!(port: ENV.fetch("PORT").to_i, no_browser: true)'; } > $A/app.rb
    start $A 7781 ruby -I $RB/lib app.rb; P=7781
  else
    { echo 'const { Router, startServer } = await import(process.env.ND_TREE + "/packages/core/dist/index.js");'
      echo 'import { existsSync } from "fs"; import { join } from "path";'; echo 'const REPORT = process.env.REPORT;'
      echo 'Router.get("/ping", async (req, res) => res.json({ pong: true }));'
      while read i kind args path; do
        if [ $kind = route ]; then echo '{'; grep -v '^import ' $A/b$i.txt; echo '}'
        else echo "Router.get(\"/b$i\", async (req, res) => {"; echo '  const filepath = REPORT;'; sed 's#"/path/to/report.pdf"#REPORT#' $A/b$i.txt; echo '});'; fi
      done < $A/manifest
      echo 'await startServer({ port: Number(process.env.PORT), basePath: process.cwd(), noBrowser: true });'; } > $A/app.mjs
    start $A 7782 node --no-warnings app.mjs; P=7782
  fi
  local pass=0 fail=0
  while read i kind args path; do
    local url=http://127.0.0.1:$P/b$i; [ $kind = route ] && url=http://127.0.0.1:$P${path/\{filename\}/q1.pdf}
    local h=$(curl -s -D - -o $A/got --max-time 10 "$url" | tr -d '\r')
    local st=$(echo "$h" | head -1 | cut -d' ' -f2) cd=$(echo "$h" | grep -i '^content-disposition:' | cut -d' ' -f2-)
    local ok=1 why=""
    [ "$st" = 200 ] || { ok=0; why="status $st"; }
    [ $ok = 1 ] && ! cmp -s $A/got $REPORT && { ok=0; why="body is not the file"; }
    [ $ok = 1 ] && [ "$args" = 2 ] && [[ "$cd" != attachment* ]] && { ok=0; why="2-arg call (download/filename) but no attachment header"; }
    local line=$(grep -m1 -o '[a-z]*\.file([^;]*' $A/b$i.txt)
    if [ $ok = 1 ] && [ $kind = route ]; then  # the example's own not-found branch must answer 404, not crash
      local m=$(curl -s -o /dev/null -w '%{http_code}' --max-time 10 "${url%q1.pdf}missing.pdf"); [ "$m" = 404 ] || { ok=0; why="missing file -> $m, not the example's 404"; st=$m; }; fi
    if [ $ok = 1 ]; then pass=$((pass+1)); echo "  PASS b$i $line -> $st ${cd:-(no Content-Disposition)}"
    else fail=$((fail+1)); echo "  FAIL b$i $line -> $why${cd:+ [$cd]} $([ "$st" = 500 ] && grep -o 'wrong number of arguments[^)]*)\|LocalJumpError[^\n]*' $RUN/log.$P | tail -1; [ "$st" = 403 ] && head -c 40 $A/got)"; fi
  done < $A/manifest
  stop $P
  # Prose: the false claims the stock page makes about file(). Plain file() sets no Content-Disposition on either
  # port, and neither port can set a custom download name.
  local c; for c in 'adds `Content-Disposition`' 'adds a `Content-Disposition`' 'The browser downloads the file' 'your chosen filename' 'ustom filename' 'specific download filename'; do
    if grep -qF "$c" "$page"; then fail=$((fail+1)); echo "  FAIL prose: page still says '$c'"; else pass=$((pass+1)); fi
  done
  echo "$label: $pass/$((pass+fail))"; TOTAL_FAIL=$((TOTAL_FAIL+fail))
}
if [ -n "${DOCS:-}" ]; then echo "docs $(git -C $DOCS rev-parse --short HEAD) $DOCS"
  check_page docs-ruby $DOCS/docs/ruby/03-request-response.md ruby; check_page docs-nodejs $DOCS/docs/nodejs/03-request-response.md nodejs; fi
if [ -n "${BOOK:-}" ]; then echo "book $(git -C $BOOK rev-parse --short HEAD) $BOOK"
  check_page book-ruby $BOOK/book-3-ruby/chapters/03-request-response.md ruby; check_page book-nodejs $BOOK/book-4-nodejs/chapters/03-request-response.md nodejs; fi
[ $TOTAL_FAIL = 0 ] && { echo "ALL PASS"; exit 0; } || { echo "FAILS: $TOTAL_FAIL"; exit 1; }

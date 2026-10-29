#!/usr/bin/env bash
# d-rt-06: `return` directly inside a Tina4::Router route block raises LocalJumpError -> 500.
# Usage: DOCS=<tina4-documentation tree> BOOK=<tina4-book tree> [SERVE=0] ./prove.sh
# Static: Prism-parse every ```ruby fence in docs/ruby and book-3-ruby/chapters; any `return`
# whose innermost scope is a route block is wrong. 03-request-response.md is excluded (owned by
# d-rt-03) and only reported. Served: four real blocks taken verbatim from each tree are run on
# tina4-ruby (FW, default the 2026-10-29 tip copy) and requested; plus a def-return control.
# STRICT=1 also counts ch03 (sections 6, 8, 10 - not covered by d-rt-03's merged fix) and serves
# its cookies block; the held fix then FAILS, by design.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
: "${DOCS:?DOCS=<docs tree>}" "${BOOK:?BOOK=<book tree>}"
FW=${FW:-$HOME/.cache/tina4-worktrees/verify-1029/fw-ruby}
WORK=${WORK:-$HOME/.cache/tina4-worktrees/verify-1029/drt06/run}
SERVE=${SERVE:-1}
export GEM_PATH=${GEM_PATH:-$(gem env gempath)}
export HOME=$WORK/home TINA4_NO_BROWSER=true TINA4_DEBUG=false TINA4_SECRET=$(ruby -rsecurerandom -e "print SecureRandom.hex(32)")
mkdir -p "$HOME"
ok=0; bad=0

static() { # $1 label, $2 dir
  local out; out=$(cd "$2" && ruby "$HERE/classify.rb" *.md 2>/dev/null | grep '^route-block')
  local own
  if [ "${STRICT:-0}" = 1 ]; then own=$(grep -c . <<<"$out"); else own=$(grep -v '03-request-response.md' <<<"$out" | grep -c . ); fi
  local d03; d03=$(grep -c '03-request-response.md' <<<"$out")
  if [ "$own" -eq 0 ]; then echo "PASS static $1: 0 route-block returns (ch03 sections 6/8/10, excluded unless STRICT=1: $d03)"; ok=$((ok+1))
  else echo "FAIL static $1: $own route-block returns (ch03 sections 6/8/10, excluded unless STRICT=1: $d03)"; { [ "${STRICT:-0}" = 1 ] && cat <<<"$out" || grep -v 03-request <<<"$out"; } | cut -f2 | sed 's/^/    /'; bad=$((bad+1)); fi
}
static docs "$DOCS/docs/ruby"
static book "$BOOK/book-3-ruby/chapters"

free_port() { local p; for p in $(seq 7300 7399); do ss -ltn | awk '{print $4}' | grep -q ":$p\$" || { echo $p; return; }; done; }

serve() { # label, file, anchor, setup-ruby, method, path, data, expect, repeat
  local label=$1 file=$2 anchor=$3 setup=$4 meth=$5 path=$6 data=$7 expect=$8 rep=${9:-1}
  local app; app=$(mktemp -d "$WORK/app.XXXX"); mkdir -p "$app/src/routes" "$app/src/templates"
  if [ -n "$file" ]; then ruby "$HERE/extract.rb" "$file" "$anchor" > "$app/src/routes/sample.rb" || { bad=$((bad+1)); return; }
  else printf '%s\n' "$anchor" > "$app/src/routes/sample.rb"; fi
  local port; port=$(free_port)
  cat > "$app/app.rb" <<RB
\$LOAD_PATH.unshift("$FW/lib"); require "tina4"
$setup
File.write(File.join(__dir__, "token"), Tina4::Auth.get_token({ "sub" => "prove" }))
Tina4.run!(__dir__, port: $port, host: "127.0.0.1", no_browser: true)
RB
  (cd "$app" && exec ruby app.rb > "$app/server.log" 2>&1) & local pid=$!
  local i; for i in $(seq 1 100); do curl -s -o /dev/null "http://127.0.0.1:$port/" && break; sleep 0.1; done
  local code body r
  for r in $(seq 1 "$rep"); do
    if [ "$meth" = GET ]; then code=$(curl -s -o "$app/body" -w '%{http_code}' "http://127.0.0.1:$port$path")
    else code=$(curl -s -o "$app/body" -w '%{http_code}' -X "$meth" -H "Authorization: Bearer $(cat "$app/token")" -H 'Content-Type: application/json' -d "$data" "http://127.0.0.1:$port$path"); fi
  done
  kill "$pid" 2>/dev/null; pkill -P "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
  for i in $(seq 1 50); do ss -ltn | awk '{print $4}' | grep -q ":$port\$" || break; sleep 0.1; done
  local why; why=$(grep -ohsE 'LocalJumpError|unexpected return' "$app/server.log" "$app/body" | sort -u | paste -sd, -)
  if [ "$code" = "$expect" ]; then echo "PASS serve $label: $meth $path -> $code"; ok=$((ok+1))
  else echo "FAIL serve $label: $meth $path -> $code (want $expect) ${why:+[$why]}"; bad=$((bad+1)); fi
  [ "$code" = 000 ] && tail -5 "$app/server.log" | sed 's/^/    log: /'
  [ -n "${KEEP:-}" ] && echo "    kept: $app" || rm -rf "$app"
}

if [ "$SERVE" = 1 ]; then
  DBSETUP='db = Tina4::Database.new("sqlite:///products.db"); db.execute("CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY, name TEXT, category TEXT, price REAL, in_stock INTEGER)"); db.execute("INSERT OR REPLACE INTO products VALUES (?, ?, ?, ?, ?)", [1, "Pen", "Office", 1.5, 1]); Tina4.bind_database(db)'
  for t in docs book; do
    if [ $t = docs ]; then D=$DOCS/docs/ruby; else D=$BOOK/book-3-ruby/chapters; fi
    serve "$t ch02 POST products" "$D/02-routing.md" '$next_id = 6' '' POST /api/products '{}' 400
    serve "$t ch08 form token" "$D/08-authentication.md" 'Tina4::Router.post("/profile/update")' '' POST /profile/update '{}' 403
    serve "$t ch10 dashboard" "$D/10-middleware-security.md" 'Tina4::Router.get "/dashboard"' '' GET /dashboard '' 302
    [ "${STRICT:-0}" = 1 ] && serve "$t ch03 cookies (strict)" "$D/03-request-response.md" 'error: "Not logged in"' '' GET /profile '' 401
    serve "$t ch11 cache hit" "$D/11-caching.md" '# Cache hit -- return immediately' "$DBSETUP" GET /api/products/1 '' 200 2
  done
  serve "control def-return" "" 'def pick(early)
  return "early" if early
  "late"
end
Tina4::Router.get("/control") do |request, response|
  response.json({ v: pick(true) })
end' '' GET /control '' 200
fi

if [ "$bad" -eq 0 ]; then echo "VERDICT PASS ok=$ok bad=$bad"; exit 0; else echo "VERDICT FAIL ok=$ok bad=$bad"; exit 1; fi

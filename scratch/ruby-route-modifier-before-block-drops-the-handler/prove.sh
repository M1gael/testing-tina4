#!/usr/bin/env bash
# d-rt-07: a route block handed to a Route modifier (`Router.post(p).no_auth do ... end`) is dropped:
# the modifier takes no block, so the route is registered with no handler.
# Usage: DOCS=<tina4-documentation tree> BOOK=<tina4-book tree> FW=<tina4-ruby tree> [SERVE=0] ./prove.sh
# Static: Prism-parse every ```ruby fence in docs/ruby and book-3-ruby/chapters (classify.rb); any
# Route modifier given a block fails. Served: three ch10 blocks, verbatim from each tree, run on FW
# and requested (CSRF off, to isolate the handler from #265's CSRF change); plus a control route.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
: "${DOCS:?}" "${BOOK:?}" "${FW:?}"
WORK=${WORK:-$(mktemp -d)}; SERVE=${SERVE:-1}
export GEM_PATH=${GEM_PATH:-$(gem env gempath)}
export HOME=$WORK/home TINA4_NO_BROWSER=true TINA4_DEBUG=false TINA4_CSRF=false TINA4_SECRET=$(ruby -rsecurerandom -e "print SecureRandom.hex(32)")
mkdir -p "$HOME"; ok=0; bad=0; PIDS=()
trap 'for p in "${PIDS[@]}"; do kill $p 2>/dev/null; done' EXIT

static() {
  local out n; out=$(cd "$2" && ruby "$HERE/classify.rb" *.md | grep 'block on')
  n=$(grep -c . <<<"$out")
  if [ "$n" -eq 0 ]; then echo "PASS static $1: 0 route blocks handed to a modifier"; ok=$((ok+1))
  else echo "FAIL static $1: $n route blocks handed to a modifier"; cut -f1,3 <<<"$out" | sed 's/^/    /'; bad=$((bad+1)); fi
}
static docs "$DOCS/docs/ruby"; static book "$BOOK/book-3-ruby/chapters"

free_port() { local p; for p in $(seq 7400 7499); do ss -ltn | awk '{print $4}' | grep -q ":$p\$" || { echo $p; return; }; done; }

serve() { # label, file, anchor, method, path, expect-status, expect-body-substring, [notoken]
  local app port code body i auth; app=$(mktemp -d "$WORK/app.XXXX"); mkdir -p "$app/src/routes"
  if [ -n "$2" ]; then ruby "$HERE/extract.rb" "$2" "$3" > "$app/src/routes/sample.rb" || { bad=$((bad+1)); return; }
  else printf '%s\n' "$3" > "$app/src/routes/sample.rb"; fi
  port=$(free_port)
  cat > "$app/app.rb" <<RB
\$LOAD_PATH.unshift("$FW/lib"); require "tina4"
File.write(File.join(__dir__, "token"), Tina4::Auth.get_token({ "sub" => "prove" }))
Tina4.run!(__dir__, port: $port, host: "127.0.0.1", no_browser: true)
RB
  (cd "$app" && exec ruby app.rb >"$app/server.log" 2>&1) & PIDS+=($!)
  for i in $(seq 1 100); do curl -s -o /dev/null "http://127.0.0.1:$port/health" && break; sleep 0.1; done
  auth="Authorization: Bearer $(cat "$app/token" 2>/dev/null)"; [ "${8:-}" = notoken ] && auth="X-No-Token: 1"
  body=$(curl -s -o - -w '\n%{http_code}' -X "$4" -H "$auth" -H 'Content-Type: application/json' -d '{}' "http://127.0.0.1:$port$5")
  code=$(tail -1 <<<"$body"); body=$(head -n -1 <<<"$body" | tr -d '\n' | cut -c1-80)
  kill "${PIDS[-1]}" 2>/dev/null; wait "${PIDS[-1]}" 2>/dev/null
  if [ "$code" = "$6" ] && [[ "$body" == *"$7"* ]]; then echo "PASS served $1${8:+ ($8)}: $4 $5 -> $code $body"; ok=$((ok+1))
  else echo "FAIL served $1${8:+ ($8)}: $4 $5 -> $code $body (want $6 with '$7')"; bad=$((bad+1)); fi
}

if [ "$SERVE" = 1 ]; then
  for t in docs book; do
    if [ $t = docs ]; then C=$DOCS/docs/ruby/10-middleware-security.md; else C=$BOOK/book-3-ruby/chapters/10-middleware-security.md; fi
    serve "$t ch10 webhook (.no_auth)" "$C" 'Router.post("/api/webhooks/stripe")' POST /api/webhooks/stripe 200 '"received":true'
    serve "$t ch10 admin users (.secure)" "$C" 'Router.get("/api/admin/users")' GET /api/admin/users 200 '"users":[]'
    serve "$t ch10 webhook (.no_auth)" "$C" 'Router.post("/api/webhooks/stripe")' POST /api/webhooks/stripe 200 '"received":true' notoken
    serve "$t ch10 admin users (.secure)" "$C" 'Router.get("/api/admin/users")' GET /api/admin/users 401 '' notoken
    serve "$t ch10 login rate limit (.no_auth.middleware)" "$C" 'class LoginRateLimit' POST /api/login 204 '' notoken
  done
  serve "control block on post" "" 'Tina4::Router.post("/control") do |request, response|
  response.call({ ok: true })
end.no_auth' POST /control 200 '"ok":true'
  # the chained middleware runs: same shape as the ch10 rate-limit sample, with a hook that answers 429
  serve "control end.no_auth.middleware runs the hook" "" 'class Hit
  def self.before_hit(request, response)
    response.status(429)
    [request, response]
  end
end
Tina4::Router.post("/hit") do |request, response|
  response.call({ handler: true })
end.no_auth.middleware(Hit)' POST /hit 429 '' notoken
fi
if [ "$bad" -eq 0 ]; then echo "VERDICT PASS ok=$ok bad=$bad"; exit 0; else echo "VERDICT FAIL ok=$ok bad=$bad"; exit 1; fi

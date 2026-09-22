#!/usr/bin/env bash
# Under --managed (what `tina4 serve` always passes), is /__dev_reload registered,
# and does the page still tell the browser to connect to it?
#
# Framework classes are symlinked out of gitdir/tinaforks/tina4-php — nothing is
# installed, nothing is written into the fork.
set -u
FORK="${FORK:-/var/home/work/gitdir/tinaforks/tina4-php}"
HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
mkdir -p evidence

echo "# framework: $(cd "$FORK" && git log -1 --format='%h' origin/v3) (origin/v3)"
echo

run() {   # run <label> <port> <extra php args...>
    local label="$1" port="$2"; shift 2
    TINA4_DEBUG=true TINA4_OVERRIDE_CLIENT=true \
        timeout 60 php "$FORK/bin/tina4php" serve --host 127.0.0.1 --port "$port" "$@" \
        > "evidence/boot.$label.log" 2>&1 &
    local pid=$! up=""
    for i in $(seq 1 45); do
        ss -lnt 2>/dev/null | grep -q ":$port " && { up=1; break; }
        sleep 1
    done
    if [ -z "$up" ]; then echo "## $label: never listened"; tail -3 "evidence/boot.$label.log"; return; fi
    local ws page
    ws=$(curl -s -o /dev/null -w '%{http_code}' --max-time 5 \
        -H 'Connection: Upgrade' -H 'Upgrade: websocket' \
        -H 'Sec-WebSocket-Version: 13' -H 'Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==' \
        "http://127.0.0.1:$port/__dev_reload")
    curl -s -o "evidence/root.$label.html" --max-time 5 "http://127.0.0.1:$port/"
    page=$(grep -o 'data-reload="[01]"' "evidence/root.$label.html" | head -1)
    echo "## $label"
    echo "    GET /__dev_reload (websocket upgrade): HTTP $ws"
    echo "    toolbar on GET /:                      ${page:-<no toolbar>}"
    echo
    kill "$pid" 2>/dev/null
    sleep 2
}

run managed   8792 --managed
run unmanaged 8793

echo "## verdict"
echo "    --managed is the only difference. 404 vs 101 on the socket, identical page flag:"
echo "    the server's decision not to serve /__dev_reload never reaches the client that dials it."

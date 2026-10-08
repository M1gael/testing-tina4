#!/usr/bin/env bash
# tina4-python: what a client sees when the app boots with a TINA4_SECRET under 32 bytes.
# Usage: TREE=<tina4-python checkout with .venv> ./prove.sh
set -u
TREE=${TREE:?set TREE to a tina4-python checkout with a .venv}
PY=${PY:-$TREE/.venv/bin/python}
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d); export HOME=$work/home; mkdir -p "$HOME"; pid=
trap '[ -n "$pid" ] && kill $pid 2>/dev/null; rm -rf "$work"' EXIT
cp "$here/app.py" "$work/"
echo "tree: $(git -C "$TREE" rev-parse --short HEAD), $(grep -m1 '^version' "$TREE/pyproject.toml"), $($PY -V)"
port=$($PY -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')

cell() { local label=$1; shift
  (cd "$work" && exec env "$@" TINA4_PORT=$port TINA4_NO_AI_PORT=true "$PY" app.py --managed) >"$work/srv.log" 2>&1 & pid=$!
  for _ in $(seq 50); do curl -s -o /dev/null "http://127.0.0.1:$port/hello" && break; kill -0 $pid 2>/dev/null || break; sleep 0.2; done
  local resp rc alive
  resp=$(curl -s -i --max-time 5 "http://127.0.0.1:$port/hello" 2>&1); rc=$?
  if kill -0 $pid 2>/dev/null; then alive=yes; kill $pid; wait $pid 2>/dev/null; else wait $pid; alive="no, exit $?"; fi; pid=
  echo "== $label"
  echo "   server running: $alive"
  if [ $rc -eq 0 ]; then echo "   client: $(printf '%s' "$resp" | head -1 | tr -d '\r')"; else echo "   client: no answer (curl exit $rc)"; fi
  echo "   trace or source path in the HTTP body: $(printf '%s' "$resp" | grep -c -E 'Traceback|tina4_python/|\.py"')"
  echo "   server output:"; grep -v '^\s*$' "$work/srv.log" | head -6 | sed 's/^/     | /'
}
cell "20-byte secret" TINA4_SECRET=short-secret-20bytes
cell "20-byte secret, TINA4_DEBUG=true" TINA4_SECRET=short-secret-20bytes TINA4_DEBUG=true
cell "64-byte secret (control)" TINA4_SECRET="$(head -c32 /dev/urandom | od -An -tx1 | tr -d ' \n')"

# The other entry point: asgi() builds the app for uvicorn/hypercorn/granian. A
# refusal there means the ASGI server cannot import the app, so it serves nothing.
echo "== asgi() with a 20-byte secret (no ASGI server needed to see the refusal)"
(cd "$work" && env TINA4_SECRET=short-secret-20bytes "$PY" -c 'from tina4_python.core.server import asgi; asgi(); print("   app built")' 2>&1; echo "   exit $?") | grep -v '^\s*$' | sed 's/^  Auth/   | Auth/'

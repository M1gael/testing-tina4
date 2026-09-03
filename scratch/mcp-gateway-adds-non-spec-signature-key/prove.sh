#!/usr/bin/env bash
# Proves: https://mcp.tina4.com/mcp puts a non-spec "signature" key at the TOP LEVEL of its
# JSON-RPC envelopes, which every spec-strict MCP client rejects.
#
# Read-only. Uses the public demo bearer documented in tina4-simple-agent/README.md.
# Exits 1 while the defect is present.
set -u
ENDPOINT="${ENDPOINT:-https://mcp.tina4.com/mcp}"
TOKEN="${TINA4_MCP_TOKEN:-FREE-TOKEN}"
tmp="$(mktemp -d)"; trap 'rm -rf "$tmp"' EXIT
fail=0

post() { # name, body
  curl -sS --max-time 30 -X POST "$ENDPOINT" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/event-stream" \
    -d "$2" -o "$tmp/$1.json" -w "%{http_code}"
}

check() { # name, label, body
  code="$(post "$1" "$3")"
  keys="$(python3 -c "
import json,sys
try: d=json.load(open('$tmp/$1.json'))
except Exception: print('<not json>'); sys.exit(0)
print(' '.join(d.keys()) if isinstance(d,dict) else '<not an object>')
")"
  case " $keys " in
    *" signature "*) printf '  http=%s  %-22s top-level keys: %-34s <- NON-SPEC\n' "$code" "$2" "$keys"; fail=1 ;;
    *)               printf '  http=%s  %-22s top-level keys: %-34s ok\n'          "$code" "$2" "$keys" ;;
  esac
}

echo "endpoint: $ENDPOINT"
echo
check init      "initialize"     '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"x","version":"1"}}}'
check tools     "tools/list"     '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
check nomethod  "error -32601"   '{"jsonrpc":"2.0","id":3,"method":"no/such/method","params":{}}'
check notool    "error -32603"   '{"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"nope","arguments":{}}}'
check badjson   "error -32700"   '{"jsonrpc":"2.0","id":5'

# The pre-auth gate is a different code path and is already clean — included so a future run
# notices if that changes.
code="$(curl -sS --max-time 30 -X POST "$ENDPOINT" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{}}' \
  -o "$tmp/unauth.json" -w '%{http_code}')"
keys="$(python3 -c "import json;print(' '.join(json.load(open('$tmp/unauth.json')).keys()))" 2>/dev/null || echo '<not json>')"
printf '  http=%s  %-22s top-level keys: %-34s %s\n' "$code" "no Authorization" "$keys" \
  "$(case " $keys " in *" signature "*) echo '<- NON-SPEC';; *) echo 'ok';; esac)"

echo
if [ "$fail" -eq 0 ]; then
  echo "PASS - every envelope is jsonrpc/id/result|error only"
else
  echo "FAIL - a top-level \"signature\" key is present; spec-strict MCP clients drop these messages"
fi
exit "$fail"

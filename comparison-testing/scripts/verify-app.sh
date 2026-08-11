#!/usr/bin/env bash
# verify-app.sh — prove an app meets spec/bookmarks-app.md before its lines are counted.
#
# Usage:  scripts/verify-app.sh <port> [openapi-path]
#
# Exits 0 only when all six acceptance checks pass. Any failure is loud and fatal:
# an app that does not serve the spec must never reach the counter.
#
# The OpenAPI path differs per framework (Tina4 /swagger/openapi.json, FastAPI
# /openapi.json, DRF /api/schema/), so it is a parameter. Everything else is
# framework-agnostic on purpose — the probe tests behaviour, not implementation.

set -uo pipefail

PORT="${1:-}"
OPENAPI_PATH="${2:-/openapi.json}"
BASE="http://127.0.0.1:${PORT}"

if [[ -z "$PORT" ]]; then
    echo "usage: $0 <port> [openapi-path]" >&2
    exit 2
fi

PASS=0
FAIL=0

ok()   { printf '  \033[32mPASS\033[0m  %s\n' "$1"; PASS=$((PASS + 1)); }
bad()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; printf '        %s\n' "$2"; FAIL=$((FAIL + 1)); }

# curl helper: prints "<http_code>\n<body>"
req() { curl -s -w '\n%{http_code}' "$@" 2>/dev/null; }
code_of() { tail -n1 <<<"$1"; }
body_of() { sed '$d' <<<"$1"; }

echo "Verifying ${BASE} against spec/bookmarks-app.md"

# ── wait for the app to answer at all ────────────────────────────────────────
for _ in $(seq 1 30); do
    curl -s -o /dev/null --max-time 2 "${BASE}/api/bookmarks" && break
    sleep 1
done

# ── 1. GET /api/bookmarks is public and returns a JSON array ─────────────────
r=$(req "${BASE}/api/bookmarks")
c=$(code_of "$r"); b=$(body_of "$r")
if [[ "$c" == "200" ]] && python3 -c "import json,sys; d=json.load(sys.stdin); sys.exit(0 if isinstance(d,list) else 1)" <<<"$b" 2>/dev/null; then
    BEFORE=$(python3 -c "import json,sys; print(len(json.load(sys.stdin)))" <<<"$b")
    ok "R2  GET /api/bookmarks -> 200, JSON array (${BEFORE} row(s))"
else
    bad "R2  GET /api/bookmarks" "got ${c}, body: ${b:0:120}"
    BEFORE=-1
fi

# ── 2. POST without a token is rejected ──────────────────────────────────────
r=$(req -X POST "${BASE}/api/bookmarks" -H 'Content-Type: application/json' \
        -d '{"title":"NoToken","url":"https://example.com"}')
c=$(code_of "$r")
if [[ "$c" == "401" ]]; then
    ok "R3  POST without token -> 401"
else
    bad "R3  POST without token should be 401" "got ${c} — the write is unprotected"
fi

# ── 3. Login issues a token ──────────────────────────────────────────────────
r=$(req -X POST "${BASE}/api/login" -H 'Content-Type: application/json' \
        -d '{"username":"demo","password":"demo"}')
c=$(code_of "$r"); b=$(body_of "$r")
TOKEN=$(python3 -c "import json,sys; print(json.load(sys.stdin).get('token',''))" <<<"$b" 2>/dev/null)
if [[ "$c" == "200" && -n "$TOKEN" ]]; then
    ok "R4  POST /api/login -> 200, token (${#TOKEN} chars)"
else
    bad "R4  POST /api/login" "got ${c}, body: ${b:0:120}"
    TOKEN=""
fi

# ── 4. Authenticated POST with a missing url is a validation error ────────────
if [[ -n "$TOKEN" ]]; then
    r=$(req -X POST "${BASE}/api/bookmarks" -H 'Content-Type: application/json' \
            -H "Authorization: Bearer ${TOKEN}" -d '{"title":"NoUrl"}')
    c=$(code_of "$r")
    if [[ "$c" == "400" ]]; then
        ok "R3  POST with token, no url -> 400"
    else
        bad "R3  POST with token, no url should be 400" "got ${c}"
    fi
else
    bad "R3  POST validation" "skipped — no token from R4"
fi

# ── 5. Authenticated POST creates a row, and it persists ─────────────────────
if [[ -n "$TOKEN" ]]; then
    r=$(req -X POST "${BASE}/api/bookmarks" -H 'Content-Type: application/json' \
            -H "Authorization: Bearer ${TOKEN}" \
            -d '{"title":"Verified","url":"https://tina4.com/verified"}')
    c=$(code_of "$r")
    if [[ "$c" == "201" ]]; then
        after=$(curl -s "${BASE}/api/bookmarks" | python3 -c "import json,sys; print(len(json.load(sys.stdin)))" 2>/dev/null || echo -1)
        if [[ "$BEFORE" -ge 0 && "$after" -eq $((BEFORE + 1)) ]]; then
            ok "R3  POST with token -> 201, row persisted (${BEFORE} -> ${after})"
        else
            bad "R1  row did not persist to the database" "count went ${BEFORE} -> ${after}"
        fi
    else
        bad "R3  POST with token should be 201" "got ${c}"
    fi
else
    bad "R3  POST create" "skipped — no token from R4"
fi

# ── 6. Generated OpenAPI document mentions the API route ─────────────────────
r=$(req "${BASE}${OPENAPI_PATH}")
c=$(code_of "$r"); b=$(body_of "$r")
if [[ "$c" == "200" ]] && grep -q '/api/bookmarks' <<<"$b"; then
    ok "R6  ${OPENAPI_PATH} -> 200, documents /api/bookmarks"
else
    bad "R6  OpenAPI document at ${OPENAPI_PATH}" "got ${c}$( [[ "$c" == 200 ]] && echo ' but /api/bookmarks is absent' )"
fi

# ── R5 is a human check, but a 404 is still a hard fail ──────────────────────
r=$(req "${BASE}/bookmarks")
c=$(code_of "$r"); b=$(body_of "$r")
if [[ "$c" == "200" ]] && grep -qi '<html\|<h1\|<ul\|<li' <<<"$b"; then
    ok "R5  GET /bookmarks -> 200, HTML (check inheritance by eye)"
else
    bad "R5  GET /bookmarks" "got ${c}, body: ${b:0:120}"
fi

echo
if [[ "$FAIL" -eq 0 ]]; then
    printf '\033[32m%s checks passed — this app may be counted.\033[0m\n' "$PASS"
    exit 0
fi
printf '\033[31m%s passed, %s FAILED — do not count this app.\033[0m\n' "$PASS" "$FAIL"
exit 1

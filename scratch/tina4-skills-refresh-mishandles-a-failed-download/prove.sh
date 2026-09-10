#!/usr/bin/env bash
# Proof for: `tina4 update` / `tina4 skills` mishandle a transient CDN outage.
#
#   ./prove.sh                    stock half only (released tina4 3.8.84)
#   ./prove.sh /path/to/tina4     stock half, then the same tests against a fixed build
#
# Exits 0 when every assertion below holds. Needs network: the control runs and
# the mirror runs both reach the real CDNs.
set -u

here="$(cd "$(dirname "$0")" && pwd)"
stock="$here/bin/tina4-3.8.84"
fixed="${1:-}"
fail=0
pass() { printf '  \033[32mok\033[0m   %s\n' "$1"; }
bad()  { printf '  \033[31mFAIL\033[0m %s\n' "$1"; fail=1; }
skip() { printf '  \033[33mskip\033[0m %s\n' "$1"; partial=$((partial + 1)); }
check() { [ "$2" = "$3" ] && pass "$1 ($2)" || bad "$1: expected $3, got $2"; }

# Several assertions need a CDN to actually be serving. When one is not, the run
# has to say so -- an outage must not read as a broken fix, and it must not read
# as a pass either. Probed at the point of use, because during the first full run
# of this script raw.githubusercontent.com went down and came back mid-suite.
RAW=https://raw.githubusercontent.com/tina4stack/tina4/main/install-skills.sh
CDN=https://cdn.jsdelivr.net/gh/tina4stack/tina4@main/install-skills.sh
partial=0
serving() { curl -fsS --max-time 20 -o /dev/null "$1" 2>/dev/null; }

[ -x "$stock" ] || { echo "missing $stock"; exit 2; }
"$stock" --version | grep -q '3\.8\.84' || { echo "$stock is not 3.8.84"; exit 2; }

# ── harness ───────────────────────────────────────────────────────────────────
start_proxy() {  # $1 = hosts to 503 (comma separated, or "all"); $2 = seconds to stall first
  MODE=proxy BLOCK="$1" DELAY="${2:-0}" python3 "$here/fake503.py" >"$here/.port" 2>"$here/.proxylog" &
  proxy_pid=$!
  for _ in $(seq 40); do [ -s "$here/.port" ] && break; sleep 0.1; done
  proxy_port="$(cat "$here/.port")"
}
stop_proxy() { kill "$proxy_pid" 2>/dev/null; wait "$proxy_pid" 2>/dev/null; rm -f "$here/.port"; }

# seed_skills <sandbox> -- make installed_skills_targets() see an existing install,
# so `tina4 update` reaches the skills refresh the reporter's run reached.
seed_skills() {
  rm -rf "$here/$1"; mkdir -p "$here/$1/.claude/skills/tina4-maintainer"
  echo "# seed" > "$here/$1/.claude/skills/tina4-maintainer/SKILL.md"
}

# update_run <binary> <sandbox> -- `tina4 update` with only the skills CDNs blocked,
# so the version check still works and the run gets as far as the refresh.
update_run() {
  local bin="$1" box="$here/$2"
  out="$(env -i PATH="$PATH" HOME="$box" \
        https_proxy="http://127.0.0.1:$proxy_port" http_proxy="http://127.0.0.1:$proxy_port" \
        "$bin" update 2>&1)"
  rc=$?
}

# run <binary> <sandbox> <target> [extra env assignments...]
# Prints "<exit-code> <files-installed>" and leaves the output in $out.
run() {
  local bin="$1" box="$here/$2" tgt="$3"; shift 3
  rm -rf "$box"; mkdir -p "$box"
  out="$(env -i PATH="$PATH" HOME="$box" \
        ${proxy_port:+https_proxy="http://127.0.0.1:$proxy_port"} \
        ${proxy_port:+http_proxy="http://127.0.0.1:$proxy_port"} \
        "$@" "$bin" skills "$tgt" 2>&1)"
  rc=$?
  files=$(find "$box" -type f 2>/dev/null | wc -l)
}

echo
echo "== the defect, on released tina4 3.8.84 =="

start_proxy all
run "$stock" sandbox-stock-dead claude
stop_proxy; proxy_port=
check "stock, both CDNs 503: files installed"    "$files" "0"
check "stock, both CDNs 503: exit code"          "$rc"    "0"
case "$out" in *"skipped"*|*"failed"*) bad "stock: said something was wrong (it should not have)";;
                                    *) pass "stock, both CDNs 503: reported nothing wrong";; esac

echo
echo "== the path the report came from: \`tina4 update\` =="
seed_skills sandbox-stock-update
start_proxy raw.githubusercontent.com,cdn.jsdelivr.net
update_run "$stock" sandbox-stock-update
stop_proxy; proxy_port=
case "$out" in *"Refreshing Tina4 AI skills"*) pass "stock update: reached the skills refresh";;
                                            *) bad "stock update: never reached the refresh -- test proves nothing";; esac
case "$out" in *"skills refresh failed"*) bad "stock update: reported the failure (it should not have)";;
                                       *) pass "stock update: refresh failed and update said nothing";; esac

echo
echo "== the same command with the network working (control) =="
if serving "$RAW"; then
  run "$stock" sandbox-stock-ok claude
  check "stock, network fine: exit code"           "$rc" "0"
  [ "$files" -gt 40 ] && pass "stock, network fine: files installed ($files)" \
                      || bad  "stock, network fine: only $files files"
  echo "  -> exit code 0 in both runs: it cannot tell 0 files from $files."
else
  skip "stock, network fine: raw.githubusercontent.com is not serving right now"
fi

echo
echo "== what each layer does about a 503 =="
python3 - <<'PY'
import http.server, socketserver, subprocess, threading
hits=[]; BODY=b"503"
class H(http.server.BaseHTTPRequestHandler):
    protocol_version="HTTP/1.1"
    def do_GET(self):
        hits.append(1); self.send_response(503)
        self.send_header("Content-Length",str(len(BODY))); self.end_headers(); self.wfile.write(BODY)
    def log_message(self,*a): pass
    def handle_one_request(self):
        try: super().handle_one_request()
        except Exception: self.close_connection=True
srv=socketserver.ThreadingTCPServer(("127.0.0.1",0),H); srv.daemon_threads=True
threading.Thread(target=srv.serve_forever,daemon=True).start()
url="http://127.0.0.1:%d/install-skills.sh"%srv.server_address[1]
for label,cmd in [("the bootstrap in setup.rs (curl -fsSL)      ",["curl","-fsSL",url]),
                  ("install-skills.sh's own downloads (--retry 3)",["curl","-fsSL","--retry","3","--retry-delay","0",url])]:
    hits.clear(); rc=subprocess.run(cmd,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode
    print("  %s attempts=%d exit=%d"%(label,len(hits),rc))
srv.shutdown()
PY
echo "  -> the installer retries what fetching the installer does not."

echo
echo "== does the pipeline hide it? (single factor: where the failure happens) =="
if serving "$RAW"; then
  sh -c "curl -fsSL $RAW | TINA4_SKILLS_TARGET=bogus sh" >/dev/null 2>&1
  check "fetch ok, script exits 2  -> pipeline status" "$?" "2"
else
  skip "fetch ok, script exits 2: raw.githubusercontent.com is not serving right now"
fi
start_proxy all
env https_proxy="http://127.0.0.1:$proxy_port" sh -c "curl -fsSL https://raw.githubusercontent.com/tina4stack/tina4/main/install-skills.sh | TINA4_SKILLS_TARGET=all sh" >/dev/null 2>&1
check "fetch fails, nothing runs -> pipeline status" "$?" "0"
stop_proxy; proxy_port=

echo
echo "== would the mirror have saved it? (install-skills.sh, primary dead) =="
if serving "$CDN"; then
  start_proxy raw.githubusercontent.com
  rm -rf "$here/sandbox-mirror"; mkdir -p "$here/sandbox-mirror"
  script="$(curl -fsSL "$CDN")"
  env https_proxy="http://127.0.0.1:$proxy_port" http_proxy="http://127.0.0.1:$proxy_port" \
      TINA4_SKILLS_TARGET=claude TINA4_SKILLS_HOME="$here/sandbox-mirror" \
      TINA4_SKILLS_RETRY_COUNT=1 TINA4_SKILLS_RETRY_DELAY=0 sh -c "$script" >/dev/null 2>&1; mrc=$?
  stop_proxy; proxy_port=
  mfiles=$(find "$here/sandbox-mirror" -type f | wc -l)
  check "installer script, raw.githubusercontent 503: exit" "$mrc" "0"
  [ "$mfiles" -gt 40 ] && pass "installer script fell back to jsDelivr ($mfiles files)" \
                       || bad  "installer script installed only $mfiles files"
else
  skip "mirror fallback: cdn.jsdelivr.net is not serving right now"
fi

# ── the fixed build ───────────────────────────────────────────────────────────
if [ -n "$fixed" ]; then
  [ -x "$fixed" ] || { echo "missing $fixed"; exit 2; }
  echo
  echo "== the fixed build =="

  start_proxy all
  run "$fixed" sandbox-fix-dead claude
  stop_proxy; proxy_port=
  check "fixed, both CDNs 503: files installed" "$files" "0"
  [ "$rc" -ne 0 ] && pass "fixed, both CDNs 503: exit code ($rc, non-zero)" \
                  || bad  "fixed, both CDNs 503: exit code 0 -- still silent"
  case "$out" in *"Could not download the skills installer"*)
        pass "fixed, both CDNs 503: named the failure";;
     *) bad "fixed, both CDNs 503: did not say what failed";; esac
  case "$out" in *jsdelivr*) pass "fixed: reported the last source it tried";;
                          *) bad "fixed: never mentions the mirror -- did it try one?";; esac

  if serving "$CDN"; then
    start_proxy raw.githubusercontent.com
    run "$fixed" sandbox-fix-mirror claude
    stop_proxy; proxy_port=
    check "fixed, primary 503 only: exit code" "$rc" "0"
    [ "$files" -gt 40 ] && pass "fixed, primary 503 only: installed from the mirror ($files files)" \
                        || bad  "fixed, primary 503 only: only $files files -- no fallback"
  else
    skip "fixed, primary 503 only: cdn.jsdelivr.net is not serving right now"
  fi

  if serving "$RAW"; then
    run "$fixed" sandbox-fix-ok claude
    check "fixed, network fine: exit code" "$rc" "0"
    [ "$files" -gt 40 ] && pass "fixed, network fine: files installed ($files)" \
                        || bad  "fixed, network fine: only $files files"

    run "$fixed" sandbox-fix-badref claude TINA4_SKILLS_REF=no-such-ref
    [ "$rc" -ne 0 ] && pass "fixed, installer itself fails: exit code ($rc, non-zero)" \
                    || bad  "fixed, installer itself fails: exit 0 -- failures past the download are hidden"
  else
    skip "fixed, network fine + installer-fails: raw.githubusercontent.com is not serving right now"
  fi

  seed_skills sandbox-fix-update
  start_proxy raw.githubusercontent.com,cdn.jsdelivr.net
  update_run "$fixed" sandbox-fix-update
  stop_proxy; proxy_port=
  case "$out" in *"skills refresh failed"*) pass "fixed update: the update run now reports the failed refresh";;
                                         *) bad "fixed update: still says nothing about the failed refresh";; esac

  start_proxy all
  run "$fixed" sandbox-fix-attempts claude
  tries=$(grep -c '^503 <- CONNECT' "$here/.proxylog")
  stop_proxy; proxy_port=
  check "fixed: fetch attempts before giving up (3 per source x 2 sources)" "$tries" "6"

  # A CDN that is slow as well as broken. Six attempts where the shipped code
  # made one must not mean six times the wait, so the walk carries a budget.
  start_proxy all 12
  t0=$(date +%s)
  run "$fixed" sandbox-fix-slow claude
  t1=$(date +%s)
  slowtries=$(grep -c '^503 <- CONNECT' "$here/.proxylog")
  stop_proxy; proxy_port=
  [ "$slowtries" -lt 6 ] && pass "fixed, slow + broken CDN: stopped early ($slowtries attempts, $((t1-t0))s)" \
                         || bad  "fixed, slow + broken CDN: ran all $slowtries attempts in $((t1-t0))s -- no budget"
  case "$out" in *"gave up after"*) pass "fixed, slow + broken CDN: said it gave up on the clock";;
                                 *) bad "fixed, slow + broken CDN: no mention of giving up";; esac

  leaked=$(find "${TMPDIR:-/tmp}" -maxdepth 1 -name 'tina4-skills-*' 2>/dev/null | wc -l)
  check "fixed: staging directories left behind" "$leaked" "0"
fi

rm -rf "$here"/sandbox-* "$here/.proxylog"
echo
if [ "$fail" != 0 ]; then echo "FAIL"; exit 1; fi
if [ "$partial" != 0 ]; then
  echo "PASS (partial: $partial check(s) skipped -- a CDN was not serving during this run)"
  exit 0
fi
echo "PASS"; exit 0

#!/bin/sh
# Proves: `tina4 update` writes its download next to the running binary and
# never elevates, so it cannot update an install in a directory the user does
# not own -- which is where the installer puts it (/usr/local/bin).
#
# Exits 0 when everything is as recorded in readme.md.
set -eu

here="$(cd "$(dirname "$0")" && pwd)"
stock="$here/bin/tina4-3.8.85"
work="$here/work"

[ -x "$stock" ] || { echo "missing $stock -- see readme.md"; exit 1; }
"$stock" --version | grep -q '3\.8\.85' || { echo "stock binary is not 3.8.85"; exit 1; }

cleanup() { chmod u+w "$work/readonly" 2>/dev/null || true; rm -rf "$work"; }
trap cleanup EXIT
cleanup
mkdir -p "$work/readonly" "$work/writable"
cp "$stock" "$work/readonly/tina4"
cp "$stock" "$work/writable/tina4"
chmod 555 "$work/readonly"

fail=0
check() {
  if [ "$2" = "$3" ]; then printf '  ok    %s\n' "$1"
  else printf '  FAIL  %s (want %s, got %s)\n' "$1" "$3" "$2"; fail=1; fi
}

echo "case A: install directory not writable by the user"
set +e
( cd "$work/readonly" && ./tina4 update ) >"$work/a.out" 2>&1
a_exit=$?
set -e
check "exits non-zero"            "$([ $a_exit -ne 0 ] && echo yes || echo no)" yes
check "names the write failure"   "$(grep -qi 'could not write the file' "$work/a.out" && echo yes || echo no)" yes
check "names the destination dir" "$(grep -qF "$work/readonly" "$work/a.out" && echo yes || echo no)" yes
check "no leftover tina4.tmp"     "$([ -e "$work/readonly/tina4.tmp" ] && echo no || echo yes)" yes
check "did NOT update"            "$("$work/readonly/tina4" --version | grep -q '3\.8\.85' && echo yes || echo no)" yes
check "never mentions sudo"       "$(grep -qi 'sudo\|root\|permission' "$work/a.out" && echo no || echo yes)" yes

echo "case B: control -- same binary, writable directory"
set +e
( cd "$work/writable" && ./tina4 update ) >"$work/b.out" 2>&1
b_exit=$?
set -e
check "exits zero"                "$([ $b_exit -eq 0 ] && echo yes || echo no)" yes
check "did update"                "$("$work/writable/tina4" --version | grep -q '3\.8\.85' && echo no || echo yes)" yes


# ---------------------------------------------------------------------------
# The gate. Optional, because it needs two builds this repo does not carry: a
# stock and a fixed binary WITH THE CRATE VERSION LOWERED, so `update` cannot
# short-circuit on "already up to date" and the download path is always reached.
#
#   cd ../../../tinaforks/tina4
#   sed -i '3s/.*/version = "3.8.60"/' Cargo.toml
#   cargo build && cp target/debug/tina4 /tmp/tina4-fixed-3.8.60
#   git show origin/main:src/main.rs > src/main.rs && cargo build
#   cp target/debug/tina4 /tmp/tina4-stock-3.8.60
#   git checkout Cargo.toml src/main.rs      # restore BOTH instruments
#
#   ./prove.sh /tmp/tina4-stock-3.8.60 /tmp/tina4-fixed-3.8.60
#
# The binaries are not stored here: debug builds are ~122MB each and this tree
# is committed.
if [ $# -eq 2 ]; then
  stock_bin="$1"; fixed_bin="$2"
  echo
  echo "gate: stock must download before failing, fixed must refuse first"
  for pair in "stock:$stock_bin" "fixed:$fixed_bin"; do
    label="${pair%%:*}"; binary="${pair#*:}"
    g="$work/gate-$label"
    mkdir -p "$g"; cp "$binary" "$g/tina4"; chmod 755 "$g/tina4"; chmod 555 "$g"
    set +e
    out="$( cd "$g" && ./tina4 update 2>&1 )"; rc=$?
    set -e
    chmod 755 "$g"
    tried="$(printf '%s' "$out" | grep -q 'Trying ' && echo yes || echo no)"
    if [ "$label" = stock ]; then
      check "stock starts a download"     "$tried" yes
      check "stock exits non-zero"        "$([ $rc -ne 0 ] && echo yes || echo no)" yes
    else
      check "fixed starts no download"    "$tried" no
      check "fixed names the directory"   "$(printf '%s' "$out" | grep -qF "$g" && echo yes || echo no)" yes
      check "fixed says what to run"      "$(printf '%s' "$out" | grep -q 'sudo tina4 update' && echo yes || echo no)" yes
      check "fixed exits non-zero"        "$([ $rc -ne 0 ] && echo yes || echo no)" yes
    fi
  done
else
  echo
  echo "note: gate skipped -- pass a stock and a fixed binary to run it (see prove.sh)"
fi

echo
[ $fail -eq 0 ] && echo "all assertions hold" || echo "SOME ASSERTIONS FAILED"
exit $fail

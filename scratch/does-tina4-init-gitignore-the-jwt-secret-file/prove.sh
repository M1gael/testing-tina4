#!/usr/bin/env bash
# Proof: a scaffolded Tina4 project does not ignore the file the framework
# writes its JWT signing secret into, so the secret is committable — in all
# four backend languages.
#
#   ./prove.sh              build both trees if needed, then probe
#   ./prove.sh --no-build   probe with whatever binaries are already built
#
# Every probe prints PASS/FAIL against what SHOULD happen, so a green run
# means the scaffold is behaving. Exit 0 = all properties hold, 2 = a property
# broke. Global git excludes are neutralised in every measurement, so a result
# never depends on the machine's own gitignore.
set -uo pipefail
cd "$(dirname "$0")"

WT="${TINA4_WORKTREES:-$HOME/.cache/tina4-worktrees}"
STOCK="$WT/fcli01v2-stock"
FIXED="$WT/fcli01v2-fixed"
CLONE="${TINA4_CLONE:-$HOME/gitdir/tinaforks/tina4}"
FAILURES=0
G="git -c core.excludesFile=/dev/null -c init.defaultBranch=main"

note() { printf '  %s\n' "$*"; }
check() { # check <expected rc> <actual rc> <description>
  if [ "$1" = "$2" ]; then printf '  PASS  %s\n' "$3"
  else printf '  FAIL  %s (wanted rc=%s, got rc=%s)\n' "$3" "$1" "$2"; FAILURES=$((FAILURES+1)); fi
}

if [ "${1:-}" != "--no-build" ]; then
  for pair in "$STOCK:" "$FIXED:fix/scaffold-gitignores-the-dev-secret-file"; do
    d=${pair%%:*}; br=${pair#*:}
    if [ ! -d "$d" ]; then
      note "creating worktree $d"
      if [ -n "$br" ]; then git -C "$CLONE" worktree add -q -b "$br" "$d" origin/main
      else git -C "$CLONE" worktree add -q --detach "$d" origin/main; fi
      [ -n "$br" ] && python3 apply_fix.py "$d/src/init.rs"
    fi
    ( cd "$d" && cargo build --release ) >/dev/null 2>&1 || { echo "build failed: $d"; exit 2; }
  done
fi

for t in "$STOCK" "$FIXED"; do
  [ -x "$t/target/release/tina4" ] || { echo "missing binary in $t — run without --no-build"; exit 2; }
done

probe() { # probe <binary> <label> <expect_ignored: yes|no>
  local BIN="$1" LABEL="$2" WANT="$3"
  echo
  echo "== $LABEL  (md5 $(md5sum "$BIN" | cut -c1-12))"
  local ROOT; ROOT=$(mktemp -d -t prove-XXXXXX)
  for LANG in python php ruby nodejs; do
    case $LANG in python) EXT=py ;; php) EXT=php ;; ruby) EXT=rb ;; nodejs) EXT=ts ;; esac
    local P="$ROOT/$LANG"
    # install_deps runs after scaffolding and needs the network; cap it. The
    # scaffold (and therefore the .gitignore) is complete before the cap bites.
    ( cd "$ROOT" && TINA4_INIT_NO_SERVE=1 timeout 45 "$BIN" init "$LANG" "$LANG" ) >/dev/null 2>&1
    [ -d "$P" ] || { echo "  FAIL  $LANG did not scaffold"; FAILURES=$((FAILURES+1)); continue; }
    printf 'TINA4_SECRET=%s\n' "$(head -c32 /dev/urandom | od -An -tx1 | tr -d ' \n')" > "$P/.env.local"
    mkdir -p "$P/src/routes/sessions" "$P/src/orm/sessions" "$P/tests/fixtures"
    echo x > "$P/src/routes/sessions/get.$EXT"
    echo x > "$P/src/orm/sessions/model.$EXT"
    echo x > "$P/tests/fixtures/seed.db"
    echo x > "$P/.env.example"
    ( cd "$P" && $G init -q && $G add -A ) >/dev/null 2>&1
    echo "  -- $LANG"
    ( cd "$P" && $G check-ignore -q .env.local ); local rc=$?
    if [ "$WANT" = yes ]; then check 0 "$rc" "$LANG: .env.local is ignored"
    else check 1 "$rc" "$LANG: .env.local is NOT ignored (the defect)"; fi
    # nothing a project needs tracked may be swallowed — this is what the
    # superseded patch got wrong by adding unanchored sessions/ and *.db
    for keep in ".env.example" "src/routes/sessions/get.$EXT" "src/orm/sessions/model.$EXT" "tests/fixtures/seed.db"; do
      ( cd "$P" && $G check-ignore -q "$keep" ); check 1 "$?" "$LANG: $keep stays tracked"
    done
    # instrument validation: .env must be ignored in the same run, or a
    # uniformly-rc1 check-ignore would "prove" anything we asked it.
    ( cd "$P" && $G check-ignore -q .env ); check 0 "$?" "$LANG: instrument sane (.env ignored)"
  done
  rm -rf "$ROOT"
}

probe "$STOCK/target/release/tina4" "STOCK — the defect" no
probe "$FIXED/target/release/tina4" "FIXED — leak closed, nothing over-ignored" yes

echo
if [ "$FAILURES" -eq 0 ]; then echo "ALL PROPERTIES HOLD"; exit 0
else echo "$FAILURES property/properties broke"; exit 2; fi

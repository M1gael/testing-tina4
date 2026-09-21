#!/usr/bin/env bash
# f-cli-01 — does `tina4 init`'s Python scaffold gitignore the file the framework
# writes the JWT signing secret into (.env.local)?
#
# Reproduces from the EXACT template bytes each CLI emits, via `git check-ignore`
# (no cargo build needed). Prints a verdict; exits non-zero if the fixed template
# fails to protect .env.local or over-ignores a file a user wants tracked.
#
# Optional real end-to-end: TINA4_BIN=/path/to/tina4 ./prove.sh
set -u

# Template literals, byte-for-byte:
#   STOCK  = tina4/src/init.rs:626-630 @ origin/main 2bb1418 (v3.8.88)
#   FIXED  = the candidate in fix.patch (reconciled with tina4-python cli/__init__.py:658-663)
STOCK=$'.venv/\n__pycache__/\n*.pyc\n*.pyo\ndata/\nlogs/\nsecrets/\n.env\n'
FIXED=$'.venv/\n__pycache__/\n*.pyc\n*.pyo\ndata/\nlogs/\nsessions/\nsecrets/\n*.db\n.env\n.env.local\n'

fail=0
ci() {  # check-ignore: prints "ignored"/"tracked" for $2 under the .gitignore in $1
  git -C "$1" check-ignore -q "$2" && echo ignored || echo tracked
}

probe_template() {  # $1=label  $2=template-bytes  $3=expect .env.local (ignored|tracked)
  local label="$1" tmpl="$2" expect="$3"
  local d; d=$(mktemp -d); git -C "$d" init -q
  printf '%s' "$tmpl" > "$d/.gitignore"
  local secret example source
  secret=$(ci "$d" .env.local)     # the auto-minted TINA4_SECRET file
  example=$(ci "$d" .env.example)  # a file the user WANTS committed
  source=$(ci "$d" app.py)         # scaffolded source
  printf '  %-6s  .env.local=%-8s .env.example=%-8s app.py=%-8s\n' "$label" "$secret" "$example" "$source"
  [ "$secret" = "$expect" ] || { echo "    !! .env.local expected $expect, got $secret"; fail=1; }
  # a fix must never hide a file the user wants tracked:
  if [ "$label" = FIXED ]; then
    [ "$example" = tracked ] || { echo "    !! over-ignore: .env.example is $example"; fail=1; }
    [ "$source"  = tracked ] || { echo "    !! over-ignore: app.py is $source"; fail=1; }
  fi
  rm -rf "$d"
}

echo "== template-level proof (git check-ignore on exact bytes) =="
probe_template STOCK "$STOCK" tracked   # tracked == LEAK (the bug)
probe_template FIXED "$FIXED" ignored    # ignored == secret protected

if [ -n "${TINA4_BIN:-}" ]; then
  echo "== real binary end-to-end ($TINA4_BIN) =="
  d=$(mktemp -d)
  ( cd "$d" && TINA4_INIT_NO_SERVE=1 timeout 120 "$TINA4_BIN" init python probe >/dev/null 2>&1 )
  if [ -f "$d/probe/.gitignore" ]; then
    git -C "$d/probe" init -q
    r=$(ci "$d/probe" .env.local)
    echo "  generated .gitignore -> .env.local=$r"
    [ "$r" = ignored ] || { echo "    !! real binary still leaks .env.local"; fail=1; }
  else
    echo "  (init produced no project; skipped)"
  fi
  rm -rf "$d"
fi

echo
if [ "$fail" -eq 0 ]; then
  echo "VERDICT: stock LEAKS .env.local; fixed template protects it and over-ignores nothing. PASS"
else
  echo "VERDICT: FAIL — see !! lines above"
fi
exit "$fail"

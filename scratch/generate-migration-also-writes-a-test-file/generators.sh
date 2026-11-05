#!/usr/bin/env bash
# Run each port's own `generate migration` in an empty dir and list EVERY file it writes.
# Runtime (framework tip trees, php vendor, node_modules) lives in $R, not here: see readme.md.
set -u
R=${R:-$HOME/.cache/tina4-worktrees/grind-1102/dorm04}
export HOME=$R/home   # framework CLIs may install skills under ~/.claude
rc=0
NAMES=${NAMES:-create_notes_table add_category_to_product}
gen(){ local port=$1; shift; local n a; for n in $NAMES; do a=$(mktemp -d)
  if ! (cd "$a" && "$@" generate migration "$n" >"$a.out" 2>&1); then
    echo "$port $n: ERROR generator failed:"; sed 's/^/  /' "$a.out"; rc=2; rm -rf "$a" "$a.out"; continue; fi
  local files; files=$(cd "$a" && find . -type f ! -path './.claude/*' | sed 's|^\./||' | sort)
  [ -z "$files" ] && { echo "$port $n: ERROR no files written"; rc=2; }
  echo "$port $n:"; echo "$files" | sed 's/^/  /'; rm -rf "$a" "$a.out"; done; }
for t in python3 php ruby node; do command -v $t >/dev/null || { echo "ERROR: $t missing"; exit 2; }; done
gen python env PYTHONPATH="$R/fw-python" python3 -c 'import sys; from tina4_python.cli import main; sys.argv[0]="tina4python"; main()'
gen php    php "$R/fw-php/bin/tina4php"
gen ruby   ruby -I "$R/fw-ruby/lib" "$R/fw-ruby/exe/tina4ruby"
gen nodejs "$R/fw-nodejs/node_modules/.bin/tsx" "$R/fw-nodejs/packages/cli/src/bin.ts"
exit $rc

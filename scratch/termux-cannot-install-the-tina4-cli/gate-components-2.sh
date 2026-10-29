#!/usr/bin/env bash
# Second pass of gate-components.sh for the two cells the first pass could not
# see, plus every control re-run against the current gate.sh:
#  - libsqlite-header: libsqlite only arrives with Ruby through a Recommends
#    chain (ruby -> pkg-config -> glib -> python -> libsqlite), so the cell
#    installs Ruby WITHOUT recommends (plus the compiler) to remove it.
#  - install-composer: the stock fallback fails silently; gate.sh now checks
#    the package manager is present straight after `tina4 install`.
# usage: gate-components-2.sh <worktree>
set -uo pipefail
WT=$1
HERE=$(cd "$(dirname "$0")" && pwd)
FIXED=$HERE/tina4-fixed-android-x86_64
RES=$HERE/gate-components-2.txt
: >"$RES"
PY_ONLY='yes | pkg install -y python >/dev/null 2>&1'
PHP_ONLY='yes | pkg install -y php >/dev/null 2>&1'
RUBY_BARE='apt-get install -y --no-install-recommends ruby clang make >/dev/null 2>&1; test ! -e $PREFIX/include/sqlite3.h && echo NO_SQLITE_HEADER'

run_cell() {
  local bin=$1 lang=$2 order=$3 pre=$4 tag=$5
  local o=; [ "$order" = install-first ] && o=install-first
  ORDER=$o PRE=$pre "$HERE/gate.sh" "$bin" "$lang" 2>&1 | tail -1
  rm -rf "$HERE/gate-out-components/$tag"
  mv "$HERE/gate-out" "$HERE/gate-out-components/$tag" 2>/dev/null
}
mkdir -p "$HERE/gate-out-components" "$HERE/mutants"

for c in "libsqlite-header|ruby|init-first|$RUBY_BARE" "install-composer|php|install-first|$PHP_ONLY"; do
  IFS='|' read -r name lang order pre <<<"$c"
  bin=$HERE/mutants/tina4-$name
  python3 "$HERE/mutate.py" "$WT" "$name" "$bin" >/dev/null 2>"$HERE/mutants/$name.build.txt" || { echo "$name: BUILD FAILED" | tee -a "$RES"; continue; }
  line=$(run_cell "$bin" "$lang" "$order" "$pre" "mutant-$name")
  echo "mutant $name [$lang $order +pre]: $([[ $line == *FAIL* ]] && echo 'red (good)' || echo 'STAYED GREEN') :: $line" | tee -a "$RES"
done

# pre goes LAST: it contains "|" (yes | pkg ...), and read gives the last field the rest of the line
for c in "python|init-first|py-only|$PY_ONLY" "php|init-first|php-only|$PHP_ONLY" \
         "php|install-first|php-only|$PHP_ONLY" "ruby|init-first|ruby-bare|$RUBY_BARE"; do
  IFS='|' read -r lang order tag pre <<<"$c"
  line=$(run_cell "$FIXED" "$lang" "$order" "$pre" "control-$lang-$order-$tag")
  echo "control $lang $order $tag: $([[ $line == *PASS* ]] && echo 'green (good)' || echo RED) :: $line" | tee -a "$RES"
done

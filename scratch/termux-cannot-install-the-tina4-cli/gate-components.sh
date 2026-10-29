#!/usr/bin/env bash
# Every component must turn the gate red ON ITS OWN. For each one: revert only
# it, build, run the gate cell that exercises it, and expect FAIL. Controls run
# the unmutated build on the same special cells and expect PASS.
# usage: gate-components.sh <worktree>
set -uo pipefail
WT=$1
HERE=$(cd "$(dirname "$0")" && pwd)
FIXED=$HERE/tina4-fixed-android-x86_64
RES=$HERE/gate-components.txt
: >"$RES"
PY_ONLY='yes | pkg install -y python >/dev/null 2>&1'
PHP_ONLY='yes | pkg install -y php >/dev/null 2>&1'
RUBY_ONLY='yes | pkg install -y ruby >/dev/null 2>&1'

# name | lang | order | pre
CELLS=(
  "init-runtime|php|init-first|"
  "init-uv|python|init-first|$PY_ONLY"
  "init-composer|php|init-first|$PHP_ONLY"
  "ruby-build-config|ruby|init-first|"
  "libsqlite-header|ruby|init-first|$RUBY_ONLY"
  "install-php|php|install-first|"
  "install-composer|php|install-first|$PHP_ONLY"
  "install-ruby|ruby|install-first|"
  "install-node|nodejs|install-first|"
  "local-bin-path|python|install-first|"
  "uv-link-mode|python|init-first|"
)

run_cell() {  # binary lang order pre -> gate line
  local bin=$1 lang=$2 order=$3 pre=$4 tag=$5
  local o=; [ "$order" = install-first ] && o=install-first
  ORDER=$o PRE=$pre "$HERE/gate.sh" "$bin" "$lang" 2>&1 | tail -1
  mv "$HERE/gate-out" "$HERE/gate-out-components/$tag" 2>/dev/null
}
mkdir -p "$HERE/gate-out-components"

for c in "${CELLS[@]}"; do
  IFS='|' read -r name lang order pre <<<"$c"
  bin=$HERE/mutants/tina4-$name; mkdir -p "$HERE/mutants"
  if ! python3 "$HERE/mutate.py" "$WT" "$name" "$bin" >/dev/null 2>"$HERE/mutants/$name.build.txt"; then
    echo "$name: BUILD FAILED" | tee -a "$RES"; continue
  fi
  line=$(run_cell "$bin" "$lang" "$order" "$pre" "mutant-$name")
  verdict=$([[ $line == *FAIL* ]] && echo "red (good)" || echo "STAYED GREEN")
  echo "mutant $name [$lang $order${pre:+ +pre}]: $verdict :: $line" | tee -a "$RES"
done

# Controls: the unmutated build on each special starting state.
for c in "python|init-first|$PY_ONLY|py-only" "php|init-first|$PHP_ONLY|php-only" \
         "php|install-first|$PHP_ONLY|php-only" "ruby|init-first|$RUBY_ONLY|ruby-only"; do
  IFS='|' read -r lang order pre tag <<<"$c"
  line=$(run_cell "$FIXED" "$lang" "$order" "$pre" "control-$lang-$order-$tag")
  verdict=$([[ $line == *PASS* ]] && echo "green (good)" || echo "RED")
  echo "control $lang $order $tag: $verdict :: $line" | tee -a "$RES"
done

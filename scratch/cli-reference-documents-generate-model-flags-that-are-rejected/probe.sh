#!/bin/bash
# Run every `generate model` form 31-cli documents, through the tina4 CLI, in a fresh
# marker project per port, and print rc + first output line + files written.
# Needs the runtime from setup.sh (RT). Prints a table; no verdict of its own.
set -u
RT=${RT:-$HOME/.cache/tina4-worktrees/docs-cli05/rt}
export HOME="$RT/home" PATH="$RT/shims:/usr/bin:/bin" SHIM_LOG="$RT/shim.log"
: > "$SHIM_LOG"
W=$(mktemp -d "$RT/probe.XXXX")
marker(){ case $1 in
  python) echo 'tina4-python' > requirements.txt; touch app.py;;
  php)    echo '{"require":{"tina4stack/tina4php":"*"}}' > composer.json; mkdir -p vendor; touch index.php;;
  ruby)   echo 'gem "tina4ruby"' > Gemfile;;
  nodejs) echo '{"dependencies":{"tina4-nodejs":"*"}}' > package.json; touch app.ts;;
esac; }
FORMS=(
  'generate model Product'
  'generate model Product --fields name:string,price:float'
  'generate model Product --fields name:string --no-migration'
  'generate model Product --auto-crud'
  'generate model Product --soft-delete'
  'generate model Product --with-route'
  'generate model Product --with-route --with-migration'
  'generate model Customer --with-route --with-migration'
  'generate route products'
  'generate crud Customer --fields name:string,email:string'
)
for p in python php ruby nodejs; do
  for f in "${FORMS[@]}"; do
    d="$W/$p-$(echo "$f" | tr -c 'a-zA-Z0-9' _)"; mkdir -p "$d"; cd "$d"; marker $p
    before=$(find . -type f | sort)
    out=$(timeout 60 tina4 $f 2>&1); rc=$?
    new=$(comm -13 <(echo "$before") <(find . -type f | sort) | sed 's|^\./||' | grep -v -E '^(\.tina4|logs/|data/)' | tr '\n' ' ')
    printf '%-6s rc=%-3s %-55s | %s | %s\n' "$p" "$rc" "tina4 $f" "$(echo "$out" | grep -v '^\s*$' | head -1 | cut -c1-90)" "$new"
  done
done
echo "forwarded verbatim: $(grep -c ' generate ' "$SHIM_LOG") of $((4*${#FORMS[@]})) calls"
rm -rf "$W"

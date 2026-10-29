#!/usr/bin/env bash
# d-orm-02: python ch05 (docs + book) must show the migration file names the
# python generator really writes, and gotcha 5 must not call them sequential.
#   DOCS=<tina4-documentation root> BOOK=<tina4-book root> ./prove.sh
# VENV (default below) must hold tina4-python; the generator is run to get the shape.
set -u
DOCS=${DOCS:-}; BOOK=${BOOK:-}
[[ -n $DOCS || -n $BOOK ]] || { echo "usage: DOCS=<docs root> BOOK=<book root> $0 (either or both)"; exit 2; }
W=${W:-$HOME/.cache/tina4-worktrees/verify-1029/d-orm-02}
VENV=${VENV:-$W/venv}

# 1. Real generator output shape.
app=$(mktemp -d); home=$(mktemp -d)
( cd "$app" && HOME=$home "$VENV/bin/tina4python" generate migration create_notes_table >/dev/null 2>&1 )
gen=$(ls "$app/migrations" 2>/dev/null | grep -v '\.down\.sql$' | head -1)
rm -rf "$app" "$home"
[[ $gen =~ ^([0-9]+)_create_notes_table\.sql$ ]] || { echo "VERDICT: ERROR generator wrote '$gen'"; exit 2; }
plen=${#BASH_REMATCH[1]}
echo "generator wrote: $gen (prefix $plen digits)"

bad=0; refs=0; files=()
[[ -n $DOCS ]] && files+=("$DOCS/docs/python/05-database.md")
[[ -n $BOOK ]] && files+=("$BOOK/book-1-python/chapters/05-database.md")
for f in "${files[@]}"; do
  [[ -f $f ]] || { echo "VERDICT: ERROR missing $f"; exit 2; }
  # 2. Every create_notes_table file name the chapter shows must have the generator's prefix length.
  n0=$refs
  while IFS=: read -r ln name; do
    refs=$((refs+1)); p=${name%%_*}
    if (( ${#p} != plen )); then bad=$((bad+1)); echo "WRONG $f:$ln $name"; fi
  done < <(grep -noE '[0-9]+_create_notes_table(\.down)?\.sql' "$f")
  # Anti-vacuity: 8 generated-file references per chapter on these tips.
  (( refs - n0 >= 8 )) || { echo "VERDICT: ERROR only $((refs-n0)) file-name refs in $f"; exit 2; }
  # 3. Gotcha 5 fix line: must not say sequential, must name the timestamp.
  g=$(grep -n 'Use `tina4 generate migration`' "$f")
  [[ -n $g ]] || { echo "VERDICT: ERROR gotcha 5 not found in $f"; exit 2; }
  if grep -qi 'sequential' <<<"$g" || ! grep -qi 'timestamp' <<<"$g"; then
    bad=$((bad+1)); echo "WRONG gotcha5 $f:${g%%:*}"
  fi
done
if (( bad )); then echo "VERDICT: FAIL $bad wrong of $refs refs + ${#files[@]} gotcha(s)"; exit 1; fi
echo "VERDICT: PASS 0 wrong of $refs refs + ${#files[@]} gotcha(s)"

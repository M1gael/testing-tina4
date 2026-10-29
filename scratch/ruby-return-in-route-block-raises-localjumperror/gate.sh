#!/usr/bin/env bash
# Gate: in the fixed trees, revert each file of the held patch alone (copy the stock file back)
# and show prove.sh goes red. Usage: STOCK_DOCS= STOCK_BOOK= FIXED_DOCS= FIXED_BOOK= [SERVE=0] ./gate.sh
set -u; HERE=$(cd "$(dirname "$0")" && pwd); fail=0
for side in docs book; do
  if [ $side = docs ]; then st=$STOCK_DOCS fx=$FIXED_DOCS sub=docs/ruby; else st=$STOCK_BOOK fx=$FIXED_BOOK sub=book-3-ruby/chapters; fi
  for f in $(diff -rq "$st/$sub" "$fx/$sub" | awk '{print $2}' | xargs -n1 basename); do
    cp "$fx/$sub/$f" "$fx/$sub/$f.keep"; cp "$st/$sub/$f" "$fx/$sub/$f"
    v=$(DOCS=$FIXED_DOCS BOOK=$FIXED_BOOK SERVE=${SERVE:-0} "$HERE/prove.sh" 2>&1); rc=$?
    mv "$fx/$sub/$f.keep" "$fx/$sub/$f"
    n=$(grep -c "^    $f:" <<<"$v")
    if [ $rc -ne 0 ]; then echo "RED   $side $f: rc=$rc, $n lines flagged, $(tail -1 <<<"$v")"; else echo "GREEN $side $f: revert NOT detected"; fail=1; fi
  done
done
[ $fail -eq 0 ] && echo "GATE PASS: every piece goes red alone" || { echo "GATE FAIL"; exit 1; }

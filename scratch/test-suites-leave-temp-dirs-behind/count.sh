#!/bin/sh
# Every temp-dir prefix any suite or the app can create, counted by prefix.
# Counting only t4a-* (what dx-04's row did) misses write-checks.mjs, whose prefix is "wc-".
for p in t4a-guards t4a-state t4a-harness t4a-e2e t4-ideation t4-dispatch t4- wc- chk_; do
  n=$(ls -d /tmp/$p* 2>/dev/null | wc -l)
  printf '%-14s %s\n' "$p" "$n"
done
printf '%-14s %s\n' TOTAL "$(ls -d /tmp/t4a-* /tmp/t4-* /tmp/wc-* /tmp/chk_* 2>/dev/null | wc -l)"

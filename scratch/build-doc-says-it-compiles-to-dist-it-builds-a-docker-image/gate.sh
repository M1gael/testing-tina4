#!/usr/bin/env bash
# Gate: revert each piece of the held fix alone (one file, or one hunk of 34-deployment)
# on a copy of the fixed tree and show prove.sh goes red.
# Usage: KIND=docs|book FIXED=<fixed tree root> PATCH=<fix.patch> WORK=<scratch dir outside repo> ./gate.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
: "${KIND:?}" "${FIXED:?}" "${PATCH:?}" "${WORK:?}"
pieces=$WORK/pieces-$KIND
rm -rf "$pieces"; mkdir -p "$pieces"
# Split: one piece per file, except */34-deployment.md -> one piece per hunk.
python3 -I - "$PATCH" "$pieces" <<'PY'
import re, sys, pathlib
text = pathlib.Path(sys.argv[1]).read_text()
out = pathlib.Path(sys.argv[2])
for fd in re.split(r"(?m)^(?=diff --git )", text):
    if not fd.strip():
        continue
    head, *hunks = re.split(r"(?m)^(?=@@ )", fd)
    name = re.search(r"^diff --git a/(\S+)", head, re.M).group(1)
    tag = name.replace("/", "_")
    if name.endswith("34-deployment.md"):
        for i, h in enumerate(hunks, 1):
            (out / f"{tag}.hunk{i}.patch").write_text(head + h)
    else:
        (out / f"{tag}.patch").write_text(fd)
PY
red=0; green=0
for p in "$pieces"/*.patch; do
  t=$WORK/gate-tree-$KIND
  rm -rf "$t"; cp -a "$FIXED" "$t"
  (cd "$t" && git apply -R "$p") || { echo "GATE $(basename "$p"): could not revert"; continue; }
  if [ "$KIND" = docs ]; then v=$(DOCS=$t "$here/prove.sh" | tail -1); rc=$?
  else v=$(BOOK=$t "$here/prove.sh" | tail -1); fi
  case $v in *FAIL*) red=$((red+1)); s=RED;; *) green=$((green+1)); s=GREEN-NOT-GATED;; esac
  echo "GATE $s $(basename "$p" .patch): ${v%% docs=*}"
  rm -rf "$t"
done
echo "GATE SUMMARY $KIND: red=$red not_gated=$green"
[ "$green" -eq 0 ]

#!/usr/bin/env bash
# f-ai-08 — tina4-js ships a .cursor skill copy that cites references/ it does not carry.
#
# Read-only. Operates on a checkout of tina4stack/tina4-js, pinned by commit so
# the result does not drift when master moves.
#
#   ./reproduce.sh [path-to-tina4-js-checkout]
#
# Exit 1 while the defect is present, 0 once every cited reference resolves.
set -euo pipefail

REPO="${1:-/var/home/work/gitdir/tinaforks/tina4-js}"
PIN="f9cffcb"          # observed 2026-08-26; origin/master at the time

cd "$REPO"
echo "repo: $REPO"
echo "HEAD: $(git rev-parse --short HEAD)   (observed on $PIN)"
git merge-base --is-ancestor "$PIN" HEAD 2>/dev/null \
  || echo "  ! note: $PIN is not an ancestor of HEAD — this checkout predates the observation"
echo

fail=0

for tree in .claude .cursor .agents; do
  skill="$tree/skills/tina4-js/SKILL.md"
  [ -f "$skill" ] || { printf '%-8s no SKILL.md\n' "$tree"; continue; }

  dir="$(dirname "$skill")"
  printf '%-8s %s (%s bytes)\n' "$tree" "$skill" "$(wc -c <"$skill")"

  # Every references/<file> the copy tells the assistant to open.
  cited="$(grep -oE 'references/[A-Za-z0-9._-]+' "$skill" | sort -u || true)"
  if [ -z "$cited" ]; then
    echo "         cites no references/"
  else
    while IFS= read -r ref; do
      if [ -e "$dir/$ref" ]; then
        printf '         ok       %s\n' "$ref"
      else
        printf '         DANGLING %s   (cited at lines: %s)\n' \
          "$ref" "$(grep -n "$ref" "$skill" | cut -d: -f1 | paste -sd, -)"
        fail=1
      fi
    done <<<"$cited"
  fi

  # The other half of the defect: files shipped that nothing points at.
  if [ -d "$dir/references" ]; then
    for f in "$dir/references"/*; do
      base="references/$(basename "$f")"
      grep -q "$base" "$skill" || printf '         ORPHAN   %s   (shipped, cited nowhere)\n' "$base"
    done
  fi
  echo
done

if [ "$fail" -eq 1 ]; then
  echo "FAIL — a SKILL.md tells the assistant to read a file its own tree does not ship."
  exit 1
fi
echo "PASS — every cited reference resolves inside its own tree."

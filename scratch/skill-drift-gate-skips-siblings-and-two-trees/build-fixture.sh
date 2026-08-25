#!/usr/bin/env bash
# Build a synthetic multi-repo root for the drift gate to run against.
#
#   build-fixture.sh <root> <A|B> <script-to-install>
#
# A — tina4-python alone. No sibling repos beside it.
# B — tina4-python plus the three siblings, carrying the real defects.
# C — negative control: all four repos, every copy consistent and clean UTF-8.
#
# The fixture reproduces the three real relationships, measured 2026-08-25 in
# gitdir/tinaforks:
#
#   tina4-maintainer   .claude is the full skill; .agents/.cursor are 755-byte
#                      stubs, all eight byte-identical across the four repos.
#                      A cross-repo diff therefore reports CLEAN even though every
#                      one of them carries a BOM and cp1252 mojibake (f-ai-03) —
#                      only an encoding assertion can catch it.
#   tina4-js           all three trees are full copies of the same file.
#   tina4-developer-*  language-specific, so nothing to compare across repos, but
#                      .agents/.cursor drift from .claude inside one repo (f-ai-07).
#
# Mojibake bytes are c3 a2 e2 82 ac e2 80 9d — an em dash read as cp1252 and
# re-saved as UTF-8, verified byte-for-byte against the real tina4-php file.
set -euo pipefail
root="$1"; variant="$2"; script="${3:?script to install under scripts/}"

rm -rf "$root"; mkdir -p "$root"

DASH=$'\xe2\x80\x94'                       # a real em dash
MOJI=$'\xc3\xa2\xe2\x82\xac\xe2\x80\x9d'   # the same dash, corrupted
BOM=$'\xef\xbb\xbf'

# full shared skill, clean UTF-8, no BOM
mk_shared_claude() {            # $1 = repo dir
  for skill in tina4-maintainer tina4-js; do
    mkdir -p "$1/.claude/skills/$skill"
    printf -- '---\nname: %s\ndescription: Use this skill %s when maintaining Tina4 %s across repos.\n---\n\nFull body for %s.\n' \
      "$skill" "$DASH" "$DASH" "$skill" > "$1/.claude/skills/$skill/SKILL.md"
  done
  mkdir -p "$1/.claude/skills/tina4-maintainer/references"
  printf -- 'Canonical subsystems reference.\n' > "$1/.claude/skills/tina4-maintainer/references/subsystems.md"
}

# the two extra trees, exactly as the real repos carry them
mk_shared_extra() {             # $1 = repo dir, $2 = .agents|.cursor
  # maintainer: a short stub, and it is the corrupted one
  mkdir -p "$1/$2/skills/tina4-maintainer"
  if [ "${CLEAN:-0}" = 1 ]; then
    printf -- '---\nname: tina4-maintainer\ndescription: Entrypoint %s see .claude/skills %s for the full skill.\n---\n' \
      "$DASH" "$DASH" > "$1/$2/skills/tina4-maintainer/SKILL.md"
  else
    printf -- '%s---\nname: tina4-maintainer\ndescription: Entrypoint %s see .claude/skills %s for the full skill.\n---\n' \
      "$BOM" "$MOJI" "$MOJI" > "$1/$2/skills/tina4-maintainer/SKILL.md"
  fi
  # tina4-js: a full copy, byte-identical to .claude
  mkdir -p "$1/$2/skills/tina4-js"
  cp "$1/.claude/skills/tina4-js/SKILL.md" "$1/$2/skills/tina4-js/SKILL.md"
}

# language-specific developer skill: .claude correct, the other two drifted
mk_developer() {                # $1 = repo dir, $2 = lang
  mkdir -p "$1/.claude/skills/tina4-developer-$2"
  printf -- '---\nname: tina4-developer-%s\n---\n\nCall initDatabase({ url }) with an object.\n' \
    "$2" > "$1/.claude/skills/tina4-developer-$2/SKILL.md"
  for tree in .agents .cursor; do
    mkdir -p "$1/$tree/skills/tina4-developer-$2"
    if [ "${CLEAN:-0}" = 1 ]; then
      cp "$1/.claude/skills/tina4-developer-$2/SKILL.md" "$1/$tree/skills/tina4-developer-$2/SKILL.md"
    else
      printf -- '---\nname: tina4-developer-%s\n---\n\nCall initDatabase(url) with a string.\n' \
        "$2" > "$1/$tree/skills/tina4-developer-$2/SKILL.md"
    fi
  done
}

build_repo() {                  # $1 = repo dir, $2 = lang
  mk_shared_claude "$1"
  mk_shared_extra "$1" .agents
  mk_shared_extra "$1" .cursor
  mk_developer "$1" "$2"
}

if [ "$variant" = C ]; then export CLEAN=1; fi

py="$root/tina4-python"
mkdir -p "$py/scripts"
build_repo "$py" python
cp "$script" "$py/scripts/sync-tina4-skills.sh"

if [ "$variant" = B ] || [ "$variant" = C ]; then
  build_repo "$root/tina4-php"    php
  build_repo "$root/tina4-ruby"   ruby
  build_repo "$root/tina4-nodejs" nodejs
fi

# A HOME of our own, so the real ~/.claude never leaks into a measurement.
# In A and B it holds no skills at all; in C it carries a correct global install,
# because the negative control has to be clean on every axis the gate looks at.
mkdir -p "$root/home"
if [ "$variant" = C ]; then
  mkdir -p "$root/home/.claude/skills"
  for skill in tina4-maintainer tina4-js; do
    cp -r "$py/.claude/skills/$skill" "$root/home/.claude/skills/$skill"
  done
fi

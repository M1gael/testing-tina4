#!/usr/bin/env bash
# Run each port's real migration generator at the 2026-10-29 tips; print the names written.
set -u
W=${W:-$HOME/.cache/tina4-worktrees/verify-1029/d-orm-02}; F=$(dirname "$W")
gen(){ local port=$1; shift; local a h; a=$(mktemp -d); h=$(mktemp -d)
  (cd "$a" && HOME=$h "$@" generate migration create_notes_table >/dev/null 2>&1)
  echo "$port: $(ls "$a/migrations" 2>/dev/null | tr '\n' ' ')"; rm -rf "$a" "$h"; }
gen python "$W/venv/bin/tina4python"                          # fw-python efa826a3 (pip -e)
gen php    php "$W/php/bin/tina4php"                          # copy of fw-php b321c1fc + composer --no-dev
gen ruby   ruby -I "$F/fw-ruby/lib" "$F/fw-ruby/exe/tina4ruby" # fw-ruby 74aa1f5
gen nodejs "$W/nodejs/node_modules/.bin/tsx" "$W/nodejs/packages/cli/src/bin.ts" # copy of fw-nodejs b447252 + npm ci

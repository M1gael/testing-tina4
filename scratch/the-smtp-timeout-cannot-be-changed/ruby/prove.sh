#!/usr/bin/env bash
# tina4-ruby: can anything bound a Messenger send to a silent SMTP host?
# Usage: TREE=<tina4-ruby checkout> BUNDLE_PATH=<installed bundle> ./prove.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
: "${TREE:?set TREE to a tina4-ruby checkout}"
: "${BUNDLE_PATH:?set BUNDLE_PATH to the bundle directory}"
export BUNDLE_PATH BUNDLE_GEMFILE=$TREE/Gemfile
echo "tree: $(git -C "$TREE" rev-parse --short HEAD) ($(sed -n 's/.*VERSION = "\(.*\)"/\1/p' "$TREE/lib/tina4/version.rb"))"
work=$(mktemp -d); mkdir -p "$work/home"
exec 3< <(python3 "$here/../blackhole-smtp.py"); read -r port <&3
trap 'fuser -k -s $port/tcp 2>/dev/null; rm -rf "$work"' EXIT
run() { # label, env..., then args after --
  local label=$1; shift; local envs=(); while [ "$1" != -- ]; do envs+=("$1"); shift; done; shift
  ( cd "$work" && env HOME=$work/home "${envs[@]}" \
      bundle exec ruby -I"$TREE/lib" "$here/send.rb" "$port" "$@" 2>&1 | grep -E '^ELAPSED|Error' | head -2 | sed "s|^|[$label] |" )
}
run "default                  " -- &
run "TINA4_MAIL_TIMEOUT=2      " TINA4_MAIL_TIMEOUT=2 -- &
run "constructor timeout: 2   " -- 2 &
wait

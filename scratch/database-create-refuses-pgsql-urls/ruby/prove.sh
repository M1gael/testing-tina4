#!/usr/bin/env bash
# tina4-ruby: pgsql:// vs postgres:// through Tina4::Database.new.
# Usage: TREE=<tina4-ruby checkout> BUNDLE_PATH=<installed bundle> ./prove.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
: "${TREE:?set TREE to a tina4-ruby checkout}"
: "${BUNDLE_PATH:?set BUNDLE_PATH to the bundle directory}"
export BUNDLE_PATH BUNDLE_GEMFILE=$TREE/Gemfile
echo "tree: $(git -C "$TREE" rev-parse --short HEAD) ($(sed -n 's/.*VERSION = "\(.*\)"/\1/p' "$TREE/lib/tina4/version.rb"))"
work=$(mktemp -d); mkdir -p "$work/home"
python3 "$here/listener.py" > "$work/count" & lpid=$!
trap 'kill $lpid 2>/dev/null; rm -rf "$work"' EXIT
for _ in $(seq 50); do [ -s "$work/count" ] && break; sleep 0.1; done
port=$(head -1 "$work/count"); echo 0 >> "$work/count"
cd "$work" && HOME=$work/home TINA4_LOG_LEVEL=NONE bundle exec ruby -I"$TREE/lib" "$here/scheme.rb" "$port" "$work/count" 2>&1 | grep -E '^(pgsql|postgres)'

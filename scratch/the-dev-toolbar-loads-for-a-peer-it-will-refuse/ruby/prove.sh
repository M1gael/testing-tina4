#!/usr/bin/env bash
# tina4-ruby: does a page carry the dev toolbar for a peer that /__dev refuses?
# Serves on 0.0.0.0 and asks from loopback and from this machine's own LAN
# address (a non-loopback socket peer), sending a Host the allow-list accepts so
# only the peer differs.
# TINA4_OVERRIDE_CLIENT=true is the documented switch for running app.rb directly in debug mode.
# Usage: TREE=<tina4-ruby checkout> BUNDLE_PATH=<installed bundle> [LAN_IP=<addr>] ./prove.sh
set -u
here=$(cd "$(dirname "$0")" && pwd)
: "${TREE:?set TREE to a tina4-ruby checkout}"
: "${BUNDLE_PATH:?set BUNDLE_PATH to the bundle directory}"
export BUNDLE_PATH BUNDLE_GEMFILE=$TREE/Gemfile
LAN_IP=${LAN_IP:-$(hostname -I | awk '{print $1}')}
echo "tree: $(git -C "$TREE" rev-parse --short HEAD) ($(sed -n 's/.*VERSION = "\(.*\)"/\1/p' "$TREE/lib/tina4/version.rb")); non-loopback peer: LAN address"
good=$(ruby -rsecurerandom -e "puts SecureRandom.hex(32)")   # never written to disk
work=$(mktemp -d); cp -r "$here/app/." "$work/"; mkdir -p "$work/home"
port=$(ruby -rsocket -e 's=TCPServer.new("0.0.0.0",0); puts s.addr[1]; s.close')
( cd "$work" && HOME=$work/home TINA4_SECRET="$good" TINA4_DEBUG=true TINA4_NO_BROWSER=true TINA4_OVERRIDE_CLIENT=true \
    TINA4_PORT=$port TINA4_HOST=0.0.0.0 \
    exec bundle exec ruby -I"$TREE/lib" app.rb >"$work/srv.log" 2>&1 ) &
pid=$!
trap 'fuser -k -s $port/tcp 2>/dev/null; kill $pid 2>/dev/null; rm -rf "$work"' EXIT
for _ in $(seq 150); do curl -s -o /dev/null "http://127.0.0.1:$port/" && break; sleep 0.1; done
for peer in 127.0.0.1 "$LAN_IP"; do
  label=$([ "$peer" = 127.0.0.1 ] && echo "loopback peer    " || echo "non-loopback peer")
  for p in /hello /nothing-here /__dev/toolbar.js /__dev/toolbar.css /__dev; do
    code=$(curl -s -o "$work/b" -w '%{http_code}' -H "Host: localhost:$port" "http://$peer:$port$p")
    case $p in
      /hello|/nothing-here) echo "[$label] GET $p -> $code; toolbar markup injected: $(grep -c 'id="tina4-dev-toolbar"' "$work/b")" ;;
      *) echo "[$label] GET $p -> $code $( [ "$code" = 403 ] && head -c 100 "$work/b")" ;;
    esac
  done
done

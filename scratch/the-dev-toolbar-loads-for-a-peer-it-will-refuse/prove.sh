#!/usr/bin/env bash
# Usage: TREE=<tina4-php tree with vendor/> ./prove.sh
# Runs peer.php (a page and /__dev for loopback, Docker-gateway and LAN peers) and
# boom.php (the same on 404 and error pages) from a throwaway copy, so the
# sessions and logs the app writes never land here.
set -u
here=$(cd "$(dirname "$0")" && pwd); : "${TREE:?set TREE to a tina4-php checkout with vendor/}"
work=$(mktemp -d); trap 'rm -rf "$work"' EXIT
cp -r "$here/app" "$here/peer.php" "$here/boom.php" "$here/reporter-shape.php" "$work/"; rm -rf "$work/app/data" "$work/app/logs"
echo "tree: $(git -C "$TREE" rev-parse --short HEAD) ($(git -C "$TREE" status --porcelain -- Tina4 | wc -l) modified framework files), $(php -r 'echo PHP_VERSION;')"
cd "$work" || exit 1
for script in peer.php boom.php reporter-shape.php; do
  echo "--- $script"
  HOME="$work" TREE="$TREE" TINA4_DEBUG=true TINA4_LOG_LEVEL=NONE TINA4_OVERRIDE_CLIENT=true TINA4_AUTO_MIGRATE=false \
    TINA4_SECRET=$(head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n') php "$script"
done

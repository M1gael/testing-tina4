#!/usr/bin/env bash
# Usage: TREE=<tina4-php tree with vendor/> ./prove.sh
# Starts a relay that accepts and never speaks, then runs one Messenger::send() per knob.
# Stock: timeout.php (every public knob; each send waits the full 30 s).
# A tree with TINA4_MAIL_TIMEOUT: with-the-fix.php (both levers and the garbage cases).
set -u
here=$(cd "$(dirname "$0")" && pwd); : "${TREE:?set TREE to a tina4-php checkout with vendor/}"
exec 3< <(python3 "$here/blackhole-smtp.py")
read -r port <&3
echo "tree: $(git -C "$TREE" rev-parse --short HEAD) ($(git -C "$TREE" status --porcelain -- Tina4 | wc -l) modified framework files), $(php -r 'echo PHP_VERSION;'), silent relay on $port"
if grep -q TINA4_MAIL_TIMEOUT "$TREE/Tina4/Messenger.php"; then
  TREE="$TREE" php "$here/with-the-fix.php" "$port"
else
  TREE="$TREE" php "$here/timeout.php" "$port"
fi
php "$here/timed-out-flag.php"
{ fuser -k -n tcp "$port"; } >/dev/null 2>&1

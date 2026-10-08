#!/usr/bin/env bash
# tina4-python: can the SMTP wait be bounded? A listener that accepts and never speaks.
# Usage: TREE=<tina4-python checkout with .venv> ./prove.sh
set -u
TREE=${TREE:?set TREE to a tina4-python checkout with a .venv}
PY=${PY:-$TREE/.venv/bin/python}
here=$(cd "$(dirname "$0")" && pwd)
work=$(mktemp -d); export HOME=$work/home; mkdir -p "$HOME"
python3 "$here/../blackhole-smtp.py" >"$work/port" & bh=$!
trap 'kill $bh 2>/dev/null; rm -rf "$work"' EXIT
for _ in $(seq 50); do [ -s "$work/port" ] && break; sleep 0.1; done; port=$(cat "$work/port")
echo "tree: $(git -C "$TREE" rev-parse --short HEAD), $(grep -m1 '^version' "$TREE/pyproject.toml"), $($PY -V); silent listener on $port"
cd "$work"
echo "== no setting:                       $(timeout 90 "$PY" "$here/send.py" "$port" plain)"
echo "== TINA4_MAIL_TIMEOUT=2:             $(TINA4_MAIL_TIMEOUT=2 timeout 90 "$PY" "$here/send.py" "$port" plain)"
echo "== socket.setdefaulttimeout(2):      $(timeout 90 "$PY" "$here/send.py" "$port" socketdefault)"
echo "== constructor timeout=2:            $(timeout 90 "$PY" "$here/send.py" "$port" ctor)"

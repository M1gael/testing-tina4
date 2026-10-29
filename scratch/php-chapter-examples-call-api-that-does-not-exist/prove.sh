#!/usr/bin/env bash
# Runs the tina4-php chapter examples of ledger d-misc-02 verbatim against a tina4-php tree
# (rebuilt 2026-10-28 against tina4-php origin/v3 b321c1fc).
# DOCS=<a docs/php directory or a book-2-php/chapters directory>; default: tina4-documentation origin/main docs/php.
# TINA4_PHP=<tina4-php tree with vendor/>; PORT (default 7774). Exit 0 = every example works.
# app/vendor is a symlink into the tree; nothing of the framework is copied into scratch/.
cd "$(dirname "$0")"
T=${TINA4_PHP:-$HOME/.cache/tina4-worktrees/docfix-dmisc02-php}; P=${PORT:-7774}
if [ -z "${DOCS:-}" ]; then
  DOCS=$(mktemp -d); git -C /var/home/work/gitdir/tinaforks/tina4-documentation archive origin/main docs/php | tar -x -C "$DOCS"; DOCS=$DOCS/docs/php
fi
ln -sfn "$T/vendor" app/vendor
echo "tina4-php $(git -C "$T" rev-parse --short HEAD)  docs $DOCS"
python3 prove.py "$DOCS" "$T" "$P"

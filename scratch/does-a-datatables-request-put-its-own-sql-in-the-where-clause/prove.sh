#!/usr/bin/env bash
# Re-runnable proof for: does a DataTables request put its own SQL into the where
# clause, and does PR #209 close it?
#
# Rebuilds two worktrees off tina4stack/tina4-php origin/v2 @ 54ecf165 if absent:
#   pr209-stock  — untouched
#   pr209-fixed  — the same commit + pr209.patch
# then drives Crud::getDataTablesFilter() through drive.php on each, and runs the
# PR's own test file on each.
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
FORK="/var/home/work/gitdir/tinaforks/tina4-php"
WT="$HOME/.cache/tina4-worktrees"
BASE="54ecf165"
PATCHFILE="$HERE/pr209.patch"

build() {  # name  apply?
  local dir="$WT/$1"
  if [ ! -d "$dir" ]; then
    git -C "$FORK" worktree add --detach "$dir" "$BASE" >/dev/null 2>&1
    [ "$2" = "apply" ] && git -C "$dir" apply "$PATCHFILE"
    ( cd "$dir" && composer install --no-interaction --no-progress >/dev/null 2>&1 )
  fi
  echo "$dir"
}

STOCK="$(build pr209-stock no)"
FIXED="$(build pr209-fixed apply)"

echo "############ DRIVER: STOCK ($BASE) ############"
php "$HERE/drive.php" "$STOCK" 2>&1 | grep -vE 'DEBUG|INFO'
echo
echo "############ DRIVER: FIXED ($BASE + pr209.patch) ############"
php "$HERE/drive.php" "$FIXED" 2>&1 | grep -vE 'DEBUG|INFO'
echo

echo "############ PR TEST FILE on STOCK (expect 6 of 8 red) ############"
cp "$FIXED/tests/CrudDataTablesFilterTest.php" "$STOCK/tests/" 2>/dev/null
( cd "$STOCK" && vendor/bin/phpunit tests/CrudDataTablesFilterTest.php 2>&1 | tail -3 )
rm -f "$STOCK/tests/CrudDataTablesFilterTest.php"
echo
echo "############ PR TEST FILE on FIXED (expect 8 green) ############"
( cd "$FIXED" && vendor/bin/phpunit tests/CrudDataTablesFilterTest.php 2>&1 | tail -3 )

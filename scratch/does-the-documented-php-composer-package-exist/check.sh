#!/usr/bin/env bash
# usage: check.sh <tree> [paths...]  — every tina4stack Composer package the docs tell readers to
# require / create-project / put in composer.json must exist on Packagist. Exit 1 if any 404s.
T=$1; shift; cd "$T" || exit 2
names=$(git grep -hoE '(composer (global )?(require|create-project|update) (--dev )?|")tina4stack/[a-z0-9._-]+(": *")?' -- "${@:-.}" ':!*public/skills*' \
  | grep -E "^composer|\": *\"$" | grep -oE "tina4stack/[a-z0-9._-]+" | sort -u)
rc=0
for n in $names; do
  c=$(curl -s -o /dev/null -w '%{http_code}' "https://repo.packagist.org/p2/$n.json")
  [ "$c" = 000 ] && { echo "SKIP packagist unreachable"; exit 3; }
  [ "$c" = 200 ] || { echo "MISSING $n ($c): $(git grep -lE "$n([^a-z0-9._-]|$)" -- "${@:-.}" ':!*public/skills*' | head -3 | tr '\n' ' ')"; rc=1; }
done
[ $rc = 0 ] && echo "OK all $(echo $names | wc -w) package names exist"
exit $rc

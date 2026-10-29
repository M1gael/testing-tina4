#!/usr/bin/env bash
# d-auth-02. A logged-in browser (identity token in the session, no Bearer) posts to a default write
# route without a form token. ch10 says CSRF is on by default, so that must 403. Run with TINA4_CSRF
# unset and with TINA4_CSRF=true, all four ports; the form is "The Template" block from each ch10, verbatim.
# Then every page that states the CSRF default is checked against what the run showed.
# DOCS=<docs dir> (default tina4-documentation origin/main docs/), BOOK=<book root> (default tina4-book origin/main).
# PORT=<base> (default 7541; uses base..base+7). Exit 0 docs agree, 1 docs wrong, 2 harness broken.
cd "$(dirname "$0")"; . ./serve4.sh; base=${PORT:-7541}
G=/var/home/work/gitdir/tinaforks; TMPS=(); trap 'rm -rf "${TMPS[@]}"' EXIT
if [ -z "${DOCS:-}" ]; then DOCS=$(mktemp -d); TMPS+=($DOCS); git -C $G/tina4-documentation archive origin/main docs | tar -x -C $DOCS; DOCS=$DOCS/docs
  echo "docs: tina4-documentation origin/main $(git -C $G/tina4-documentation rev-parse --short origin/main)"; else echo "docs: $DOCS"; fi
if [ -z "${BOOK:-}" ]; then BOOK=$(mktemp -d); TMPS+=($BOOK); git -C $G/tina4-book archive origin/main | tar -x -C $BOOK
  echo "book: tina4-book origin/main $(git -C $G/tina4-book rev-parse --short origin/main)"; else echo "book: $BOOK"; fi
echo "frameworks: py $(git -C $PYT rev-parse --short HEAD) php $(git -C $PHPT rev-parse --short HEAD) rb $(git -C $RBT rev-parse --short HEAD) nd $(git -C $(readlink -f nd/node_modules/tina4-nodejs) rev-parse --short HEAD)"
declare -A LANG=([py]=python [php]=php [rb]=ruby [nd]=nodejs) BK=([py]=book-1-python [php]=book-2-php [rb]=book-3-ruby [nd]=book-4-nodejs)
probe(){ # prints "<no-token code> <with-token code> <token len> <noauth no-token code>"
  local p=$1 J=$(mktemp); curl -s -c $J -b $J -o /dev/null http://127.0.0.1:$p/login
  local ft=$(curl -s -c $J -b $J http://127.0.0.1:$p/profile | grep -o 'name="formToken"[^>]*value="[^"]*"\|value="[^"]*"[^>]*name="formToken"' | grep -o 'value="[^"]*"' | cut -d'"' -f2)
  local a=$(curl -s -c $J -b $J -o /dev/null -w '%{http_code}' -d 'name=Alice' http://127.0.0.1:$p/api/profile)
  local b=$(curl -s -c $J -b $J -o /dev/null -w '%{http_code}' --data-urlencode 'name=Alice' --data-urlencode "formToken=$ft" http://127.0.0.1:$p/api/profile)
  local c=$(curl -s -o /dev/null -w '%{http_code}' -d 'name=Alice' http://127.0.0.1:$p/api/open)
  rm -f $J; echo "$a $b ${#ft} $c"; }
broken=0; declare -A DEF; i=0
for l in py php rb nd; do
  python3 docblock.py "$DOCS/${LANG[$l]}/10-middleware-security.md" "The Template" > $l/src/templates/profile.twig
  p=$((base+i)); i=$((i+1)); EXTRA_ENV= start_port $l $p || { broken=1; continue; }; read d0 d1 dl dn <<<"$(probe $p)"; stop_port || broken=1
  p=$((base+i)); i=$((i+1)); EXTRA_ENV=TINA4_CSRF=true start_port $l $p || { broken=1; continue; }; read e0 e1 el en <<<"$(probe $p)"; stop_port || broken=1
  echo "$l  TINA4_CSRF unset: no token $d0, form token $d1 | TINA4_CSRF=true: no token $e0, form token $e1 (token len $el) | noauth route, CSRF on, no token: $en"
  # harness reaches CSRF only if the enabled run refuses the bare post and accepts the token
  [ "$e0" = 403 ] && [ "$e1" = 200 ] || { echo "  HARNESS: enabled run did not gate ($e0/$e1)"; broken=1; }
  [ "$d0" = 403 ] && DEF[$l]=on || DEF[$l]=off; rm -f $l/src/templates/profile.twig
done
[ $broken = 0 ] || { echo "VERDICT harness-broken"; exit 2; }
echo "observed default: py=${DEF[py]} php=${DEF[php]} rb=${DEF[rb]} nd=${DEF[nd]}"
# pages that state the default. "on" claims vs "off" claims.
ON='CSRF protection is on by default|TINA4_CSRF=true` \(the default\)|`TINA4_CSRF` \| `true`|CSRF is \*\*on by default\*\*|CSRF protection\*\* -- Built-in, enabled by default|CSRF tokens protect forms\. Security headers|Leave it enabled for anything a browser can reach|To disable for internal services'
OFF='CSRF protection is off by default|`TINA4_CSRF` \| `false`|CSRF is \*\*off by default\*\*'
bad=0; lines=0  # bad counts failing checks (a page per check), lines counts the wrong lines inside them
check(){ local l=$1 f=$2 tag=$3; [ -f "$f" ] || return 0
  local on=$(grep -n -E "$ON" "$f" | cut -d: -f1 | tr '\n' ' ') off=$(grep -c -E "$OFF" "$f")
  if [ "${DEF[$l]}" = off ] && [ -n "$on" ]; then echo "  WRONG $tag says on (lines $on)"; bad=$((bad+1)); lines=$((lines+$(wc -w <<<"$on"))); fi
  if [ "${DEF[$l]}" = on ] && [ "$off" != 0 ]; then echo "  WRONG $tag says off"; bad=$((bad+1)); lines=$((lines+off)); fi; }
for l in py php rb nd; do n=${LANG[$l]}; b=${BK[$l]}
  check $l "$DOCS/$n/10-middleware-security.md" "docs/$n/10"; check $l "$DOCS/$n/33-environment-variables.md" "docs/$n/33"; check $l "$DOCS/$n/37-upgrading-from-v2.md" "docs/$n/37"
  check $l "$BOOK/$b/chapters/10-middleware-security.md" "$b/10"; check $l "$BOOK/$b/chapters/33-environment-variables.md" "$b/33"; check $l "$BOOK/$b/chapters/37-upgrading-from-v2.md" "$b/37"
  # ch10 must also say what the default is, not just stop claiming "on"
  for f in "$DOCS/$n/10-middleware-security.md" "$BOOK/$b/chapters/10-middleware-security.md"; do grep -q -E "CSRF protection is ${DEF[$l]} by default" "$f" || { echo "  MISSING ${f#$DOCS/} does not state the ${DEF[$l]} default"; bad=$((bad+1)); }; done
done
# the general page covers all four ports; they agree, so use py's result
check py "$DOCS/general/04-environment-variables.md" "docs/general/04"; check py "$BOOK/book-0-understanding/chapters/04-environment-variables.md" "book-0/04"
echo "VERDICT docs-wrong=$bad (wrong lines $lines)"; [ $bad = 0 ]

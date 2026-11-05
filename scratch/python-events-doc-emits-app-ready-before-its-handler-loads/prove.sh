#!/usr/bin/env bash
# Runs python ch13 §10 "Solution" (13-events.md) as written against tina4-python through a real
# `python app.py` start: every python block goes to the path its lead-in prose names, then the app
# boots and must print the @once("app.ready") handler's "Application ready." exactly once.
# Page: DOCS=<tina4-documentation tree> | BOOK=<tina4-book tree> | default tina4-documentation origin/main.
# Framework: TINA4_PY=<tree with .venv> (default: grind-1102 stock copy of py 8fbc2254). Port PY_PORT (7610).
cd "$(dirname "$0")"; H=$PWD; . ./portguard.sh
PY=${TINA4_PY:-$HOME/.cache/tina4-worktrees/grind-1102/dmisc04/stock-tina4-python}; YP=${PY_PORT:-7610}
[ -x "$PY/.venv/bin/python" ] || { echo "ERROR no interpreter at $PY/.venv"; exit 2; }
T=$(mktemp -d); trap '[ -n "$PID" ] && kill $PID 2>/dev/null; wait 2>/dev/null; rm -rf "$T"' EXIT
if [ -n "$DOCS" ]; then cp "$DOCS/docs/python/13-events.md" $T/p.md; src="$DOCS"
elif [ -n "$BOOK" ]; then cp "$BOOK/book-1-python/chapters/13-events.md" $T/p.md; src="$BOOK"
else git -C /var/home/work/gitdir/tinaforks/tina4-documentation show origin/main:docs/python/13-events.md > $T/p.md; src="docs origin/main"; fi
echo "page: $src; framework: $PY ($("$PY/.venv/bin/python" -c 'import tina4_python as t;print(getattr(t,"__version__","?"))'))"
ok=0; bad=0; pass(){ echo "  PASS $1"; ok=$((ok+1)); }; fail(){ echo "  FAIL $1"; bad=$((bad+1)); }
app(){ A=$(mktemp -d "$T/py.XXXX"); mkdir -p $A/src/routes
  printf '%s\n' '"""Tina4 Application."""' 'from tina4_python.core import run' '' 'if __name__ == "__main__":' '    run()' > $A/app.py
  placed=$(python3 "$H/place.py" $T/p.md "10. Solution" $A) || { echo "  ERROR $placed"; exit 2; }; }
up(){ port_busy $YP && { echo "  ERROR port $YP busy before start"; exit 2; }
  ( cd $A && exec env HOME=$(mktemp -d "$T/home.XXXX") TINA4_NO_BROWSER=true TINA4_OVERRIDE_CLIENT=true TINA4_SECRET=0123456789abcdef0123456789abcdef0123456789abcdef PYTHONUNBUFFERED=1 TINA4_DEBUG=$1 TINA4_PORT=$YP "$PY/.venv/bin/python" app.py >server.log 2>&1 ) & PID=$!
  for i in $(seq 80); do curl -s -o /dev/null http://127.0.0.1:$YP/ && return 0; kill -0 $PID 2>/dev/null || break; sleep 0.25; done
  echo "  ERROR server did not start: $(tail -c 300 $A/server.log | tr '\n' ' ')"; down; exit 2; }
down(){ kill $PID 2>/dev/null; wait $PID 2>/dev/null; PID=; pkill -f "$A" 2>/dev/null; wait_port_free $YP || exit 2; }
for dbg in false true; do
  app; up $dbg; sleep 0.5; down; n=$(grep -c 'Application ready.' $A/server.log)
  [ "$n" = 1 ] && pass "A1 debug=$dbg as written ($(echo $placed)): 'Application ready.' printed once" \
               || fail "A1 debug=$dbg as written ($(echo $placed)): 'Application ready.' printed $n times"
  # control: same files, any non-routes file renamed to sort after src/routes/ (server.py:467 sorted import)
  app; for f in $placed; do case $f in src/routes/*) ;; src/*) mv $A/$f $A/src/zz_$(basename $f); c=1;; esac; done
  if [ -n "$c" ]; then up $dbg; sleep 0.5; down; n=$(grep -c 'Application ready.' $A/server.log); c=
    [ "$n" = 1 ] && pass "C1 debug=$dbg control: emit file renamed under src/zz_*: printed once" || fail "C1 debug=$dbg control: printed $n times"; fi
done
echo "result: $ok pass, $bad fail"; [ $bad = 0 ]

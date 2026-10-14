#!/bin/bash
# Posts one multipart form with tags[] twice, colour[] once, and a plain field, to each port's
# own server (python/ruby/nodejs built-in; php's Tina4\Server via `tina4php serve`, NOT php -S,
# whose native $_POST parsing is a different code path), and prints the parsed body.
# Trees default to stock: PY= PHP= RB= ND= override; ONLY="python php" narrows.
HERE=$(cd "$(dirname "$0")" && pwd); WT=$HOME/.cache/tina4-worktrees
PY=${PY:-$WT/tip-stock-py}; PHP=${PHP:-$WT/tip-stock-php}; RB=${RB:-$WT/tip-stock-rb}; ND=${ND:-$WT/tip-stock-nd}
RB_BUNDLE=${RB_BUNDLE:-$WT/rb-bundle}; ONLY=${ONLY:-python php ruby nodejs}
NODEBIN=$(dirname "$(command -v node)")
freeport() { python3 -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])'; }
for name in $ONLY; do
  run=$(mktemp -d); port=$(freeport); mkdir -p "$run/home" "$run/app"; cp -r "$HERE/$name/." "$run/app/"
  common=(HOME="$run/home" PATH="$NODEBIN:/usr/bin:/bin" TINA4_SECRET=multipart-proof-secret-0123456789abcdef
          TINA4_DEBUG=false TINA4_NO_BROWSER=true TINA4_NO_AI_PORT=true TINA4_OVERRIDE_CLIENT=true TINA4_HOST=127.0.0.1 TINA4_PORT="$port")
  case $name in
    python) tree=$PY; (cd "$run/app" && exec env -i "${common[@]}" "$PY/.venv/bin/python" app.py --managed) >"$run/srv.log" 2>&1 & ;;
    ruby) tree=$RB; (cd "$run/app" && exec env -i "${common[@]}" BUNDLE_PATH="$RB_BUNDLE" BUNDLE_GEMFILE="$RB/Gemfile" \
            "$(command -v bundle)" exec ruby -I"$RB/lib" app.rb) >"$run/srv.log" 2>&1 & ;;
    nodejs) tree=$ND; sed -i "s|TREE_ND|$ND|g" "$run/app/app.mts"
      (cd "$run/app" && exec env -i "${common[@]}" node --import "file://$ND/node_modules/tsx/dist/loader.mjs" app.mts) >"$run/srv.log" 2>&1 & ;;
    php) tree=$PHP; (cd "$run/app" && exec env -i "${common[@]:0:7}" TREE="$PHP" php "$PHP/bin/tina4php" serve 127.0.0.1:"$port") >"$run/srv.log" 2>&1 & ;;
  esac
  pid=$!; up=no
  for _ in $(seq 150); do curl -s -o /dev/null "http://127.0.0.1:$port/" 2>/dev/null && { up=yes; break; }; kill -0 $pid 2>/dev/null || break; sleep 0.1; done
  echo "== $name  tree $(git -C "$tree" rev-parse --short HEAD), $(git -C "$tree" status --porcelain | wc -l) uncommitted paths"
  if [ $up = yes ]; then
    compact() { python3 -c 'import json,sys;print(json.dumps(json.load(sys.stdin),separators=(",",":")))' 2>/dev/null || echo "(not JSON)"; }
    out=$(curl -s -F 'tags[]=red' -F 'tags[]=blue' -F 'colour[]=green' -F 'name=x' "http://127.0.0.1:$port/echo" | compact)
    echo "   multipart   $out"
    case "$out" in *'"blue"'*'"red"'*|*'"red"'*'"blue"'*) echo "   tags[] both values kept: ok";; *) echo "   tags[] lost a value: BUG";; esac
    # Control: the same fields urlencoded, the shape each port already gives a form without files.
    [ -n "$URLENC" ] && echo "   urlencoded  $(curl -s --data 'tags[]=red&tags[]=blue&colour[]=green&name=x&f[a]=1' "http://127.0.0.1:$port/echo" | compact)"
    [ -n "$URLENC" ] && echo "   query       $(curl -s "http://127.0.0.1:$port/q?tags%5B%5D=red&tags%5B%5D=blue&f%5Ba%5D=1&p=1&p=2" | compact)"
    [ -n "$URLENC" ] && echo "   nested mp   $(curl -s -F 'f[a]=1' -F 'f[b][]=2' -F 'plain=p' -F 'plain=q' "http://127.0.0.1:$port/echo" | compact)"
  else echo "   server never came up"; head -5 "$run/srv.log" | sed 's/^/   | /'; fi
  kill $pid 2>/dev/null; fuser -k "$port/tcp" >/dev/null 2>&1; wait $pid 2>/dev/null
done

#!/usr/bin/env bash
# d-cli-03 behaviour: what `tina4 build` and the nodejs/ruby framework `build` really do.
# Docker is not installed here; a `docker` shim earlier on PATH logs its argv and exits 0.
#
# Usage: CLI=<tina4 binary> ND=<tina4-nodejs tree with packages/cli/dist/bin.js built>
#        RB=<tina4-ruby tree> WORK=<throwaway dir outside the repo> ./behaviour.sh
# Prints one CASE line per run and a final BEHAVIOUR verdict; rc 1 if any expectation fails.
set -u
: "${CLI:?}" "${ND:?}" "${RB:?}" "${WORK:?}"
rm -rf "$WORK/b"; mkdir -p "$WORK/b/shim" "$WORK/b/nodebin" "$WORK/b/home"
B=$WORK/b
export HOME=$B/home                        # tina4 CLIs install skills into ~/.claude
LOG=$B/docker.argv

cat > "$B/shim/docker" <<EOF
#!/bin/sh
echo "\$*" >> "$LOG"
exit 0
EOF
cat > "$B/shim/tina4nodejs" <<EOF
#!/bin/sh
exec node "$ND/packages/cli/dist/bin.js" "\$@"
EOF
cat > "$B/shim/tina4ruby" <<EOF
#!/bin/sh
exec ruby "$RB/exe/tina4ruby" "\$@"
EOF
cp "$CLI" "$B/shim/tina4"
chmod +x "$B/shim/"*
ln -s "$(command -v node)" "$B/nodebin/node"
ln -s "$(command -v npx)" "$B/nodebin/npx"
# No-docker PATH: same wrappers, docker removed.
mkdir -p "$B/nodocker"; for f in tina4 tina4nodejs tina4ruby; do cp "$B/shim/$f" "$B/nodocker/$f"; done
P_DOCKER=$B/shim:$B/nodebin:/usr/bin:/bin
P_NODOCKER=$B/nodocker:$B/nodebin:/usr/bin:/bin
PATH=$P_NODOCKER command -v docker >/dev/null && { echo "real docker on PATH; refusing"; exit 2; }

fails=0; n=0
mkapp() { # lang dir dockerfile(yes/no)
  rm -rf "$2"; mkdir -p "$2"
  case $1 in
    nd) echo '{"name":"x","version":"1.0.0","dependencies":{"tina4-nodejs":"*"}}' > "$2/package.json";;
    rb) printf 'source "https://rubygems.org"\ngem "tina4ruby"\n' > "$2/Gemfile";;
  esac
  [ "$3" = yes ] && printf 'FROM scratch\n' > "$2/Dockerfile"
  return 0
}
run() { # label path expect_rc expect_argv_regex|NONE expect_out_regex cmd...
  local label=$1 path=$2 erc=$3 eargv=$4 eout=$5; shift 5
  : > "$LOG"
  out=$(PATH=$path "$@" 2>&1); rc=$?
  argv=$(cat "$LOG"); dist=absent; [ -e dist ] && dist=PRESENT
  ok=1
  [ "$rc" = "$erc" ] || ok=0
  if [ "$eargv" = NONE ]; then [ -z "$argv" ] || ok=0; else echo "$argv" | grep -Eq "$eargv" || ok=0; fi
  echo "$out" | grep -Eq "$eout" || ok=0
  [ $dist = absent ] || ok=0
  n=$((n+1)); [ $ok = 1 ] || fails=$((fails+1))
  printf 'CASE %-4s %-48s rc=%s docker_argv=[%s] dist/=%s :: %s\n' \
    "$([ $ok = 1 ] && echo ok || echo FAIL)" "$label" "$rc" "$argv" "$dist" \
    "$(echo "$out" | grep -E "$eout" | head -1 | sed 's/^ *//')"
}

for lang in nd rb; do
  fwcli=$([ $lang = nd ] && echo tina4nodejs || echo tina4ruby)
  app=$B/${lang}app
  for via in "$fwcli build" "tina4 build"; do
    mkapp $lang "$app" no;  cd "$app"
    run "$lang: '$via', no Dockerfile"            "$P_DOCKER"   1 NONE '✗ No Dockerfile found' $via
    mkapp $lang "$app" yes; cd "$app"
    run "$lang: '$via', Dockerfile, docker shim"  "$P_DOCKER"   0 "^build -t ${lang}app:latest -f Dockerfile \.$" 'Built image' $via
    run "$lang: '$via', Dockerfile, no docker"    "$P_NODOCKER" 1 NONE 'docker was not found on PATH' $via
  done
done

# SCSS step of the Rust CLI runs first, writes src/public/css, still no dist/.
mkapp nd "$B/ndapp" yes; cd "$B/ndapp"; mkdir -p src/scss; printf '$c: red;\nbody { color: $c; }\n' > src/scss/app.scss
run "nd: 'tina4 build' compiles SCSS then docker" "$P_DOCKER" 0 "^build -t ndapp:latest" 'Built image' tina4 build
css=absent; [ -s src/public/css/app.min.css ] && css=present
n=$((n+1)); [ $css = present ] || fails=$((fails+1)); echo "CASE $([ $css = present ] && echo ok || echo FAIL)   nd: src/public/css/app.min.css after tina4 build: $css ($(tr -d '\n' < src/public/css/app.min.css 2>/dev/null))"

# 34-deployment §13 zero-downtime script on a plain server (no docker): set -e aborts at tina4 build.
mkapp nd "$B/ndapp" no; cd "$B/ndapp"
out=$(PATH=$P_NODOCKER bash -c 'set -e; tina4 build; echo REACHED-tina4-migrate' 2>&1); rc=$?
ok=1; [ $rc != 0 ] && ! echo "$out" | grep -q REACHED || ok=0
n=$((n+1)); [ $ok = 1 ] || fails=$((fails+1))
echo "CASE $([ $ok = 1 ] && echo ok || echo FAIL)   nd: §13 set -e script, plain server: rc=$rc, migrate step reached: $(echo "$out" | grep -q REACHED && echo yes || echo no)"

# Fixed text: "`tina4 deploy docker` writes one" — then build uses it.
mkapp nd "$B/ndapp" no; cd "$B/ndapp"
PATH=$P_DOCKER tina4 deploy docker >/dev/null 2>&1; drc=$?
df=absent; [ -s Dockerfile ] && df=present
n=$((n+1)); [ $df = present ] || fails=$((fails+1)); echo "CASE $([ $df = present ] && echo ok || echo FAIL)   nd: tina4 deploy docker rc=$drc, Dockerfile $df"
run "nd: 'tina4 build' with deploy-docker Dockerfile" "$P_DOCKER" 0 "^build -t ndapp:latest -f Dockerfile \.$" 'Run: docker run -p 7148:7148 ndapp:latest' tina4 build

# Informational (not counted): nodejs project WITH node_modules -> Rust CLI runs `npx tina4nodejs` (f-cli-27).
mkapp nd "$B/ndapp" yes; cd "$B/ndapp"; mkdir -p node_modules/.bin
ln -s "$ND/packages/cli/dist/bin.js" node_modules/.bin/tina4nodejs
: > "$LOG"; out=$(PATH=$P_DOCKER tina4 build 2>&1); rc=$?
echo "INFO nd: 'tina4 build' via npx (node_modules present): rc=$rc docker_argv=[$(cat "$LOG")] output=[$(echo "$out" | tr '\n' ' ' | cut -c1-80)]"

echo "BEHAVIOUR: $([ $fails = 0 ] && echo PASS || echo FAIL) $((n-fails))/$n cases as claimed (cli=$("$CLI" --version 2>&1))"
[ $fails = 0 ]

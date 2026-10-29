#!/bin/bash
# Usage: repro.sh <tina4 binary>. A php project whose vendor/ exists but holds no
# PATH is cut to /usr/bin:/bin so a globally installed tina4php (composer global) cannot mask it.
# bin/tina4php (the case tina4#127 hit). Runs `tina4 serve` and `tina4 routes` there,
# plus two controls. Prints one line per case; exits non-zero if a case is wrong.
BIN=$(readlink -f "$1"); fails=0
mk() { # dir, vendor-shape: none | empty | full
  mkdir -p "$1"; cd "$1"
  printf '{"require":{"tina4stack/tina4php":"*"}}\n' > composer.json
  printf 'TINA4_SECRET=%s\n' "$(head -c 24 /dev/urandom | base64)" > .env
  case $2 in
    empty) mkdir -p vendor/composer ;;
    full) mkdir -p vendor/bin; printf '#!/usr/bin/env php\n<?php echo "STUB tina4php ", implode(" ", array_slice($argv,1)), "\\n";\n' > vendor/bin/tina4php ;;
  esac
}
check() { # name, want-regex, reject-regex, cmd...
  local name=$1 want=$2 reject=$3; shift 3
  out=$(env PATH=/usr/bin:/bin HOME="$T/home" TINA4_NO_BROWSER=true timeout 20 "$BIN" "$@" 2>&1)
  if grep -qE "$want" <<<"$out" && ! grep -qE "$reject" <<<"$out"; then echo "PASS $name"; r=0; else echo "FAIL $name"; r=1; fi
  grep -E 'spawn|Failed|not installed|tina4php|STUB' <<<"$out" | head -3 | sed 's/^/    /'
  return $r
}
T=$(mktemp -d)
# The defect: vendor/ present, vendor/bin/tina4php absent.
(mk "$T/empty" empty; check serve-vendor-without-tina4php "vendor/bin/tina4php.*composer install" "program not found|No such file" serve --no-browser --port 7491)
fails=$((fails+$?))
(mk "$T/empty2" empty; check routes-vendor-without-tina4php "vendor/bin/tina4php.*composer install" "program not found|No such file" routes)
fails=$((fails+$?))
# Control: no vendor/ at all, already says to run composer install.
(mk "$T/none" none; check serve-no-vendor "composer install" "program not found|No such file" serve --no-browser --port 7492)
fails=$((fails+$?))
# Control: tina4php present, delegation reaches it.
(mk "$T/full" full; check routes-with-tina4php "STUB tina4php routes" "program not found|No such file" routes)
fails=$((fails+$?))
rm -rf "$T"; exit $fails

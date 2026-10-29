#!/usr/bin/env bash
# d-cli-04. Shows the tina4 client hands `migrate --rollback` etc. to the framework CLI unchanged, so the
# rejection prove.sh records is what a reader typing `tina4 ...` gets.
# Each port's framework CLI is replaced by a shim that logs its argv and then runs the real CLI (cli.sh).
#   TINA4=<tina4 binary>  default: tina4 on PATH.  PATH is scrubbed to the shims + /usr/bin:/bin + node.
cd "$(dirname "$0")"; HERE=$PWD; export HOME_REAL=$HOME
TINA4=${TINA4:-$(command -v tina4)}; echo "client: $TINA4 ($($TINA4 --version 2>&1 | head -1))"
NODEDIR=$(dirname "$(command -v node)")
SECRET=0123456789abcdef0123456789abcdef0123456789abcdef; fails=0
for p in py php rb nd; do for a in "migrate --rollback" "migrate --status" "routes --method POST" "migrate:rollback"; do
  T=$(mktemp -d); mkdir -p $T/shim $T/p/migrations $T/p/src/routes; cd $T/p
  for n in tina4python tina4ruby tina4nodejs; do
    printf '#!/bin/sh\nprintf "%%s|" "$@" > %s/argv.log\nexec bash %s/cli.sh %s "$@"\n' $T $HERE \
      $(case $n in tina4python) echo py;; tina4ruby) echo rb;; *) echo nd;; esac) > $T/shim/$n; chmod +x $T/shim/$n; done
  case $p in
    py)  : > app.py;;
    rb)  echo 'source "https://rubygems.org"' > Gemfile; : > app.rb;;
    nd)  echo '{"name":"x","dependencies":{"tina4-nodejs":"*"}}' > package.json; : > app.ts;;
    php) echo '{"require":{"tina4stack/tina4php":"*"}}' > composer.json; : > index.php; mkdir -p vendor bin
         printf '<?php file_put_contents("%s/argv.log", implode("|", array_slice($argv,1))."|"); passthru("bash %s/cli.sh php ".implode(" ", array_map("escapeshellarg", array_slice($argv,1))), $rc); exit($rc);\n' $T $HERE > bin/tina4php;;
  esac
  read -r -a argv <<<"$a"
  out=$(HOME=$T PATH=$T/shim:/usr/bin:/bin:$NODEDIR TINA4_SECRET=$SECRET TINA4_DATABASE_URL=sqlite:///$T/p/app.db timeout 60 "$TINA4" "${argv[@]}" 2>&1); rc=$?
  got=$(cat $T/argv.log 2>/dev/null); want="${a// /|}|"
  [ "$got" = "$want" ] && v=verbatim || { v="NOT-VERBATIM(got '$got')"; fails=$((fails+1)); }
  echo "$p tina4 $a -> framework argv $v rc=$rc: $(grep -v -E 'level|Experimental|^\s*$' <<<"$out" | head -1 | cut -c1-80)"
  cd $HERE; rm -rf $T
done; done
echo "VERDICT not-verbatim=$fails"; [ $fails = 0 ]

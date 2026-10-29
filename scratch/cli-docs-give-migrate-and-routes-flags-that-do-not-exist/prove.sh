#!/usr/bin/env bash
# d-cli-04. Runs every `tina4 migrate*` / `tina4 routes` command the CLI, routing, database, index and
# architecture pages print, verbatim, through that language's real framework CLI -- which is what the
# tina4 client forwards to unchanged (tina4 src/main.rs:314-323, :526). Each command gets a fresh project
# with a SQLite DB and its own HOME. A command is BAD when the CLI's own parser rejects it
# (Unknown option / Unknown command / needs a value), ok otherwise.
#   DOCS=<tina4-documentation tree>  BOOK=<tina4-book tree>   default: each repo's origin/main, exported fresh
#   VERBOSE=1 also lists the ok commands.   Exit 0 only when bad=0.
cd "$(dirname "$0")"; HERE=$PWD; export HOME_REAL=$HOME
G=${TINAFORKS:-/var/home/work/gitdir/tinaforks}
TMPS=(); trap 'rm -rf "${TMPS[@]}"' EXIT
exp(){ local t; t=$(mktemp -d); TMPS+=("$t"); git -C $G/$1 archive origin/main $2 | tar -x -C $t; echo $t; }
[ -n "$DOCS" ] || { DOCS=$(exp tina4-documentation docs); echo "DOCS = tina4-documentation origin/main $(git -C $G/tina4-documentation rev-parse --short origin/main)"; }
[ -n "$BOOK" ] || { BOOK=$(exp tina4-book .);           echo "BOOK = tina4-book origin/main $(git -C $G/tina4-book rev-parse --short origin/main)"; }
W=${TINA4_WT:-$HOME/.cache/tina4-worktrees}
for p in python php ruby nodejs; do echo "CLI  $p $(git -C $W/dcli04-stock-$p rev-parse --short HEAD 2>/dev/null)"; done
declare -A PORT=([python]=py [php]=php [ruby]=rb [nodejs]=nd [book-1-python]=py [book-2-php]=php [book-3-ruby]=rb [book-4-nodejs]=nd)
files=()
for l in python php ruby nodejs; do for f in 31-cli 02-routing 05-database index; do files+=("$DOCS/docs/$l/$f.md|${PORT[$l]}"); done; done
for b in book-1-python book-2-php book-3-ruby book-4-nodejs; do for f in 31-cli 02-routing 05-database; do files+=("$BOOK/$b/chapters/$f.md|${PORT[$b]}"); done; done
for p in py php rb nd; do files+=("$DOCS/docs/general/02-architecture.md|$p" "$BOOK/book-0-understanding/chapters/02-architecture.md|$p"); done
SECRET=0123456789abcdef0123456789abcdef0123456789abcdef
ok=0; bad=0
for e in "${files[@]}"; do f=${e%|*}; p=${e#*|}; [ -f "$f" ] || continue
  while IFS= read -r c; do
    T=$(mktemp -d); mkdir -p $T/migrations $T/src/routes
    printf 'TINA4_DATABASE_URL=sqlite:///%s/app.db\nDATABASE_URL=sqlite:///%s/app.db\nTINA4_SECRET=%s\n' $T $T $SECRET > $T/.env
    read -r -a argv <<<"${c#tina4 }"
    out=$(cd $T && HOME=$T TINA4_SECRET=$SECRET TINA4_DATABASE_URL=sqlite:///$T/app.db timeout 60 bash $HERE/cli.sh $p "${argv[@]}" 2>&1); rc=$?
    rm -rf $T
    rel=${f#$DOCS/}; rel=${rel#$BOOK/}
    if grep -q -E 'Unknown option|Unknown command|needs a value' <<<"$out"; then
      bad=$((bad+1)); echo "BAD  $p $rel: $c -> rc=$rc $(grep -m1 -E 'Unknown|needs a value' <<<"$out")"
    else ok=$((ok+1)); [ -n "$VERBOSE" ] && echo "ok   $p $rel: $c (rc=$rc)"; fi
  done < <(python3 $HERE/doccmds.py "$f")
done
echo "VERDICT ok=$ok bad=$bad"; [ $bad = 0 ]

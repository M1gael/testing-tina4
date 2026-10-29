#!/usr/bin/env bash
# d-orm-01: nodejs docs call async Database/ORM APIs without `await`.
# 1. counts every un-awaited call scan.py finds in the nodejs pages of both repos (minus excluded.txt);
# 2. serves five of the docs' own blocks verbatim (only model import paths rewritten) on tina4-nodejs
#    and checks each returns what the page says it returns. Runs for the docs tree and the book tree.
# DOCS=<tina4-documentation tree> BOOK=<tina4-book tree>; default: each repo's origin/main (stock).
# NODEJS=<built tina4-nodejs checkout>; default ~/.cache/tina4-worktrees/dorm01-stock-nodejs.
# PORT (default 7463). The app runs from a mktemp copy; nothing heavy is kept in this directory.
cd "$(dirname "$0")"; H=$PWD; P=${PORT:-7463}
TF=/var/home/work/gitdir/tinaforks
NODEJS=${NODEJS:-$HOME/.cache/tina4-worktrees/dorm01-stock-nodejs}
[ -f "$NODEJS/packages/orm/dist/index.js" ] || { echo "no built tina4-nodejs at $NODEJS (npm run build --workspaces)"; exit 2; }
if [ -z "$DOCS" ]; then DOCS=$(mktemp -d); TMPD="$TMPD $DOCS"; git -C $TF/tina4-documentation archive origin/main docs | tar -x -C $DOCS
  dsha=$(git -C $TF/tina4-documentation rev-parse --short origin/main); else dsha=$(git -C $DOCS rev-parse --short HEAD 2>/dev/null)+wt; fi
if [ -z "$BOOK" ]; then BOOK=$(mktemp -d); TMPD="$TMPD $BOOK"; git -C $TF/tina4-book archive origin/main book-0-understanding book-4-nodejs | tar -x -C $BOOK
  bsha=$(git -C $TF/tina4-book rev-parse --short origin/main); else bsha=$(git -C $BOOK rev-parse --short HEAD 2>/dev/null)+wt; fi
echo "tina4-nodejs $(git -C $NODEJS log -1 --format=%h)  docs $dsha ($DOCS)  book $bsha ($BOOK)"

# ---- 1. count (scope: docs/nodejs, docs/general, book-0 + book-4 chapters; 36-releases is history)
files=$(ls $DOCS/docs/nodejs/*.md $DOCS/docs/general/*.md $BOOK/book-0-understanding/chapters/*.md \
           $BOOK/book-4-nodejs/chapters/*.md | grep -v '/36-releases\.md$')
all=$(python3 scan.py $files | sed -e "s#^$DOCS/##" -e "s#^$BOOK/##")
ex=$(grep -v '^#' excluded.txt | grep .)
nall=$(grep -c . <<<"$all"); left=$(grep -vEf <(echo "$ex") <<<"$all"); nleft=$(grep -c . <<<"$left")
echo "un-awaited async calls: $nall found, $((nall - nleft)) excluded (excluded.txt), $nleft to fix"
[ "$nleft" -gt 0 ] && cut -d: -f1 <<<"$left" | sort | uniq -c | sed 's/^/   /'
[ -n "$VERBOSE" ] && echo "$left"

# ---- 2. samples
APP=$(mktemp -d); mkdir -p $APP/node_modules; ln -s "$NODEJS" $APP/node_modules/tina4-nodejs; cp app/app.mts $APP/
trap 'nd_stop 2>/dev/null; rm -rf $APP $TMPD' EXIT
port_busy(){ curl -s -o /dev/null --max-time 1 "http://127.0.0.1:$1/" && return 0; ss -ltn 2>/dev/null | grep -q ":$1 "; }
nd_start(){ port_busy $P && { echo "PORT $P BUSY before start"; return 1; }
  ( cd $APP && HOME=$(mktemp -d) TINA4_DEBUG=false TINA4_DATABASE_URL=sqlite:///$APP/data/app.db \
    TINA4_SECRET=0123456789abcdef0123456789abcdef0123456789abcdef PORT=$P exec node --no-warnings app.mts >server.log 2>&1 ) &
  NDPID=$!; for i in $(seq 75); do curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:$P/" | grep -qv 000 && return 0
    kill -0 $NDPID 2>/dev/null || break; sleep 0.2; done; echo "server did not start"; tail -20 $APP/server.log; return 1; }
nd_stop(){ [ -n "$NDPID" ] || return 0; kill $NDPID 2>/dev/null; wait $NDPID 2>/dev/null; NDPID=
  for i in $(seq 60); do port_busy $P || return 0; sleep 0.25; done; echo "PORT $P STILL BUSY after stop"; }
bad=0
samples(){ # <chapter dir> <label>
  local C=$1 g=$APP/gen fix='s#"(\.\./)+models/(\w+)\.js"#"./models/\2.ts"#'
  rm -rf $g $APP/data; mkdir -p $g/models $APP/data
  python3 docblock.py $C/06-orm.md "hasMany" 1 > $g/models/Author.ts
  python3 docblock.py $C/06-orm.md "hasMany" 2 > $g/models/BlogPost.ts
  python3 docblock.py $C/06-orm.md "2. Defining a Model" 1 > $g/models/Note.ts
  python3 docblock.py $C/05-database.md "3. Getting the Database Object" 1 > $g/s1.ts
  python3 docblock.py $C/06-orm.md "hasMany" 3 | sed -E "$fix" > $g/s2.ts
  python3 docblock.py $C/06-orm.md "belongsTo" 1 | sed -E "$fix" > $g/s3.ts
  { echo 'import Note from "./models/Note.ts";'; python3 docblock.py $C/06-orm.md "create -- Build and Save in One Step" 1
    echo 'export const result = note;'; } > $g/s4.ts
  python3 docblock.py $C/07-query-builder.md "List Endpoint with Filters" 1 > $g/s5.ts
  nd_start || { bad=$((bad+5)); return; }
  local u=http://127.0.0.1:$P
  check "$2 ch05 getConnection   GET /api/test-db " "$(curl -s $u/api/test-db)" 'b[0]["answer"]==2 if isinstance(b,list) else b["answer"]==2'
  check "$2 ch06 hasMany         GET /api/authors/1" "$(curl -s $u/api/authors/1)" 'len(b["posts"])==2'
  check "$2 ch06 belongsTo       GET /api/posts/1  " "$(curl -s $u/api/posts/1)" 'b["author"]["name"]=="Alice"'
  check "$2 ch06 Note.create     note is a saved Note" "$(curl -s $u/s4)" 'b["isNote"] and isinstance(b["id"],int)'
  check "$2 ch07 qb.count/get    GET /api/products " "$(curl -s $u/api/products)" 'b["total"]==3 and len(b["products"])==3'
  [ -n "$VERBOSE" ] && grep -E 'ERROR|Error' $APP/server.log | cut -c1-200 | sort -u | head
  nd_stop
}
check(){ # <label> <body> <python expr over b>
  if python3 -c "import json,sys; b=json.loads(sys.argv[1]); sys.exit(0 if ($3) else 1)" "$2" 2>/dev/null
  then echo "  ok   $1"; else echo "  FAIL $1 -> $(head -c 160 <<<"$2" | tr '\n' ' ')"; bad=$((bad+1)); fi
}
samples $DOCS/docs/nodejs docs; samples $BOOK/book-4-nodejs/chapters book
echo "sample failures: $bad of 10"
[ "$nleft" = 0 ] && [ "$bad" = 0 ] && echo "VERDICT awaited" || { echo "VERDICT un-awaited"; exit 1; }

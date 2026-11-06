#!/bin/bash
# Revert one piece of the fix at a time (nodejs + php docs page) and confirm prove.py goes red.
# Pieces: options table, section-4 output, section-5 output, section-8 commands, exercise commands, php output.
W=${W:-$HOME/.cache/tina4-worktrees/docs-cli05}
G=$(mktemp -d); trap 'rm -rf $G' EXIT
piece(){ # $1 lang  $2 python expression mutating t (fixed) back towards stock
  rm -rf $G/t; mkdir -p $G/t/docs; cp -r $W/docs/docs/{python,php,ruby,nodejs} $G/t/docs/ 2>/dev/null
  python3 -I - "$G/t/docs/$1/31-cli.md" "$2" <<'P'
import sys; p=sys.argv[1]; t=open(p).read(); exec(sys.argv[2]); open(p,'w').write(t)
P
  out=$(python3 -I prove.py $G/t | tail -1); echo "$3: $out"
}
piece nodejs 't=t.replace("| `--no-migration` | Skip","| `--with-route` | Also generate a CRUD route file | `--with-route` |\n| `--no-migration` | Skip",1)' "options table"
piece nodejs 't=t.replace("Created src/models/Product.ts\n","Created src/orm/Product.ts\n",1)' "section 4 output"
piece nodejs 't=t.replace("Created src/routes/api/products/post.ts\n","",1)' "section 5 output"
piece nodejs 't=t.replace("tina4 generate model Product\ntina4 generate route products","tina4 generate model Product --with-route --with-migration",1)' "section 8 commands"
piece nodejs 't=t.replace("tina4 generate model Customer\ntina4 generate route customers","tina4 generate model Customer --with-route --with-migration",1)' "exercise commands"
piece php 't=t.replace("Created tests/OrderTest.php\n","",1)' "php route output"

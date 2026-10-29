#!/usr/bin/env bash
# Per-piece gating: put back ONE stock piece into the fixed pages and show prove.sh goes red on that check alone.
# FIXED=<fixed tina4-documentation tree> (default ~/.cache/tina4-worktrees/docfix-dapi01-docs).
cd "$(dirname "$0")"; FIXED=${FIXED:-$HOME/.cache/tina4-worktrees/docfix-dapi01-docs}; T=$(mktemp -d); trap 'rm -rf "$T"' EXIT
for p in nodejs/25-wsdl-soap.md nodejs/13-events.md ruby/25-wsdl-soap.md; do mkdir -p $T/stock/$(dirname $p)
  git -C /var/home/work/gitdir/tinaforks/tina4-documentation show origin/main:docs/$p > $T/stock/$p; done
# swap <page> <section number> : fixed page with that "## N." section taken from stock
swap(){ python3 - "$FIXED/docs/$1" "$T/stock/$1" "$2" <<'PY'
import sys, re
fx, st, n = open(sys.argv[1]).read(), open(sys.argv[2]).read(), sys.argv[3]
def cut(s):
    m = re.search(r"^## %s\. .*$" % n, s, re.M); e = re.search(r"^## \d+\. ", s[m.end():], re.M)
    return m.start(), m.end() + (e.start() if e else len(s) - m.end())
a, b = cut(fx); c, d = cut(st); sys.stdout.write(fx[:a] + st[c:d] + fx[b:])
PY
}
# edit <page> <old> <new> : fixed page with one literal string replaced
edit(){ python3 -c 'import sys; s=open(sys.argv[1]).read(); assert s.count(sys.argv[2])==1; sys.stdout.write(s.replace(sys.argv[2], sys.argv[3]))' "$FIXED/docs/$1" "$2" "$3"; }
# run <label> <lang> <var> <file> <expected FAIL id>: prove.sh on the fixed tree with one page replaced; GATED when
# the only failing check is the expected one
bad=0
run(){ local label=$1 lang=$2 var=$3 file=$4 want=$5 got; echo "== stock $label"
  local out; out=$(env DOCS="$FIXED" "$var=$file" ./prove.sh $lang 2>&1 | grep -E '^  FAIL'); [ -n "$out" ] && cut -c1-220 <<<"$out"
  got=$(printf '%s\n' "$out" | grep . | sed -E 's/^  FAIL ([A-Z][0-9]+( 13\/[0-9]+)?).*/\1/' | sort -u | tr '\n' ' ')
  [ "$got" = "$want " ] && echo "   GATED: only $want red" || { echo "   NOT GATED: wanted '$want', got '$got'"; bad=$((bad+1)); }; }
swap nodejs/25-wsdl-soap.md 2 > $T/a; run "nd25 section 2 (client)" nd ND25 $T/a N1
swap nodejs/25-wsdl-soap.md 3 > $T/a; run "nd25 section 3 (decorator)" nd ND25 $T/a N2
swap nodejs/25-wsdl-soap.md 4 > $T/a; run "nd25 section 4 (publish)" nd ND25 $T/a N3
swap nodejs/25-wsdl-soap.md 7 > $T/a; run "nd25 section 7 (solution)" nd ND25 $T/a N4
edit nodejs/25-wsdl-soap.md $'export const secure = false;\n\nexport default async (req, res) => {\n    return res.xml(await currencyService' $'export default async (req, res) => {\n    return res.xml(await currencyService' > $T/a; run "nd25 4 without secure=false only" nd ND25 $T/a N3
swap nodejs/13-events.md 9 > $T/a; run "nd13 section 9 (app.ts)" nd ND13 $T/a "N5 13/9"
swap nodejs/13-events.md 11 > $T/a; run "nd13 section 11 (app.ts)" nd ND13 $T/a "N5 13/11"
swap ruby/25-wsdl-soap.md 3 > $T/a; run "rb25 section 3 (define)" rb RB25 $T/a R1
swap ruby/25-wsdl-soap.md 4 > $T/a; run "rb25 section 4 (mount)" rb RB25 $T/a R1
edit ruby/25-wsdl-soap.md $'  response.xml(CalculatorService.new(request).handle)\nend.no_auth' $'  response.xml(CalculatorService.new(request).handle)\nend' > $T/a; run "rb25 4 without .no_auth only" rb RB25 $T/a R1
swap ruby/25-wsdl-soap.md 8 > $T/a; run "rb25 section 8 (fields/lists)" rb RB25 $T/a R2
swap ruby/25-wsdl-soap.md 9 > $T/a; run "rb25 section 9 (fault)" rb RB25 $T/a R3
echo "GATE not_gated=$bad"; [ $bad = 0 ]

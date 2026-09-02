#!/usr/bin/env bash
# Proves f-cli-02 and f-cli-03 on the STOCK, INSTALLED tina4 CLI, then proves the
# candidate fix closes both without introducing the leak that the obvious spelling
# of the fix does introduce.
#
# Exit 0  = stock is broken and the fix closes it, exactly as the ledger says.
# Exit 2  = something no longer matches; the row needs re-reading before it is trusted.
#
# Needs: tina4 on PATH, npm, network. Nothing here touches the fork.
set -u

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT
FAIL=0
say()  { printf '\n=== %s ===\n' "$1"; }
want() { # want <label> <expected-exit> <actual-exit>
  if [ "$2" = "$3" ]; then printf '  ok   %s (exit %s)\n' "$1" "$3"
  else printf '  FAIL %s: expected exit %s, got %s\n' "$1" "$2" "$3"; FAIL=1; fi
}

printf 'tina4 CLI: %s\n' "$(tina4 --version 2>&1 | head -1)"

say "1. scaffold on stock"
cd "$WORK" && printf 'n\n' | tina4 init js app >/dev/null 2>&1
APP="$WORK/app"; cd "$APP" || { echo "scaffold failed"; exit 2; }
printf 'tina4js: %s   vite: %s   typescript: %s\n' \
  "$(node -p "require('$APP/node_modules/tina4js/package.json').version" 2>/dev/null)" \
  "$(node -p "require('$APP/node_modules/vite/package.json').version" 2>/dev/null)" \
  "$(npx tsc --version 2>/dev/null | awk '{print $2}')"
[ -f src/vite-env.d.ts ] && { echo "  NOTE: this CLI already ships src/vite-env.d.ts - the defect is fixed upstream"; exit 2; }

say "2. f-cli-02 - src/main.ts does not type-check"
npx tsc --noEmit > "$WORK/o1" 2>&1; want "tsc --noEmit fails" 2 "$?"
grep -c "TS2339: Property 'glob' does not exist on type 'ImportMeta'" "$WORK/o1" | grep -qx 2 \
  && echo "  ok   two TS2339 on import.meta.glob" || { echo "  FAIL glob errors"; FAIL=1; }
grep -q "TS2339: Property 'env' does not exist on type 'ImportMeta'" "$WORK/o1" \
  && echo "  ok   one TS2339 on import.meta.env" || { echo "  FAIL env error"; FAIL=1; }
sed 's/^/       /' "$WORK/o1"

say "3. f-cli-03 - vite.config.ts, as an editor sees it"
# tsconfig "include" is src/ only, so plain tsc never opens this file. This is the
# inferred project an editor falls back to.
npx tsc --noEmit --target ES2020 --module ESNext --moduleResolution bundler \
  --skipLibCheck vite.config.ts > "$WORK/o2" 2>&1; want "vite.config.ts fails" 2 "$?"
for code in "TS2307" "TS2339" "TS2769"; do
  grep -q "$code" "$WORK/o2" && echo "  ok   $code present" || { echo "  FAIL $code missing"; FAIL=1; }
done
sed 's/^/       /' "$WORK/o2"

say "4. the obvious fix, and why it is the wrong one"
# Adding "types": ["vite/client"] clears the errors and silently disarms every
# other @types/* package. Shown against @types/node, which section 5 needs anyway.
npm i -D @types/node >/dev/null 2>&1
printf 'export const mode = process.env.NODE_ENV;\n' > src/probe-node.ts
python3 - <<'PY'
import json; d=json.load(open('tsconfig.json')); d['compilerOptions']['types']=['vite/client']
json.dump(d, open('tsconfig.json','w'), indent=2)
PY
npx tsc --noEmit > "$WORK/o3" 2>&1; want '"types" array breaks @types/node' 2 "$?"
grep -q "TS2591: Cannot find name 'process'" "$WORK/o3" \
  && echo "  ok   TS2591 - @types/node no longer reaches the project" || { echo "  FAIL"; FAIL=1; }

say "5. the candidate fix"
# Browser project takes no ambient @types/*; vite/client arrives by triple-slash
# reference, which still resolves under "types": []. vite.config.ts is a Node
# file and gets its own project.
printf '/// <reference types="vite/client" />\n' > src/vite-env.d.ts
python3 - <<'PY'
import json
t = json.load(open('tsconfig.json'))
t['compilerOptions']['types'] = []
t['include'] = ['src/**/*.ts', 'tests/**/*.ts']
json.dump(t, open('tsconfig.json','w'), indent=2)
json.dump({"compilerOptions": {"target":"ES2022","module":"ESNext","moduleResolution":"bundler",
  "strict":True,"skipLibCheck":True,"lib":["ES2022"],"noEmit":True},
  "include":["vite.config.ts"]}, open('tsconfig.node.json','w'), indent=2)
p = json.load(open('package.json'))
p['scripts']['typecheck'] = 'tsc --noEmit && tsc -p tsconfig.node.json --noEmit'
json.dump(p, open('package.json','w'), indent=2)
PY
sed -i "s|import { defineConfig } from 'vite';|import { defineConfig } from 'vitest/config';|" vite.config.ts
rm -f src/probe-node.ts
npm run typecheck > "$WORK/o4" 2>&1; want "both projects type-check" 0 "$?"

say "6. the leak the fix must not introduce"
# @types/node is a devDependency for vite.config.ts. Ambient in the browser
# project it redefines setTimeout, and correct browser code stops compiling.
printf 'const id: number = setTimeout(() => {}, 1);\nexport const probe = id;\n' > src/probe-dom.ts
npx tsc --noEmit > "$WORK/o5" 2>&1; want "browser setTimeout still returns number" 0 "$?"
python3 -c "
import json; d=json.load(open('tsconfig.json')); del d['compilerOptions']['types']
json.dump(d, open('tsconfig.json','w'), indent=2)"
npx tsc --noEmit > "$WORK/o6" 2>&1; want 'without "types": [] it leaks' 2 "$?"
grep -q "TS2322: Type 'Timeout' is not assignable to type 'number'" "$WORK/o6" \
  && echo "  ok   TS2322 - Node's setTimeout reached the browser tree" || { echo "  FAIL"; FAIL=1; }
sed 's/^/       /' "$WORK/o6"

say "verdict"
if [ "$FAIL" = 0 ]; then echo "  PASS - stock is broken, the fix closes it, and it does not leak"; exit 0
else echo "  MISMATCH - re-read the ledger row before trusting it"; exit 2; fi

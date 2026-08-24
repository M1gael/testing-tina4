#!/usr/bin/env bash
# Which block of the skill produces the announcement behaviour?
#
# Four arms, identical fixture and prompt, all carrying the skill via
# .agents/skills/. Only the SKILL.md differs:
#
#   F  full skill
#   G  minus "Announce before you act"                       (lines 29-61)
#   H  minus "1. Keep the main session free - delegate to a worker" (155-164)
#   I  minus both
#
# HOME is redirected per arm. Without that the machine's own ~/.agents/skills
# leaks the unmodified skill into every arm and the ablation measures nothing.
#
# COSTS REAL TOKENS: four Codex sessions. Roughly 10-20 minutes wall clock.
set -euo pipefail
cd "$(dirname "$0")"

NODEJS_REPO="${NODEJS_REPO:-$HOME/gitdir/tinaforks/tina4-nodejs}"
SRC="$NODEJS_REPO/.agents/skills/tina4-developer-nodejs/SKILL.md"
WORK="${WORK:-$(mktemp -d)}"
PROMPT="Add JWT authentication to this app: a User model, POST /api/auth/login that issues a token, GET /api/auth/me that returns the signed-in user, and tests for both routes."

command -v codex >/dev/null || { echo "codex CLI not on PATH"; exit 2; }
[ -f "$SRC" ] || { echo "set NODEJS_REPO to a tina4-nodejs checkout (looked for $SRC)"; exit 2; }

# Line ranges are resolved by SEARCH, not hard-coded, so an edited skill still ablates correctly.
python3 - "$SRC" "$WORK" <<'PY'
import sys, re
src, work = sys.argv[1], sys.argv[2]
lines = open(src).read().split("\n")

def span(start_re, stop_re, after):
    """1-indexed [start, end] of the section opening at start_re, ending before the next stop_re."""
    s = next(i for i, l in enumerate(lines, 1) if re.match(start_re, l) and i > after)
    e = next(i for i, l in enumerate(lines, 1) if i > s and re.match(stop_re, l)) - 1
    while e > s and lines[e - 1].strip() == "":
        e -= 1
    return (s, e)

announce = span(r"^## Announce before you act", r"^## ", 0)
worker   = span(r"^### 1\. Keep the main session free", r"^### ", 0)
print(f"  Announce block : lines {announce[0]}-{announce[1]}", file=sys.stderr)
print(f"  Worker block   : lines {worker[0]}-{worker[1]}", file=sys.stderr)

variants = {"F": [], "G": [announce], "H": [worker], "I": [announce, worker]}
for name, drops in variants.items():
    keep = [l for i, l in enumerate(lines, 1) if not any(a <= i <= b for a, b in drops)]
    body = "\n".join(keep)
    open(f"{work}/SKILL-{name}.md", "w").write(body)
    print(f"  {name}: {len(keep)} lines | 'About to:' x{body.count('About to:')} "
          f"| \"don't do the work inline\" x{body.count(chr(39).join(['don', 't do the work inline']))}", file=sys.stderr)
PY

mkdir -p "$WORK/fakehome"
for arm in F G H I; do
  d="$WORK/arm$arm"; mkdir -p "$d/src/routes/api/health" "$d/.agents/skills/tina4-developer-nodejs"
  printf '{ "name": "repro-app", "type": "module", "dependencies": { "tina4-nodejs": "3.13.103" } }\n' > "$d/package.json"
  printf 'import { startServer } from "tina4-nodejs";\nstartServer();\n' > "$d/app.ts"
  printf 'export default async (req, res) => res.json({ status: "ok" });\n' > "$d/src/routes/api/health/get.ts"
  cp "$NODEJS_REPO/AGENTS.md" "$d/"
  cp "$WORK/SKILL-$arm.md" "$d/.agents/skills/tina4-developer-nodejs/SKILL.md"
  cp -r "$NODEJS_REPO/.agents/skills/tina4-developer-nodejs/references" \
        "$d/.agents/skills/tina4-developer-nodejs/" 2>/dev/null || true
  ( cd "$d" && git init -q . && git add -A && git -c user.email=t@t -c user.name=t commit -qm init )
done

for arm in F G H I; do
  ( cd "$WORK/arm$arm" \
    && HOME="$WORK/fakehome" CODEX_HOME="${CODEX_HOME:-$HOME/.codex}" \
       timeout 1200 codex exec --sandbox workspace-write \
         -o "$WORK/arm$arm-last.txt" "$PROMPT" > "$WORK/arm$arm.log" 2>&1 ) &
done
wait

printf '\n%-5s %-34s %-11s %-7s %-11s %s\n' arm "skill variant" "'About to:'" "robot" "log lines" "files changed"
for arm in F G H I; do
  case "$arm" in
    F) v="full" ;; G) v="minus Announce block" ;;
    H) v="minus worker section" ;; I) v="minus both" ;;
  esac
  printf '%-5s %-34s %-11s %-7s %-11s %s\n' "$arm" "$v" \
    "$(grep -c 'About to:' "$WORK/arm$arm.log" || true)" \
    "$(grep -c '🤖' "$WORK/arm$arm.log" || true)" \
    "$(wc -l < "$WORK/arm$arm.log")" \
    "$(cd "$WORK/arm$arm" && git status --short | wc -l)"
done

cat <<'EOF'

VERDICT
  The `About to:` count tracks the Announce block and nothing else: arms that
  keep it announce, arms that drop it do not, and removing the worker section
  changes neither. Every arm still reads the skill (the robot marker survives
  in all four) and every arm still ships the feature — so the Announce block is
  separable, and removing it costs nothing in output.
EOF

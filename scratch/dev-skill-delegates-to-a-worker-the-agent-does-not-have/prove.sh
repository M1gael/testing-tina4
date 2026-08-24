#!/usr/bin/env bash
# Reproduce: the tina4-developer-<lang> skill's behavioural contract reaches an
# OpenAI Codex session through BOTH delivery paths, and changes how the agent
# works — it announces with the skill's own `About to:` formula, prefixes every
# reply with 🤖, and keeps a plan/ folder.
#
# Three arms, identical prompt, identical fixture except for skill delivery:
#
#   C  project .agents/skills/tina4-developer-nodejs/   (Codex's native registry)
#   D  no skills at all                                 (control)
#   E  AGENTS.md pointer -> .claude/skills/...          (what `tina4 ai` writes)
#
# HOME is redirected to a throwaway directory for every arm. Without that the
# machine's own ~/.agents/skills and ~/.claude/skills leak the same skills into
# the control arm and the comparison measures nothing — that happened on the
# first run of this experiment.
#
# COSTS REAL TOKENS: three Codex sessions against whatever model ~/.codex/config.toml
# selects. Roughly 5-10 minutes wall clock.
set -euo pipefail
cd "$(dirname "$0")"

NODEJS_REPO="${NODEJS_REPO:-$HOME/gitdir/tinaforks/tina4-nodejs}"
WORK="${WORK:-$(mktemp -d)}"
PROMPT="Add JWT authentication to this app: a User model, POST /api/auth/login that issues a token, GET /api/auth/me that returns the signed-in user, and tests for both routes."

command -v codex >/dev/null || { echo "codex CLI not on PATH"; exit 2; }
[ -d "$NODEJS_REPO/.claude/skills/tina4-developer-nodejs" ] || {
  echo "set NODEJS_REPO to a tina4-nodejs checkout (looked in $NODEJS_REPO)"; exit 2; }

echo "codex $(codex --version)"
echo "skill $(wc -c < "$NODEJS_REPO/.claude/skills/tina4-developer-nodejs/SKILL.md") bytes"
echo "work  $WORK"
echo

mkdir -p "$WORK/fakehome"

build() {                                       # build <arm>
  local arm="$1" d="$WORK/arm$arm"
  rm -rf "$d"; mkdir -p "$d/src/routes/api/health"
  printf '{ "name": "repro-app", "type": "module", "dependencies": { "tina4-nodejs": "3.13.103" } }\n' > "$d/package.json"
  printf 'import { startServer } from "tina4-nodejs";\nstartServer();\n' > "$d/app.ts"
  printf 'export default async (req, res) => res.json({ status: "ok" });\n' > "$d/src/routes/api/health/get.ts"

  case "$arm" in
    C) mkdir -p "$d/.agents/skills"
       cp -r "$NODEJS_REPO/.agents/skills/tina4-developer-nodejs" "$d/.agents/skills/"
       cp "$NODEJS_REPO/AGENTS.md" "$d/" ;;
    D) cp "$NODEJS_REPO/AGENTS.md" "$d/" ;;
    E) mkdir -p "$d/.claude/skills"
       cp -r "$NODEJS_REPO/.claude/skills/tina4-developer-nodejs" "$d/.claude/skills/"
       cat > "$d/AGENTS.md" <<'MD'
# repro-app

<!-- tina4-skills:start -->
## Tina4 Skills

When working on this Tina4 project, these skills give the assistant project-aware behaviour:

- **tina4-developer-nodejs** — Read `.claude/skills/tina4-developer-nodejs/SKILL.md` before building features.
- **tina4-js** — Read `.claude/skills/tina4-js/SKILL.md` for frontend work.
- **tina4-maintainer** — Read `.claude/skills/tina4-maintainer/SKILL.md` for framework-level changes.

If Tina4 behaves differently from what these skills describe, that is a bug in the skill.
Tell the developer, then report it at https://tina4.com/report-a-skill
(or open an issue on the matching tina4stack/* GitHub repo).

See https://tina4.com for full docs.
<!-- tina4-skills:end -->
MD
       ;;
  esac
  ( cd "$d" && git init -q . && git add -A && git -c user.email=t@t -c user.name=t commit -qm init )
}

for arm in C D E; do build "$arm"; done

for arm in C D E; do
  ( cd "$WORK/arm$arm" \
    && HOME="$WORK/fakehome" CODEX_HOME="${CODEX_HOME:-$HOME/.codex}" \
       timeout 900 codex exec --sandbox workspace-write \
         -o "$WORK/arm$arm-last.txt" "$PROMPT" > "$WORK/arm$arm.log" 2>&1 ) &
done
wait

printf '\n%-5s %-28s %-11s %-7s %-10s %s\n' arm "skill delivery" "'About to:'" "robot" "log lines" "plan/ dir"
for arm in C D E; do
  case "$arm" in
    C) how=".agents/skills (native)" ;;
    D) how="none (control)" ;;
    E) how="AGENTS.md -> .claude/skills" ;;
  esac
  printf '%-5s %-28s %-11s %-7s %-10s %s\n' \
    "$arm" "$how" \
    "$(grep -c 'About to:' "$WORK/arm$arm.log" || true)" \
    "$(grep -c '🤖' "$WORK/arm$arm.log" || true)" \
    "$(wc -l < "$WORK/arm$arm.log")" \
    "$([ -d "$WORK/arm$arm/plan" ] && echo yes || echo no)"
done

cat <<'EOF'

VERDICT
  Arms C and E carry the skill's fingerprints — the `About to:` formula and the
  🤖 reply prefix are its own literal instructions. Arm D, identical but for the
  skill, emits neither. Both delivery paths therefore reach Codex.

  NOT reproduced here: a stall. `codex exec` is non-interactive, and all three
  arms finish the task. The reported failure needs the interactive multi-turn
  condition the skill's own wording depends on ("the main session is always free
  for the NEXT input"). See readme.md.
EOF

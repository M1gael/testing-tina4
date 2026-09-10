#!/bin/sh
# Mirror the real skills tree for one ref into ./mirror, laid out in the SAME shape
# jsDelivr serves (<repo>@<ref>/...), so a local file server can stand in for it.
# Real bytes, so the installer's own checksum verification is exercised for real.
set -eu
ref="${1:-3.13.135}"
src="https://cdn.jsdelivr.net/gh/tina4stack"
DEV_REFS="auth-and-services.md data-and-orm.md deployment.md routes-and-api.md templates-and-frontend.md realtime.md web-push.md ai-coder-rule-path.svg"
get() {
  dest="mirror/$1"; url="$src/$1"
  mkdir -p "$(dirname "$dest")"
  curl -fsSL --retry 3 --retry-delay 1 "$url" -o "$dest"
}
skill() {
  repo="$1"; skill="$2"; shift 2
  get "$repo@$ref/.claude/skills/$skill/SKILL.md"
  for r in "$@"; do get "$repo@$ref/.claude/skills/$skill/references/$r"; done
}
get "tina4@$ref/skills.sha256"
skill tina4-python tina4-developer-python $DEV_REFS
skill tina4-php    tina4-developer-php    $DEV_REFS
skill tina4-ruby   tina4-developer-ruby   $DEV_REFS
skill tina4-nodejs tina4-developer-nodejs $DEV_REFS
skill tina4-python tina4-js         html-and-components.md signals-and-reactivity.md persistence.md rtc.md
skill tina4-python tina4-maintainer cli-and-deployment.md frond-and-frontend.md routing-and-orm.md subsystems.md
skill tina4-python tina4-architect
echo "mirrored $(find mirror -type f | wc -l) files for ref $ref"

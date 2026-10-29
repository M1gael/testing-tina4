#!/bin/bash
# Build the runtime prove.sh uses, OUTSIDE scratch/. Idempotent-ish: re-run on a clean RT.
# FW = extracted framework source at the tips (read only; copied, never edited).
set -euo pipefail
FW=${FW:-$HOME/.cache/tina4-worktrees/verify-1029}
RT=${RT:-$FW/d-cli-02}
mkdir -p "$RT/home" "$RT/shims"
export HOME="$RT/home"          # tina4 CLI / framework tooling install skills into ~/.claude
for p in python php ruby nodejs; do [ -d "$RT/rt-$p" ] || cp -a "$FW/fw-$p" "$RT/rt-$p"; done
[ -x "$RT/py-venv/bin/tina4python" ] || { python3 -m venv "$RT/py-venv"; "$RT/py-venv/bin/pip" install -q "$RT/rt-python"; }
(cd "$RT/rt-php" && composer install -q --no-dev)
(cd "$RT/rt-ruby" && BUNDLE_PATH="$RT/rb-gems" bundle install -j4 >/dev/null)
(cd "$RT/rt-nodejs" && npm ci --silent && cd packages/cli && npm run build >/dev/null)
# tina4 CLI at ebb846b
(cd "$FW/fw-cli" && CARGO_TARGET_DIR="$FW/target" cargo build --release -q)
NODE=$(readlink -f "$(command -v node)")
S="$RT/shims"
mk(){ printf '#!/bin/bash\necho "%s $*" >> "${SHIM_LOG:-/dev/null}"\n%s "$@"\n' "$1" "$2" > "$S/$1"; chmod +x "$S/$1"; }
mk tina4python "exec $RT/py-venv/bin/tina4python"
mk tina4php    "exec php $RT/rt-php/bin/tina4php"
mk tina4ruby   "BUNDLE_GEMFILE=$RT/rt-ruby/Gemfile BUNDLE_PATH=$RT/rb-gems exec bundle exec ruby $RT/rt-ruby/exe/tina4ruby"
mk tina4nodejs "exec $NODE $RT/rt-nodejs/packages/cli/dist/bin.js"
ln -sf "$FW/target/release/tina4" "$S/tina4"
"$S/tina4" --version

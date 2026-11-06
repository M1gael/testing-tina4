#!/bin/bash
# Build the runtime probe.sh/prove.py use, OUTSIDE scratch: detached worktrees of each port's
# origin/v3 and the tina4 CLI origin/main, installed, with argv-logging shims. HOME redirected.
set -euo pipefail
RT=${RT:-$HOME/.cache/tina4-worktrees/docs-cli05/rt}; F=${F:-/var/home/work/gitdir/tinaforks}
mkdir -p "$RT/home" "$RT/shims"; export HOME="$RT/home"
for r in python php ruby nodejs; do [ -d "$RT/fw-$r" ] || git -C "$F/tina4-$r" worktree add -q --detach "$RT/fw-$r" origin/v3; done
[ -d "$RT/fw-cli" ] || git -C "$F/tina4" worktree add -q --detach "$RT/fw-cli" origin/main
python3 -m venv "$RT/py-venv"; "$RT/py-venv/bin/pip" install -q "$RT/fw-python"
(cd "$RT/fw-php" && composer install -q --no-dev)
(cd "$RT/fw-ruby" && BUNDLE_PATH="$RT/rb-gems" bundle install -j4 >/dev/null)
(cd "$RT/fw-nodejs" && npm ci --silent && cd packages/cli && npm run build >/dev/null)
(cd "$RT/fw-cli" && CARGO_TARGET_DIR="$RT/target" cargo build --release -q)
NODE=$(readlink -f "$(command -v node)"); S="$RT/shims"
mk(){ printf '#!/bin/bash\necho "%s $*" >> "${SHIM_LOG:-/dev/null}"\n%s "$@"\n' "$1" "$2" > "$S/$1"; chmod +x "$S/$1"; }
mk tina4python "exec $RT/py-venv/bin/tina4python"
mk tina4php    "exec php $RT/fw-php/bin/tina4php"
mk tina4ruby   "BUNDLE_GEMFILE=$RT/fw-ruby/Gemfile BUNDLE_PATH=$RT/rb-gems exec bundle exec ruby $RT/fw-ruby/exe/tina4ruby"
mk tina4nodejs "exec $NODE $RT/fw-nodejs/packages/cli/dist/bin.js"
ln -sf "$RT/target/release/tina4" "$S/tina4"; "$S/tina4" --version

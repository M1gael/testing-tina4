#!/usr/bin/env bash
#
# prove.sh [path-to-a-tina4-python-checkout]
#
# Default: a detached worktree at tina4-python origin/v3 built on demand.
#
# Proves that installing the 3.13.117 import-hint helper imports every optional
# subsystem in the package, and that this is what makes the public realtime()
# API stop being callable.
#
# Each arm runs in its OWN interpreter — the defect is about what a single
# `import tina4_python` does, so it cannot be measured twice in one process.
set -uo pipefail
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo="${1:-}"
if [ -z "$repo" ]; then
  repo="$(mktemp -d)/v3"
  git -C /var/home/work/gitdir/tinaforks/tina4-python worktree add -q --detach "$repo" origin/v3
  trap 'git -C /var/home/work/gitdir/tinaforks/tina4-python worktree remove --force "$repo" 2>/dev/null' EXIT
fi
echo "checkout : $repo"
echo "version  : $(cd "$repo" && git log --oneline -1)"
echo "helper   : md5 $(md5sum "$repo/tina4_python/_import_helper.py" | cut -d' ' -f1)"
echo

probe() {   # $1 = label, $2 = extra python prelude
  python3 - "$repo" <<PY
import sys
sys.path.insert(0, sys.argv[1])
$2
import tina4_python as t
OPT = ('crud','docstore','graphql','messenger','mqtt','queue','seeder','swagger','wsdl')
eager = sorted(m for m in sys.modules
               if m.startswith('tina4_python.') and any(k in m for k in OPT))
print(f"    eager optional subsystems : {len(eager)}")
print(f"    tina4_python.realtime     : {type(t.realtime).__name__}, callable={callable(t.realtime)}")
print(f"    first few eager           : {eager[:4]}")
PY
}

echo "=== ARM 1 — stock: the helper installs and walks ==="
probe stock ""
echo
echo "=== ARM 2 — same tree, the eager walk neutralised (nothing else changed) ==="
probe patched "import pkgutil; pkgutil.walk_packages = lambda *a, **k: iter(())"
echo
echo "Arm 2 changes ONE thing: pkgutil.walk_packages stops importing what it lists."
echo "If realtime goes from module to function across those two arms, the walk is"
echo "the cause — not the lazy loader, not the test, not the realtime package."

#!/usr/bin/env bash
# Does tina4-php PR #210's regression test gate the Windows branch it was written for?
#
# Mutation: delete the Windows arm of the redirect choice, keep the method name.
# If the suite stays green, the test gates the method's existence, not its behaviour.
set -u
FORK="${FORK:-/var/home/work/gitdir/tinaforks/tina4-php}"
W="${W:-$HOME/.cache/tina4-worktrees/php210}"

if [ ! -d "$W" ]; then
    git -C "$FORK" fetch -q origin pull/210/head
    git -C "$FORK" worktree add -q --detach "$W" FETCH_HEAD
    # A symlinked vendor resolves composer's baseDir back to the fork, which
    # silently loads the UNFIXED Metrics.php. Copy it.
    cp -a "$FORK/vendor" "$W/vendor"
fi
cd "$W"
echo "# head: $(git log -1 --format='%h %s')"
run() { php -d memory_limit=256M vendor/bin/phpunit tests/MetricsEnginePathTest.php 2>&1 | tail -2 | sed 's/^/    /'; }

echo "## as submitted"; run
sed -i 's|\$discard = \$isWindows ? "2>nul" : "2>/dev/null";|$discard = "2>/dev/null"; // MUTATION|' Tina4/Metrics.php
grep -q MUTATION Tina4/Metrics.php || { echo "mutation did not apply - anchor moved"; exit 2; }
echo "## Windows arm deleted"; run
git checkout -- Tina4/Metrics.php
echo "## restored: $(grep -c '2>nul' Tina4/Metrics.php) occurrences of 2>nul back"

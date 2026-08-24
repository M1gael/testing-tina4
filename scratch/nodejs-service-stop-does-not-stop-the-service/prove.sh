#!/usr/bin/env bash
# Proves f-svc-01 in tina4-nodejs: ServiceRunner.stop() does not stop a
# class-based Tina4Service.  Runs the same reproduction twice — once against the
# stock released bundle, once with the candidate fix applied to it — and puts the
# bundle back exactly as it was, md5-verified.
#
# Exit 0 = defect reproduced on stock AND closed by the candidate fix.
set -uo pipefail
cd "$(dirname "$0")"

[ -d node_modules/tina4-nodejs ] || npm install --no-audit --no-fund >/dev/null

run() { node repro.mjs 2>&1 | grep -v 'ExperimentalWarning\|trace-warnings'; return "${PIPESTATUS[0]}"; }

echo "=============================================================="
echo " 1. STOCK — released tina4-nodejs, unmodified"
echo "=============================================================="
python3 patch.py verify || { echo "bundle is not stock; run: npm ci"; exit 2; }
run; stock=$?
echo "exit $stock  (expect 1 — the defect)"

echo
echo "=============================================================="
echo " 2. CANDIDATE FIX — stop() routes to the stashed instance"
echo "=============================================================="
python3 patch.py apply || exit 2
run; fixed=$?
echo "exit $fixed  (expect 0 — the defect is gone)"

echo
python3 patch.py revert || { echo "RESTORE FAILED — reinstall before trusting any later run"; exit 2; }

echo
echo "=============================================================="
if [ "$stock" -eq 1 ] && [ "$fixed" -eq 0 ]; then
  echo " VERDICT: reproduced on stock, closed by the candidate fix."
  exit 0
fi
echo " VERDICT: INCONCLUSIVE — stock exit $stock, fixed exit $fixed."
exit 1

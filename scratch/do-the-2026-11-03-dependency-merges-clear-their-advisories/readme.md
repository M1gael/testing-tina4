# Do the 2026-11-03 dependency merges clear their advisories?

Question: do the four dependency-security merges of 2026-11-03 remove every known advisory
from their lock files, and does anything break?

| repo | PR | merge (tip, fetched 2026-11-03) | parent |
|---|---|---|---|
| tina4-python | #275 | 1977fe5cf5 | ba84f43c4c |
| tina4-php | #346 | b82729b8be | dffce724d1 |
| tina4-nodejs | #183 | 7ea02ba5eb | 47e3a7a4d7 |
| tina4-js | #38 | 3a98a0c7ea | 16bbffe384 |

`osvscan.py <lockfile>` sends every locked package+version to the OSV batch API and lists the
affected ones (exit 2 if OSV unreachable). `scan.log` holds each lock file before and after its merge.

## Result (run)

- python: 80 to 61 packages; pillow 12.3.0 (~40 ids) and setuptools 84.0.0 gone; certifi
  2026.7.22 and dnspython 2.8.0 remain (our private reports, f-dep-03/04).
- php: symfony/yaml 7.4.15 (dev, GHSA-2v3c-qxhr-7vpv) to 7.4.22; 0 affected.
- nodejs: 5 affected to 0 (msal-node 5.6.0 to 7.1.2, grpc-js 1.14.4 to 1.14.7, vitest/mocker,
  fast-uri, vite). grpc-js was never a Dependabot alert.
- js: happy-dom 20.14.6 to 21.x (dev, major bump); 0 affected.
- Dependabot open alerts after rescan: python 2 (certifi, dnspython), others 0.

The scanner can say "affected": every "before" lock produced hits.

## Breakage checks

- python: nothing outside benchmarks/ imports the removed packages (git grep on the tip, static and
  importorskip). Competitor frameworks moved to benchmarks/requirements.txt (unpinned floors).
- CI on each merge commit (run on GitHub, read 2026-11-03): python, php, nodejs `test` jobs success; js test/build success; all CodeQL Analyze jobs success.
- nodejs msal-node is a major jump (5 to 7), required by @azure/identity 4.14.1 itself (`^7.1.0`).
  Not run locally; covered only by CI.

# tina4-python `uv.lock` pins certifi and dnspython versions with published advisories

Ledger rows: `f-dep-certifi`, `f-dep-dnspython` (see ledger for codes). Run 2026-11-03 on py `ba84f43c` (origin/v3).

The framework has zero core dependencies. These pins come from the lock only: certifi via `requests`
(pulled by `python-arango`, the `arango`/`graph` extras), dnspython via `pymongo` (`mongo` extra).
They reach anyone who runs `uv sync --all-extras` from the repo, and the repo's Dependabot alerts
(#110 certifi critical, #111 dnspython high, both 2026-10-29).

- certifi 2026.7.22: GHSA-6q48-6c7w-9gw2 (bundles emSign roots with compromised intermediate keys), fixed 2026.10.18.
- dnspython 2.8.0: GHSA-45c3-73f7-pv4m (`dns.name.from_wire_parser()` CPU use), fixed 2.9.0.

Pillow and setuptools (the other open alerts) are removed by the maintainer's open PR #275; it does not touch these two.

Fix: `uv lock --upgrade-package <pkg>` (uv 0.11.14), 3-line lock diff each: certifi 2026.10.23, dnspython 2.9.1.
`uv lock --check` passes. `check.sh <uv.lock>` queries OSV: stock.log shows both advisories, fixed.log none.
Tests touching mongo/arango/graph/queue/http-client/api: stock 298 passed 108 skipped; same on each bump.

# Issue #47 — Upstream comment

**Posted:** 2026-06-09T12:56:30Z
**Posted by:** MichaelC8E
**Upstream URL:** https://github.com/tina4stack/tina4-python/issues/47#issuecomment

---

## Confirmed on tina4-python 3.13.5

`psycopg2` is required for PostgreSQL — the adapter lazy-imports it at `postgres.py:54-58` and raises if missing. METADATA declares it only under `Requires-Dist: psycopg2-binary>=2.9; extra == 'postgres'`, so `pip install tina4-python` resolves with zero deps as intended. Same pattern for the other five drivers (`mysql.py:31`, `mssql.py:31`, `firebird.py:118`, `mongodb.py:350`, `odbc.py:33`).

The extras already exist — METADATA lines 145-155 list `tina4-python[postgres]`, `[mysql]`, `[mssql]`, `[firebird]`, `[mongo]`, `[odbc]`, `[all-db]`. PyPI and the repo README both render that block.

The gap is on the book side: https://tina4.com/python/01-getting-started.html never mentions a driver requirement, and https://tina4.com/python/05-database.html flags the requirement but recommends `uv add psycopg2-binary` (bare driver) rather than the extras form. A one-line prerequisites callout in Getting Started, and switching the install block in Chapter 5 to `uv add 'tina4-python[postgres]'`, would close it.

### Alternatives, if a UX change is on the table

- **Bundle into base deps.** Move `psycopg2-binary` (or all six drivers) out of extras and into unconditional `Requires-Dist`. Simplest install path, but breaks the "zero-dependency" framing in Ch1 / PyPI / repo README and forces the driver on every user — including SQLite-only and non-DB projects. Prebuilt wheels cover most platforms but not all (some Alpine/ARM/musl combos fall back to source build needing `libpq-dev`).
- **Baseline subset.** Ship `tina4-python` with a small default like `[postgres,mysql]` pre-included. Caps bloat versus full bundle but still drops the strict zero-dep claim and still forces drivers on users who don't need them.
- **Scaffolder flag.** `tina4 init python --db=postgres` writes `tina4-python[postgres]` into the generated `pyproject.toml` directly. Keeps the base zero-dep, makes the right install happen at project creation, no runtime ImportError.

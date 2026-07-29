# Issue #47 — Database dependency not included by default

**Upstream:** https://github.com/tina4stack/tina4-python/issues/47
**Reporter:** SAB13711
**Author comment (2026-06-08):** *"This is by design it seems. Just need it documented."*
**Framework version under test:** tina4-python **3.13.5** (upgraded from 3.13.4 on 2026-06-09; bug behaviour identical between the two)
**Status:** comment posted upstream 2026-06-09 (MichaelC8E); doc gap, no probe required.

---

## Reporter's symptom

```
error:psycopg2 is required for PostgreSQL connections.
Install: pip install psycopg2-binary
```

PostgreSQL support is not installable through the framework's default
install path.

## OP's claim — verified part-by-part on 3.13.5

| OP claim | Verification | Verdict |
|---|---|---|
| `psycopg2` required for PG | Adapter lazy-imports at `postgres.py:54-58`; raises ImportError when missing | True |
| Not bundled by default | METADATA declares only `Requires-Dist: psycopg2-binary>=2.9; extra == 'postgres'` — no unconditional Requires-Dist. `pip install tina4-python` resolves with zero runtime deps | True |
| "By design" | Matches the "zero-dependency" framing in Ch1 line 5 + PyPI badge + repo README. 8 extras declared in METADATA: postgres / mysql / mssql / firebird / mongo / odbc / all-db / dev-reload. Same lazy-import pattern at all six adapters (`postgres.py:54-58`, `mysql.py:31`, `mssql.py:31`, `firebird.py:118`, `mongodb.py:350`, `odbc.py:33`) | True |
| "Just needs documented" | Partially documented already — see next section | Partially true |

## Where the driver requirement IS documented

- **PyPI page + repo README** — METADATA lines 145-155 list the full extras block (`tina4-python[postgres]`, `[mysql]`, `[mssql]`, `[firebird]`, `[mongo]`, `[odbc]`, `[all-db]`, `[dev-reload]`). PyPI and the GitHub repo both render this from the same `long_description` source.
- **Book Ch5 Database** (`documentation/tina4-book/book-1-python/chapters/05-database.md` / `https://tina4.com/python/05-database.html`) — table at lines 25-36 includes a "Package Required" column; install instructions at lines 38-57 list `uv add psycopg2-binary` etc.

## Where the driver requirement is NOT documented (the gap)

- **Book Ch1 Getting Started** (`documentation/tina4-book/book-1-python/chapters/01-getting-started.md` / `https://tina4.com/python/01-getting-started.html`) — line 5 promises *"zero-dependency web framework"*, line 152 reinforces *"One package. No dependency tree. No version conflicts. Just `tina4-python`."* The chapter never flags that switching `TINA4_DATABASE_URL` to anything other than SQLite triggers an extra install. Verified via grep across all 1132 lines: zero matches for `postgres`, `psycopg`, `mysql`, `mssql`, `firebird`, `mongo`, `odbc`, `driver`, `extras`, `optional`.
- **The ImportError text at all 6 adapters** recommends bare `pip install <driver>`, not the canonical `tina4-python[<extra>]` form documented in METADATA itself. Verbatim from 3.13.5:

  | File:line | Recommended install |
  |---|---|
  | `postgres.py:55-58` | `Install: pip install psycopg2-binary` |
  | `mysql.py:31-34` | `Install: pip install mysql-connector-python` |
  | `mssql.py:31-34` | `Install: pip install pymssql` |
  | `firebird.py:118-121` | `Install: pip install firebird-driver  (or pip install fdb for legacy)` |
  | `mongodb.py:350-353` | `Install: pip install pymongo` |
  | `odbc.py:33-35` | `Install: pip install pyodbc` |

- **`tina4 init python .` scaffolded `pyproject.toml`** — comments suggest `uv add psycopg2-binary` (bare), matching Ch5 wording rather than the METADATA extras wording. Verified on `pypy/pyproject.toml` lines 12-17.

Repo-wide grep across `documentation/tina4-book/` and `pypy/.venv/Lib/site-packages/tina4_python/` for the `tina4-python[` syntax returns **zero matches** outside METADATA itself. The extras live in METADATA and the repo README only; every other user-facing surface bypasses them.

## Adversarial disproof attempts (2026-06-09, pre-comment)

| Tried to break | Result |
|---|---|
| Maybe Ch1 mentions DB drivers later (only first 220 of 1132 lines initially read) | Grep across all 1132 lines for postgres / psycopg / mysql / driver / extras / optional returned 0 matches. Holds. |
| Maybe a `/python/installation` or `/python/getting-started.html` separate docs page exists | WebFetch on both returned HTTP 404. No alternate surface. |
| Maybe CHANGELOG documents extras | `dist-info/` contains only METADATA, RECORD, WHEEL, entry_points.txt — no CHANGELOG. |
| Maybe pip is reachable in the tina4-init venv even without pip.exe | `ls .venv/Scripts/ \| grep -iE "^pip"` returned empty. Bare `pip install psycopg2-binary` literal advice fails for a uv-scaffolded project — user would need `uv pip install` or `uv add`. |
| Maybe the "version pin" angle was a real cost | METADATA pin is `>=2.9` — very loose; bare `pip install psycopg2-binary` would also satisfy it. Dropped this angle from the comment — real cost is maintainer can't redirect (psycopg2 → psycopg3 etc.) without rewriting six ImportError sites + book chapter. |
| Maybe Ch1's "zero-dep" claim was actually flagged as exception-bound elsewhere | No. The claim is unqualified. Tone in the comment was softened from "contradicts" to "no callout in Ch1; Ch5 introduces the install without flagging it as exception". |

Survived: all 4 user-journey surfaces (Ch5 install block, ImportError ×6, scaffolded `pyproject.toml` comments, no pip in uv venv) route the user past the extras docs.

## Upstream comment (posted 2026-06-09T12:56:30Z by MichaelC8E)

See `bug-hunting/issue-47-comment.md` for the exact body.

## Potential fixes (suggestions, not implemented here)

### A. Docs-only (matches OP's framing — primary recommendation)

- **Ch1 prerequisites callout.** Add one line near the SQLite default mention pointing at the extras list for any non-SQLite DB.
- **Ch5 install block.** Switch lines 38-57 from `uv add psycopg2-binary` to `uv add 'tina4-python[postgres]'`. Keep bare-driver as fallback.
- **6 ImportError messages.** Rewrite each lazy-import error to recommend the extras form (`postgres.py:55-58`, `mysql.py:31-34`, `mssql.py:31-34`, `firebird.py:118-121`, `mongodb.py:350-353`, `odbc.py:33-35`).

### B. Alternative UX changes (if maintainer wants to reduce friction further)

- **Bundle into base deps.** Move `psycopg2-binary` (or all six drivers) from `extra == '...'` to unconditional `Requires-Dist`. Simplest install path, but breaks the zero-dep framing in Ch1 / PyPI / repo README and forces the driver on every user — including SQLite-only and non-DB projects. Prebuilt wheels cover most platforms but not all (some Alpine/ARM/musl combos still need `libpq-dev` for a source build).
- **Baseline subset.** Ship `tina4-python` with a small default like `[postgres,mysql]` pre-included. Caps bloat versus full bundle but still drops the strict zero-dep claim.
- **Scaffolder flag.** `tina4 init python --db=postgres` writes `tina4-python[postgres]` into the generated `pyproject.toml` directly. Keeps the base zero-dep, makes the right install happen at project creation, no runtime ImportError. Lowest-disruption option that meaningfully changes the new-user experience.

The doc-only fix (A) matches OP's accepted-as-design framing. Anything from (B) is a separate design call.

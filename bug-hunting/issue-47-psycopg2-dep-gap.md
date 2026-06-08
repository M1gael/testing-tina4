# Issue #47 — Database dependency not included by default

**Upstream:** https://github.com/tina4stack/tina4-python/issues/47
**Reporter:** SchalkAB13711
**Author comment:** *"This is by design it seems. Just need it documented."*
**Status:** doc gap + minor error-message refinement; no probe required.

---

## Reporter's symptom

```
error:psycopg2 is required for PostgreSQL connections.
Install: pip install psycopg2-binary
```

PostgreSQL support is not installable through the framework's default
install path.

## What the package actually ships

`tina4-python` 3.13.4 already declares the right optional dependency
groups via PEP 621 extras (verified in
`.venv/Lib/site-packages/tina4_python-3.13.4.dist-info/METADATA`):

```
Provides-Extra: postgres
Requires-Dist: psycopg2-binary>=2.9; extra == 'postgres'

Provides-Extra: all-db
Requires-Dist: psycopg2-binary>=2.9; extra == 'all-db'
Requires-Dist: mysql-connector-python>=9.0; extra == 'all-db'
Requires-Dist: pymssql>=2.3; extra == 'all-db'
Requires-Dist: pymongo>=4.0; extra == 'all-db'
Requires-Dist: pyodbc>=5.0; extra == 'all-db'
Requires-Dist: firebird-driver>=1.10; extra == 'all-db'

# … plus per-driver extras: firebird, memcache, mongo, mssql, mysql, odbc, redis
```

So the *packaging* is fine. PostgreSQL support is reachable via:

```
uv add 'tina4-python[postgres]'    # or
pip install 'tina4-python[postgres]'
```

## What's actually broken (the doc gap)

Three things make this invisible to a new user:

1. **`tina4 init python .` does not install any DB extra.** The
   scaffolded `pyproject.toml` adds `tina4-python` bare, so out of the
   box only SQLite (and ODBC, lazily) works. Any other driver fails
   on first use with the `ImportError` raised at
   `tina4_python/database/postgres.py:54-58`:

   ```python
   try:
       import psycopg2
       import psycopg2.extras
   except ImportError:
       raise ImportError(
           "psycopg2 is required for PostgreSQL connections. "
           "Install: pip install psycopg2-binary"
       )
   ```

   The same shape exists for every optional driver (`mysql.py`,
   `mssql.py`, `firebird.py`, `mongodb.py`). None of them mention
   the extras syntax.

2. **The error message recommends the *wrong* install command.**
   `pip install psycopg2-binary` installs the driver to the venv
   but does *not* record the dep in the project's
   `pyproject.toml`/`uv.lock`, so a teammate cloning the repo
   later has no record that postgres is needed. The correct hint
   is `uv add 'tina4-python[postgres]'` (or
   `pip install 'tina4-python[postgres]'`).

3. **No documentation surfaces the extras at all.** The
   getting-started flow on tina4.com walks through `tina4 init`,
   `tina4 serve`, and assumes SQLite. The ORM chapter shows
   `Database("postgresql://...")` as a one-line example without a
   prerequisite callout. The framework's own
   `tina4_python/CLAUDE.md` (which an AI assistant *will* read
   during a build session) shows the same — connection URLs for
   all 5 engines side-by-side, no install step:

   ```
   db = Database("postgresql://localhost:5432/mydb", "user", "password")
   ```

   `Chapter 6 — Database` (the next chapter to be reviewed under
   the doc-fidelity protocol on `main`) is where the fix needs to
   land.

## Recommended changes (suggestion, not implemented here)

A. **Docs (`tina4-book` Chapter 6, "Database"):** add a one-block
   prerequisites callout near the top of the Database section:

   > **Optional drivers.** Tina4 ships with SQLite working out of
   > the box. Other engines need a one-time extra install:
   >
   > ```
   > uv add 'tina4-python[postgres]'   # PostgreSQL  (psycopg2-binary)
   > uv add 'tina4-python[mysql]'      # MySQL       (mysql-connector-python)
   > uv add 'tina4-python[mssql]'      # SQL Server  (pymssql)
   > uv add 'tina4-python[firebird]'   # Firebird    (firebird-driver)
   > uv add 'tina4-python[mongo]'      # MongoDB     (pymongo)
   > uv add 'tina4-python[odbc]'       # ODBC        (pyodbc)
   > uv add 'tina4-python[all-db]'     # everything above
   > ```

B. **Error messages (framework):** rewrite each lazy-import
   `ImportError` to recommend the extras form, e.g.

   ```python
   raise ImportError(
       "psycopg2 is required for PostgreSQL connections. Install: "
       "uv add 'tina4-python[postgres]'  (or 'pip install "
       "tina4-python[postgres]')"
   )
   ```

   Five files to update mechanically: `postgres.py:54-58`,
   `mysql.py`, `mssql.py`, `firebird.py`, `mongodb.py`.

C. **(Optional) `tina4 doctor`:** the existing "Tina4 CLIs"
   section (see `PY-01-08` on `main`) could grow a "Database
   drivers" sub-section listing which extras are installed in
   the current venv. Low priority — A + B already close the gap.

## Draft upstream comment (paste into issue #47)

> Confirmed — the packaging is already correct (PEP 621 extras for
> `postgres`, `mysql`, `mssql`, `firebird`, `mongo`, `odbc`,
> `memcache`, `redis`, and `all-db` are all declared in
> `tina4-python` 3.13.4's METADATA), but three things make this
> invisible to a new user:
>
> 1. `tina4 init python .` does not install any DB extra — the
>    scaffolded `pyproject.toml` adds `tina4-python` bare, so only
>    SQLite works out of the box.
> 2. The lazy-import error at `postgres.py:54-58` recommends `pip
>    install psycopg2-binary` rather than the extras syntax `pip
>    install 'tina4-python[postgres]'`. The bare install bypasses
>    the project's lockfile and creates a hidden dep.
> 3. The Database chapter on tina4.com shows connection URLs for
>    all 5 engines without a prerequisites callout. A reader
>    following the chapter top-down can't tell that PG needs an
>    extra install.
>
> Suggested fixes: a one-paragraph extras callout at the top of
> Chapter 6 Database, plus updating the five lazy-import
> `ImportError` messages
> (`postgres.py`/`mysql.py`/`mssql.py`/`firebird.py`/`mongodb.py`)
> to recommend `uv add 'tina4-python[<driver>]'` instead of the
> bare-package install.

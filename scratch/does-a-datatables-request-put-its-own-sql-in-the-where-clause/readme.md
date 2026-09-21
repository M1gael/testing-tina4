# Does a DataTables request put its own SQL into the where clause?

**Question.** `Tina4\Crud::getDataTablesFilter()` (tina4php **v2**) turns a DataTables
request into SQL fragments a caller concatenates into a statement. Do values, column
names, the sort direction, or the paging numbers reach that SQL text verbatim — i.e. is
request input treated as SQL rather than as data? And does **PR #209** close it?

**Answer (run).** Yes, on stock v2 every one of those inputs reaches the statement without
binding or validation, and one benign input — a person named `O'Brien` — is enough to see
it: the apostrophe ends the string literal and the statement is malformed. PR #209 closes
each path (values quoted as literals, column names validated against the model's own fields,
direction restricted to `asc`/`desc`, paging cast to int) and deliberately leaves one
documented per-column passthrough open. It adds 8 tests, all green, and breaks nothing.

Pinned: stock `origin/v2` at **`54ecf165`** ("Adds ability to search at column level for
datatables"), PHP 8.4.25, `tina4php-sqlite3` v2.0.5. Fixed = the same commit + `pr209.patch`.

---

## Mechanism (read), all in `Tina4/Routing/Crud.php` on `54ecf165`

| Input | Stock line | What happens |
|---|---|---|
| global search value | `:426` `" like '%" . strtoupper($singleValue) . "%'"` | request value concatenated inside `'...'`, not escaped |
| per-column regex value | `:445` `" REGEXP '" . $searchValue . "'"` | request value concatenated inside `'...'`, not escaped |
| per-column non-regex value | `:448` `$filter[] = $searchValue;` | request value used as a raw SQL fragment (documented "any sql") |
| sortable / searchable column name | `:412`, `:458` `$ORM->getFieldName($column["data"], …)` then concatenated | resolved name concatenated with no check it is a bare identifier or a real field |
| sort direction | `:459` `… . " " . $orderEntry["dir"]` | request direction concatenated verbatim |
| `start` / `length` | `:499`, `:505` `$start = $request["start"]` | assigned verbatim (no cast); caller builds `limit {length} offset {start}` |
| by-id update / delete | `:324`, `:345` `load("{pk} = '{$id}'")` | inline `{id}` from `inlineParams` interpolated inside `'...'` |

`getDataTablesFilter` has exactly one caller — the list route at `Crud.php:276`,
`Crud::getDataTablesFilter("t.", new $object())` — so the ORM is always a real model.

## Observed (run) — `drive.php`, five cases, each built into a `select … from people t`

3 people exist; one is `Ann`, one is `O'Brien`. "rows" is how many the built query returned.

| Case | Stock `54ecf165` | Fixed (`+pr209.patch`) |
|---|---|---|
| A — search `ann` | rows [1] — works | rows [1] — works (now `upper()` on the columns too) |
| B — search the name `O'Brien` | **SQL ERROR** `near "BRIEN": syntax error` | rows [3] — literal doubled to `'%O''BRIEN%'`, found |
| C — sort by a column the model has no field for | **SQL ERROR** `no such column: t.no_such_column` | column rejected, `where`/`orderBy` empty, rows [1,2,3] |
| D — sort direction that is not asc/desc | **SQL ERROR** `near "nonsense": syntax error` | forced to `t.first_Name asc`, rows [1,2,3] |
| E — search `ann` with no DB connection bound | `Undefined variable $columnsToSearch` at `:491` (used before it is set when `$ORM->DBA` is empty), emits ` like '%ANN%'` (nothing on the left) → **SQL ERROR** | filter dropped, `where` empty, rows [1,2,3] |

Case A works on both trees — the instrument can report success, so the errors in B–E are
the code's, not the harness's.

## The PR's own test file (run), independent instrument

`tests/CrudDataTablesFilterTest.php` (new in the PR), driven on each tree:

- stock `54ecf165`: **8 tests, 6 failures** — matches the author's "6 of them fail without
  these changes". The three named failures confirm the mechanism from the other side:
  `testColumnNameThatIsNotAPlainIdentifierIsIgnored` (stock lets a non-identifier column
  through), `testOrderDirectionIsLimitedToAscOrDesc` (direction unrestricted),
  `testStartAndLengthAreIntegers` (`start` stays a string instead of an int).
- fixed: **8 / 8 green.**

## Full suite (run), before vs after

- stock: 32 tests, **1 failure** — `ResponseTest::testRender` (`'Hello Test'` vs
  `'index.twig'`), a pre-existing twig-render failure unrelated to Crud.
- fixed: 40 tests (the same 32 + the PR's 8), **1 failure** — the identical
  `ResponseTest::testRender`. The PR adds nothing red and removes nothing.

## Disprove

- **Both directions.** Apply the cause (stock) → B–E break; remove it (fixed) → B–E clean;
  A works on both. Single-factor: only the patch differs between the two worktrees, both at
  `54ecf165`.
- **Instrument could report otherwise** — case A returned a clean "1 of 3" on both; the
  queries are really prepared and run by SQLite3, the errors are real prepare failures.
- **One path the fix does not close, by design (read).** The per-column non-regex branch
  `$filter[] = $searchValue;` survives at `Crud.php:466` on the fixed tree; the author
  documents it as a deliberate SQL passthrough and asks for a decision. It is reachable when
  a request sends a per-column `search[value]` (not the global search box) on a resolvable
  column with `regex` ≠ `true`. On the fixed tree the *column name* in that branch is
  validated, but the *value* is still emitted raw.
- **Allow-list bound (read).** `getSafeColumnName` enforces the model's field list; when an
  ORM exposes no fields (a bare `Tina4\ORM`) the allow-list is empty and only the
  `^[A-Za-z_][A-Za-z0-9_]*$` identifier shape is enforced. The single in-tree caller always
  passes a real model, so this weaker path is reachable only by a direct caller of
  `getDataTablesFilter`.
- **Scope (run).** `getDataTablesFilter` exists on `origin/v2` only — `origin/v3` and
  `origin/main` carry no such method; mainline replaced `Crud` with `AutoCrud`. So this is a
  **v2 defect**, and current 3.13.x (v3) releases do not contain this code.

## Bounds / not visited

- **Engine.** Run on SQLite3 only. The quoting the fix emits is engine-specific
  (`pg_escape_literal` on PostgreSQL, backslash handling on MySQL, doubled quote elsewhere);
  those branches were read, not run. The correctness of the *stock* defect is engine-agnostic
  (a raw apostrophe breaks every one), but each engine's escaping in the fix is unverified
  here.
- **AutoCrud (v3/main).** Whether the AutoCrud path that replaced this has an analogous
  issue is a separate question, not answered.
- **Other ports.** php-only. Whether ruby/nodejs/python have a v2-era Crud DataTables filter
  with the same shape is not checked.
- **HTTP reachability.** The fragments were driven through the method directly and executed;
  they were not driven end-to-end through a running `Crud::route()` over HTTP. The single
  caller wires request → method → statement with no intervening validation (read).

## Verdict

PR #209 is a correct, well-tested fix for a real v2 defect, safe to merge: the 200/list path
still works, the fix is proven in both directions, its own 8 tests are green, and the full
suite is unchanged but for a pre-existing unrelated failure. The one open passthrough is the
author's flagged decision, not a regression — it is equally open on stock.

Reproduce: `./prove.sh` (needs the two worktrees; it rebuilds them if absent).

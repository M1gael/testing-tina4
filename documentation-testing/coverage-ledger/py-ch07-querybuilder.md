# Coverage Ledger — Python · Chapter 7: QueryBuilder

Per-section proof-of-coverage for the chapter evaluation. A section is never "complete" —
only **ledger-complete**: every snippet AND every named option marked `✓ tested` /
`⛔ blocked` / `⏸ deferred` / `n/a`, and **every sign-off stamped with the date + the tina4
versions it was verified on**. See [`documentation-testing/readme.md`](../readme.md) → Workflow step 7. The
Evaluation Progress table in [`README.md`](README.md) links here.

- **Doc:** `documentation/tina4-book/book-1-python/chapters/07-query-builder.md` (11 numbered sections + NoSQL/Gotchas/Exercise)
- **Framework under test (READ-ONLY):** `documentation-testing/pypy/.venv/Lib/site-packages/tina4_python/query_builder.py`
- **Tests:** `documentation-testing/pypy/tests/test_ch07_querybuilder_*.py` · **Live mock:** section-by-section explorer `GET /chapter/7` (verbatim snippet + live execution per S1/S2, like Ch12's `/chapter/12`); also the raw `GET /api/ch07/qb/select-demo`
- **DB:** live PG `tina4testingdb` (suite default, bound by `conftest`); `users` table present

Legend: `✓` tested · `⚠` diverges (logged finding) · `⛔` blocked (can't stand up here) · `⏸` deferred (USER) · `n/a` (no testable claim)

This chapter is the QueryBuilder thread continued from Ch06 (the Ch06 "QueryBuilder Integration"
note deferred the full builder API here). Implementation is **at most 2 sections per the USER
directive** — S1 + S2 done; S3–S11 + NoSQL/Gotchas/Exercise not yet started.

---

## S1 — The Factory: from_table()
> Signed off: 2026-06-29 · tina4-python 3.13.47 · CLI 3.8.53 · pytest + `tina4 serve` (port 7146)

- `from tina4_python.query_builder import QueryBuilder` + `from_table("users", db)` returns a `QueryBuilder` — `✓` `test_ch07_querybuilder_s1_factory.py::test_from_table_returns_a_querybuilder_instance`
- "`from_table()` returns a fresh `QueryBuilder` instance" — `✓` `::test_from_table_returns_a_fresh_instance_each_call` (two calls are distinct objects)
- "Every method you call on it returns the same instance, so you can chain" — `✓` `::test_methods_return_the_same_instance_so_you_can_chain` (`select()`/`where()` return `self`)
- "If you omit the database, QueryBuilder will fall back to the global ORM database (set via `bind_database()`)" — `✓` `::test_omitting_db_falls_back_to_the_global_orm_database` (no-db `from_table` + `bind_database` → `get()` succeeds) · also live: served `s1_global_fallback_sql` (serve binds the global from `.env`)
- "If neither exists, it raises a `RuntimeError` when you try to execute" — `✓` `::test_no_db_and_no_global_raises_runtimeerror_on_execute` (clean subprocess, no env URL, no bind → `get()` raises `RuntimeError: QueryBuilder: No database connection provided.`)
- first arg = table name, second = `Database` connection — `✓` (both forms exercised: explicit `db` and global fallback)

**Verdict: FAITHFUL — no divergence.** All five S1 claims behave exactly as documented.

## S2 — Choosing Columns: select()
> Signed off: 2026-06-29 · tina4-python 3.13.47 · CLI 3.8.53 · pytest + `tina4 serve` (port 7146)

- "By default, QueryBuilder selects all columns (`*`)" — `✓` `test_ch07_querybuilder_s2_select.py::test_default_selects_all_columns_star` (`to_sql()` → `SELECT * FROM users`)
- verbatim `select("id", "name", "email")` narrows; "Pass column names as separate arguments, not a list" — `✓` `::test_select_narrows_with_separate_column_arguments` (`SELECT id, name, email FROM users`)
- "Each call to `select()` replaces the previous column selection" + `.select("id","name").select("email")` "selects only email" — `✓` `::test_each_select_replaces_the_previous_selection` (`SELECT email FROM users`)
- "If you want all columns, skip `select()` entirely. The default is `*`" — `✓` `::test_skipping_select_entirely_defaults_to_star`

SQL shape is read with `to_sql()` (the inspection method introduced in S8), used here purely as
the observation tool for S2's documented SQL — no execution / table rows required.

**Verdict: FAITHFUL — no divergence.** All four S2 claims behave exactly as documented.

---

## Open items / not yet started (per the ≤2-section directive)
- S3 Filtering (`where()`/`or_where()`), S4 Joins, S5 Aggregation, S6 Sorting, S7 Pagination,
  S8 `to_sql()`, S9 Execution Methods, S10 Chaining, S11 Using with ORM Models — **not started**.
- NoSQL: MongoDB Queries (`to_mongo()`) — **not started** (broker-dependent; brokers down this session).
- Gotchas, Exercise: Product Search API — **not started**.
- Carry-over note from Ch06 QueryBuilder Integration: `get()`/`first()` return `DatabaseResult`/`dict`
  rows (not ORM model instances). Not an S1/S2 claim — revisit at S9/S11 where execution + model
  integration are documented.

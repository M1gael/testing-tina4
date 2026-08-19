# Coverage index

**Bugs live in [`known-issues/ledger.md`](../../known-issues/ledger.md).** This directory is chapter coverage only — which snippets and options were exercised, not the issue list.

A chapter is covered when every snippet and every named option is `✓` / `⚠` / `⛔` / `⏸` / `n/a` in its per-chapter file. Template: [`_TEMPLATE.md`](_TEMPLATE.md).

## Evaluation Progress

Refreshed whenever a new test file is added or a finding ID is logged. Status values:
`in-progress` (some sections touched) | `complete` (all sections implemented) | `not-started`.

| Language | Chapter | Sections covered | Status | Findings |
| :--- | :--- | :--- | :--- | :--- |
| Python | 01 — Getting Started | (whole chapter, narrative) | in-progress | PY-01-01, PY-01-03, PY-01-05, PY-01-06, PY-01-07, PY-01-08, PY-01-09, PY-01-10 |
| Python | 10 — Middleware & Security | S3, S4, S9, S10, S12 (source + coworker incident — not yet implemented verbatim) | findings logged, impl pending | ✅ PY-10-01, ✅ PY-10-02, ✅ PY-10-03 (all fixed in 3.13.4) |
| Python | 18 — Testing | S2–S12 of 13 (S13 gotchas = guidance prose) | in-progress | **[Ledger](py-ch18-testing.md)** · open: PY-18-01, 02, 03, 07b/c, 11, 12, 13, 14 + **AUD-18-1** (test_auth_flow.py missing, HIGH); fixed 3.13.4: PY-18-04, 08, 10. 11 ch18 test files. Per-section detail + gaps in the ledger. |
| Python | 06 — ORM | glance + S2–S15 + QueryBuilder Integration (all) | complete | **[Ledger](py-ch06-orm.md)** · PY-06-01…27 (PY-06-22 fixed 3.13.39). 16 ch06 test files; full suite 208 passed / 2 skipped / 4 xfailed on 3.13.39 · CLI 3.8.51. Open coverage gaps AUD-06-1…6 tracked in the ledger. |
| Python | 12 — Queues | S1–S13 (all) | complete — audit gaps closed | **[Ledger](py-ch12-queues.md)** · PY-12-01…11 + BH-50/51/52 — ALL filed on #144 (PY-12-03 last, 2026-07-02). AUD-12-1/2/3/L closed 2026-07-02 · 3.13.48 (all faithful, no new findings). 20 ch12 test files; 86 passed / 26 skipped (broker-gated) on 3.13.48. Backend matrix + per-section detail in the ledger. |
| Python | 07 — QueryBuilder | S1 from_table + S2 select (of 11 + NoSQL/Gotchas/Exercise) | in-progress | **[Ledger](py-ch07-querybuilder.md)** · none (S1+S2 fully faithful, 9/9 tests) on 3.13.47 · CLI 3.8.53. S3+ deferred per USER cap. Live mock `GET /chapter/7`. |
| Python | 02–05, 08, 09, 11, 13–17, 19–38 | — | not-started | — |
| PHP | all | — | not-started (workspace not bootstrapped) | — |
| Ruby | all | — | not-started (workspace not bootstrapped) | — |

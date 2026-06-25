# Tina4 Evaluation — Findings Log

The mutable record for the Tina4 framework evaluation: chapter coverage, the
Known Issues Log, the Bug Hunt index, and Suggested Fixes. **Conventions and
protocol live in [`readme.md`](readme.md)** — this file is data, not rules.

Known Issues / Bug Hunt table schema (defined in `readme.md` → Issue Report
Format): `ID | Status | Filed | Found | Suggested fix | Note`. The first four
columns are always populated. **Note** carries as much context as the issue
needs — how it was tested, how certain the cause is, the probe/test filename(s)
if any, or nothing when the row title says enough. **Suggested fix** is a short
inline fix, a `→ FIX-NN` pointer to a long-form write-up below, or `—`.

---

## Evaluation Progress

Refreshed whenever a new test file is added or a finding ID is logged. Status values:
`in-progress` (some sections touched) | `complete` (all sections implemented) | `not-started`.

| Language | Chapter | Sections covered | Status | Findings |
| :--- | :--- | :--- | :--- | :--- |
| Python | 01 — Getting Started | (whole chapter, narrative) | in-progress | PY-01-01, PY-01-03, PY-01-05, PY-01-06, PY-01-07, PY-01-08, PY-01-09, PY-01-10 |
| Python | 10 — Middleware & Security | S3, S4, S9, S10, S12 (source + coworker incident — not yet implemented verbatim) | findings logged, impl pending | ✅ PY-10-01, ✅ PY-10-02, ✅ PY-10-03 (all fixed in 3.13.4) |
| Python | 18 — Testing | S2, S3, S4, S5, S6, S7, S8, S9, S10, S11/S12 (of 13) | in-progress | PY-18-01, PY-18-02, PY-18-03 (re-verified open across S8 + S9), ✅ PY-18-04, PY-18-07 (-07a fixed; -07b/-07c open), ✅ PY-18-08, ✅ PY-18-10, PY-18-11, PY-18-12, PY-18-13 (5 sub-symptoms a–e), PY-18-14 (new on 3.13.39: `/health` is error-aware — HTTP 503 + `status:"error"` when any unresolved error recorded, file-backed in `data/.broken/` across restarts; S5 health-test's 200/"ok" holds only on a clean error slate). S10 clean. S11/S12 user model exercise: 5/5 pass after 4 PATCH blocks. **Re-verified 2026-06-22 on tina4-python 3.13.39 + CLI 3.8.51: all persisted Ch18 tests green; `test_health_endpoint` passes on a clean error store (the version-bump 503 was stale recorded errors, not a regression — see PY-18-14).** **Doc-fidelity audit 2026-06-22: all Ch18 section-units (S2–S7, S10) verdict faithful / faithful-with-known-findings, ZERO confirmed impl-errors, coverage complete. PY-18-07a/08/10 confirmed fixed (3.13.4); PY-18-07b/07c handled via cited PATCH blocks; PY-18-14 correctly left as a logged framework finding, not papered over in the verbatim health test.** |
| Python | 06 — ORM | S2, S3, S4, S6, S7, S8, S9, S10, S11, S12, S13/S14, S15, QueryBuilder (of 15) | complete | PY-06-01 (no DB-binding callout), PY-06-02 (no create_table shown past S3), PY-06-03 (multi-language content in the Python book), PY-06-04 (`slug` column in S4 `select_one`/`load` examples not on the Note model), PY-06-05 (glance `Post` and S6 `BlogPost` collide on `table_name="posts"`), PY-06-06 (S4/S6 positional path-param handlers serve under `tina4 serve` but raise `TypeError` via the documented Test client), PY-06-07 (write routes Bearer-gated by default, undocumented in Ch06), PY-06-08 (`BooleanField` is native `BOOLEAN` on PG; S4 `select([1])` fails), PY-06-09 (S6 handler snippets omit imports), PY-06-10 (`has_one` example refs undefined `Profile`/`user`), PY-06-11 (S7 eager example precedes descriptor declaration → silent no-op on S6 model), PY-06-12 (S7 refs undefined `Comment` model), PY-06-13 (Test client skips the write-route auth gate — serve 401 vs client 201), PY-06-14 (S8 `with_trashed("completed = ?", [1])` boolean hazard on PG), PY-06-15 (S8 `count` filters nonexistent `category` column), PY-06-16 (S3 `tina4 shell` subcommand doesn't exist — real is `tina4 console`), PY-06-17 (`tina4 console` can't import `src.*` — documented S3 interactive flow unrunnable in the program), PY-06-18 (S9 auto-CRUD shadows custom same-path routes — doc claims custom wins), PY-06-19 (S9 paginated payload is a superset of the documented keys), PY-06-20 (S9 validation-detail wording differs from the doc), PY-06-21 (S10 ORM `.save()` auto-invalidates the query cache — undocumented), ✅ PY-06-22 (S10 `clear_cache()` — clears the module-level ORM cache, not the DB-layer `Database.fetch()` cache that `cached()` reads; framework defect — **FIXED in 3.13.39**), PY-06-23 (S11 `recent()` scope uses SQLite `datetime('now', ?)` → `UndefinedFunction` on PG; `published()`/`drafts()` and dynamic `scope()`/`active()` all work), PY-06-24 (S12 `validate()` error-message wording differs from the doc example — behaviour faithful), PY-06-25 (S15 Gotcha 6: doc says `save()` doesn't validate — actual `save()` DOES validate + refuses invalid data), PY-06-26 (S15 Gotcha 7: FK-not-enforced is engine-agnostic — `ForeignKeyField` emits 0 FK DDL on PG too, not a SQLite default), PY-06-27 (S15 Gotcha 3: `find(bare_pk)` returns the record — doc calls it a mistake). S8 (soft delete) exercised 2026-06-18 on 3.13.30 — core behaviour (soft `delete`, query exclusion, `restore`, `force_delete`, `with_trashed`, `count` respects soft delete) works as documented; two verbatim filter examples break (PY-06-14/15). Running S8 in the program (`tina4 console`) surfaced PY-06-16 (S3 `tina4 shell` subcommand doesn't exist — real is `tina4 console`) and PY-06-17 (`tina4 console` can't import `src.*` — `No module named 'src'`; the documented S3 interactive `create_table()` flow is unrunnable in the program, though the ORM/soft-delete behaviour works under pytest + `tina4 serve`). S7 (eager loading + declarative descriptors) exercised 2026-06-17 on 3.13.30 — descriptors integrated onto `src/orm/author.py` (`posts`) + `blog_post.py` (`author`, `comments`); `pypy/tests/test_ch06_eager_loading.py` 7/7 (lazy `posts`/`author`, `include=` eager, posts-only nested work; comments paths assert the PY-06-12 `Comment`-not-found block). S4/S6 routes additionally driven over HTTP under `tina4 serve` — reads 200, write `POST` 401 (PY-06-07). **All snippets/examples in S2, S3, S4, S6 + the "ORM at a Glance" section exercised 2026-06-17 on tina4-python 3.13.30.** Verbatim models: `note.py` (S2), `author.py` + `blog_post.py` (S6). The S4/S6 route handlers (save/find_by_id/delete/listing; has_many/belongs_to) are implemented verbatim in `src/routes/ch06_notes.py` + `src/routes/ch06_blog.py` (documented positional path-param signatures, no patch) and driven over HTTP under `tina4 serve` — reads return 200 with the documented JSON, write `POST` 401 (PY-06-07). Eleven persisted ch06 test files (84/84): `test_ch06_note_crud.py` (S2/S3/S4/S5), `test_ch06_field_mapping.py` (S2 mapping + utils), `test_ch06_relationships.py` (S6 imperative), `test_ch06_glance.py` (glance + 8 Common Query Operations), `test_ch06_foreignkey.py` (S6 ForeignKeyField), `test_ch06_eager_loading.py` (S7), `test_ch06_routes.py` (S4/S6 handlers via the Test client: list_notes 200, get_note TypeError [PY-06-06], create_note 201 [PY-06-13]), `test_ch06_soft_delete.py` (S8), `test_ch06_autocrud.py` (S9), `test_ch06_cached.py` (S10), `test_ch06_scopes.py` (S11: published/drafts work, recent() PY-06-23 sentinel, dynamic scope()/active() work). **S11 (Scopes) exercised 2026-06-19 on 3.13.30 under `tina4 serve` (port 7150, CLI 3.8.50) + pytest.** Scopes added to `src/orm/blog_post.py` (published/drafts/recent); routes verbatim in `src/routes/ch06_scopes.py` driven over HTTP — `GET /api/posts/published` 200 (2 posts), `GET /api/posts/recent?days=7` 500 (PY-06-23: SQLite `datetime('now', ?)` → `UndefinedFunction` on PG). `published()`/`drafts()` return status-filtered lists; dynamic `BlogPost.scope("active", "status != ?", ["archived"])` → `BlogPost.active()` works as documented (pytest). Only `recent()` diverges. (Note: default python serve port 7146 was held by a stale elevated tina4 process — served on 7150 instead.) S10 (Cached Queries) exercised 2026-06-18 on 3.13.30 — both documented calls run verbatim against live PG: `cached()` returns `list[Note]`, honours the filter/limit, and genuinely serves STALE rows within the TTL window for out-of-band writes; `pinned = ?` with `[True]` binds as a real PG boolean (no `= 1` hazard). But `clear_cache()` doesn't refresh `cached()` (PY-06-22 — it clears only the module-level ORM cache, not the DB-layer `Database.fetch()` cache that `cached()` actually reads through; proven by serving cached rows after the table is dropped) and ORM `.save()` silently auto-invalidates it via the write path (PY-06-21, undocumented). S10 has no route in the chapter, so the live-program check is the ORM calls under the real DB binding (not an HTTP endpoint). **EOD 2026-06-18 — adversarial verification (two 3-agent passes): PY-06-01, 02, 08, 13, 18, 22 all confirmed real, none mis-impl; PY-06-22 reframed to the two-cache-layer root cause; PY-06-18 reframed to the `auto_crud=True` flag path (discovery imports `orm/` before `routes/` + first-match), the manual-register recipe does not reproduce. Posted on tina4-book#142 today: PY-06-08, PY-06-22, PY-06-02, PY-06-13, PY-06-18 (PY-06-01–05 were filed 06-17; PY-06-02 now appears twice — batch + standalone, candidate to collapse). Filed total on #142: PY-06-01–05, 08, 13, 18, 22 (9). Unfiled (for a later batch): PY-06-06, 07, 09, 10, 11, 12, 14, 15, 16, 17, 19, 20, 21 (13).** S9 (Auto-CRUD) exercised 2026-06-18 on 3.13.30 — `auto_crud=True` on Task (`src/orm/task.py`) + `AutoCrud.register(Note, prefix="/api/v2")` (`src/routes/ch06_autocrud.py`); 5 generated routes work over `tina4 serve` + Test client (paginated list, create, validation 400, GET/{id}, soft-aware DELETE, `AutoCrud.models()`); documented custom-route precedence is false (PY-06-18). The remaining S2/S4/S6 forms were also confirmed via a scratch coverage sweep (not retained — see test-persistence convention). Verbatim issues: `slug` snippets (PY-06-04), Post/BlogPost table_name collision (PY-06-05), Test-client dispatch parity (PY-06-06). **Re-verified 2026-06-22 on tina4-python 3.13.39 + CLI 3.8.51 (docs rev 7a4290b, confirmed latest): full persisted suite 129 passed / 2 skipped, no regressions. PY-06-22 (`clear_cache()`) now FIXED — the two `test_ch06_cached.py` sentinels flipped and were rewritten to assert the corrected behaviour. PY-06-23 (`recent()` SQLite `datetime`) unchanged (still 500 on PG). S11 re-checked under `tina4 serve` (port 7150): `published` 200, `recent` 500.** **Doc-fidelity audit 2026-06-22 (20-agent adversarial workflow): all 11 Ch06 section-units (glance, S2–S11) verdict faithful / faithful-with-known-findings, ZERO confirmed impl-errors — every doc snippet faithfully rendered, no test asserting other than the doc, every divergence justified by a logged finding or USER PATCH. Two coverage gaps found + CLOSED: (1) S2 short field aliases `IntField`/`StrField`/`BoolField` (06-orm.md:142) now exercised — they ARE the verbose classes + round-trip works (test_ch06_field_mapping.py); (2) S9 registration surfaces now exercised in new `test_ch06_autocrud_registration.py` — `auto_crud=True` on-load via the verbatim `Product` model, `AutoCrud.register(Note)` default prefix → `/api/notes`, `AutoCrud.discover('src/orm', prefix='/api')` registers all models. All work as documented. Ch06 suite now 12 test files.** **S12 (Input Validation) + S13/S14 (Build a Blog exercise & solution) exercised 2026-06-22 on tina4-python 3.13.39 (CLI 3.8.51) under pytest + `tina4 serve` (port 7150). S12: `validate()` behaviour FAITHFUL — returns a list, one entry per failed constraint, catches `required`/`min_length`/`regex`/`min_value`/`choices`, `[]` when valid; only the per-field message WORDING diverges from the doc example (PY-06-24). New `test_ch06_validation.py` (6 tests; the save path uses an isolated `products_s12_save` table so the shared Ch18 `products` is untouched — S12's `Product` reuses `table_name="products"`, PY-06-05 family). S13/S14: new verbatim `src/orm/comment.py` + `src/routes/blog.py`; all six documented endpoints (create/get author, create/list/get post, add comment) behave as documented incl. validation + 404 paths — new `test_ch06_blog_exercise.py` (12 tests, model+handler-logic style to stay collision-immune). Defining `Comment` (S14) resolves the S7 `comments` descriptor: the three PY-06-12 sentinels in `test_ch06_eager_loading.py` were reframed to assert the now-working comments eager-loading (lazy `post.comments`, `include=["author","comments"]`, nested `posts.comments`), and the S7-reader block (Comment undefined) is preserved as an isolated subprocess sentinel — **PY-06-12 stays OPEN as a doc-ORDERING finding** (S7 uses `Comment` at :697/:718/:727; defined only at S14 :1150). Serve smoke: app boots with `blog.py`+`comment.py` (router last-wins, no duplicate-route crash, router.py:358); `GET /api/posts` 200 (published+author+count); write routes 401 (PY-06-07); `GET /api/posts/{id}` is shadowed by the S6 `ch06_blog.py` handler (last-loaded wins — workspace artifact, not a doc divergence). Ch06 suite was 14 test files.** **S15 (Gotchas) exercised 2026-06-22 on tina4-python 3.13.39 — all ten gotchas' behaviour claims checked against live PG via new `test_ch06_gotchas.py` (11 tests). FAITHFUL: G1 (`save()` returns self/`False`), G2 (`find_by_id` None on miss + excludes soft-deleted), G4 (circular top-level import → ImportError; the framework's string-name descriptors sidestep it), G5 (`to_dict()` includes all fields incl. sensitive), G8 (N+1 fix snippet `select(... IN ...)` + manual grouping runs), G10 (soft delete needs both `soft_delete=True` flag + `is_deleted` field; with → row kept flagged 1, without → hard delete). DIVERGENT: G6 → PY-06-25 (`save()` DOES validate + refuses invalid data, contradicting "save() does not validate"), G7 → PY-06-26 (`ForeignKeyField` emits 0 FK constraints on PG too — engine-agnostic, not a SQLite default), G3 → PY-06-27 (`find(bare_pk)` returns the record, doc calls it a mistake). G9 → maps to PY-06-18 (custom routes do NOT take precedence; auto-CRUD shadows) + Gotcha 9 is internally contradictory (Cause "first registered wins" vs Fix "custom take precedence"). Full suite 2026-06-22: 184 passed / 2 skipped / 4 xfailed (the 5 `test_issue_46_*` failures are pre-existing, fail in isolation, unrelated to Ch06). Ch06 now 15 test files. All 15 numbered sections + glance done.** **QueryBuilder Integration exercised 2026-06-22 on 3.13.39 — `Model.query()` returns a `QueryBuilder`; all four documented fluent forms work as documented (`.select().where().order_by().limit().get()`, `.first()`, `.count()`, `.exists()`) — new `test_ch06_querybuilder.py` (5 tests). Minor (no doc claim broken in this section): `get()`/`first()` return `DatabaseResult`/`dict` rows, not ORM model instances (unlike `find_by_id`/`find`/`where`); full builder API deferred to Ch07. **Ch06 COMPLETE** — glance + S2–S15 + QueryBuilder all exercised; 16 ch06 test files; full suite 189 passed / 2 skipped / 4 xfailed (5 `test_issue_46_*` pre-existing, unrelated).** **Verification pass 2026-06-22 (fidelity audit drove test-quality fixes): `test_ch06_note_crud.py` now asserts `save()` returns `self` (was `is not False`), proves `order_by created_at DESC` actually orders (explicit out-of-order timestamps), and round-trips `create()` values; `test_ch06_autocrud.py` closed the S9 endpoint-table coverage gap — now exercises GET `/api/tasks/{id}` + PUT `/api/tasks/{id}` + asserts the paginated `total`/`data` reflect real rows. (`snake_to_camel`/`camel_to_snake` already covered in `test_ch06_field_mapping.py`.) Fidelity audit verdict for the 12 audited Ch06 units: 0 impl-errors, all faithful/faithful-with-findings; weak-assertion + coverage gaps now closed.** **All-out verification (resumed — full 17-unit Ch06+Ch18 fidelity audit completed) 2026-06-22: ONE impl-error found + FIXED — S14 Author (`06-orm.md:1120`) declares `name min_length=2` but `src/orm/author.py` carried only `required=True`; aligned `author.py` to the S14 definition and added boundary test `test_ch06_blog_exercise.py::test_create_author_name_min_length`. Closed two route-coverage gaps in `test_ch06_routes.py` — `get_author`/`get_post` now DEMONSTRATE the PY-06-06 Test-client `TypeError` (previously only claimed in the header). 0 remaining impl-errors across all 17 units. Full suite 208 passed / 2 skipped / 4 xfailed (the 5 `test_issue_46_*` failures are the BH-49 gap-sentinel flips — see BH-49 row). The 53-finding ADVERSARIAL verification sweep (Phase B) is now COMPLETE — see the "All-out verification pass" note above the KI Log table: 0 refuted, 36 confirmed real, 12 stale-fixed (BH-49 marked fixed + sentinels reframed), 5 unconfirmable (CLI/web — runtime re-check owed before EOD filing).** |
| Python | 12 — Queues | S1 (concept, no code), S2 (config — **backend-parity done: file/rabbitmq/mongodb work identically; kafka diverges, PY-12-02**), S3 (create/push — **file-backend complete**), S4 (consume — **file-backend complete; continuous-poll worker loop now exercised live in the backend matrix; PY-12-07: consume(job_id) broker-broken**), S5 (priority — **file-backend complete**), S6 (job lifecycle — **file-backend complete; PY-12-05**), S7 (retry & dead letters — **file-backend complete; PY-12-04, PY-12-06**) (of 13; chapter rewritten + deps bumped to 3.13.43 on 2026-06-24) | in-progress | PY-12-01 (S3 blockquote says backend is "selected via environment variables, not constructor parameters" — but `Queue(..., backend=...)` IS an accepted constructor kwarg that selects the backend; found during S2 config impl), PY-12-02 (S2/S9 "work identically" claim holds for file/RabbitMQ/MongoDB but is FALSE for Kafka — `size()` always 0, immediate `pop()`/drain-once empty; verified with live Docker brokers), PY-12-03 (the S6/S7 retry→dead-letter lifecycle + management API — `size(status)`, `dead_letters()`, `retry()` revive, `purge()` count — diverges per backend: RabbitMQ never dead-letters, MongoDB misses `size(status)`/`retry()`-revive, only the file backend is fully faithful; full op×backend matrix verified with live Docker brokers), PY-12-04 (file `queue.retry()` no-arg revives only ONE of N dead, not "every"), PY-12-05 (file `job.retry()` leaves a dead-letter duplicate — same id in pending AND dead), PY-12-06 (file `size("failed")`==0 while `failed()` lists the job), PY-12-07 (documented S4 `consume(job_id)` yields nothing on ANY broker — `pop_by_id` is hardcoded file-only). **Framework-code twins logged as BH-50** (RabbitMQ `fail()` never dead-letters — attempts don't persist), **BH-51** (`size("dead"/"failed")` hardcoded 0 on all 3 broker adapters), **BH-52** (Mongo `Queue.clear()` `AttributeError` on a fresh queue — missing `_ensure_connected()`); these are tina4-python code bugs (fix lives in the framework), distinct from the tina4-book doc-fidelity PY rows. **Filed 2026-06-24 on tina4-book [#144](https://github.com/tina4stack/tina4-book/issues/144) (Tina4 Chapter Queues) as 4 comments: PY-12-02, BH-50, BH-51, BH-52.** NOT filed: PY-12-01 (minor S3 clause) and PY-12-03 (its RabbitMQ + size("dead") parts are covered by BH-50/BH-51, but its **MongoDB `retry()`-doesn't-revive** divergence is not captured in any filed comment). **S1+S2+S3 exercised 2026-06-23 on tina4-python 3.13.39 (CLI 3.8.51) under pytest.** S1: concept prose, no code. S2 (`test_ch12_queue_config.py`, 4 tests): file backend is the zero-config default, first push auto-creates `data/queue/<topic>`, `TINA4_QUEUE_PATH` redirects the dir; `backend=` kwarg yields LiteBackend (`file`) vs RabbitMQBackend (`rabbitmq`). S3 (`test_ch12_queue_create_push.py`, 5 tests, all faithful, no new findings): `Queue(topic=)` names the queue, `push()` returns a message id, payload is any JSON-serialisable dict (nested round-trip peeked from the stored job file), `produce()` pushes to a named topic, `size()` reflects pending count. **S4+S5 exercised 2026-06-24 on tina4-python 3.13.43 (after the doc refresh + framework bump), under both pytest and `tina4 serve`.** S4 (`test_ch12_queue_consume.py`, 5 tests, all faithful): `consume(poll_interval=0)` drains once and stops, `consume(iterations=N)` stops after N jobs, `consume(job_id=)` yields one job once then returns, `pop()` returns the highest-priority job then `None` when empty, `complete()` removes / `fail()` re-enqueues under the retry limit. S5 (`test_ch12_queue_priority.py`, 2 tests, all faithful): the verbatim priority example pops `urgent → normal → also normal` (highest-priority first, ties oldest-first), and a `delay_seconds` job stays hidden regardless of priority (file backend enforces ordering; brokers follow their own semantics per the doc, not exercised here). No new findings in S4/S5. **S2 backend-parity — DONE 2026-06-24 · 3.13.43 (was the deferred blocker):** stood up live Docker brokers (`rabbitmq:3`, `mongo:7`, `apache/kafka:3.7.0`), installed `pika`/`pymongo`/`confluent-kafka` per S2, and ran the identical documented code path against each. **file / RabbitMQ / MongoDB satisfy the "work identically" claim** — identical push→id, pop→payload, `consume(poll_interval=0)` drain→`[1,2]`, `size()`→0 (`test_ch12_queue_backend_parity.py`, 3 pass). **Kafka diverges → PY-12-02**: `size()` is hardcoded 0 and an immediate `pop()`/drain-once yields nothing (first delivery ~16s via a long-running `consume()`) — `test_ch12_queue_kafka_semantics.py` (2 divergence sentinels). Correction to the earlier note: kafka/rabbitmq CAN be selected without their drivers (raw-socket fallbacks); only **mongodb** hard-requires `pymongo` at construction. **Then the FULL documented op surface (priority, delay, cross-topic, fail→retry→dead-letter, `size(status)`, `dead_letters()`, `retry()` revive, `purge()`, `consume(iterations=)`) was exercised per backend → `test_ch12_queue_backend_lifecycle.py` (21 tests, per-backend expectation maps for file/rabbitmq/mongodb) — surfacing PY-12-03** (broker retry/dead-letter/management divergences; full matrix in the ledger). Tests are broker-gated (skip when a broker is down — logged blocker, not rigged). Full ch12 suite: 42 passed (live brokers up). These are library sections (no routes until S7/S11), so doc-fidelity tests are pytest-level. **Live per-section mock — generalized 2026-06-24 into a registry-driven engine, `src/routes/chapter_explorer.py`, serving `GET /chapters` (index) + `GET /chapter/{num}` (back-compat `GET /queue` → ch12) under `tina4 serve`** (verified port 7150, per Workflow step 6; queue-specific write API `POST /api/queue/push` + `GET /api/queue/topics` stay in `queue_explorer.py`): per section (S2–S5) it shows the verbatim `12-queues.md` snippet and EXECUTES it live, surfacing real return values / stdout / files created — S2 file-default + env-var backend selection, S3 create/push/size/produce/JSON-payload, S4 consume drain/iterations/job_id/pop, S5 priority order + delayed-hidden, PY-12-01 shown as a divergence (verified on the served path 2026-06-24: 11 pass, 1 diverge). **Caveat: the S2/S3 mock snippets + their `12-queues.md` line refs predate the 2026-06-24 chapter rewrite — reconcile against the current chapter before filing.** Sandbox-isolated demos (no leak into real storage, verified) + a hands-on `@noauth() POST /api/queue/push` form writing to the visible `data/queue`. Restart serve after edits (`--no-reload`). **Coverage ledger (per-snippet/option ✓/⛔/⏸, version-stamped sign-offs):** [`coverage-ledger/py-ch12-queues.md`](coverage-ledger/py-ch12-queues.md). S2 backend-parity now resolved there (live Docker brokers → PY-12-02); remaining open item: S4 continuous-poll. Extended section-by-section as the chapter progresses. **Re-verification sweep 2026-06-25 on tina4-python 3.13.47 (was 3.13.43; maintainer shipped .44–.47 with independent queue work — Kafka dequeue assignment-wait + RabbitMQ connector size/handshake fixes, NOT a response to our #144 comments, which the fix commit predates by ~23h). Doc unchanged (Ch12 blob sha identical to upstream). Full ch12 queue suite re-run: ALL 5 filed/logged findings (PY-12-02, PY-12-03, BH-50, BH-51, BH-52) STILL REPRODUCE — none fixed. The only behaviour change: Kafka drain-once now blocks for the 15s assignment window instead of failing fast, but still returns `[]` for a freshly-pushed message (latest-offset). The drain sentinel was de-flaked (unique topic + short assign timeout); suite now 27 passed ×3 deterministically.** **S6 (Job Lifecycle) + S7 (Automatic Retry and Dead Letters) implemented verbatim 2026-06-25 · 3.13.47 — file backend (the documented default; S6/S7 carry no per-backend caveat except S7 `retry_backoff` "applies to the file backend"). New `test_ch12_queue_lifecycle_s6.py` (7) + `test_ch12_queue_retry_deadletter_s7.py` (11), all 18 pass. Faithful/green: `complete()` terminal, `fail()` increments+re-enqueues, `reject()` alias, `job.retry()` re-queue, payload/id/attempts/error fields, claimed-on-pop-not-retried, `max_retries=3`→3-attempts→dead, default `max_retries`=3, `failed()` dicts, `dead_letters()` Job objects, `retry(job_id)`, `retry_failed()`, `retry_backoff` hold-then-release, `size`/`purge` pending+dead. THREE new FILE-backend divergences found (the file backend is the doc's reference!): PY-12-04 (`queue.retry()` no-arg revives only ONE of N dead, not "every"), PY-12-05 (`job.retry()` leaves a dead-letter duplicate — same id in pending AND dead), PY-12-06 (`size("failed")`==0 while `failed()` lists the job). Also wired S6/S7 into the live mock `src/routes/chapter_explorer.py` (`GET /chapter/12`), verified under `tina4 serve` on 3.13.47 (port 7146): S6 2 pass+1 diverge, S7 3 pass+2 diverge. Full ch12 suite: 61 passed. Ledger: [`coverage-ledger/py-ch12-queues.md`](coverage-ledger/py-ch12-queues.md) S6/S7 signed off.** **S2 exhaustive backend showcase 2026-06-25 · 3.13.47 (USER-requested visual): new `src/routes/queue_backend_matrix.py` serves `GET /queue/backends` (linked from `/chapter/12`) — runs the FULL documented queue API (20 ops: push/pop/produce/consume drain+iterations, priority, delay, size/purge by status, fail→retry→dead-letter, failed/dead_letters, retry/retry_all/retry(job_id), reject, job.retry) against ALL 4 live backends on each load and renders a per-claim grid (works / documented-diff / diverges / blocked). Kafka included exhaustively (daemon-thread timeouts so non-delivery shows, never hangs). Verified live with all brokers up: file 17 pass/3 diverge (PY-12-04/05/06), RabbitMQ 9/2 doc/8/1 na, MongoDB 11/1 doc/8, Kafka 2/18. This is the visual proof of the S2 "work identically" claim per backend.** **Average-user API-surface pass 2026-06-25 · 3.13.47: enumerated the full public Queue+Job surface from source and expanded the matrix to 30 ops (added continuous consume() worker loop, consume(job_id), consume(batch_size=), process(handler), pop_batch(), pop_by_id(), clear(), get_topic(), retry_backoff, job.to_json()). New finding PY-12-07 — `consume(job_id=)` (documented S4) yields nothing on every broker because `pop_by_id()` is hardcoded file-only (sentinel `test_consume_job_id_file_only[rabbitmq|mongodb]`, 3 pass). BH-52 (mongo `clear()` crash) now also shown live in the matrix. Live tallies (30 ops): file 27/3, RabbitMQ 16/3 doc/10/1 na, MongoDB 18/1 doc/11, Kafka 4/26. Deferred (not average-user): `visibility_timeout` constructor param (undocumented; candidate probe vs S6:240).** **Adversarial verification 2026-06-25 (16-agent workflow, one skeptic per finding + one auditor per section, read-only): ALL 9 doc-fidelity findings confirmed REAL — PY-12-01 (.96), PY-12-02 (.85), PY-12-03 (.90), PY-12-04 (.98), PY-12-05 (.82), PY-12-06 (.88), PY-12-07 (.96), BH-50 (.90), BH-51 (.95) — neither refutable as doc-misread nor test-artifact; skeptics independently re-read the whole chapter for rescuing caveats (none) and re-confirmed via source + live brokers. BH-52 verdict = "test-artifact" in the doc-fidelity sense = CORRECTLY framed as out-of-Ch12-scope (`clear()` is undocumented; real code bug, not a doc divergence) — matches how it's already logged. Section thoroughness audit (S2 thorough; S3–S7 minor-gaps): gaps logged in the ledger Open items — S3 `priority`/`delay_seconds` default-0 not asserted; S4 continuous-poll consume() (sleep-when-empty + mid-stream arrivals) untested; S5 priority via `consume()` (only `pop()` tested) + broker "stores priority on message" not verified; S6 `job.retry(delay_seconds=)` arg never passed; S7 `purge("failed")` never called + consume-loop auto-retry only proven via pop+fail.** |
| Python | 02–05, 07–09, 11, 13–17, 19–38 | — | not-started | — |
| PHP | all | — | not-started (workspace not bootstrapped) | — |
| Ruby | all | — | not-started (workspace not bootstrapped) | — |

## Known Issues Log

All confirmed framework bugs and documentation discrepancies are tracked here.
Status values: `open` | `fixed` | `workaround` | `pending-retest` | `not-a-bug`.
Two row kinds share this table: `PY-NN-NN` doc-fidelity findings (from walking chapters) and `BH-<n>` assigned bug-hunt investigations (against upstream `tina4-python` issues; see the *Bug Hunt* note below). Column schema is defined in [`readme.md`](readme.md) → *Issue Report Format*.
**Filed** is the upstream GitHub issue/PR link, or `no` if not yet filed. **Found**
is the log date · the framework version it was found on. **Note** carries the detail —
how/whether it was tested, how certain the cause is, and the probe/test filename(s)
if any. **Suggested fix** is a short inline fix, a `→ FIX-NN` pointer, or `—`.

Both tina4-book testing/middleware filings ([#140](https://github.com/tina4stack/tina4-book/issues/140), [#141](https://github.com/tina4stack/tina4-book/issues/141)) landed and the PY-18/PY-10 rows marked `fixed` were resolved in **tina4-python 3.13.4 (2026-06-05)**; their probes flip to bug-absent against ≥3.13.4 (regression sentinels).

**All-out verification pass — 2026-06-22 · 3.13.39 (CLI 3.8.51).** Full implementation-fidelity audit (17 Ch06+Ch18 units: 0 impl-errors after fixing the S14 Author `min_length=2` drop + strengthening weak assertions / closing coverage gaps) plus adversarial verification of all 53 logged findings (7 grouped agents, disprove-by-default). Verdict: **0 refuted** (every finding legitimate), 36 confirmed real, 12 stale-fixed (11 already marked; **BH-49 newly marked fixed** here — all 3 gaps closed, the 5 gap sentinels reframed to assert-absent guards), 5 **unconfirmable by source** — CLI/website runtime claims that MUST be re-checked live before EOD filing: **PY-06-16** (`tina4 shell` absent), **PY-06-17** (`tina4 console` `src.*` import), **PY-01-07** (`tina4 install` naming), **PY-01-08** (`tina4 doctor` output), **PY-01-10** (tina4.com `/python` landing-page install — filed #143). Suite at pass end: 213 passed / 2 skipped / 4 xfailed / 0 failed.

| ID | Status | Filed | Found | Suggested fix | Note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| PY-01-01 | open | no | 2026-06-03 | → FIX-01 | **The Getting Started page's top section is structurally confused — three distinct concepts (external prerequisites, the Tina4 CLI, and the `tina4-python` framework package) are collapsed into a single "What You Need / Install" block.** Three concrete symptoms a reader hits: (a) **Inconsistent prereq treatment** — Python is only verified via `python3 --version`, but `uv` gets three platform-specific install snippets (macOS/Linux curl, Windows PowerShell, Cargo). Either both prereqs get install instructions or neither does. (b) **Tina4 CLI vs. `tina4-python` framework package not distinguished** — a reader can't tell whether "Tina4 CLI" is the framework or just a tool. The actual `tina4-python` PyPI package only surfaces buried in `uv` output during `tina4 init`. (c) **The Tina4 CLI is listed as prereq #3 in "What You Need" AND has its own "Installing the Tina4 CLI" section directly below** — framed as both an external prerequisite and as something you install in step 1, contradictory. Prereqs should be external deps only (Python, uv); the CLI belongs purely in the install section. Single structural fix in Suggested Fixes: see **FIX-01** — restructure the page into three top-level headings (Prerequisites / Install the Tina4 CLI / Create your first project) that mirror the actual dependency chain. |
| PY-01-03 | open | no | 2026-06-03 | → FIX-02 | Getting Started page offers `cargo install tina4` as a CLI install option and describes the CLI as "Rust-based", but Cargo (Rust toolchain) is never listed as a prerequisite and there is no link to install it. A reader who picks the cargo path without Rust installed hits a wall with no doc support. Recommend either removing the cargo option (Homebrew/curl/PowerShell already cover all platforms) or moving it under an "Advanced / from source" section with a note about needing Rust ([rustup.rs](https://rustup.rs)). |
| PY-01-05 | open | no | 2026-06-03 | Add a "Versioning & updates" subsection: which version is which, how to update each, that CLI and framework evolve independently. | (Light suggestion.) The CLI/framework version decoupling is not explained anywhere in the docs. The `tina4` CLI is installed globally and updated by re-running the installer; the `tina4-python` framework is per-project and updated via `uv add tina4-python@latest`. Users have to derive this from first principles. Nice-to-have: a short "Versioning & updates" subsection on the Getting Started page covering (1) which version is which, (2) how to update each, (3) that they evolve independently. |
| PY-01-06 | open | no | 2026-06-03 | Add a one-line note: PyPI package is `tina4-python` (imported as `tina4_python`); `tina4 init` adds it, else `uv add tina4-python` / `pip install tina4-python`. | Docs only show the greenfield happy path (`tina4 init python my-app`) and never reveal the underlying package name or direct install commands. Consequences: (1) `uv` is listed as a hard prerequisite but the reader never types a `uv` command — the CLI invokes it invisibly. (2) The PyPI package name (`tina4-python`) does not match the framework's marketing name (`tina4`), and a Python dev's natural reflex `pip install tina4` fails with `No matching distribution found for tina4`. Import path is also `tina4_python`, not `tina4`. (3) A reader migrating an existing project, or troubleshooting, has no fallback path documented. Recommend a one-line note on the Getting Started page: *"On PyPI the package is `tina4-python` (imported as `tina4_python`). `tina4 init` adds it for you; if you're adding it to an existing project use `uv add tina4-python` (or `pip install tina4-python`)."* |
| PY-01-07 | open | no | 2026-06-03 | Rename `tina4 install` → `install-runtime`/`setup-runtime`, or make the help text explicit that it installs a language runtime, not Tina4 itself. | `tina4 install <lang>` subcommand naming is ambiguous: it installs the *language runtime* (Python itself), but a reader's intuition reads "install python = install the Python edition of Tina4." The framework install actually happens during `tina4 init python .` (as a per-project `uv add tina4-python`). Recommend either renaming `tina4 install` → `tina4 install-runtime` / `tina4 setup-runtime` for clarity, or making the help text explicit: *"Install a missing LANGUAGE runtime (not Tina4 itself — `tina4 init` installs the framework per project)."* |
| PY-01-08 | open | no | 2026-06-03 | Retitle the doctor "Tina4 CLIs" section → "Language-Specific Frameworks" (or hide it outside a project); note the entries auto-install via `tina4 init`. | `tina4 doctor` exposes a section titled **"Tina4 CLIs"** listing `tina4python`, `tina4php`, `tina4ruby`, `tina4nodejs`, `vite` and reporting them as "not found" with manual install commands (`pip install tina4-python` etc.). Three problems: (1) **The section title is wrong** — these are not CLIs in any meaningful sense, they are the framework packages themselves (`tina4-python` and friends). The CLI face each one exposes is plumbing the main `tina4` Rust CLI delegates to; users should never invoke `tina4python` directly. Better label: **"Language-Specific Frameworks"** — names what these actually are (the Tina4 framework, one per language) without exposing the plumbing CLI face. (2) **The "not found" warning is misleading** outside a project context — these packages are *expected* to be absent until `tina4 init` adds them to a project's `.venv`. (3) **The suggested install commands pollute global runtimes** when run outside a venv. Recommend: doctor should hide the section entirely outside a project, OR retitle it and add a note that the entries auto-install via `tina4 init`. The "four-names" confusion (`tina4`, `tina4-python`, `tina4python`, `tina4_python`) is largely caused by exposing this row as if it were a separate user-installable thing — it's not, it's the framework. |
| PY-01-09 | open | no | 2026-06-19 · 3.13.38 | Make CLI help printable on non-UTF-8 consoles: reconfigure stdout to UTF-8 (`sys.stdout.reconfigure(encoding="utf-8")`) before `_help()`, or drop the non-cp1252 glyphs (`→` and the em-dash in the banner) from the help string. Also accept `--version`/`-V`. | The pip-shipped `tina4python` console script crashes on a stock Windows console (cp1252) on **bare invocation** and on **any unknown command**. `_help()` at `tina4_python/cli/__init__.py:207` `print()`s a help banner containing `→` (U+2192); cp1252 can't encode it, so the print raises `UnicodeEncodeError: 'charmap' codec can't encode character '→' in position 1703: character maps to <undefined>` and the process dies with a traceback instead of showing help. `tina4python --version` is also unsupported ("Unknown command: --version") and routes through the same crashing `_help([])`. Surfaced while testing the Chapter 1 Getting Started, S8 Manual Setup (No CLI) path — `pip install tina4-python` then running `tina4python`, the command name surfaced by `tina4 doctor` (see PY-01-08). Reinforces PY-01-08: the framework exposes `tina4python` to users yet its first-run output is unusable on a default Windows shell. Verified on a clean global `pip install tina4-python==3.13.38` (Python 3.13, Windows). Origin: `cli/__init__.py:207` `_help()` prints non-ASCII help text with no stdout re-encode; `main()` dispatch at `cli/__init__.py:126`/`:157` routes both no-arg and unknown-arg to `_help`. |
| PY-01-10 | open | [#143](https://github.com/tina4stack/tina4-book/issues/143) | 2026-06-19 · 3.13.38 | The landing-page quickstart must install the `tina4` CLI before invoking it: add the CLI install step ahead of `tina4 init` (Windows `irm https://raw.githubusercontent.com/tina4stack/tina4/main/install.ps1 \| iex`; brew/install-script/cargo elsewhere), OR replace `tina4 init`/`tina4 serve` with the No-CLI flow (`python app.py`) so the sequence is self-consistent for a from-zero reader. See FIX-07 (consolidated Installation / Update page). | **The primary install path on the Python landing page fails verbatim.** The Python book landing page (`/python/`, "Installation" section — the intuitive entry point at `/python/#installation`) presents the whole install as four commands with no prerequisites and no CLI-install step: `pip install tina4-python` → `tina4 init my-project` → `cd my-project` → `tina4 serve`. Followed exactly it breaks at step 2: `pip install tina4-python` installs the framework package + the `tina4python` script, **not** the `tina4` Rust CLI, so `tina4 init` → `'tina4' is not recognized`. The page's own framing ("installs one package, and starts the server") implies a single install, but the commands require two separate installs (pip package **and** the Rust CLI). Directly contradicts Chapter 1 Getting Started, which installs the CLI separately (brew/install script/cargo) and uses the pip package only on the "S8 Manual Setup (No CLI)" path via `python app.py` — never `tina4 init`. Reproduced verbatim on a clean global `pip install tina4-python==3.13.38` (Windows): pip succeeds, `tina4 init` not recognized. Related: PY-01-01 (same CLI-vs-framework conflation, but on the deeper Getting Started page); PY-01-09 (if a reader instead tries the `tina4python` script the page never mentions, it crashes on a cp1252 Windows console). |
| PY-18-01 | open | no | 2026-06-03 | Fix S3 to the honest signatures (`assert_true(actual, message='')`); document all 13 exported assertion functions, not 7. | **Section 3 (Assertion Methods) misdocuments existing assertions and omits six others entirely.** (1) Signature inconsistency: documented signatures show `assert_true/false/none/not_none(actual, expected, message)` — 3 args — but every example call uses 2 args: `assert_true(True, "Should be true")`. Confirmed runtime signatures (via `inspect.signature`): `assert_true(actual, expected=<sentinel>, message='')`. The function accepts both 2-arg `(actual, message)` and 3-arg `(actual, expected, message)` calls via sentinel detection — but `expected` is **semantically meaningless** for single-value assertions. The 2-arg examples are the intended usage; the signature heading is misleading. Recommend deprecating the `expected` parameter and updating docs to the honest signature `assert_true(actual, message='')`. (2) `assert_raises` has an undocumented overload — runtime signature is `(callable_or_exception, exception_class=None, message='')`, suggesting it accepts either a callable OR an exception class as the first arg, but the docs show only the `(callable, exception_class, message)` form. (3) **The module exports six undocumented assertion functions.** Chapter Section 3 documents 7 (`assert_equal`, `assert_true`, `assert_false`, `assert_raises`, `assert_not_equal`, `assert_none`, `assert_not_none`). Actual exports from `tina4_python.test`: those 7 plus `assert_almost_equal`, `assert_greater`, `assert_less`, `assert_in`, `assert_not_in`, `assert_is_instance` — six common assertions that aren't mentioned anywhere in the chapter. Recommend extending Section 3 to cover all 13. |
| PY-18-02 | open | no | 2026-06-03 | Make `tina4 init` install pytest; drop the "no external packages" claim. Workaround: `uv add --dev pytest`. | Section 1 claims: *"Tina4 includes an inline testing framework. **No external packages.** No configuration. Write a test. Run it. Done."* But `tina4 test` on a fresh `tina4 init python .` scaffold fails with `No module named pytest`. Pytest is a hard requirement — the CLI invokes it directly. The `pyproject.toml` scaffolded by `tina4 init` does declare `pytest>=9.0.3` in `[dependency-groups] dev`, but the dep is not actually installed into `.venv` during init, so the first `tina4 test` invocation breaks. Two bugs in one: (a) docs claim "no external packages" but pytest is required; (b) `tina4 init` declares pytest but doesn't install it. Workaround: `uv add --dev pytest` after init. **Verify-pass 2026-06-22 · 3.13.39: the DOC-CLAIM half is FIXED — current `18-testing.md` S1 (line 26) no longer says "No external packages"; it now reads "Tina4 ships a `Test` class layered on top of pytest" (bundled with the PY-18-04 doc rewrite). The `tina4 init` half (does init actually install pytest into `.venv`?) is a CLI-runtime claim, NOT re-verified this pass — stays open pending a `tina4 init` runtime check.** |
| PY-18-03 | open | [#140](https://github.com/tina4stack/tina4-book/issues/140) | 2026-06-03 | → FIX-03 (`--file`); otherwise implement `--method`/`--verbose`/`--cov*` in the CLI or remove the flag examples from the docs. | Section 8 documents CLI flags `--file`, `--method`, `--verbose`, and (Section 9) `--cov`/`--cov-report` — **none of these flags exist**. `tina4 test --help` shows zero options besides `--help`. Either the flags need to be implemented in the CLI, or the docs need to be reduced to "run all tests" with no flag examples. **Re-verified 2026-06-05 on CLI 3.8.28 + tina4-python 3.13.4 — still open.** `--verbose` and `--file` both raise `error: unexpected argument '--<flag>' found`. S9 re-verification 2026-06-05: `--cov=src` and `--cov-report=term`/`=html` reject with the same error; `uv run python -m pytest --cov=src --cov-report=term` works against the same suite (73 statements, 97% covered), so the underlying tool path is fine — the wrapper just drops the flags. |
| PY-18-04 | fixed | [#140](https://github.com/tina4stack/tina4-book/issues/140) | 2026-06-03 · pre-3.13.4 | — (fixed 3.13.4 via doc rewrite; optional output formatter is → FIX-04) | **Fixed in tina4-python 3.13.4 (2026-06-05) via doc update — chapter S1 now says *"Tina4 ships a `Test` class layered on top of pytest"* and every output example shows real pytest output.** Originally: **Tina4's "inline testing framework" is actually a thin pytest wrapper, and the chapter misrepresents it as standalone.** Three concrete symptoms a reader hits: (a) Section 1 frames it as *"an inline testing framework. No external packages. No configuration."* — but it's pytest underneath, requiring pytest to be installed (see PY-18-02) and inheriting all of pytest's discovery/config/output behavior. (b) Section 2's claim *"Every `.py` file in that directory is auto-discovered when you run `tina4 test`"* is false — pytest's default requires `test_*.py` or `*_test.py` prefix; a file named `ch18_basic.py` is silently skipped (`collected 0 items`, no warning). (c) Every output example in the chapter (Sections 1, 2, 4, 8 PASS examples, 8 FAIL example) shows a fictional Tina4-styled format (`Running tests...`, `BasicTest`, `[PASS] test_addition`, `N tests, N passed, 0 failed (Ns)`). Actual output is raw pytest (`================ test session starts ================`, dots, `N passed in Ns`). Recommend: rewrite Section 1 to acknowledge `tina4 test` is a pytest wrapper, state that pytest's discovery rules / config / output format apply, and reframe Tina4's value-add as the `Test` base class (with `self.get`/`self.post`/etc.) plus the `assert_*` helpers. Either replace every output example with real pytest output, or implement a custom output formatter to match what the docs show. |
| PY-18-07 | open | [#140](https://github.com/tina4stack/tina4-book/issues/140) | 2026-06-03 | Make S4 self-contained: `Product` import (-07a, done 3.13.4), show the required DB bind (-07b), document that `where()` returns a 2-tuple only with `with_count=True` (-07c). | **PY-18-07a fixed in tina4-python 3.13.4 (2026-06-05) — `from src.orm.Product import Product` is now in S4 of the chapter (line 170 of refreshed `18-testing.md`). Sub-symptoms -07b (claimed auto test DB) and -07c (`Product.where` 2-tuple unpack without `with_count=True`) remain open.** Originally: **Section 4 (Testing ORM Models) is broken end-to-end as written.** A reader copy-pasting the snippet hits a cascade of failures: (1) `NameError: name 'Product' is not defined` — `Product` is used throughout but never imported; the chapter only imports `Test` and `assert_*` from `tina4_python.test`. (2) After adding `from src.orm.product import Product`, the next failure is `RuntimeError: No database bound. Call orm_bind(db) or set TINA4_DATABASE_URL in .env` — but Section 4 explicitly promises *"By default, `tina4 test` uses a separate test database... created at `data/test.db` (SQLite) and is reset before each test run."* That default does not exist. `tina4 init` does not set `TINA4_DATABASE_URL`. The chapter frames the env var as optional ("If you want to use a different database for tests, set it in `.env`") but it's actually required. (3) Even with both fixed, the snippet relies on ORM APIs the section never documents: `Product.find(id)` returns model-or-None (contract not stated), `Product.where(sql, params)` returns the unusual tuple `(records, count)` (no explanation), `product.in_stock = True` assumes a boolean field type but Chapter 6 documents no `BooleanField`, and `save()`/`delete()` return semantics aren't specified anywhere. (4) Reset-between-runs claim is also unverified — even with a bound DB there's no evidence the framework wipes it. **Recommend: rewrite Section 4 to be self-contained.** Include the `Product` import, show the required `.env` line, define the Product model inline (or recap from Ch 6), and document each ORM method's contract. Or, alternatively, make the framework actually deliver the "auto test DB, just write a test" experience the section promises. |
| PY-18-08 | fixed | [#140](https://github.com/tina4stack/tina4-book/issues/140) | 2026-06-03 · pre-3.13.4 | — (fixed 3.13.4 via doc rewrite; see Note) | **Fixed in tina4-python 3.13.4 (2026-06-05) via doc update — all three sub-symptoms addressed across the chapter: positional body → `json=` keyword, `resp.status_code` → `resp.status` (~14 sites), and S5 "Response Object" reference rewritten to list `resp.status`, `resp.body` (bytes), `resp.text()`, `resp.json()`, lowercased headers.** Originally: **Section 5 (Testing Routes) documents a test client API that doesn't match what the framework actually exposes.** Three concrete mismatches a reader hits when copy-pasting the snippet: (a) **Body argument is keyword-only, docs show positional.** Docs example: `self.post("/api/products", {"name": "Widget", ...})`. Actual signature: `Test.post(self, path: str, *, json=None, body=None, headers=None)` — the body must be passed as `json=` or `body=`, never positionally. Result: every `self.post(path, dict)` call in the chapter raises `TypeError: Test.post() takes 2 positional arguments but 3 were given`. Same applies to `self.put()` and `self.patch()`. (b) **`TestResponse` has no `status_code` attribute.** Section 5's "Response Object" subsection explicitly lists `resp.status_code` as a property. Real attribute is `resp.status`. Every `assert_equal(resp.status_code, 200, ...)` from the docs raises `AttributeError: 'TestResponse' object has no attribute 'status_code'`. (c) **Two undocumented convenience attributes exist.** Real `TestResponse` exposes `resp.json` (parsed JSON body) and `resp.text` — the chapter never mentions them. Readers manually do `json.loads(resp.body)` when `resp.json` would be simpler. Recommend: rewrite Section 5 to match the real API — (1) show keyword form `self.post("/api/products", json={...})`, (2) replace every `resp.status_code` with `resp.status`, (3) document `resp.json` and `resp.text` alongside the other Response Object attributes. |
| PY-10-01 | fixed | [#141](https://github.com/tina4stack/tina4-book/issues/141) | 2026-06-04 · pre-3.13.4 | — (fixed 3.13.4; probe `test_ch10_middleware_probe.py`) | **Fixed in tina4-python 3.13.4 (2026-06-05) — framework now ships `_invoke_handler_with_middleware` (`server.py:1238`) and `_is_function_middleware` (`server.py:1154`), forming a Russian-doll continuation chain. Verified end-to-end by `Ch10FunctionMiddlewareEndToEndProbe`: function middleware body runs before/after the handler, multi-layer chains nest in declaration order, and omitting `await next_handler(...)` short-circuits the chain.** Originally: **Function-based middleware is documented but not implemented.** Section 3 ("Writing Custom Middleware") states *"Tina4 Python supports two styles of middleware: function-based and class-based"* and shows the canonical signature `async def fn(request, response, next_handler): ... result = await next_handler(request, response); return result`. The chapter has 8+ examples using this pattern across S3, S4, S6, S7, S8, S10 (`log_middleware`, `require_json`, `maintenance_mode`, `require_api_key`, `inject_user_agent`, `add_security_headers`, `api_key_middleware`, `auth_middleware`). Empirically the framework dispatcher (`server.py:1154-1185`) only handles class-based middleware — it iterates `dir(instance)` looking for attributes starting with `before_` / `after_`. A function passed to `@middleware(fn)` is stored in `route["middleware"]` but its body never executes because `dir(fn)` returns no `before_*` attributes. `grep -rn next_handler tina4_python/` returns 0 hits across the entire framework. Recommend either implementing the documented function-based path or removing S3 "Function-Based Middleware" + all `next_handler` examples from the chapter. Source: framework read + coworker incident (a developer wrote a JWT auth middleware following S3 verbatim; the body never ran, the route was silently unauthenticated). |
| PY-10-02 | fixed | [#141](https://github.com/tina4stack/tina4-book/issues/141) | 2026-06-04 · pre-3.13.4 | — (fixed 3.13.4; probe `test_ch10_middleware_probe.py`) | **Fixed in tina4-python 3.13.4 (2026-06-05) — `@middleware()` is now purely additive. POST/PUT/PATCH/DELETE routes stay Bearer-gated even with custom middleware attached; use `@noauth()` to open a write route explicitly. Verified by the existing probe assertion `test_decorated_post_route_silently_unauthenticated` flipping from PASS to FAIL (the bug-direction assertion is the regression sentinel).** Originally: **`@middleware(...)` silently disables the framework's built-in Bearer-token gate.** `router.py:689-704` — when `@middleware(...)` decorates a POST/PUT/PATCH/DELETE route, the decorator sets `route["auth_required"] = False` *"unless @secured() was explicitly set"*, on the assumption that "developer handles auth — disable built-in gate." This is undocumented in the chapter. Combined with PY-10-01, applying a function-based middleware intended to enforce auth produces a route with **zero authentication**: neither the custom middleware (never runs, per PY-10-01) nor the framework default (disabled by the decorator). A developer reading Ch10 alone would not know to add `@secured()` to restore the default gate. Recommend either documenting this behaviour explicitly in S4 ("The @middleware Decorator") with a security-implications callout, or making the auth-required default sticky unless explicitly overridden with `@noauth()`. |
| PY-10-03 | fixed | [#141](https://github.com/tina4stack/tina4-book/issues/141) | 2026-06-04 · pre-3.13.4 | — (fixed 3.13.4; probe `test_ch10_middleware_probe.py`) | **Fixed in tina4-python 3.13.4 (2026-06-05) — `request.headers` is now a `CaseInsensitiveDict` (`request.py:18`). `headers.get("Content-Type")`, `headers.get("content-type")`, `headers.get("CONTENT-TYPE")` all return the same value. The 6 mixed-case chapter examples now work as written. Verified by the existing probe assertion `test_docs_pattern_capital_A_returns_None` flipping from PASS to FAIL (regression sentinel).** Originally: **Header-key casing mismatch in chapter examples.** `request.py:55` stores all incoming headers under lowercase keys: `req.headers[name.decode().lower()] = value.decode()`. So `request.headers.get("Authorization")` returns `None` — the key is actually `"authorization"`. Several chapter examples use mixed-case keys against this dict — S9 line 500 uses `"authorization"` (correct), S10 line 546 + S12 line 677 use `"X-API-Key"` (broken — returns None), S12 line 664 uses `"Authorization"` (broken — returns None). The chapter never states that `request.headers` is lowercase-keyed, nor mentions the convenience helpers: `request.header(name)` does case-insensitive lookup (`request.py:128`), and `request.bearer_token()` extracts the raw token (`request.py:132`). Recommend: (a) add a one-line callout in S3 or S8 that `request.headers` is lowercase-keyed, (b) normalise all chapter examples to either lowercase keys or the `request.header()` helper, (c) document `request.bearer_token()` as the canonical way to read the auth header. |
| PY-18-12 | open | [#140](https://github.com/tina4stack/tina4-book/issues/140) | 2026-06-05 | Add `from src.orm.User import User` to the S7 snippet (mirror the S4 -07a fix). | **S7 (Setup and Teardown) example references `User` with no import and no model definition — same defect class as PY-18-07a in S4 before the 3.13.4 fix.** S7 snippet uses `User()`, `User.find(self.user_id)`, `user.save()`, `user.delete()` across `set_up`, `tear_down`, and both test methods. Chapter imports only `Test, assert_equal, assert_not_none` from `tina4_python.test`. No `User` ORM model defined in Ch18 or referenced from Ch06. Empirically: `NameError: name 'User' is not defined` on every test before any framework code runs. The 3.13.4 fix for PY-18-07a added `from src.orm.Product import Product` to S4; the parallel fix is missing for S7. Recommend: add `from src.orm.User import User   # assumes src/orm/User.py exists` to the snippet, mirroring the S4 fix. (Combined with the broader scaffold-gap pattern PY-18-11: a one-line callout that S7 assumes Ch06 ORM territory would also help.) |
| PY-18-11 | open | [#140](https://github.com/tina4stack/tina4-book/issues/140) | 2026-06-05 | Add an S6 callout that it assumes Ch08 auth, plus a minimal `/api/auth/login` + `/api/profile` route and user fixture. | **S6 (Testing Authentication) assumes prior-chapter scaffold with no callout.** S6 test code references `/api/auth/login` POST + `/api/profile` GET, hardcoded credentials `admin@example.com` / `correct-password`, and expects a JWT in the response. None of these routes/users/credentials are shown in Ch18 or earlier sections of Ch18. A reader following the chapter top-down hits 6 consecutive 404s with no hint why. S5 has the same shape gap (`/api/products` not shown) but at least appears alongside S4's ORM model, which makes the link to Ch06 implicit. S6 has no equivalent anchor — the auth setup lives in Ch08 (not yet read by a sequential reader). Recommend: add a one-paragraph callout at the top of S6 stating "this section assumes Ch08 (Authentication) has been implemented and the `/api/auth/login` + `/api/profile` routes exist; minimal setup below," followed by a 10-line auth route + user fixture. Verified locally: building a minimal `src/routes/ch18_auth.py` using `Auth.get_token()` / `@secured()` flips all 6 S6 tests from 404 to PASS, confirming the framework is fine — only the chapter scaffolding is missing. |
| PY-18-13 | open | no | 2026-06-08 | Rewrite S11/S12: add `User` import + DB setup, show uniqueness (index or `unique`), use `where(..., with_count=True)`, and assert `save()` returns `False` instead of `assert_raises`. | **S11 exercise + S12 solution (`tests/test_user_model.py`) broken in 5 independent ways before the first assertion runs.** (a) **PY-18-13a — missing `User` import.** S12 `test_user_model.py` uses `User()` throughout but imports only `Test, assert_equal, assert_true, assert_not_none, assert_raises`. `NameError: name 'User' is not defined` on every test. Same defect class as PY-18-07a (Product) and PY-18-12 (S7 User). Fix: add `from src.orm.User import User`. (b) **PY-18-13b — no DB binding or table creation.** S12 never calls `orm_bind()`, sets `TINA4_DATABASE_URL`, or runs DDL. `RuntimeError: No database bound` on first `user.save()`. Same defect class as PY-18-07b. Fix: `os.environ.setdefault("TINA4_DATABASE_URL", "sqlite:///data/test.db")` + `User.create_table()`. (c) **PY-18-13c — `StringField` has no `unique` kwarg; no uniqueness mechanism shown.** S11 requirement 2 + S12 `test_duplicate_email` expects an exception or error on duplicate email save. `Field.__init__` (fields.py:19-34) accepts no `unique` parameter — verified. The chapter shows no migration, no `save()` override, and no mechanism to enforce uniqueness. A UNIQUE INDEX must be created manually (e.g. `db.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_email_unique ON users(email)")`), but this is not in the chapter. (d) **PY-18-13d — `User.where("1=1")` unpacked as 2-tuple raises `ValueError`.** S12 line 808: `users, count = User.where("1=1")`. `Model.where()` returns `list[Self]` by default; `(list, int)` tuple requires `with_count=True` (model.py:624). As written: `ValueError: too many values to unpack (expected 2)`. Fix: `User.where("1=1", with_count=True)`. Same defect class as PY-18-07c. (e) **PY-18-13e — `assert_raises(create_duplicate, Exception, ...)` cannot fire; `ORM.save()` swallows all exceptions.** `ORM.save()` (model.py:336-338) wraps every insert/update in `except Exception: db.rollback(); return False`. A UNIQUE constraint violation is caught internally and returns `False` — it never propagates. S12's `assert_raises` test therefore always fails with `AssertionError: Should reject duplicate email` even when a UNIQUE INDEX is present. The framework's actual contract is "duplicate save returns `False`"; the test must assert `assert_false(user2.save(), ...)` not `assert_raises(...)`. Recommend: S11/S12 rewrite to (1) include `from src.orm.User import User` and DB-setup lines, (2) either add `unique=True` to `StringField` or show the migration/index step, (3) fix the `where()` call to use `with_count=True`, (4) fix `test_duplicate_email` to assert `save()` returns `False` rather than raises. Evidence: `pypy/tests/test_user_model.py` — 4 PATCH markers (PY-18-13a–e) required to reach 5/5 pass. |
| PY-06-01 | open | [#142](https://github.com/tina4stack/tina4-book/issues/142) | 2026-06-17 · 3.13.30 | → FIX-05 | **Chapter 6 (ORM) shows no database-binding step anywhere — a reader exercising the chapter in isolation hits `RuntimeError: No database bound. Call bind_database(db) or set TINA4_DATABASE_URL in .env` on the first ORM call (`Note.create_table()`, S3).** Grep of `06-orm.md`: zero mentions of `TINA4_DATABASE_URL`, `Database(`, `.env`, `bind_database`, or `orm_bind`. Binding is established only in Ch05 (`05-database.md:20` sets `TINA4_DATABASE_URL=sqlite:///data/app.db`; L7 notes *"No ORM required (Chapter 6 adds that)"*). So Ch06 silently assumes the reader completed Ch05's `.env` setup — same scaffold-dependency-callout class as PY-18-11, not the false "auto test DB" promise of PY-18-07b. Once a DB is bound (verified via `os.environ.setdefault("TINA4_DATABASE_URL", "sqlite:///data/test.db")`), the full S2–S4 documented API works: model definition, `create_table()`, `save()`, `create()` (dict + kwargs), `find_by_id()`, `find()` filter dict, `where()`, `count()`, `delete()` — 7/7 pass (`pypy/tests/test_ch06_note_crud.py`). Recommend a one-line callout at the top of S2 or S3: *"This chapter assumes a database is configured per Chapter 5 (`TINA4_DATABASE_URL` in `.env`). The ORM auto-binds to it."* Evidence: `pypy/tests/test_ch06_note_crud.py` — 1 PATCH block (PY-06-01) to bind the DB. **Verified 2026-06-18 (adversarial pass): real, not mis-impl; 4 disprove angles failed (no sqlite/default fallback in `_get_db`; chapter grep = 0 binding tokens, no Ch5 prereq before S3; it IS the first ORM call; on-disk `.env` doesn't suppress it under bare python). Source raise at `orm/model.py:306-308` (`_get_db`). Doc-completeness defect, not a framework bug — error message itself is clear.** |
| PY-06-02 | open | [#142](https://github.com/tina4stack/tina4-book/issues/142) | 2026-06-17 · 3.13.30 | → FIX-05 | **Chapter 6 shows `create_table()` only once (for `Note`, S3 line 255) — every later section then defines a model and immediately queries/saves it with no table-creation step.** The ORM requires the backing table to exist (named by `table_name` or the lowercased class name); `save()` does not auto-create it. Affected: S6 (`Author`/`BlogPost` relationships), S8 (`Task` soft delete), S12 (`Product` validation), and the S13/14 blog exercise + solution (`src/routes/blog.py` saves `Author`/`BlogPost`/`Comment` with no `create_table` or migration anywhere). Empirically (3.13.30): running S6 verbatim, the first `author.save()` fails silently — the framework logs `UndefinedTable: relation "authors" does not exist` (PG) / `no such table: authors` (SQLite), but `save()` swallows it, returns `False`, and nothing is persisted (`id` stays `None`). Read methods (`create_table`, `select_one`, `load`) propagate the error; write methods (`save`, `create`) swallow it. Once the tables are created (`Author.create_table()` + `BlogPost.create_table()`), the documented relationship API works — `has_many`/`belongs_to` 2/2 pass (`pypy/tests/test_ch06_relationships.py`). Recommend: either a one-line note at S3 that `create_table()` (or a migration) must be run for every model before use, or a per-section "assuming the `<x>` table exists" callout, or fold the table-creation step into each section's example. Same defect family as PY-06-01 (chapter omits its own DB setup). Evidence: `pypy/tests/test_ch06_relationships.py` — 1 PATCH block (PY-06-02). **Verified 2026-06-18 (adversarial pass): real, not mis-impl; 5 disprove angles failed — `save()` returns literal `False` with NO exception to the caller (a direct `db.insert()` DOES raise, isolating the swallow to `save()`); silent to the caller but the adapter logs the `UndefinedTable` one layer below; nothing persisted (`to_regclass` stays None); engine-agnostic (same on SQLite). `create()` inherits the swallow (returns `<id=None>`). Origin: `ORM.save()` bare `except Exception: db.rollback(); return False` at `orm/model.py:393-395` (vs `delete()` re-raises at :421-423, read path `db.fetch` re-raises at `connection.py:549-556`).** |
| PY-06-03 | open | [#142](https://github.com/tina4stack/tina4-book/issues/142) | 2026-06-17 · 3.13.30 | → FIX-06 | **The Python ORM chapter carries multi-language content that doesn't belong in the Python book.** The "ORM at a Glance: Four Languages, One Shape" section (`06-orm.md:13-98`) shows the same model in Python, PHP (native typed properties), Ruby (DSL), and Node.js (TypeScript config objects), plus a "Common Query Operations" comparison table (`06-orm.md:85-94`) with PHP/Ruby/Node columns and prose like *"PHP needs `(new Post())` for instance methods"* and *"Ruby methods drop the parentheses"*. A reader in the Python book gets ~85 lines of PHP/Ruby/Node code and cross-language caveats before the Python material proper (S2) begins. Recommend: strip the chapter to Python only — drop the PHP/Ruby/Node code blocks and the four-language table (or reduce it to the Python column). The cross-language parity story, if wanted, belongs in a shared/overview page, not inside each language's chapter. (Worth checking whether the same multi-language interludes appear in other Python chapters.) Documentation-only; no code to run. |
| PY-06-04 | open | [#142](https://github.com/tina4stack/tina4-book/issues/142) | 2026-06-17 · 3.13.30 | Add `slug = StringField()` to the S2 Note model, or switch the S4 `select_one`/`load` examples to an existing column (e.g. `category`). | **S4 `select_one` (`06-orm.md:412`) and `load(filter)` (`06-orm.md:428`) examples query a `slug` column the documented `Note` model never defines.** The Note model (S2, `06-orm.md:108-121`) declares `id`, `title`, `content`, `category`, `pinned`, `created_at`, `updated_at` — no `slug`. The two S4 snippets — `Note.select_one("SELECT * FROM notes WHERE slug = ?", ["my-note"])` and `note.load("slug = ?", ["my-note"])` — therefore fail when copied verbatim: `UndefinedColumn: column "slug" does not exist` (PG; `no such column: slug` on SQLite). Intra-chapter contradiction — the chapter's own examples reference a column its own model definition omits (same defect family as PY-18-12, but within one chapter rather than cross-chapter). Every other documented S2/S4/S6 form is functional once a DB is bound + tables created: `find_or_fail` (hit + ValueError on miss), `find(filter, limit, order_by)`, `find()` all, `all()`/`all(limit,offset)`, `where(..., limit, offset)`, `select(sql, params)`, `load()` by PK, `count(conditions, params)`, `field_mapping` round-trip + `_get_db_column`/`_get_db_data`, `snake_to_camel`/`camel_to_snake`, `ForeignKeyField` auto-wired `belongs_to`/`has_many`, `has_one` — 20/20 in a scratch coverage sweep (not retained; those forms are now covered by the six persisted `test_ch06_*.py` files). Recommend either add a `slug = StringField()` to the Note model in S2, or change the S4 examples to an existing column (e.g. `category`). Documentation-only; the framework behaves correctly (the column genuinely doesn't exist). Found on tina4-python 3.13.30. Evidence: verbatim `slug` repro under Observed terminal output below + retained slug tests `pypy/tests/test_ch06_note_crud.py::test_select_one_slug_verbatim_known_broken` and `::test_load_slug_verbatim_known_broken`; the other S2/S4/S6 forms were confirmed via a scratch coverage sweep (not retained). |
| PY-06-05 | open | [#142](https://github.com/tina4stack/tina4-book/issues/142) | 2026-06-17 · 3.13.30 | Drop the glance `Post` model (→ FIX-06) or give it a distinct `table_name`; and surface `create()` DB errors instead of returning an unsaved `id=None` instance. | **The "ORM at a Glance" `Post` model (`06-orm.md:23-33`) and the S6 has_many `BlogPost` model (`06-orm.md:551-565`) both declare `table_name = "posts"` with incompatible schemas.** Glance `Post`: `id, title, body, created_at`. S6 `BlogPost`: `id, author_id, title, slug, content, status, created_at, updated_at`. `create_table()` is `CREATE TABLE IF NOT EXISTS`, so whichever model's table is built first wins and the other silently runs against the wrong schema. Empirically, with the S6 `BlogPost` table present (`author_id`/`slug` NOT NULL), the verbatim "Build and save" row of the Common Query Operations table — `Post.create(title="x")` — emits `UndefinedColumn: column "body" of relation "posts" does not exist`, and `create()` then **silently returns an unsaved instance with `id=None`** (no exception, no `False` — same swallow class as PY-18-13e, `ORM.save()` model.py:336-338). Against `Post`'s own clean schema, all 8 Common Query Operations work — `create`/`save`/`find_by_id`/`find`/`where`/`all`/`count`/`delete` (verified by isolating the `posts` table). Two concerns: (a) two documented models on one `table_name` with incompatible schemas is a copy-paste hazard; (b) `create()` masks a real DB error as a benign-looking `id=None` instance. Recommend: drop the glance `Post` model (consistent with PY-06-03 — the four-language section doesn't belong in the Python book), or give it a distinct `table_name`. (b) is the broader swallow behaviour already logged at PY-18-13e. Documentation-only for (a); (a)+(b) confirmed against live PG 18 on tina4-python 3.13.30 (found-version). **Blocking dependency (N blocks N+1):** a strictly sequential reader who runs the glance "Common Query Operations" against `Post` first builds `posts` with the glance schema (`id, title, body, created_at`); reaching S6, `BlogPost.create_table()` is a no-op (`CREATE IF NOT EXISTS`), so every S6 relationship op then runs against the wrong columns — the glance section blocks S6 unless the `posts` table is dropped/recreated between them (which the chapter never tells the reader to do). Sidestepped in tests via per-module table drops; a verbatim reader has no such step. |
| PY-06-06 | open | no | 2026-06-17 · 3.13.30 | Align the `tina4_python.test` client dispatch with the server's signature-aware `_invoke_handler` (inject path params by name), OR document in Ch06/Ch18 that handlers tested via the Test client must read path params from `request.params` rather than as positional arguments. | **S4/S6 route handlers use the documented positional path-param signature (`async def get_note(id, request, response)`), which works under `tina4 serve` but raises `TypeError` when driven through the documented `tina4_python.test` client.** The server dispatch (`core/server.py:1272` `_invoke_handler`) is signature-aware: it matches `{id:int}` route params to handler parameter names by name and injects them positionally, then appends `request`/`response` for the remaining params — so the verbatim S4 (`get_note`, `delete_note`) and S6 (`get_author`, `get_post`) handlers serve correctly. The test client (`test_client/__init__.py:155`) instead calls `handler(request, response)` flatly with no signature inspection, so a handler whose first positional parameter is the path arg gets `(request, response)` → `id`=request, `request`=response, `response` missing → `TypeError: get_note() missing 1 required positional argument: 'response'`. Handlers with no path param (`create_note`, `list_notes`) are unaffected — confirms the gap is path-param injection, not the `response({...}, status)` call form (which works). The book's signature also matches the framework's own routing docs (`tina4_python/CLAUDE.md`: `async def get_user(id, request, response)`), so a reader who writes handlers as documented and then tests them with the documented Test client (Ch18 route testing) hits a `TypeError` that does not reflect real serving behaviour. Empirically confirmed on tina4-python 3.13.30 via direct dispatcher invocation: `_invoke_handler` returns `{"got":42}` for the positional handler; the Test client raises `TypeError`. Routes implemented verbatim in `pypy/src/routes/ch06_notes.py` + `pypy/src/routes/ch06_blog.py` with the documented positional path-param signatures and no patch. Server side re-confirmed 2026-06-17 on 3.13.30 by driving the handlers over HTTP under `tina4 serve`: `GET /api/notes/{id}`, `/api/authors/{id}` (has_many), `/api/posts/{id}` (belongs_to) all return 200 with the documented JSON. The Test-client `TypeError` was captured in the earlier session that logged this row; that session's `test_ch06_route_dispatch_probe.py` was removed when the ch06 scratch work was reset and has not been recreated — so the Test-client side is unverified this session (re-confirm at the EOD pass). Found on tina4-python 3.13.30. |
| PY-06-07 | open | no | 2026-06-17 · 3.13.30 | Add an S4 callout that write routes (POST/PUT/PATCH/DELETE) are Bearer-gated by default — open them with `@noauth()` or show the token flow; fix the S9 Auto-CRUD curl + S14 solution POSTs the same way. | **Every documented Ch06 write route is a plain `@post`/`@put`/`@delete` with no auth, but Tina4 gates POST/PUT/PATCH/DELETE behind a Bearer token by default — a verbatim `POST /api/notes` (S4 `create_note`, `06-orm.md:276-285`) returns `401 {"error":"Unauthorized","message":"Valid authorization token required"}`.** Driven over HTTP under `tina4 serve` on 3.13.30. Read routes serve 200 (`GET /api/notes`, `/api/notes/{id}`, `/api/authors/{id}`, `/api/posts/{id}`); only writes 401. Chapter grep for `auth`/`token`/`secured`/`noauth`/`bearer`/`login`: zero matches outside the word "author" — the chapter never tells the reader writes need auth or `@noauth()`. Not a framework bug — the gate is the intended default (see PY-10-02); the gap is documentation. Same omission affects the S9 Auto-CRUD `curl -X POST` example (`06-orm.md:928-931`) and the S14 blog solution (`create_author`/`create_post`/`add_comment`). Cross-ref PY-10-02. |
| PY-06-08 | open | [#142](https://github.com/tina4stack/tina4-book/issues/142) | 2026-06-17 · 3.13.30 | Note that `BooleanField` maps to a native `BOOLEAN` column on PostgreSQL (`INTEGER (0/1)` only on SQLite), and change the S4 `select` example to pass `[True]` not `[1]`. | **S2 field-types table (`06-orm.md:136`) states `BooleanField → INTEGER (0/1)`, but on PostgreSQL the column is created as native `BOOLEAN` (confirmed via `information_schema.columns`: `notes.pinned` data_type = `boolean`).** The S4 SQL-first example (`06-orm.md:401-404`) passes integer `[1]` for the boolean `pinned` column; verbatim on PG it raises `UndefinedFunction: operator does not exist: boolean = integer` (`pinned = 1`). `[True]` works, and `find({"pinned": True})` works (the ORM translates) — only the documented raw-SQL `select(..., [1], ...)` path breaks. The `[1]` form is SQLite-shaped. Cross-ref BH-46 (`SQLTranslator.boolean_to_int`). Found on tina4-python 3.13.30. Evidence: `pypy/tests/test_ch06_note_crud.py::test_select_sql_first_verbatim_known_broken_on_pg` (bug-direction; asserts the verbatim line raises). **Verified 2026-06-18 (adversarial pass): real, not mis-impl; 5 disprove angles failed — `[True]` succeeds while `[1]`/`[0]` fail (same SQL → param type, not syntax); `find({"pinned": True})` works (ORM path unaffected); `boolean_to_int` rewrites only literal text + is skipped on PG (no silent rescue); mapping IS engine-dependent (`orm/model.py:764-772` — sqlite/firebird→INTEGER so doc is SQLite-accurate, PG/MySQL→BOOLEAN/BIT); real `notes.pinned` = boolean too (not my artefact). Framework source comments already flag this `boolean=integer` mode as a fixed regression — framework corrected, doc (`:136`, `:401-404`) not updated.** |
| PY-06-09 | open | no | 2026-06-17 · 3.13.30 | Add the import lines to the S6 `get_author`/`get_post` snippets (`from tina4_python.core.router import get`, `from src.orm.author import Author`, `from src.orm.blog_post import BlogPost`), mirroring S4. | **S6 route-handler snippets (`get_author` `06-orm.md:570-582`, `get_post` `06-orm.md:613-625`) use `@get`, `Author`, and `BlogPost` but show no import statements.** S4 shows per-snippet imports (`from tina4_python.core.router import get`, `from src.orm.note import Note`); S6 omits them, so a reader copying an S6 block verbatim into a fresh file hits `NameError` for `get`/`Author`/`BlogPost`. (Counter-angle for the EOD pass: the `Author`/`BlogPost` models are defined just above in S6 and S4 sets the router-import pattern, so a strictly sequential reader can supply them.) Surface-logged; not yet exercised. |
| PY-06-10 | open | no | 2026-06-17 · 3.13.30 | Give `has_one` a runnable example with a defined `Profile` model + `user` instance, matching the `has_many`/`belongs_to` treatment. | **The S6 `has_one` example (`06-orm.md:603`) is an orphan one-liner — `profile = user.has_one(Profile, "user_id")` — referencing a `Profile` model and a `user` instance defined nowhere in the chapter.** `has_many` and `belongs_to` each get a full runnable route handler with models in scope; `has_one` gets only this fragment, so it can't be implemented as written. Documentation-only (structural). Surface-logged. |
| PY-06-11 | open | no | 2026-06-17 · 3.13.30 | Introduce the declarative descriptors (or note `ForeignKeyField` auto-wiring) before the `list_authors` eager example, or add `posts = has_many("BlogPost", foreign_key="author_id")` to the model the example uses. | **S7's first eager example `list_authors` (`06-orm.md:653-664`) calls `Author.all(include=["posts"])` + `author.to_dict(include=["posts"])`, but the `posts` relationship isn't declared until the later "Declarative Relationships with Descriptors" subsection (`06-orm.md:684`).** On the S6 `Author` model (`src/orm/author.py` — plain `author_id`, no descriptor), `include=["posts"]` is a **silent no-op**: no error, and `to_dict(include=["posts"])` produces no `posts` key (returns `None`). Confirmed on 3.13.30 against the S6-state model, before S7's descriptor is added — `hasattr(Author,'posts')` was `False` and `Author.all(include=["posts"])` returned authors with no posts (no error, no `posts` key). Eager loading works once the S7 `has_many`/`belongs_to` descriptor (or `ForeignKeyField`) declares the relationship — now integrated onto `src/orm/author.py` + `blog_post.py` and verified in `pypy/tests/test_ch06_eager_loading.py` (posts/author paths). Chapter ordering presents the eager example before its prerequisite descriptor, so a top-down reader silently gets empty relationships. Surface-logged. |
| PY-06-12 | open | no | 2026-06-17 · 3.13.30 | Define (or recap) a `Comment` model in S7 — its descriptors and nested includes reference one, but it first appears in S14. | **S7 references a `Comment` model defined nowhere in the section.** The descriptor `BlogPost.comments = has_many("Comment", foreign_key="post_id")` (`06-orm.md:697`), the nested include `Author.all(include=["posts", "posts.comments"])` (`06-orm.md:727`), and `BlogPost.find_by_id(1, include=["author", "comments"])` (`06-orm.md:718, 737`) all need a `Comment` model; `Comment` first appears in the S14 solution (`06-orm.md:1150-1162`). A reader implementing S7 top-down has no Comment class, so every comments example raises `ValueError: Related model 'Comment' not found` — the `comments` descriptor access, `include=[..., "comments"]` (`:718`), the nested `posts.comments` (`:727`), and the to_dict-with-comments example (`:737-738` → the JSON at `:741-754`). The posts/author descriptors work; the comments half of S7 cannot be reproduced verbatim. Same missing-model class as PY-06-10. Confirmed on 3.13.30; `pypy/tests/test_ch06_eager_loading.py` asserts the block (3 tests). Surface-logged. |
| PY-06-13 | open | [#142](https://github.com/tina4stack/tina4-book/issues/142) | 2026-06-18 · 3.13.30 | Make the `tina4_python.test` client apply the same Bearer-auth gate as the HTTP server for write methods, or document that the Test client skips auth so route tests don't give false confidence. | **The documented Test client does not enforce the Bearer-token gate that `tina4 serve` applies to write routes.** Same handler, two dispatchers: `POST /api/notes` (verbatim S4 `create_note`) returns **401** over `tina4 serve` (PY-06-07) but **201** through `tina4_python.test`'s `self.post(...)` — the create succeeds with no token. A reader who tests a write route the Ch18 way (Test client) sees 201 and ships a route that 401s in production. Same dispatch-parity family as PY-06-06 (path params), here on auth. Confirmed 3.13.30. Evidence: `pypy/tests/test_ch06_routes.py::test_create_note_post_via_test_client_py_06_13` (asserts the 201; flips if the client is aligned to server auth). **Verified 2026-06-18 (adversarial pass): real, not mis-impl; 5 disprove angles failed — POST route registers `auth_required=True`; Test client returns 201 with NO token AND with a bogus token (no auth stage at all); GET via same client 200 (client correctly wired); server `_check_auth` on the identical route → 401. Client also skips before/after middleware. Origin: `test_client/__init__.py:136-155` dispatches `Router.match` → `handler(...)` with no auth stage, vs served path `core/server.py:1586` (`_check_auth` before handler) + the gate at `server.py:1097-1151`.** Surface-logged → EOD-verified. |
| PY-06-14 | open | no | 2026-06-18 · 3.13.30 | Change the S8 `with_trashed` example to pass `[True]` not `[1]` for the boolean `completed` column (same fix as PY-06-08). | **S8 "Including Soft-Deleted Records" example (`06-orm.md:809`) passes integer `[1]` for the boolean `completed` column: `Task.with_trashed("completed = ?", [1])`.** On PG `completed` is native `BOOLEAN`, so `completed = 1` raises `UndefinedFunction: operator does not exist: boolean = integer`. `[True]` works (`with_trashed(filter)` itself is fine). Same hazard family as PY-06-08 (BooleanField + `[1]`), different code block. Found 3.13.30. Evidence: `pypy/tests/test_ch06_soft_delete.py::test_with_trashed_filter_verbatim_known_broken_on_pg` (+ `::test_with_trashed_filter_works_with_boolean`). Surface-logged. |
| PY-06-15 | open | no | 2026-06-18 · 3.13.30 | Change the S8 `count` example to filter on a column the Task model has (e.g. `completed`), or add `category` to the model. | **S8 "Counting with Soft Delete" example (`06-orm.md:820`) filters on a `category` column the `Task` model never defines: `Task.count("category = ?", ["work"])`.** Task fields (S8, `06-orm.md:765-773`): `id, title, completed, is_deleted, created_at` — no `category`. Verbatim → `UndefinedColumn: column "category" does not exist` (PG). Same family as PY-06-04 (a verbatim example references a column its own model omits), different code block. Found 3.13.30. Evidence: `pypy/tests/test_ch06_soft_delete.py::test_count_category_verbatim_known_broken`. Surface-logged. |
| PY-06-16 | open | no | 2026-06-18 · 3.13.30 · CLI 3.8.28 | Update S3 to `tina4 console` — `tina4 shell` does not exist. | **S3 (`06-orm.md:260-264`) documents `tina4 shell` to run `Note.create_table()` interactively, but the CLI has no `shell` subcommand:** `tina4 shell` → `error: unrecognized subcommand 'shell'`. The real REPL is `tina4 console` ("Start an interactive REPL with the framework loaded"). Book-doc fix: `tina4 shell` → `tina4 console`. (But see PY-06-17 — `console` then can't import the model.) Surfaced running S8 in the program. Surface-logged. |
| PY-06-17 | open | no | 2026-06-18 · 3.13.30 · CLI 3.8.28 | Make `tina4 console` put the project root on `sys.path` (as `tina4 serve` does) so `from src.orm.X import Y` works. Root cause framework/CLI — candidate for a tina4-python filing, not a book-text fix. | **`tina4 console` cannot import project `src.*` modules — the S3 interactive flow `from src.orm.note import Note` raises `ModuleNotFoundError: No module named 'src'`.** At console startup the auto-loader fails to load every `src/orm/*.py` + `src/routes/*.py` (`Failed to load …: No module named 'src'`); a manual `from src.orm.task import Task` fails identically, so every downstream model call `NameError`s. The same modules load fine under `tina4 serve` (14 routes discovered; ch06 routes served over HTTP) — the project root is on `sys.path` under serve but not console. Net: the documented S3 interactive `create_table()` flow is unrunnable in the program (`shell` missing per PY-06-16, `console` can't import). The soft-delete functionality itself works — verified via pytest against live PG (`test_ch06_soft_delete.py` 9/9). Root cause framework/CLI (console `sys.path`). Found 3.13.30 / CLI 3.8.28. Surface-logged. |
| PY-06-18 | open | [#142](https://github.com/tina4stack/tina4-book/issues/142) | 2026-06-18 · 3.13.30 | Fix S9 "Custom Routes Alongside Auto-CRUD": auto-CRUD routes register before and shadow same-path custom routes — make custom win (as claimed) or correct the docs. | **S9 claims (`06-orm.md:941-943`) "Custom routes defined in `src/routes/` load before auto-CRUD routes. They take precedence." — false on 3.13.30.** With `auto_crud = True` on `Note` (verbatim S9 flag) plus the custom `/api/notes` routes (`src/routes/ch06_notes.py`), `tina4 serve` registers the auto-CRUD routes FIRST ("AutoCrud: registered 5 routes for Note (/api/notes)" logs before the custom `POST /api/notes (auth=required)`), and `GET /api/notes` returns the auto-CRUD paginated payload (`{records,data,count,total,…}`), NOT the custom `list_notes` `{notes,count}`. Auto-CRUD shadows custom — opposite of the documented precedence. Confirmed under `tina4 serve` (serve log + curl) and the Test client. Observed by transiently setting `auto_crud=True` on Note (reverted to preserve the S4/S6 custom-route tests; the clean auto-CRUD demo lives on `Task`/`/api/tasks` + `/api/v2/notes`). **Verified + refined 2026-06-18 (adversarial pass): real, not mis-impl; 7 disprove angles. Precedence is purely registration-order — `Router.match` is first-match (`core/router.py:359-368`), there is NO custom-vs-generated priority. Auto-CRUD registers first specifically via the `auto_crud=True` flag: `ORMMeta` registers AutoCrud at class-definition time (`orm/model.py:146-152`) and auto-discovery imports `src/orm/` before `src/routes/` (`core/server.py:72`, sorted `rglob` — "orm" < "routes"), so the model's routes land before any custom route file loads. IMPORTANT nuance: manually calling `AutoCrud.register(Note)` AFTER importing the custom routes makes CUSTOM win — so the symptom is intrinsic to the documented `auto_crud=True` flag path, not the manual-register order. Best upstream framing: internal doc contradiction (S9 "custom take precedence" vs Common Issues "first registered wins"; nothing guarantees custom registers first).** **S15 Gotcha 9 "Auto-CRUD endpoint conflicts" (`06-orm.md:1358-1364`) is a SECOND doc location repeating the same false precedence claim ("Custom routes ... load before Auto-CRUD routes. They take precedence") — and is internally contradictory: its Cause says *"The first registered route wins"* while its Fix says custom routes *"take precedence."* Per this finding, with `auto_crud=True` the model's routes register FIRST, so first-wins = auto-CRUD wins, directly contradicting the Fix. Re-confirmed reading on 3.13.39 (behaviour proven on 3.13.30, PY-06-18 served-verified).** Surface-logged → EOD-verified. |
| PY-06-19 | open | no | 2026-06-18 · 3.13.30 | Update the S9 paginated-response example to the actual key set (or note it's a superset). | **S9 documents the auto-CRUD list payload as `{data, total, limit, offset}` (`06-orm.md:913-922`), but the actual payload is a superset:** `{records, data, count, total, limit, offset, page, per_page, totalPages, total_pages}` (live `GET /api/tasks` under `tina4 serve`). The documented keys are all present — example just incomplete. Found 3.13.30. Surface-logged. |
| PY-06-20 | open | no | 2026-06-18 · 3.13.30 | Align the S9 validation-error example detail wording with the framework's actual message. | **S9's validation-failure example (`06-orm.md:935-937`) shows `"detail": ["title: This field is required"]`, but the framework returns `"detail": ["Field 'title' is required"]`** (live `POST /api/tasks` with `{}`). The envelope (`{"error":"Validation failed","detail":[…]}`) and 400 status match; only the per-field wording differs. Found 3.13.30. Surface-logged. |
| PY-06-21 | open | no | 2026-06-18 · 3.13.30 | Note in S10 that ORM writes (`.save()`) already auto-invalidate the query cache; `clear_cache()` is only relevant for out-of-band changes (raw SQL / another process). | **S10 frames `clear_cache()` as how you handle "when data changes" (`06-orm.md:968-971`) but never mentions that ORM writes already auto-invalidate the cache.** After `Note.cached(SQL, [True], ttl=60)` returns 2 rows, a `Note(...).save()` makes the next identical `cached()` call return 3 (fresh) with no `clear_cache()` — the save auto-dropped the cache. Contrast: an out-of-band raw `INSERT` does NOT refresh (cache serves stale within TTL — by design). Doc-completeness gap, minor. Found 3.13.30. Evidence: `pypy/tests/test_ch06_cached.py::test_orm_save_auto_invalidates_cache` (+ `::test_cached_serves_stale_within_ttl`). Surface-logged. |
| PY-06-22 | fixed | [#142](https://github.com/tina4stack/tina4-book/issues/142) | 2026-06-18 · 3.13.30 (FIXED 3.13.39, re-verified 2026-06-22) | Make `clear_cache()` also invalidate the DB-layer cache (`db._query_cache`) that `cached()` → `Database.fetch()` reads, not only the module-level ORM `_query_cache`. Root cause framework (code-side fix), but logged on the Ch6 tina4-book thread (#142) like all chapter findings. | **At the documented-API level, `Note.clear_cache()` does not make a subsequent `cached()` reflect changed data — contradicting S10 (`06-orm.md:968-971` "Clear the cache when data changes: `Note.clear_cache()`").** **Verified + reframed via adversarial pass (2026-06-18):** the original "`clear_cache()` is a no-op for the query cache" framing was imprecise — there are TWO cache layers. `clear_cache()` DOES clear the module-level ORM cache (`_query_cache.clear_tag(cls.__name__)`, `orm/model.py:882-884`; the store empties to `[]`). But `cached()` reads through `cls.select()` → `Database.fetch()`, which has its OWN request-scoped cache (`db._query_cache`, default-on, mode=`request`, ttl=5s, `database/connection.py:521-548`) that `clear_cache()` never touches. Attribution proof: clearing BOTH `M.clear_cache()` + `db.cache_clear()` → fresh (3); `clear_cache()` alone → stale (2); after `DROP TABLE` + `clear_cache()`, `cached()` STILL serves cached rows (no DB hit). Explains PY-06-21: `Database.insert/update/delete` (`connection.py:598/608/615`) each call `_cache_invalidate()`, so `.save()` refreshes — a different code path from `clear_cache()`. **Severity nuance:** the DB-layer cache is request-scoped — under `tina4 serve`, `cache_new_request()` clears it at each request start, so staleness is bounded to within one handler + the 5s TTL; but a reader who calls `clear_cache()` then `cached()` in the same handler still gets stale data, so the user-facing conclusion holds. Disprove attempts (7) all failed: signature is the documented no-arg classmethod; cached()/clear_cache() share tag `M`; not TTL/key artefact; DB-layer cache is on by default (no env set). Root cause framework/ORM (not book text). Potential fix location: `orm/model.py:882-884`. Found + verified 2026-06-18 · 3.13.30. **FIXED in 3.13.39 (re-verified 2026-06-22 on the version bump, CLI 3.8.51): `clear_cache()` now invalidates the DB-layer cache too — after an out-of-band insert + `clear_cache()`, `cached()` returns the fresh count (2→3); after `clear_cache()` + `DROP TABLE`, `cached()` re-hits the DB and raises `UndefinedTable` instead of serving stale rows.** Evidence: `pypy/tests/test_ch06_cached.py` — the two sentinels flipped red on the fix and were renamed to assert the corrected behaviour (`::test_clear_cache_refreshes_cached`, `::test_clear_cache_rehits_db`). Surface-logged → EOD-verified. |
| PY-06-23 | open | no | 2026-06-19 · 3.13.30 | Replace the SQLite-only `datetime('now', ?)` in the `recent()` scope with portable / PG-correct date math (e.g. `created_at > NOW() - (? \|\| ' days')::interval`), or mark the example as SQLite-specific. The chapter's example SQL should match the database the book targets. | **S11's `recent()` scope (`06-orm.md:997-1002`) uses SQLite-only `datetime('now', ?)`; on PostgreSQL `BlogPost.recent()` raises `psycopg2.errors.UndefinedFunction: function datetime(unknown, unknown) does not exist`.** The framework forwards the literal `datetime(...)` to PG via `where()` → `Database.fetch()` (`orm/model.py:676` → `database/connection.py:540`), so both the auto COUNT subquery and the main SELECT fail. The section's other snippets all work as documented: `published()`/`drafts()` (`:989-995`) return status-filtered `list[BlogPost]`, and dynamic registration `BlogPost.scope("active", "status != ?", ["archived"])` → `BlogPost.active()` (`:1022-1026`) correctly excludes archived rows. Only `recent()` is non-portable. Same SQLite-syntax-in-a-PG-example family as PY-06-08 (BooleanField) and PY-06-14 (S8 `with_trashed` boolean filter). Evidence: `pypy/tests/test_ch06_scopes.py::test_recent_scope_breaks_on_postgres` (sentinel asserts the `UndefinedFunction`; flips red if the example becomes portable). Also confirmed over HTTP under `tina4 serve` (port 7150, CLI 3.8.50): `GET /api/posts/published` → 200 (2 posts); `GET /api/posts/recent?days=7` → 500 with server log `Route error: function datetime(unknown, unknown) does not exist {"path": "/api/posts/recent"}`. Served routes: `src/routes/ch06_scopes.py`; scopes on `src/orm/blog_post.py`. **Re-verified still present 2026-06-22 · 3.13.39 (CLI 3.8.51), served port 7150: `GET /api/posts/recent?days=7` → 500, `GET /api/posts/published` → 200 (2 posts) — no change on the version bump.** Surface-logged. |
| PY-06-24 | open | no | 2026-06-22 · 3.13.39 | Update the S12 error-message example (`06-orm.md:1070-1077`) to the framework's actual `validate()` wording, or note the messages are illustrative. | **S12's documented `validate()` error example (`06-orm.md:1070-1077`) shows per-field messages the framework does not emit.** The `validate()` *behaviour* is faithful — it returns a `list`, one entry per failed constraint, catches every documented rule (`required`/`min_length`/`regex`/`min_value`/`choices`), and returns `[]` for valid input — but the wording differs on every line: doc `"name: Must be at least 2 characters"` vs actual `"Field 'name': minimum length is 2, got 1"`; doc `"price: Must be at least 0.01"` vs actual `"Field 'price': minimum value is 0.01, got 0.0"`; doc `"category: Must be one of: Electronics, Kitchen, Office, Fitness"` vs actual `"Field 'category': must be one of ['Electronics', 'Kitchen', 'Office', 'Fitness'], got 'Nope'"` (choices rendered as a Python list repr). A reader who shows these strings in an API response or asserts on them gets different text. Same divergence class as PY-06-20 (S9 validation-detail wording). Origin: the field validators emit the `"Field '<name>': …"` format (`tina4_python/orm/fields.py`), not the doc's `"<name>: Must …"` shape. Found 2026-06-22 · 3.13.39. Evidence: `pypy/tests/test_ch06_validation.py::test_validate_message_format_py_06_24` (asserts the actual format AND that the doc strings are absent; flips if framework/doc align). Surface-logged. |
| PY-06-25 | open | no | 2026-06-22 · 3.13.39 | Correct S15 Gotcha 6 (`06-orm.md:1324-1330`): `save()` DOES validate and refuses invalid data (returns `False`) — it does not silently let invalid data into the DB. If a bypass-validation path is intended, document how to invoke it. | **S15 Gotcha 6 "Validation only runs on validate()" (`06-orm.md:1324-1330`) is FALSE on 3.13.39.** The doc states *"`save()` does not validate. This is by design -- sometimes you need to save partial data or bypass validation for bulk operations,"* with the Problem being *"you call `save()` without calling `validate()` first, and invalid data gets into the database."* Actual: `save()` runs validation and **refuses** invalid data — for a model failing a constraint (e.g. `StringField(min_length=3)` set to `"ab"`), `save()` logs `"<Model>.save() refused: validation failed — Field 'name': minimum length is 3, got 2"`, returns `False`, and persists nothing (`id` stays `None`, table count 0). So the documented "bypass validation by skipping validate()" workflow does not exist; a reader relying on it will find saves silently rejected (return `False`). Note this also means S12's separate `validate()` call is only for obtaining the error LIST to return (e.g. 400) — `save()` itself blocks bad writes. Origin: framework/ORM `save()` now validates before writing (vs the doc's stated no-validate-by-design). Found 2026-06-22 · 3.13.39. Evidence: `pypy/tests/test_ch06_gotchas.py::test_g6_save_actually_validates_py_06_25`. Surface-logged. |
| PY-06-26 | open | no | 2026-06-22 · 3.13.39 | Reframe S15 Gotcha 7 (`06-orm.md:1332-1338`): FK is unenforced because `ForeignKeyField` emits no FK constraint on ANY engine (incl. PostgreSQL), not because "SQLite does not enforce FK by default." Note `ForeignKeyField` wires the ORM relationship only, not a DB-level constraint. | **S15 Gotcha 7 "Foreign key not enforced" (`06-orm.md:1332-1338`) attributes orphan-save success to SQLite — but it is engine-agnostic.** The doc's Cause: *"SQLite does not enforce foreign key constraints by default,"* implying a stricter engine (PostgreSQL) would. Actual on live PG: saving `GBPost(author_id=999)` with no such author **succeeds** (returns the model, persists), and `information_schema.table_constraints` shows **0 FOREIGN KEY constraints** on the table even though the field is `author_id = ForeignKeyField("GAuthor")`. So `ForeignKeyField` emits no `REFERENCES` DDL on PostgreSQL (and the orphan save would succeed on PG regardless of any SQLite default). A reader on PG who expects DB-level referential integrity from `ForeignKeyField` does not get it — the field wires only the ORM `has_many`/`belongs_to` relationship. Same SQLite-shaped-doc-in-a-PG-book family as PY-06-08 / PY-06-14 / PY-06-23. Found 2026-06-22 · 3.13.39. Evidence: `pypy/tests/test_ch06_gotchas.py::test_g7_foreign_key_not_enforced_engine_agnostic_py_06_26`. Surface-logged. |
| PY-06-27 | open | no | 2026-06-22 · 3.13.39 | Soften S15 Gotcha 3 (`06-orm.md:1300-1306`): `find()` DOES accept a bare primary key (returns the single record); the surprise is that `find(pk)` returns a model while `find(dict)` returns a list. State that, rather than calling bare-PK use a mistake. | **S15 Gotcha 3 "find() vs find_by_id()" (`06-orm.md:1300-1306`) is inaccurate.** The doc's Cause: *"`find()` takes a dict filter (`find({"id": 42})`), not a bare primary key value,"* and the Problem frames `Note.find(42)` as giving "unexpected results." Actual: `find(42)` is accepted and returns the **single matching record** (a model instance), while `find({"id": 42})` returns a **list** of one. So bare-PK use is not rejected and does not misbehave — the only real surprise is the differing return shape (model vs list). Mild; the recommended `find_by_id()` is still clearer for PK lookups. Found 2026-06-22 · 3.13.39. Evidence: `pypy/tests/test_ch06_gotchas.py::test_g3_find_bare_pk_actually_returns_record_py_06_27`. Surface-logged. |
| PY-12-01 | open | no | 2026-06-23 · 3.13.39 | Reconcile S3's blockquote (`12-queues.md:91`) with the actual constructor: either drop "not constructor parameters" (the `backend=` kwarg works and overrides env), or document `backend=` as a supported per-instance override alongside `TINA4_QUEUE_BACKEND`. | **Chapter 12 Queues, S3 Creating a Queue and Pushing Messages — the backend-selection blockquote contradicts the `Queue` constructor.** The doc states *"The queue backend is selected via environment variables, not constructor parameters. Set `TINA4_QUEUE_BACKEND` to `file` (default), `rabbitmq`, `kafka`, or `mongodb`."* (also framed in S2 as *"The backend is configured via environment variables."*). Actual constructor signature: `Queue(self, topic='default', max_retries=3, backend: str | None = None, retry_backoff=0)` — `backend` IS a constructor parameter and it DOES select the backend: `Queue(backend="file")` → `LiteBackend`, `Queue(backend="rabbitmq")` → `RabbitMQBackend` (constructed lazily, no broker connection at init). So the kwarg is honoured, not ignored, directly contradicting "not constructor parameters." Found while implementing S2 config as a new reader (the kwarg appears the moment you `inspect.signature(Queue)`). Mild — env-var selection also works as documented; the false part is the exclusivity claim. Found 2026-06-23 · 3.13.39. Evidence: `pypy/tests/test_ch12_queue_config.py::test_s2_backend_is_a_constructor_param_py_12_01`. Surface-logged. |
| PY-12-02 | open | [#144](https://github.com/tina4stack/tina4-book/issues/144) | 2026-06-24 · 3.13.43 | Qualify the S2/S9 "work identically" claim: it holds for file/RabbitMQ/MongoDB but not Kafka. Either scope the guarantee to `push` + a long-running `consume()`, or add a Kafka caveat — `size()` is unsupported (always 0) and an immediate `pop()` / `consume(poll_interval=0)` returns nothing until the consumer group joins (~16 s); only a long-running `consume()` delivers. | **S2 (`12-queues.md:70`) and S9 (`:422`) claim push/pop/consume "work identically whether the backend is file, RabbitMQ, Kafka, or MongoDB" / "the same `queue.push()` and `queue.consume()` calls work with every backend" — verified TRUE for file/RabbitMQ/MongoDB but FALSE for Kafka on 3.13.43 against live brokers.** Stood up all four backends (Docker `rabbitmq:3`, `mongo:7`, `apache/kafka:3.7.0`; drivers `pika`/`pymongo`/`confluent-kafka` installed per S2) and ran the identical documented code path (`Queue(topic=).push(dict)` → `pop()` → `job.payload` → `complete()`; `produce()`×2 → `consume(poll_interval=0)` drain; `size()`): file/rabbitmq/mongodb returned identical results (push→str id, pop→payload, drain→`[1, 2]`, size→0). Kafka diverges two ways: **(1)** `pop()` and the documented drain-once `consume(poll_interval=0)` (S4 `:147-153`) return nothing immediately after a push — first delivery is only ~16 s later via repeated polling (confluent-kafka consumer-group join + earliest-offset rebalance), so a single `pop()` or a drain-once loop yields `[]`; only a long-running `consume()` (default `poll_interval=1.0`) eventually delivers (manually verified — `pop()` succeeded on attempt 16). **(2)** `size()` (documented S3 `:120-124` "Check how many pending messages are in the queue") is hardcoded `return 0` on Kafka (`tina4_python/queue_backends/kafka_backend.py:123-126`) — 3 pushes still report `size()==0`. The chapter's only broker caveats concern priority/delay *timing* (S3 `:107`, S5 `:208`), not pop/consume/size returning differently; the "work identically" sentences are unqualified. (Conversely MongoDB even honors priority via a DESC sort in `MongoConnector.dequeue`, over-satisfying the claim.) Origin: the doc overpromises — Kafka's log / consumer-group model (offsets, no queue-depth) fundamentally differs from the file/AMQP/Mongo claim-ack model; the framework's own Kafka adapter documents `size` as unsupported. Found 2026-06-24 · 3.13.43. Evidence: `pypy/tests/test_ch12_queue_backend_parity.py` (broker-gated round-trip across file/rabbitmq/mongodb — 3 pass) + `pypy/tests/test_ch12_queue_kafka_semantics.py` (kafka `size()`==0 with 3 pending + drain-once empty — 2 divergence sentinels that flip if Kafka converges). Brokers via Docker; tests skip when a broker is unreachable (logged blocker per rule 9, not rigged). **Aside (not a ch12 finding):** `Queue.clear()` on a freshly-constructed MongoDB-backed queue raises `AttributeError: 'NoneType' object has no attribute 'delete_many'` — `MongoBackend.clear()` (`queue/mongo_backend.py:127-131`) skips `_ensure_connected()`; `clear()` is not a Chapter-12-documented method, so out of scope here (candidate standalone tina4-python BH). Surface-logged; EOD adversarial pass owed before filing. **Re-verified STILL OPEN 2026-06-25 · tina4-python 3.13.47** (CLI 3.8.51): both halves persist. `size()` still hardcoded 0 (sentinel green). The 3.13.44 Kafka connector change (`queue_backends/kafka_backend.py` dequeue assignment-wait, bounded by `TINA4_KAFKA_ASSIGN_TIMEOUT`, default 15s) changed only the SYMPTOM — drain-once now BLOCKS for the assignment window instead of failing fast, but a freshly-pushed message still drains to `[]` (a fresh consumer joins at the latest offset, after the push). Deterministic 5/5 across independent processes on unique topics (~15.4s at the 15s default; identical `[]` at 2s). The `test_ch12_queue_kafka_semantics.py` drain sentinel was made deterministic (unique topic per run + short assign timeout) — the earlier full-suite "delivered 7 items" flake was a shared-topic accumulation artifact (old retained messages + a warmed consumer), NOT a fix. |
| PY-12-03 | open | no | 2026-06-24 · 3.13.43 | The S6/S7 retry → dead-letter lifecycle and management API (`size(status)`, `dead_letters()`, `retry()` revive, `purge()` count) don't behave on external brokers as the unqualified chapter shows. Either implement attempts-accumulation + dead-letter + `size(status)` + `retry()`-revive in the RabbitMQ/MongoDB/Kafka adapters, or scope S6/S7 to the file backend and state, per backend, which management ops apply. | **The documented S7 lifecycle (auto-retry → dead-letter) and management calls (`size(status)`, `dead_letters()`, `retry()` revive, `purge()`) behave very differently per backend on 3.13.43 — verified against live Docker brokers across the full documented op matrix.** S2/S9 claim everything "works identically"; S6/S7 present `max_retries`/`fail()`/`dead_letters()`/`retry()`/`size("dead")`/`purge()` with NO backend caveat (the only S7 caveat is that `retry_backoff` "applies to the file backend"). Actual: **(a) RabbitMQ never dead-letters** — `job.fail()` bumps `attempts` only on the local Job while RabbitMQ requeues the ORIGINAL message body (`reject(requeue=True)`), so every redelivery shows `attempts==0`, never reaches `max_retries`, and loops forever (verified: 4 consecutive fails → attempts `[0,0,0,0]`, `dead_letters()`==0). Even with `max_retries==1` (dead-letters on the first fail) `dead_letters()` returns 0 because it filters `attempts >= max_retries` against the stored `attempts==0`. **(b) `size(status)` supports only "pending"** on RabbitMQ/MongoDB/Kafka — `size("dead")`/`size("failed")` are hardcoded `0` (`queue/mongo_backend.py:65-68`, `queue/rabbitmq_backend.py:76-79`, `queue/kafka_backend.py:49-52`) even when MongoDB's own `dead_letters()` returns the dead job — contradicting S7 `:323-326`. **(c) `retry()` revives nothing on MongoDB or RabbitMQ** (S7 `:310-312` "Re-queue every dead-letter job") — MongoDB's `retry_job()` matches `status="failed"` in the main topic, but dead letters live in a separate `.dead_letter` collection (status "dead"), so it matches nothing and returns `False`; RabbitMQ has nothing to revive because (a) keeps `dead_letters()` empty. **(d) `purge()` returns `None`** on brokers vs the file backend's removed-count (minor). What DOES work cross-backend: basic push/pop/`complete()`, cross-topic `produce()`/`consume()`, `consume(iterations=)`; MongoDB additionally honors the full fail→dead-letter path AND priority. DOCUMENTED (NOT part of this finding): RabbitMQ ignoring priority (FIFO) and brokers ignoring `delay_seconds` are covered by S5 `:208` / S3 `:107`. Origin: the broker adapters implement transport (enqueue/dequeue/ack) but only partially implement the file backend's retry/dead-letter/status bookkeeping; the chapter documents the file backend's richer semantics as if universal. Found 2026-06-24 · 3.13.43. Evidence: `pypy/tests/test_ch12_queue_backend_lifecycle.py` (per-backend expectation maps across file/rabbitmq/mongodb — 21 tests) + `test_ch12_queue_backend_parity.py` + `test_ch12_queue_kafka_semantics.py`. Brokers via Docker; broker-gated skips. Surface-logged; EOD adversarial pass owed before filing. **Re-verified STILL OPEN 2026-06-25 · 3.13.47**: (a) RabbitMQ never dead-letters, (b) `size("dead")`==0 on rabbitmq+mongodb, (c) `retry()` revives nothing on rabbitmq+mongodb, (d) `purge()`→None on brokers — every expectation-map entry held; full ch12 suite 27 passed ×3 (deterministic). No `queue/` adapter file changed 3.13.43→3.13.47 (the diff touched only `queue_backends/` connectors + tests), so the lifecycle/management divergences are untouched. |
| BH-50 | open | [#144](https://github.com/tina4stack/tina4-book/issues/144) | 2026-06-24 · 3.13.43 | In `RabbitMQBackend.fail()` (`queue/rabbitmq_backend.py:173-181`) persist the incremented `attempts` into the redelivered message (re-`enqueue` the body with `attempts+1`, or carry attempts in message headers, instead of `reject(requeue=True)` which redelivers the original body) so a repeatedly-failing job reaches `max_retries` and dead-letters; also stamp `attempts` onto the dead-lettered body so `dead_letters()`' `attempts >= max_retries` filter returns it. | **RabbitMQ-backed `Queue` never dead-letters a repeatedly-failing job — it redelivers forever.** `job.fail()` does `job.attempts += 1` on the in-memory Job, then `reject(self._topic, id, requeue=True)`, which makes RabbitMQ requeue the ORIGINAL message body (still `attempts=0`). The next `pop()` rebuilds a Job from that body with `attempts=0`, so the `attempts >= max_retries` check in `fail()` never trips → the job loops indefinitely and `dead_letters()` stays empty. Even with `max_retries=1` (dead-letters on the first fail) `dead_letters()` returns 0 because it filters `attempts >= max_retries` against the dead-lettered body's stored `attempts=0`. Pure framework bug; fix lives in tina4-python. Found during Ch12 queue eval (S7). Found 2026-06-24 · 3.13.43 against a live RabbitMQ broker (Docker `rabbitmq:3`). Evidence: `pypy/tests/test_ch12_queue_backend_lifecycle.py::test_fail_accumulates_to_dead_letter[rabbitmq]` (asserts `dead_letters()`==0 — the divergence; flips when attempts persist); reproduced 4 consecutive fails → attempts `[0,0,0,0]`, dead 0. Doc-fidelity twin: PY-12-03 (book documents this lifecycle as universal). Surface-logged; EOD adversarial pass owed before filing. **Re-verified STILL OPEN 2026-06-25 · 3.13.47**: `queue/rabbitmq_backend.py` is byte-identical 3.13.43→3.13.47 (the diff touched only the `queue_backends/rabbitmq_backend.py` connector — a fresh-topic `size()` passive-declare crash + raw-AMQP TuneOk handshake, neither related to dead-lettering); `test_fail_accumulates_to_dead_letter[rabbitmq]` (dead_letters()==0) green ×3. Not fixed. |
| BH-51 | open | [#144](https://github.com/tina4stack/tina4-book/issues/144) | 2026-06-24 · 3.13.43 | Make `size(status)` honor non-pending statuses on the broker adapters: count the `.dead_letter` queue/collection for `"dead"` and the failed set for `"failed"` (MongoDB can `count_documents` the dead-letter docs; RabbitMQ can `queue_declare(passive)` `<topic>.dead_letter`) instead of the blanket `if status != "pending": return 0`. | **`size("dead")` and `size("failed")` always return 0 on the RabbitMQ, MongoDB, and Kafka backends, even when dead letters exist.** All three adapters hardcode `if status != "pending": return 0` — `queue/mongo_backend.py:65-68`, `queue/rabbitmq_backend.py:76-79`, `queue/kafka_backend.py:49-52`. On MongoDB this is self-inconsistent: `dead_letters()` returns the dead job while `size("dead")` reports 0. Only `LiteBackend` (file) implements size-by-status. Pure framework bug; fix lives in tina4-python. Found during Ch12 queue eval (S7 `size(status)`, `:323-326`). Found 2026-06-24 · 3.13.43 against live Docker brokers. Evidence: `pypy/tests/test_ch12_queue_backend_lifecycle.py::test_size_by_status_dead[rabbitmq|mongodb]` (asserts `size("dead")`==0 — the divergence; flips when implemented) + source read. Doc-fidelity twin: PY-12-03. Surface-logged; EOD adversarial pass owed before filing. **Re-verified STILL OPEN 2026-06-25 · 3.13.47**: the `queue/*_backend.py` adapter `if status != "pending": return 0` is untouched. (The 3.13.44 RabbitMQ *connector* `size()` change fixes a DIFFERENT bug — a fresh-topic `passive=True` declare that raised `ChannelClosedByBroker` 404 — not size-by-status.) `test_size_by_status_dead[rabbitmq|mongodb]` green ×3. Not fixed. |
| BH-52 | open | [#144](https://github.com/tina4stack/tina4-book/issues/144) | 2026-06-24 · 3.13.43 | Add `self._backend._ensure_connected()` at the top of `MongoBackend.clear()` (`queue/mongo_backend.py:127-131`), mirroring every other method on that adapter — they all call it before touching `self._backend._collection`. | **`Queue.clear()` on a freshly-constructed MongoDB-backed queue raises `AttributeError: 'NoneType' object has no attribute 'delete_many'`.** `MongoBackend.clear()` calls `self._backend._collection.delete_many({...})` directly, but `_collection` is `None` until `_ensure_connected()` runs (lazy connect). Every other MongoBackend method (`push`/`pop`/`size`/`purge`/`retry_failed`/`failed`/`dead_letters`/`retry_job`) guards with `_ensure_connected()` first; `clear()` is the only one that doesn't, so calling it before any other operation crashes. Pure framework bug, no documentation angle (`clear()` is not used in Chapter 12; surfaced while building the S2 backend-parity harness). Found 2026-06-24 · 3.13.43 against a live MongoDB broker (Docker `mongo:7`). Evidence: `pypy/tests/test_ch12_queue_mongo_clear_probe.py::test_mongo_clear_on_fresh_queue_raises_attributeerror` (asserts the `AttributeError`; flips when `_ensure_connected()` is added). Surface-logged; EOD adversarial pass owed before filing. **Re-verified STILL OPEN 2026-06-25 · 3.13.47**: no mongo file changed 3.13.43→3.13.47 (`queue/mongo_backend.py` + `queue_backends/mongo_backend.py` both untouched); `test_mongo_clear_on_fresh_queue_raises_attributeerror` green ×3 (the `AttributeError` is still raised). Not fixed. (Reminder: `clear()` is not a Chapter-12 method — this is a pure tina4-python code bug, filed on #144 per the chapter-thread convention, not a doc-fidelity finding.) |
| PY-12-04 | open | no | 2026-06-25 · 3.13.47 | In the file backend (LiteBackend) `retry()` no-arg path, loop over and re-queue ALL dead-letter jobs (not just one) so the no-argument form matches the documented "re-queue every dead-letter job"; or change the doc to say `retry()` revives one-at-a-time. | **Chapter 12 Queues, S7 Reviving Dead Letters — `queue.retry()` (no argument) re-queues only ONE dead-letter job, not "every" one.** The doc (`12-queues.md:310-312`) shows `queue.retry()` with the comment "Re-queue every dead-letter job". Actual on the file backend (the documented default/reference): with 3 dead-letter jobs queued, a single `queue.retry()` moves exactly ONE back to pending and leaves the other two dead (pending 0→1, dead 3→2). `retry(job_id)` (the one-specific form, S7:315) works correctly. Found while implementing S6/S7 verbatim as a reader. Found 2026-06-25 · 3.13.47. Evidence: `pypy/tests/test_ch12_queue_retry_deadletter_s7.py::test_retry_noarg_requeues_only_one_not_every_PY_12_04` (sentinel asserts only one of three revived; flips when all are re-queued). Surface-logged; EOD adversarial pass owed before filing. |
| PY-12-05 | open | no | 2026-06-25 · 3.13.47 | In the file backend Job.retry()/manual-retry path, remove the job from the dead-letter store when re-queuing it to pending (move, not copy), so a revived job is not simultaneously pending and dead. | **Chapter 12 Queues, S6 Job Methods — `job.retry()` on a dead-letter Job leaves a duplicate.** The doc (`12-queues.md:236`) says `job.retry(delay_seconds=0)` "manually re-queue the job, optionally after a delay. Bypasses the retry limit." Actual on the file backend: calling `.retry()` on a Job obtained from `dead_letters()` re-queues it to pending (good) but does NOT remove the dead-letter entry — the SAME job id then appears in BOTH pending (next `pop()` returns it) AND `dead_letters()`, so it will be delivered again from pending while still counted dead (duplicate processing). Verified: identical id present in both stores after one `dead.retry()`. Found 2026-06-25 · 3.13.47. Evidence: `pypy/tests/test_ch12_queue_lifecycle_s6.py::test_job_retry_leaves_duplicate_in_dead_PY_12_05` (asserts the duplicate; flips when the dead-letter copy is removed). Surface-logged; EOD adversarial pass owed before filing. |
| PY-12-06 | open | no | 2026-06-25 · 3.13.47 | Make file-backend `size("failed")` count the still-retrying jobs that `failed()` reports (0 < attempts < max_retries) so `size(status)` and the inspection methods agree; or document that `size("failed")` counts only a distinct holding state. | **Chapter 12 Queues, S7 Counting by Status — `size("failed")` returns 0 while `failed()` lists the failed job.** The doc (`12-queues.md:323-326`) states "`size` and `purge` accept a status: `pending`, `failed`, or `dead`," and (`:288-290`) `failed()` returns "Jobs that failed at least once but are still being retried (0 < attempts < max_retries)." Actual on the file backend: after one `fail()` under the retry limit, `failed()` returns the job (len 1) but `size("failed")` returns 0 — the documented "failed" status is not counted by `size()` even though `failed()` reports it (`size("pending")` is 1, the re-enqueued job counting as pending). The two documented surfaces disagree on the same job. Found 2026-06-25 · 3.13.47. Evidence: `pypy/tests/test_ch12_queue_retry_deadletter_s7.py::test_size_failed_zero_while_failed_lists_it_PY_12_06`. Surface-logged; EOD adversarial pass owed before filing. |
| PY-12-07 | open | no | 2026-06-25 · 3.13.47 | Implement `pop_by_id()` on the broker adapters (so `consume(job_id=)` works everywhere), or scope S4 "Consume a Single Job by ID" to the file backend with an explicit broker caveat. | **Chapter 12 Queues, S4 "Consume a Single Job by ID" — `consume(job_id=)` yields nothing on every broker.** The doc (`12-queues.md:163-171`) shows `for job in queue.consume("emails", job_id="specific-job-id")` with "Pass `job_id` to process one specific job. It yields that job once, then returns" — NO backend caveat. Actual: `consume(job_id=)` routes through `Queue.pop_by_id()`, which is hardcoded file-only — `if not isinstance(self._backend, LiteBackend): return None` (`tina4_python/queue/__init__.py`). So on RabbitMQ, MongoDB and Kafka, `consume(job_id=)` (and `pop_by_id()` directly) yields an empty result — the targeted job is never delivered. Verified live: file yields the target job; rabbit/mongo/kafka yield `[]`. A reader following S4 on any broker silently gets nothing back. Found during the average-user API-surface pass (the earlier S4 `consume(job_id)` test only covered the file backend). Found 2026-06-25 · 3.13.47 against live Docker brokers. Evidence: `pypy/tests/test_ch12_queue_backend_lifecycle.py::test_consume_job_id_file_only[rabbitmq|mongodb]` (sentinel: file yields the job, brokers yield []; flips when a broker delivers) + the live backend matrix (`/queue/backends`, `consume_jobid` + `pop_by_id` rows). Surface-logged; EOD adversarial pass owed before filing. |
| PY-18-10 | fixed | [#140](https://github.com/tina4stack/tina4-book/issues/140) | 2026-06-04 · pre-3.13.4 | — (fixed 3.13.4; probe `test_ch18_response_object_probe.py`) | **Fixed in tina4-python 3.13.4 (2026-06-05) via doc update — bundled into the PY-18-08 release. New S5 "Response Object" subsection (refreshed `18-testing.md:379-386`) correctly lists `resp.status`, `resp.body` (raw bytes), `resp.text()`, `resp.json()`, lowercased headers, `resp.content_type`. The framework itself is unchanged — the docs were brought into line with the real `TestResponse` class.** Originally: **Section 5 "Response Object" subsection (`18-testing.md:384-393`) reference table doesn't match `TestResponse`.** The code block lists four properties — `resp.status_code`, `resp.body` (string), `resp.headers`, `resp.content_type`. Empirically verified against `tina4_python.test_client.TestResponse` (`__slots__ = ("status", "body", "headers", "content_type")`) via probe in `pypy/tests/test_ch18_response_object_probe.py`: (a) `resp.status_code` does not exist — the real attribute is `resp.status`. Probe `test_doc_resp_status_code_attribute_exists` fails with `AttributeError`. (b) `resp.body` documented as "string" — actual type is `bytes`. Probe `test_doc_resp_body_is_a_string` fails; `test_real_resp_body_is_bytes` passes. Side-effect: chapter's `json.loads(resp.body)` calls work by luck (since Python 3.6 `json.loads` accepts bytes), but any user who does `resp.body.startswith(...)` or string-concatenates the body will hit `TypeError`. (c) Helper methods `resp.json()` and `resp.text()` exist on the class but are absent from the reference table. (Note: PY-18-08(b) and PY-18-08(c) overlap with parts of this finding — they were lumped under the test-client signature filing before the "one code block = one finding" convention was set. PY-18-10 is the canonical row for the Response Object code block; PY-18-08 keeps the test-client methods block.) |
| BH-49 | fixed | [#49](https://github.com/tina4stack/tina4-python/issues/49) — filed upstream 2026-06-10 (MichaelC8E), follow-on to BH-46 | 2026-06-10 · 3.13.8 | Gaps 1+2 → `Log.warning` from `_on_query_error` even inside an explicit txn; Gap 3 → capture `last_error` in `Database.fetch()` (mirror `Database.execute()`). | **Investigating (follow-on to #46):** whether 3 residual cascade-visibility gaps still hide the original cause. **Three paths still surface BH-46 symptom (cascade hides original cause) on 3.13.8** — all inside-explicit-transaction or `fetch()`-asymmetry. (Gap 1) `fetch()` inside `db.start_transaction()` cascades — `_heal_aborted_txn()` (postgres.py:79) + `_on_query_error` auto-rollback (postgres.py:162) defer by design (postgres.py:127-130 *"user owns that transaction"*); (Gap 2) `execute()` inside explicit txn cascades AND `Database.execute()` (connection.py:412-414) silently catches and returns `False` — caller has no signal; second poisoned call's `db.last_error` overwrites original cause with cascade message; (Gap 3) `db.last_error` asymmetric — `Database.fetch()` (connection.py:438-439) doesn't capture, `Database.execute()` (connection.py:412-414) does. Adapter has data on `adapter.last_error` (postgres.py:154) either way. **Suggested fixes (in filed body):** Gaps 1+2 → `Log.warning` from `_on_query_error` even inside-txn (preserves SAVEPOINT/retry contract, closes visibility); Gap 3 → one-line capture in `Database.fetch()` mirroring `Database.execute()`. **Verification (in repo, not in filed body — stripped per user during draft review):** 13-test matrix probe `pypy/tests/test_issue_46_matrix_probe.py` covers `{fetch, execute} × {outside txn, inside txn} × {fresh, post-failure, pre-poisoned}`. 5 gap assertions written as positive-direction regression sentinels — flip to fail (XPASS) when maintainer extends fix. Evidence: `bug-hunting/issue-49-comment.md` (posted body), `bug-hunting/issue-46-pg-silent-abort.md` (full analysis + disproof matrix). **VERIFY-PASS 2026-06-22 · 3.13.39 (own re-run): the 5 residual-gap sentinels FLIPPED red — framework behaviour changed. Gap 3 (`Database.fetch()` didn't capture `db.last_error`) is CLOSED: after a failing `GiftCard.where(...)`, `db.get_error()` now returns the original cause, so `test_gap_fetch_failure_does_not_populate_db_last_error` + `test_db_last_error_does_not_capture_the_original_cause` (both assert `get_error() is None`) now fail. The Gaps 1/2 (inside-explicit-txn cascade) sentinels also flipped. Per the standing rule (mark-fixed only on our own PER-GAP re-verification + sentinel reframe), BH-49 stays OPEN pending a careful per-gap reframe (queued — the all-out adversarial workflow that would do this hit the account session limit). Also note: the boolean/integer cause now surfaces as `DatatypeMismatch` in some paths (was `UndefinedFunction` on 3.13.8) — error-type drift to confirm during the reframe.** **NOW RESOLVED 2026-06-22 (own re-verify, lean adversarial workflow + source read): all 3 gaps CLOSED on 3.13.39 — (Gap 3) `Database.fetch()` now captures `last_error`, so `get_error()` returns the original cause after a failed `fetch()` (was None); (Gaps 1+2) `_on_query_error` emits the original cause via `Log.*` even inside an explicit txn (v3.13.11), and `Database.execute()` now RAISES instead of silently returning `False`. The 5 residual-gap sentinels were REFRAMED from assert-gap-present to assert-gap-absent and pass as regression guards (`test_issue_46_matrix_probe.py` + `test_issue_46_live_repro.py`; full suite 213 passed / 0 failed). Marked fixed on OUR testing per the standing rule; GitHub #49 left for the maintainer to close.** |
| BH-46 | closed | [#46](https://github.com/tina4stack/tina4-python/issues/46) — closed upstream 2026-06-09 (v3.13.6 + v3.13.8); residual gaps → #49 | 2026-06-08 · 3.13.8 | — maintainer fixed via `_heal_aborted_txn()` + `_on_query_error` routing; residual gaps tracked in #49. **Note: 3 residual-gap probes flipped on 3.13.30 — re-check whether the gaps are now addressed.** | **Investigating #46:** reproduce the reporter's silent PG-abort cascade and pin the original cause it was hiding. **Original symptom for reporter's exact call shape: FIXED in 3.13.8.** `GiftCard.where("created_by_email = ? AND is_deleted = 0", [email])` now raises the original `UndefinedFunction: operator does not exist: boolean = integer` with LINE/HINT pointer, and `Log.error` emits with full sql+params context. Cascade message no longer surfaces for the documented call path. Verified empirically against live PG 18 — exception type `psycopg2.errors.UndefinedFunction`, full ERROR log line carrying sql + params + LINE + HINT, no `"current transaction is aborted"` anywhere in the surfaced output. **Maintainer's fix shape differs from patches drafted at `bug-hunting/fix-issue-46-patches/`:** instead of SAVEPOINT around the count probe (the original suggestion mirroring lastval probe at `postgres.py:240-248`), maintainer used full `self._conn.rollback()` (postgres.py:288-292) outside explicit txn, routed `Log.error` via a new `_exec_with_handling` wrapper → `_on_query_error` (postgres.py:106-167) on the paginated query path. v3.13.8 added `_heal_aborted_txn()` pre-flight check (postgres.py:52-104) using `psycopg2 transaction_status == TRANSACTION_STATUS_INERROR` to recover connections that arrived poisoned from anywhere — broader coverage than the original suggestion. Both shapes solve the reporter's symptom; maintainer's is simpler at the count-probe site. **Residual gaps verified on 3.13.8 via 13-test matrix probe** (`pypy/tests/test_issue_46_matrix_probe.py`): (Gap 1) `fetch()` inside `db.start_transaction()` still cascades, original cause lost — heal step defers to explicit txns by design (postgres.py:79 + 127-130: *"Inside an explicit transaction we do NOT auto-rollback — the user owns that transaction"*); (Gap 2) `execute()` inside explicit txn cascades AND `Database.execute()` (connection.py:412-414) silently catches the exception and returns `False` — caller has no signal at all without polling `db.get_error()`, which on a second poisoned call returns the cascade message, not the original cause; (Gap 3) `db.last_error` asymmetry — `Database.fetch()` (connection.py:438-439) routes straight to `adapter.fetch()` with no `last_error` capture, while `Database.execute()` does capture. After `fetch()` failure, `db.get_error()` returns `None` even though `adapter.last_error` has the original cause — trivial one-line fix maintainer-side. **Empirical verification:** 22 BH-46 assertions pass on 3.13.8 across 3 files — `test_issue_46_pg_silent_abort_probe.py` (4 mocked, fix-direction code-path shape), `test_issue_46_live_repro.py` (5 live PG, reporter's call + log/last_error), `test_issue_46_matrix_probe.py` (13 live PG — 6 fix-direction + 5 residual-gap + 2 asymmetry, all positive-direction regression sentinels if maintainer extends fix to txn paths). **Adversarial disproof outcomes:** tried to break each fix claim — confirmed fix survives second valid call outside txn (heal works), survives different error types (`UndefinedFunction`, `DatatypeMismatch`, `UndefinedTable` all behave identically), confirmed `_heal_aborted_txn` fires correctly on raw-psycopg2-poisoned connections (WARNING log + ROLLBACK + cleared `transaction_status`), confirmed explicit-txn cascade reproduces on FRESH `Database()` instance with no prior pollution (gap is design choice, not stale state), confirmed `Database.execute()` swallow-and-return-False path makes silent-failure detection impossible inside txn without polling `last_error`. Two adjacent bugs still on backlog: (a) `SQLTranslator.boolean_to_int` (adapter.py:538-542) unconditionally rewrites `TRUE`/`FALSE` → `1`/`0` on PG, re-introducing the boolean/integer hazard — confirmed during matrix probe (valid `is_deleted IS FALSE` becomes invalid `is_deleted IS 0`); (b) framework's SAVEPOINT names (`_t4_lastval_probe` remains as fixed name in postgres.py:240-248) can collide with user-named savepoints — less urgent since maintainer chose ROLLBACK over SAVEPOINT for count probe. Evidence: `bug-hunting/issue-46-pg-silent-abort.md` (full post-fix analysis + disproof matrix + maintainer's actual fix shape + source-read of new wrappers), `bug-hunting/fix-issue-46-patches/` (3 original patches + README, kept for reference even though maintainer chose different shape), `pypy/tests/test_issue_46_*.py` (3 files, 22 assertions passing on 3.13.8). |
| BH-48 | fixed | [#48](https://github.com/tina4stack/tina4-python/issues/48) — maintainer fixed v3.13.14; GitHub issue still open pending OP upgrade-confirm | 2026-06-10 · 3.13.8 (fixed 3.13.14) | Not a framework bug; flag 4 adjacent doc/UX gaps — schema-qualified `table_name` (Ch6), naive `.lower()` name resolution, model name absent from `Log.error`, ignored `TINA4_DATABASE_URL` query string. | **FIXED in v3.13.14 (maintainer andrevanzuydam, 2026-06-13): introspection is now schema-aware on every engine — PostgreSQL `table_exists` uses `to_regclass()` (honours schema + `search_path`), `get_columns` filters by `table_schema`, `get_tables` returns non-`public` tables schema-qualified; MySQL/MSSQL/SQLite handled too. Maintainer-claimed AND OUR-VERIFIED locally on 3.13.39 (2026-06-22): against live PG, `table_exists('gift_cards.gift_card')` → True (pre-fix False), `table_exists('gift_cards.nope')` → False, `get_tables()` returns it schema-qualified, `get_columns()` → 3 cols. Probe `pypy/tests/test_issue_48_schema_introspection_probe.py`. The adjacent doc/UX gaps this finding also flagged (Ch6 schema-qualified `table_name` callout, ignored `TINA4_DATABASE_URL` query string) are NOT addressed by this code fix.** **Investigating #48:** reproduce the reporter's `UndefinedTable` error against a table they claim exists, and find what produces the schema-qualified name. **Status (2026-06-10):** pivoted after OP response — initial "user typo" hypothesis broken; investigating connection-target mismatch (pgAdmin on `staging` vs framework on `giftcard-service-dev`); awaiting OP env confirmation. **Reporter (same as #46/#47) hits `UndefinedTable: relation "gift_cards.gift_card" does not exist` against a table they claim exists.** Error log uses the new `_on_query_error` wrapper format from BH-46's v3.13.6 fix — pre-3.13.6 this error would have been hidden behind the cascade message. SQL emits `SELECT * FROM gift_cards.gift_card WHERE ...` — PG parses as schema-qualified (schema=`gift_cards`, table=`gift_card`). **Empirical reproduction (trial matrix against live PG 18, table `gift_cards` in `public` schema):** setting `table_name = "gift_cards.gift_card"` literally on a `GiftCard` ORM class produces byte-identical SQL + error to the reporter's log. Framework table-name resolution at `model.py:246-258` (`_get_table()`) returns `cls.table_name` verbatim with no transformation, no quoting, no schema-prefix injection. `where()` at `model.py:613-615` interpolates into `SELECT * FROM {table}` literally. **Thorough adversarial disproof attempts (11 angles tested):** (1) broader repo-wide grep across `tina4_python/` for f-string dot-concatenation between table-like names — 0 hits in framework code; (2) no schema env var exists (`TINA4_DB_SCHEMA`/`TINA4_SCHEMA`/`PGSCHEMA`); (3) `_translate_sql` empirically verified untouched table refs (all 3 transforms preserve `my_table` in `SELECT * FROM my_table`); (4) `ORMMeta` source-read — only collects fields/relationships/auto_crud, never modifies `table_name`; (5) `tina4 generate model` scaffold contains no `table_name` line at all; (6) default class-name resolution (`GiftCard` → `giftcard` via `.lower()`, or `giftcards` with `TINA4_ORM_PLURAL_TABLE_NAMES=true`) never generates dots; (7) 17 `_get_table()` call sites in `model.py` + 2 in `orm/fields.py` + 2 in `crud/` — all use same method, no alternative path; (8) PG `search_path` empirically confirmed NOT to help — created `CREATE SCHEMA gift_cards` + `SET search_path TO gift_cards, public`, query `SELECT * FROM gift_cards.gift_card` still fails (search_path only resolves unqualified names, dotted schema.table parsed literally); (9) `TINA4_DATABASE_URL` query string empirically confirmed IGNORED — connected with `?options=-csearch_path%3Dgift_cards`, resulting connection's search_path stays default `"$user", public` (urlparse extracts only host/port/user/password/dbname, query string dropped — separate gap); (10) PG error normalization confirmed — all three dotted forms (unquoted, double-quoted schema-qualified, single-quoted identifier with dot) produce byte-identical PG error text, but framework's logged `"sql": ...` payload preserves the SOURCE form, and reporter's log shows UNQUOTED → pins to `table_name = "gift_cards.gift_card"` (no quotes); (11) `soft_delete` default = `False` (verified empirically) and reporter's logged SQL has no parens or `OR is_deleted IS NULL` → their `is_deleted = 0` is explicit, not auto-injected. **Hypothesis stands.** **Disproof byproduct — BH-46 recalibration:** BH-46 and BH-48 are likely the SAME underlying user-side bug. The BH-46 cascade was hiding `UndefinedTable: relation "gift_cards.gift_card" does not exist`, NOT `operator does not exist: boolean = integer` as my BH-46 reproduction assumed. My BH-46 live_repro happened to work because I used `table_name = "gift_cards"` (sensible default) and built `CREATE TABLE gift_cards`, which triggers boolean=integer on reporter's WHERE clause. Reporter's actual trigger was missing-table — surfaced only after v3.13.6's cascade fix. **Doesn't invalidate BH-46 fix verification** — fix solves cascade for ANY trigger error, not specifically boolean=integer. **Not a framework bug strictly**, but issue surfaces 4 adjacent doc/UX gaps worth flagging: (a) Ch6 `table_name` paragraph (line 125) never mentions PG schema-qualified syntax / quoting / `search_path` interaction; (b) default class-name resolution is naive — `.lower()` only, no snake_case despite `camel_to_snake` utility existing at `model.py:67`. `GiftCard` → `giftcard`, not `gift_card`/`gift_cards`. Concrete UX consequence: scaffolding flow (`tina4 generate model GiftCard` + migration `CREATE TABLE gift_cards`) breaks because resolved name is `giftcard`; (c) `Log.error` output doesn't include model class name — could add `model=cls.__name__` at ORM call sites; (d) `TINA4_DATABASE_URL` query string ignored — users wanting non-public schema have to use `PGOPTIONS` env or manual `SET search_path` (undocumented). **Reply will:** acknowledge error visibility comes from BH-46 fix; walk reporter through empirical reproduction matrix; ask for `src/orm/GiftCard.py` to confirm `table_name` literal; flag the 4 adjacent gaps as separate concerns. Evidence: `bug-hunting/issue-48-undefined-table-relation.md` (full investigation + trial matrix + 11-angle disproof + BH-46 recalibration note + adjacent gaps + reply guidance). No probe — investigation-only at this stage. |
| BH-47 | fixed | [#47](https://github.com/tina4stack/tina4-python/issues/47) — maintainer shipped ImportError fix v3.13.6; GitHub issue still open (closing left to us) | 2026-06-08 · 3.13.5 (ImportError fixed 3.13.6) | Docs-only: add a Ch1 prerequisites callout, switch Ch5 to `tina4-python[<extra>]` extras syntax, and rewrite the 6 lazy-import ImportError texts to recommend the extras form. | **FIXED (primary recommendation) in v3.13.6 (maintainer andrevanzuydam, 2026-06-10): the 6 lazy-import ImportError messages are now multi-line and recommend both the `tina4-python[<extra>]` uv-extras form and the bare pip driver; same treatment across MySQL/MSSQL/Firebird/ODBC/MongoDB + cross-framework parity. Maintainer-claimed AND OUR-VERIFIED locally on 3.13.39 (2026-06-22): shipped `postgres.py:249-253` raises the multi-line ImportError recommending `uv add tina4-python[postgres]` / `pip install psycopg2-binary` / `uv add tina4-python[all-db]` (psycopg2 is installed here, so verified by source-read of the raised message; probe `pypy/tests/test_issue_47_importerror_extras_probe.py`). The Ch1-prerequisites-callout / Ch5-extras-syntax DOC parts of this finding are unconfirmed (maintainer comment addressed only the ImportError texts); GitHub issue left open for us to close.** **Investigating #47:** verify the OP's claim that the DB drivers are required at runtime but unbundled and under-documented. **`psycopg2-binary` (and the other 5 DB drivers) is required at runtime but not bundled by default.** Verified on tina4-python **3.13.5** (upgraded from 3.13.4 on 2026-06-09; bug-direction behaviour identical). OP's claim is correct on all 4 parts: (a) `psycopg2` required — `postgres.py:54-58` lazy-imports + raises; (b) not bundled — METADATA only declares it under `Requires-Dist: psycopg2-binary>=2.9; extra == 'postgres'`, no unconditional Requires-Dist; (c) "by design" matches the zero-dep framing in Ch1 line 5 + 8 declared extras (postgres/mysql/mssql/firebird/mongo/odbc/all-db/dev-reload), same pattern at all 6 adapters; (d) "needs documenting" — partially true. **Where the requirement IS documented:** METADATA lines 145-155 + PyPI page + repo README (full extras list); Book Ch5 Database flags it but only with bare `uv add psycopg2-binary` (no extras syntax). **Where it ISN'T:** Book Ch1 Getting Started — zero hits on postgres / psycopg / mysql / driver / extras / optional across all 1132 lines, despite Ch1 line 152's *"One package. No dependency tree. Just `tina4-python`."* claim. Plus the 6 lazy-import ImportError messages all recommend bare `pip install <driver>` rather than the canonical `tina4-python[<extra>]` form from METADATA itself. Plus `tina4 init python .` scaffolded `pyproject.toml` comments suggest bare `uv add psycopg2-binary`. Repo-wide grep for `tina4-python[` across `documentation/tina4-book/` and `pypy/.venv/Lib/site-packages/tina4_python/`: zero matches outside METADATA. **Adversarial disproof attempts (2026-06-09):** checked for hidden DB-driver mention later in Ch1 (none); checked for separate `/python/installation` or `/python/getting-started.html` docs (404); checked for CHANGELOG mentioning extras (no CHANGELOG in dist-info); confirmed pip absent from uv-scaffolded `.venv/Scripts/` (bare `pip install` literal advice would fail). Dropped "version pin bypass" angle (pin is `>=2.9`, loose); real cost = maintainer can't redirect driver choice (e.g. psycopg2 → psycopg3) without rewriting 6 ImportError sites + book chapter. Softened Ch1 framing from "contradicts" to "no callout". **Recommendations (in posted comment):** primary = docs-only (Ch1 prerequisites callout + Ch5 switch to extras syntax + rewrite 6 ImportError texts); alternatives if maintainer wants a UX change = bundle all 6 into base deps (kills zero-dep claim), baseline subset like `[postgres,mysql]` pre-included, or `tina4 init python --db=postgres` scaffolder flag (lowest-disruption). Evidence: `bug-hunting/issue-47-psycopg2-dep-gap.md` (full analysis + adversarial disproof results), `bug-hunting/issue-47-comment.md` (exact posted body). No probe — pure doc gap. |
| PY-18-14 | open | no | 2026-06-22 · 3.13.39 | Note in Ch18 S5 that `/health` reflects recorded errors (HTTP 503 + `status:"error"` when any unresolved error exists) and that errors persist in `data/.broken/` across restarts; the health-test snippet's `200`/`"ok"` assertions only hold on a clean error slate. Either document clearing/resolving recorded errors before the health assertion, or make the example error-state-independent. | **New 3.13.39 behaviour surfaced re-verifying Ch18 S5 "Testing Routes" on the version bump (3.13.30→3.13.39).** On 3.13.30 `GET /health` returned `200` `{"status":"ok",...}` and the chapter's `test_health_endpoint` (asserts `resp.status == 200`, `body["status"]=="ok"`, version present) passed on a fresh scaffold. On 3.13.39 `/health` is error-aware: body expanded to `{"status","uptime_seconds","version","framework","errors","latest_error"}` and returns **HTTP 503** with `status:"error"` whenever ≥1 unresolved error is recorded. Errors are **file-backed** at `data/.broken/<ts>_<type>.broken` and **survive serve restarts** — a single earlier error (e.g. the PY-06-23 `recent()` 500) keeps `/health` red until the store is cleared or the error marked resolved. Reproduced under `tina4 serve` (port 7150): with the stale PY-06-23 `.broken` record present → `/health` 503; after moving `data/.broken/` aside + restart → `/health` 200 `{"status":"ok","errors":0}`; after one `GET /api/posts/recent` (re-triggers PY-06-23) → `data/.broken/` repopulates and `/health` → 503 again (`errors:1`, fresh timestamp). The pytest in-process Test path does NOT write `data/.broken/` (only the served HTTP error handler does), so `test_health_endpoint` stays green under pytest on a clean store. Surface-logged. |

### Observed terminal output

Snippets attached to the findings above, where the issue is about code that doesn't run.

#### PY-01-06 — `pip install tina4` fails (wrong package name)

```
PS C:\Users\work\Documents\projects\testing-tina4\pypy> pip install tina4
ERROR: Could not find a version that satisfies the requirement tina4 (from versions: none)
ERROR: No matching distribution found for tina4
```

#### PY-01-07 — `tina4 install --help` shows it installs runtimes, not framework

```
$ tina4 install --help
Install a language runtime (python, php, ruby, nodejs)

Usage: tina4.exe install <LANG>

Arguments:
  <LANG>  Language to install: python, php, ruby, nodejs
```

#### PY-01-08 — `tina4 doctor` exposes the mis-labelled "Tina4 CLIs" section

```
  Tina4 CLIs
  ──────────────────────────────────────────────────────────────────────
  ✗ tina4python      Python       not found  →  run: pip install tina4-python
  ✗ tina4php         PHP          not found  →  run: composer global require tina4/tina4php
  ✗ tina4ruby        Ruby         not found  →  run: gem install tina4ruby
  ✗ tina4nodejs      Node.js      not found  →  run: npm install -g tina4nodejs
  ✗ vite             tina4js      not found  →  run: npm install vite
```

#### PY-01-10 — Python landing-page quickstart fails verbatim (no `tina4` CLI install step)

Documentation shows (Python landing page, Installation section):

```
pip install tina4-python
tina4 init my-project
cd my-project
tina4 serve
```

Actual (followed verbatim, Windows):

```
PS C:\Users\work> pip install tina4-python
Successfully installed tina4-python-3.13.38

PS C:\Users\work\Documents> tina4 init my-first-tina
tina4 : The term 'tina4' is not recognized as the name of a cmdlet, function,
script file, or operable program. ...
    + FullyQualifiedErrorId : CommandNotFoundException
```

#### PY-01-09 — `tina4python` CLI crashes on Windows (cp1252) printing help

```
PS C:\Users\work> tina4python
Traceback (most recent call last):
  File "...\Python313\Scripts\tina4python.exe\__main__.py", line 5, in <module>
    sys.exit(main())
  File "...\site-packages\tina4_python\cli\__init__.py", line 126, in main
    _help()
  File "...\site-packages\tina4_python\cli\__init__.py", line 207, in _help
    print(""" Tina4 Python — CLI ... """)
  File "...\Python313\Lib\encodings\cp1252.py", line 19, in encode
    return codecs.charmap_encode(input,self.errors,encoding_table)[0]
UnicodeEncodeError: 'charmap' codec can't encode character '→' in position 1703: character maps to <undefined>

PS C:\Users\work> tina4python --version
Traceback (most recent call last):
  ...
  File "...\site-packages\tina4_python\cli\__init__.py", line 157, in main
    _help([])
  ...
UnicodeEncodeError: 'charmap' codec can't encode character '→' in position 1703: character maps to <undefined>
Unknown command: --version
```

#### PY-06-23 — S11 `recent()` scope uses SQLite `datetime('now', ?)`, fails on PostgreSQL

```
>       posts = BlogPost.recent()        # @classmethod -> cls.where("created_at > datetime('now', ?)", [f"-{days} days"])

E       psycopg2.errors.UndefinedFunction: function datetime(unknown, unknown) does not exist
E       LINE 1: SELECT * FROM posts WHERE created_at > datetime('now', '-7 d...
E                                                      ^
E       HINT:  No function matches the given name and argument types. You might need to add explicit type casts.

  query = "SELECT * FROM posts WHERE created_at > datetime('now', %s) LIMIT %s OFFSET %s"
  vars  = ['-7 days', 20, 0]
```

#### PY-06-04 — S4 `select_one`/`load` examples query a `slug` column the Note model lacks

Documentation shows (`06-orm.md:412`, `:428`):

```python
note = Note.select_one("SELECT * FROM notes WHERE slug = ?", ["my-note"])
note.load("slug = ?", ["my-note"])
```

Note model fields (S2, `06-orm.md:108-121`): `id, title, content, category, pinned, created_at, updated_at` — no `slug`.

Actual output:

```
select_one slug RAISED: UndefinedColumn | column "slug" does not exist
load slug RAISED:       UndefinedColumn | column "slug" does not exist
```

Issues:
- `slug` is referenced in two S4 query examples but is not a field on the documented Note model.
- Verbatim copy raises `UndefinedColumn` (PG) / `no such column: slug` (SQLite).
- Framework behaves correctly — the column genuinely does not exist; the gap is in the chapter.

#### PY-06-06 — S4/S6 positional path-param handlers can't be driven by the documented Test client

Documentation shows (`06-orm.md:314`, S4 `find_by_id` handler; same shape at `:361`, `:570`, `:613`):

```python
@get("/api/notes/{id:int}")
async def get_note(id, request, response):
    note = Note.find_by_id(id)
    ...
```

Actual output (driving the verbatim handler through `tina4_python.test`'s client):

```
E       TypeError: get_note() missing 1 required positional argument: 'response'
.venv\Lib\site-packages\tina4_python\test_client\__init__.py:155: TypeError
```

Issues:
- The server dispatch (`core/server.py:1272` `_invoke_handler`) injects `{id:int}` by parameter name, so the handler works under `tina4 serve`.
- The Test client (`test_client/__init__.py:155`) calls `handler(request, response)` flatly — a handler whose first positional param is the path arg raises `TypeError`.
- Handlers with no path param (`create_note`, `list_notes`) run fine via the Test client → the gap is path-param injection, not the `response(...)` call form.
- The positional signature matches the framework's own routing docs (`tina4_python/CLAUDE.md`), so testing documented handlers with the documented Test client fails on dispatch parity, not on user error.

#### PY-06-05 — glance `Post` and S6 `BlogPost` share `table_name="posts"` with incompatible schemas

Documentation shows two models on the same table — `06-orm.md:23-33` (glance) and `06-orm.md:551-565` (S6):

```python
class Post(ORM):       # ORM at a Glance
    table_name = "posts"
    id = IntegerField(primary_key=True, auto_increment=True)
    title = StringField(required=True, max_length=200)
    body = StringField(default="")
    created_at = DateTimeField()

class BlogPost(ORM):   # S6 has_many
    table_name = "posts"
    id = IntegerField(primary_key=True, auto_increment=True)
    author_id = IntegerField(required=True)
    title = StringField(required=True, max_length=300)
    slug = StringField(required=True)
    # ...content, status, created_at, updated_at
```

Actual output — verbatim `Post.create(title="x")` against the S6 `BlogPost` table:

```
PostgreSQL query failed: UndefinedColumn: column "body" of relation "posts" does not exist
Post.create(title='x') -> <Post id=None>
```

Against `Post`'s own clean schema, all 8 Common Query Operations work:

```
create(title='x')        -> id=1
post.save()              -> id=2
find_by_id(p.id)         -> <Post id=1>
find({'title':'x'})      -> 1 rows
where('title = ?',['x']) -> 1 rows
all()                    -> 2 rows
count()                  -> 2
post.delete()            -> True
```

Issues:
- Two documented models declare `table_name = "posts"` with incompatible columns — copy-paste collision.
- Verbatim `Post.create(title="x")` hits `UndefinedColumn: column "body"` when the S6 table exists first.
- `create()` swallows the error and returns an unsaved `<Post id=None>` (no exception, no `False`) — same swallow class as PY-18-13e.

#### PY-06-07 — documented write routes return 401 (undocumented Bearer gate)

Documentation shows (`06-orm.md:276-285`):

```python
@post("/api/notes")
async def create_note(request, response):
    note = Note()
    note.title = request.body["title"]
    # ...
    note.save()
    return response({"message": "Note created", "note": note.to_dict()}, 201)
```

Actual output (verbatim `POST /api/notes` under `tina4 serve`, no token):

```
{"error":"Unauthorized","message":"Valid authorization token required","status":401}
```

Issues:
- Tina4 gates POST/PUT/PATCH/DELETE behind a Bearer token by default; the chapter shows the write route as a plain `@post` with no auth note.
- Read routes (`GET /api/notes`, `/api/notes/{id}`, `/api/authors/{id}`, `/api/posts/{id}`) serve 200 over HTTP — only writes 401.
- Chapter 6 never mentions `auth`, `token`, `@noauth()`, or a Bearer header (grep: zero matches outside the word "author").
- Not a framework bug — the gate is the intended default (PY-10-02); the gap is documentation. Same shape in the S9 Auto-CRUD `curl -X POST` example and the S14 solution.

#### PY-06-08 — `BooleanField` is native BOOLEAN on PG; S4 `select([1])` fails

Documentation shows — S2 field-types table (`06-orm.md:136`) and the S4 SQL-first example (`06-orm.md:401-404`):

```
| BooleanField | bool | INTEGER (0/1) | True/False |
```

```python
notes = Note.select(
    "SELECT * FROM notes WHERE pinned = ? ORDER BY created_at DESC",
    [1], limit=20, offset=0
)
```

Actual output (verbatim, PostgreSQL):

```
psycopg2.errors.UndefinedFunction: operator does not exist: boolean = integer
LINE 1: SELECT * FROM notes WHERE pinned = 1 ORDER BY created_at DES...
information_schema.columns: notes.pinned data_type = boolean
```

Issues:
- On PG the `pinned` column is native `BOOLEAN`, not `INTEGER (0/1)` as the field-types table states.
- The raw-SQL `select(..., [1], ...)` example passes integer `1`; PG rejects `boolean = integer`.
- `[True]` works, and `find({"pinned": True})` works (the ORM translates) — only the documented raw `[1]` form breaks.
- Cross-ref BH-46 (`SQLTranslator.boolean_to_int`).

#### PY-06-13 — Test client skips the write-route auth gate (serve 401 vs client 201)

`POST /api/notes` — verbatim S4 `create_note` (`06-orm.md:276-285`):

Over `tina4 serve` (real HTTP):

```
{"error":"Unauthorized","message":"Valid authorization token required","status":401}
```

Through the `tina4_python.test` client (`self.post("/api/notes", json={...})`):

```
STATUS 201
{"message":"Note created","note":{"id":1,"title":"X",...}}
```

Issues:
- Same handler, two dispatchers, two outcomes — `tina4 serve` enforces the Bearer gate, the Test client does not.
- A write-route test via the documented Test client passes (201) while the route 401s in production.
- Dispatch-parity family with PY-06-06 (path params); here the divergence is auth.

#### PY-06-16 / PY-06-17 — S3 interactive `create_table()` flow broken in the program

Documentation shows (`06-orm.md:260-264`):

```bash
tina4 shell
>>> from src.orm.note import Note
>>> Note.create_table()
```

Actual output:

```
$ tina4 shell
error: unrecognized subcommand 'shell'        # PY-06-16 — REPL is `tina4 console`

$ tina4 console
[ERROR] Failed to load .../src/orm/note.py: No module named 'src'   # PY-06-17 (startup auto-load)
>>> from src.orm.note import Note
ModuleNotFoundError: No module named 'src'      # PY-06-17 — manual import fails too
```

Issues:
- `tina4 shell` is not a CLI subcommand (real REPL: `tina4 console`).
- `tina4 console` does not put the project root on `sys.path`, so `from src.orm.X import Y` fails — the same modules load fine under `tina4 serve`.
- Together: the documented S3 interactive `create_table()` flow cannot be run in the program. The ORM/soft-delete behaviour itself works (pytest vs live PG).

#### PY-06-18 — auto-CRUD shadows custom routes (doc says custom wins)

Documentation shows (`06-orm.md:941-943`): *"Custom routes defined in `src/routes/` load before auto-CRUD routes. They take precedence."*

Actual — `Note` with `auto_crud = True` + custom `/api/notes` routes, under `tina4 serve`:

```
[INFO] AutoCrud: registered 5 routes for Note (/api/notes)   # auto-CRUD registers FIRST
...
[DEBUG] Route registered: POST /api/notes (auth=required)    # custom registers AFTER

$ curl http://localhost:7146/api/notes
{"records":[],"data":[],"count":0,"total":0,"limit":10,"offset":0,"page":1,...}   # auto-CRUD payload, not custom {notes,count}
```

Issues:
- Auto-CRUD routes register before custom same-path routes and serve the request — custom routes are shadowed.
- Directly contradicts the documented precedence ("custom routes take precedence").

#### PY-18-02 — `tina4 test` fails because pytest isn't installed

```
$ tina4 test
C:\Users\work\Documents\projects\testing-tina4\pypy\.venv\Scripts\python.exe: No module named pytest
```

#### PY-18-03 — `tina4 test --help` has no options

```
$ tina4 test --help
Run tests (delegates to language CLI)

Usage: tina4.exe test

Options:
  -h, --help  Print help
```

Re-verified 2026-06-05 on CLI 3.8.28 + tina4-python 3.13.4:

```
$ tina4 test --verbose
error: unexpected argument '--verbose' found

$ tina4 test --file tests/test_ch18_basic.py
error: unexpected argument '--file' found
```

S9 re-verification (2026-06-05, CLI 3.8.28 + tina4-python 3.13.4) — the
chapter's two Code Coverage examples both reject at the CLI before pytest is
reached:

```
$ tina4 test --cov=src --cov-report=term
error: unexpected argument '--cov' found

$ tina4 test --cov=src --cov-report=html
error: unexpected argument '--cov' found
```

The underlying tooling works — `uv run python -m pytest --cov=src
--cov-report=term` produces the expected report against the same suite
(73 statements, 97% covered) — but the chapter's documented invocation path
through `tina4 test` does not.

#### PY-18-04 — Discovery silently skips non-`test_*.py` files; actual output is raw pytest

A file named `ch18_basic.py` (without the `test_` prefix) is not discovered:

```
$ tina4 test
collected 0 items
no tests ran in 0.01s
```

Docs claim this output format:

```
Running tests...

  BasicTest
    [PASS] test_addition
    [PASS] test_string_contains
    [PASS] test_array_length

  3 tests, 3 passed, 0 failed (0.02s)
```

Actual output is raw pytest:

```
============================= test session starts =============================
platform win32 -- Python 3.13.13, pytest-9.0.3, pluggy-1.6.0
rootdir: C:\Users\work\Documents\projects\testing-tina4\pypy
configfile: pyproject.toml
collected 3 items

tests\test_ch18_basic.py ...                                             [100%]

============================== 3 passed in 0.22s ==============================
```

#### PY-18-07 — Section 4 snippet fails twice in a row

Before adding the `Product` import:

```
tests\test_ch18_product.py FFFFF                                         [100%]
================================== FAILURES ===================================
_______________________ ProductTest.test_create_product _______________________

    def test_create_product(self):
>       product = Product()
E       NameError: name 'Product' is not defined

tests\test_ch18_product.py:7: NameError
```

After adding `from src.orm.product import Product`, every `product.save()` hits:

```
_______________________ ProductTest.test_create_product _______________________

    def test_create_product(self):
        product = Product()
        product.name = "Test Widget"
        ...
>       product.save()

.venv\Lib\site-packages\tina4_python\orm\model.py:308: in save
    db = self._get_db()
...
E       RuntimeError: No database bound. Call orm_bind(db) or set TINA4_DATABASE_URL in .env
```

#### PY-18-08 — Section 5 route-test signatures don't match reality

We used this from the docs:

```python
resp = self.get("/health")
assert_equal(resp.status_code, 200, "Health check should return 200")
```

It didn't work and said:

```
E       AttributeError: 'TestResponse' object has no attribute 'status_code'
```

We used this from the docs:

```python
resp = self.post("/api/products", {
    "name": "Route Test Product",
    "category": "Testing",
    "price": 42.00
})
```

It didn't work and said:

```
E       TypeError: Test.post() takes 2 positional arguments but 3 were given
```

#### PY-18-12 — S7 `User` referenced with no import

Documentation shows (`18-testing.md:466-501`, refreshed 2026-06-05):

```python
from tina4_python.test import Test, assert_equal, assert_not_none
import time

class UserTest(Test):

    def set_up(self):
        user = User()
        user.name = "Test User"
        user.email = f"test-{int(time.time())}@example.com"
        user.save()
        self.user_id = user.id
    ...
```

Actual output:

```
    def set_up(self):
        # Runs before each test
>       user = User()
E       NameError: name 'User' is not defined

tests\test_ch18_setup_teardown.py:12: NameError
```

Issues:
- `User` referenced in `set_up`, `tear_down`, and both test methods. Not imported anywhere in the chapter.
- No `User` ORM model defined or shown in Ch18.
- Same defect class as PY-18-07a (S4 Product) before the 3.13.4 fix; the parallel fix was not applied to S7.

#### PY-18-13 — S12 `test_user_model.py` broken in 5 independent ways

Documentation shows (`18-testing.md:744-811`):

```python
import uuid
from tina4_python.test import Test, assert_equal, assert_true, assert_not_none, assert_raises

class UserModelTest(Test):

    def test_duplicate_email(self):
        ...
        assert_raises(create_duplicate, Exception, "Should reject duplicate email")

    def test_select_users(self):
        ...
        users, count = User.where("1=1")
        assert_true(len(users) >= 3, "Should have at least 3 users")
```

Actual output (verbatim, sequential — each error reached after patching the previous):

```
# PY-18-13a — on collection before any test runs:
NameError: name 'User' is not defined

# PY-18-13b — after adding import, on first test:
RuntimeError: No database bound. Call orm_bind(db) or set TINA4_DATABASE_URL in .env

# PY-18-13d — test_select_users (reaches this after a/b patched):
ValueError: too many values to unpack (expected 2)
tests\test_user_model.py:82: ValueError

# PY-18-13e — test_duplicate_email (with UNIQUE index manually applied):
AssertionError: Should reject duplicate email
.venv\Lib\site-packages\tina4_python\test\__init__.py:387: AssertionError
```

Issues:
- `User` never imported — `NameError` before any test runs (PY-18-13a).
- No `TINA4_DATABASE_URL`, no `create_table()` — `RuntimeError` on first `user.save()` (PY-18-13b).
- No `unique` kwarg on `StringField`, no migration/index shown — chapter mandates duplicate rejection with no mechanism (PY-18-13c).
- `User.where("1=1")` returns `list`, not `(list, int)` — needs `with_count=True` (PY-18-13d).
- `ORM.save()` swallows all exceptions (model.py:336-338) — `assert_raises` can never fire; real contract is `save()` returns `False` (PY-18-13e).

#### PY-18-10 — Response Object reference doesn't match `TestResponse`

Documentation shows (`18-testing.md:384-393`):

```python
resp.status_code   # HTTP status code (200, 201, 404, etc.)
resp.body          # Response body as a string
resp.headers       # Response headers as a dict
resp.content_type  # Content-Type header value
```

Framework reality (`tina4_python/test_client/__init__.py:28-52`):

```python
class TestResponse:
    __slots__ = ("status", "body", "headers", "content_type")
    self.status: int = response.status_code
    self.body: bytes = response.content
    self.content_type: str = response.content_type
    self.headers: dict = {...}
    def json(self): ...
    def text(self): ...
```

Probe (`pypy/tests/test_ch18_response_object_probe.py`):

```
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_doc_resp_status_code_attribute_exists FAILED
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_real_resp_status_attribute_works     PASSED
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_doc_resp_body_is_a_string            FAILED
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_real_resp_body_is_bytes              PASSED
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_undocumented_text_helper_exists      PASSED
tests/test_ch18_response_object_probe.py::ResponseObjectProbe::test_undocumented_json_helper_exists      PASSED
```

Failure details:

```
E       AttributeError: 'TestResponse' object has no attribute 'status_code'
E       AssertionError: docs claim resp.body is a string
```

Issues:
- `resp.status_code` documented; real attribute is `resp.status`.
- `resp.body` documented as string; real type is `bytes`.
- `resp.json()` and `resp.text()` methods exist on the class; not listed in the reference.

## Bug Hunt — `BH-<n>` rows

Bug-hunt findings live in the **Known Issues Log above**, labelled `BH-<n>` where `<n>` is
the upstream `tina4-python` issue number (e.g. `BH-46` ↔ [`#46`](https://github.com/tina4stack/tina4-python/issues/46)).
They share the KI Log's format and differ only in origin:

- **`PY-NN-NN`** — surfaced by the documentation-fidelity protocol while walking chapters.
- **`BH-<n>`** — a bug the user *assigned*: a reproduction / root-cause request against an
  existing GitHub issue ("go investigate this, dig with tests and theories until the root
  cause is nailed down"). Each `BH-<n>` row's **Note** opens with what's being investigated.

Per-finding evidence is kept on the `bug-hunting` branch (never `main`):
- `bug-hunting/issue-<n>-<slug>.md` — root cause, source-line evidence, adversarial
  verification, recommended fix, draft upstream comment.
- `pypy/tests/test_issue_<n>_*.py` — probes that *try to trigger the bug*: the assertion
  reads as FAIL while the bug is present (functionality goal unmet) and PASSES once the
  upstream fix lands — the same correct-state sentinel direction as the `PY-NN-NN` probes
  (readme.md → Convention Recap → *Probe pattern*). Legacy exception: some BH-46/49
  gap-assertions were authored inverted (pass-while-buggy, "flip to fail when fixed") — their
  row Notes describe them as-built; new probes follow the canonical direction above.

The GitHub issue thread is the "official log"; the **Filed** column links it.

## Suggested Fixes

Proposed remedies for entries in the Known Issues Log. Each fix tags one or more issue IDs
and includes rationale, concrete edits, and acceptance criteria.

Status values: `proposed` | `accepted` | `applied` | `rejected`.

### Editorial principles

These guidelines apply to every fix proposed in this section. Future fixes should default
to them unless there's a specific reason not to:

1. **Tina4 docs are not install guides for other people's tools.** Prerequisites
   (Python, uv, Rust/Cargo, Ruby, PHP, Composer, Node, etc.) get listed and linked
   out — never embedded as platform-specific install snippets. The owners of those
   tools maintain better install docs than the Tina4 docs ever can, and trying to mirror them
   creates drift and bloats every page.
2. **Required vs. optional prereqs are marked as such.** If a tool is needed only
   for one specific path (e.g. Cargo for `cargo install tina4`), label it optional
   and tie it to the path that needs it.
3. **One concept per heading.** External prereqs, the CLI, and the framework package
   are three different things and live in three different sections. Don't mix them.
4. **Show the dependency chain, in order.** Language runtime → tool → project. Pages
   should follow that flow so a reader following them top-down never has to scroll
   back.
5. **Annotate every prerequisite with what it's for.** Each entry in a prereqs list
   carries a one-line note explaining its role — not "install Python," but "Python
   3.12+ — the runtime that executes your app." A reader scanning the list should
   know *why* each item is required, not just that it is.

### FIX-01 — Restructure the Python Getting Started page

**Tags:** PY-01-01
**Page:** `https://tina4.com/python/01-getting-started.html`
**Status:** proposed

**The problem in one sentence.** The current page collapses three distinct concepts —
external prerequisites, the Tina4 CLI (a Rust tool), and the `tina4-python` framework
package — into a single "What You Need / Install" mash-up. A first-time reader can't tell
where the boundary is between "things outside Tina4," "the tool," and "the framework."

**Proposed structure.** Replace the current "What You Need" + "Installing the Tina4 CLI"
sections with three top-level headings that follow the actual dependency chain:

```
## 1. Prerequisites
   Python 3.12+    — the language runtime that executes your app.
                     Install from python.org/downloads.
   uv              — manages your project's Python dependencies; `tina4 init`
                     uses it to add the framework package to your project.
                     Install from docs.astral.sh/uv/getting-started/installation.

## 2. Install the Tina4 CLI
   What it is:     a Rust binary that scaffolds and runs Tina4 projects.
                   It is NOT the Python framework — that lives inside your project
                   and is pulled in by `tina4 init` (see step 3).
   macOS:          brew install tina4stack/tap/tina4
   Linux/macOS:    curl -fsSL https://.../install.sh | bash
   Windows:        irm https://.../install.ps1 | iex
   Verify:         tina4 --version

## 3. Create your first project
   tina4 init python my-app
   cd my-app
   tina4 serve
   What just happened: `tina4 init` scaffolded the project structure and
   added `tina4-python` to your dependencies via uv.
```

**What to delete from the current page.**

- The "What You Need" list item #3 ("The Tina4 CLI — a Rust-based binary...") — the CLI
  is the subject of the next heading, not a prerequisite to itself.
- The `python3 --version` verification command in prereqs (or move it inline with the
  Python link). It currently implies Python is installable but no instructions are given —
  worse than just linking out.
- Any platform-specific `uv` install snippets in prereqs. Replace with a single line:
  *"uv — install from [astral.sh/uv](https://docs.astral.sh/uv/getting-started/installation/)."*

**Rationale.**

- Mirrors the actual dependency chain: language → tool → project.
- Equalizes Python and uv (PY-01-01 symptom a): both link out, neither gets snippets.
- Distinguishes the CLI from the framework (PY-01-01 symptom b): they live in different
  headings, with an explicit "this is NOT the Python framework" call-out.
- Eliminates the contradiction of listing the CLI as a prerequisite while also installing
  it on the same page (PY-01-01 symptom c).

**Acceptance criteria.**

- A reader who has only Python + uv installed can follow steps 2→3 and reach a running
  server without needing to scroll back to re-read prereqs.
- The words "Tina4 CLI" and "tina4-python" each appear in exactly one heading scope, and
  the page text explicitly states that they are different things.
- The prereqs section contains zero install commands — only link-outs.

---

### FIX-02 — Cargo install option

**Tags:** PY-01-03
**Page:** `https://tina4.com/python/01-getting-started.html` (and any sibling
language pages that show the same option).
**Status:** proposed

**The problem in one sentence.** The page offers `cargo install tina4` as an install
path without ever listing Cargo (the Rust toolchain) as a prerequisite or linking to
how to get it.

**Three acceptable resolutions** — pick one:

**Option A: remove the cargo option from this page.**
The Homebrew, curl, and PowerShell paths already cover every supported platform.
Removing cargo shortens the page and eliminates the unannounced-prereq trap.
Mention cargo only in the project's GitHub README for contributors building from source.

**Option B: keep cargo, but quarantine it.**
Move the `cargo install tina4` snippet under a clearly labelled subsection — e.g.
*"Install from source (advanced)"* — that opens with a one-line prereq note:

> *Requires the Rust toolchain. If you don't already have it, install via
> [rustup.rs](https://rustup.rs) first.*

**Option C (recommended): list Cargo as an *optional* prerequisite, with the note inline at the cargo command.**
Keeps the cargo install path visible alongside the other platforms (no new subsection),
but makes its dependency explicit so the reader can't be ambushed. Two parts:

1. In the Prerequisites section, after the required items, add a third entry:

   > *Cargo / Rust toolchain (optional) — only needed if you plan to install the
   > Tina4 CLI via `cargo install`. See [rustup.rs](https://rustup.rs).*

2. In the install snippets, label the cargo line clearly so the conditional nature
   is obvious at the point of use:

   ```
   macOS:        brew install tina4stack/tap/tina4
   Linux/macOS:  curl -fsSL .../install.sh | bash
   Windows:      irm .../install.ps1 | iex
   From source:  cargo install tina4   (requires Rust — see Prerequisites)
   ```

This is the recommended option because it preserves user choice, sets expectations
up-front *and* at the point of use, and avoids creating a new "advanced" subsection
for what is really just one extra line.

**What NOT to do.**

- Do not leave the cargo command alongside the brew/curl/PowerShell options as a
  same-level "alternative" with no prereq note. That's the current state and the
  source of the issue.
- Do not silently assume readers who reach for cargo "obviously" have Rust — many will
  recognize the syntax from copy-paste habits without having the toolchain.

**Acceptance criteria.**

- Either no `cargo install tina4` appears on the Getting Started page (Option A), OR
  every occurrence of it is accompanied — either inline or via a clearly named parent
  subsection — by a note that names Rust/Cargo as a requirement and links to
  [rustup.rs](https://rustup.rs) (Options B or C).
- A reader with no Rust toolchain who follows the recommended install path on any
  platform succeeds without a missing-tool error.
- The global Prerequisites section, if it mentions Cargo at all, marks it as
  *optional* and ties it to a specific install path (Option C).

---

### FIX-03 — `tina4 test --file` should auto-resolve in `tests/`

**Tags:** PY-18-03
**Page:** `https://tina4.com/python/18-testing.html` S8 (Running Tests), plus
the CLI implementation in the Rust binary.
**Status:** proposed

**The problem in one sentence.** When `--file` is eventually implemented for
`tina4 test`, the documented call form `tina4 test --file tests/test_product.py`
forces the reader to type the `tests/` prefix even though the framework
already knows tests live in `tests/`. Discovery is convention-based; the flag
shouldn't undo that convention.

**Recommendation.** The CLI should accept a bare filename and resolve it
against `tests/` automatically. Full paths still work for explicit cases.

```
tina4 test --file test_ch18_basic.py            # auto-resolves tests/test_ch18_basic.py
tina4 test --file tests/test_ch18_basic.py      # explicit path also accepted
tina4 test --file src/probes/check_x.py         # absolute-from-project path: used as-is
```

Resolution order (first match wins):
1. Path exists relative to cwd (current behaviour shown in docs).
2. Path exists relative to `tests/`.
3. Glob match within `tests/` for `**/{name}` (e.g. `--file test_ch18_basic.py`
   resolves even if it sits in `tests/ch18/test_ch18_basic.py`).

**Doc update once implemented.** S8 examples should drop the `tests/` prefix to
demonstrate the convention:

```
tina4 test --file test_product.py                              # specific file
tina4 test --file test_product.py --method test_create_product # specific method
```

With a one-line callout: *"Bare filenames resolve in `tests/` automatically.
Pass an explicit path (`tests/sub/test_x.py`) when needed."*

**Why.** Tina4's design philosophy is convention over configuration (per the
framework's own `CLAUDE.md`). The current docs contradict that by making the
reader spell out the location of a dir the framework already owns. Pytest
itself supports this via test IDs (`pytest test_x.py::Class::method`) but
only when invoked from project root with `tests/` on the discovery path —
`tina4 test --file` is positioned as the user-friendly wrapper, so the
ergonomics should be at least as good.

**Acceptance criteria.**

- `tina4 test --file test_product.py` succeeds without `tests/` prefix when
  the file lives at `tests/test_product.py`.
- `tina4 test --file tests/test_product.py` continues to work (no breaking
  change).
- S8 doc examples updated to use the bare-filename form, with a one-line
  callout naming the resolution rule.

---

### FIX-04 — `tina4 test` output formatter: per-file bar, right-anchored status, bottom printer line

**Tags:** PY-18-04
**Page:** `https://tina4.com/python/18-testing.html` S1, S2, S4, S8 output
examples, plus the CLI implementation in the Rust binary.
**Status:** proposed

**The problem in one sentence.** S1's framing of `tina4 test` as having its
own readable output format was honest-on-paper but fictional in practice;
the 3.13.4 fix corrected the docs to acknowledge pytest. A real custom
formatter would let the chapter's *original* visual intent ship, and would
read better than raw pytest dots for the typical Tina4 workflow.

**Proposed layout — two modes.** Both modes share: per-file fill-bar (fills
as the file's tests complete), bottom "printer line" updating in place with
the running test ID, final failure list showing exact failing test IDs.

**Normal mode** (default): per-file row only. PASS/FAIL right-anchored to a
fixed column so status doesn't drift with varying filename widths. Bar
leftmost, filename middle. No per-file counts, no per-file times.

```
================================= Tina4 test run =================================

 ████████████████████  test_ch18_basic.py                                     PASS
 ████████████████████  test_ch18_assertions.py                                PASS
 ████████████████████  test_ch18_product.py                                   PASS
 ████████████░░░░░░░░  test_ch18_routes.py                                    ····
 ░░░░░░░░░░░░░░░░░░░░  test_ch18_client_methods.py                              -
 ░░░░░░░░░░░░░░░░░░░░  test_ch18_auth.py                                        -

──────────────────────────────────────────────────────────────────────────────────
 [█████████████████░░░░░░░░░░░░░░░]  26/59  •  test_ch18_routes::test_create_product
```

Final state of normal mode:

```
================================= Tina4 test run =================================

 ████████████████████  test_ch18_basic.py                                     PASS
 ████████████████████  test_ch18_assertions.py                                PASS
 ████████████████████  test_ch18_product.py                                   PASS
 ██████░░░░░░░░░░░░░░  test_ch18_routes.py                                    FAIL
 ████████████████████  test_ch18_client_methods.py                            PASS
 ████████████████████  test_ch18_auth.py                                      PASS
 ████████████████████  test_ch18_setup_teardown.py                            PASS

──────────────────────────────────────────────────────────────────────────────────
 [████████████████████████████████]  55/59 passed  •  4 failed  •  0.33s

 Failures (4):
   FAIL  test_ch18_routes::test_get_products       AssertionError: Should return 200
   FAIL  test_ch18_routes::test_create_product     TypeError: Test.post() takes ...
   FAIL  test_ch18_routes::test_delete_product     KeyError: 'id'
   FAIL  test_ch18_routes::test_validation         AssertionError: empty body
```

**Verbose mode** (`--verbose`, see FIX-03 / PY-18-03): per-file header
unchanged in shape but adds counts (`n/m`) and per-file time on the right;
each test rendered as an indented row underneath with its own PASS/FAIL
and time. Status left-anchored on the per-file row so the indented per-test
rows line up under it.

```
========================== Tina4 test run (verbose) ==========================

 PASS   ████████████████████  test_ch18_basic.py                    3/3    0.02s
        PASS  test_addition                                                0.001s
        PASS  test_string_contains                                         0.000s
        PASS  test_array_length                                            0.001s

 PASS   ████████████████████  test_ch18_assertions.py             13/13    0.03s
        PASS  AssertEqualTest::test_equal_numbers                          0.000s
        ...

 ····   ████████████░░░░░░░░  test_ch18_routes.py                   4/6    ...
        PASS  test_health_endpoint                                         0.005s
        PASS  test_get_products                                            0.012s
        FAIL  test_create_product                                          0.008s
              TypeError: Test.post() takes 2 positional arguments but 3 given
        PASS  test_get_product_not_found                                   0.003s

──────────────────────────────────────────────────────────────────────────────────
 [█████████████████░░░░░░░░░░░░░░░]  26/59  •  test_ch18_routes::test_create_product
```

**What each mode does and doesn't surface.**

| Element                              | Normal | Verbose |
|--------------------------------------|:------:|:-------:|
| Per-file fill-bar + PASS/FAIL        |   ✓    |    ✓    |
| Per-file counts (n/m tests)          |   ✗    |    ✓    |
| Per-file time                        |   ✗    |    ✓    |
| Per-test indented rows               |   ✗    |    ✓    |
| Per-test time                        |   ✗    |    ✓    |
| Bottom printer line (current test)   |   ✓    |    ✓    |
| Bottom failure list (exact test IDs) |   ✓    |    ✓    |

The failure list at the bottom of normal mode is the key trade-off — normal
mode hides per-test detail in the body but never hides which specific tests
failed. A reader scanning the right-hand column for `FAIL` knows which file
broke; the failure list tells them exactly which test inside.

**Rationale.**

- Right-anchored status in normal mode = the rightmost column becomes a
  fail roll-call. Eye finds failures at a fixed x-coordinate regardless of
  filename length.
- Fill-bar per file = real progress signal (fills as the file's tests run),
  not pytest's "% of total collected" which jumps unpredictably across files.
- Bottom printer line in place of file-by-file dot stream = one moving
  cursor showing the current test ID. Friendlier than the percentage
  progress at the end of each pytest file line.
- Mode split = readers who only want "did anything break" use normal;
  readers debugging a specific test use verbose. Pytest's `-q` / `-v` split
  is the same split; this is the same idea with a Tina4-native skin.

**Doc updates once implemented.** S1, S2, S4 output examples currently
show raw pytest output (post-PY-18-04 fix). Replace those with the normal-
mode mock above. S8 currently mentions `--verbose` (rejected by the CLI per
PY-18-03); once the formatter ships, the `--verbose` example should output
the verbose-mode mock above.

**Acceptance criteria.**

- `tina4 test` (default) emits the normal-mode layout: per-file bar +
  right-anchored PASS/FAIL, bottom printer line, bottom failure list with
  exact failing test IDs.
- `tina4 test --verbose` emits the verbose-mode layout: same per-file row
  but with counts + time, plus per-test indented rows.
- Both modes share the same final failure list format.
- S1, S2, S4, S8 doc examples updated to match the actual output.
- Raw pytest output remains accessible (e.g. `tina4 test --raw` or
  `uv run python -m pytest`) so users who need the underlying tool aren't
  blocked.

#### Implementation specification — exact characters, widths, and rules

This section nails down the visual primitives so an implementer can build
the formatter without guessing. Mocks above are illustrative; the rules
below are normative.

**Character set (Unicode codepoints).**

| Glyph | Codepoint | Name             | Where used                                              |
|-------|-----------|------------------|---------------------------------------------------------|
| `█`   | U+2588    | FULL BLOCK       | Bar — filled cell (per-file bar and bottom overall bar) |
| `░`   | U+2591    | LIGHT SHADE      | Bar — empty cell                                        |
| `·`   | U+00B7    | MIDDLE DOT       | "Running" status glyph (four of them: `····`)           |
| `─`   | U+2500    | BOX DRAWINGS LIGHT HORIZONTAL | Section separator above the bottom bar     |
| `=`   | U+003D    | EQUALS SIGN (ASCII) | Run header rule (`=== Tina4 test run ===`)           |
| `•`   | U+2022    | BULLET           | Inline separator in the bottom line (e.g. `26/59 • test_…`) |
| ` `   | U+0020    | SPACE            | All padding (NEVER tab / U+0009)                        |
| `-`   | U+002D    | HYPHEN-MINUS (ASCII) | Not-started status placeholder in normal mode       |

Do **not** substitute visually-similar glyphs:
- `█` ≠ `■` (U+25A0 BLACK SQUARE) — squares mis-render half-height in some terminals.
- `░` ≠ `▒` (U+2592 MEDIUM SHADE) — medium shade reads as 50% fill, not "empty".
- `·` ≠ `•` ≠ `.` — middle dot is the running glyph, bullet is the inline
  separator, full stop is never used.
- `─` ≠ `—` (em dash) ≠ `-` (hyphen-minus) — the separator must be
  U+2500 box drawing.
- ASCII `=` is correct for the header rule. Do NOT use `═` (U+2550 DOUBLE
  HORIZONTAL) — pytest uses `=` and the header reads as the Tina4 layer
  above pytest; keeping `=` reinforces continuity.

**Fallback for non-UTF8 / Windows legacy code-page terminals.** Detect
encoding at startup; if the stream can't encode U+2588/U+2591/U+00B7, fall
back to:

| Unicode | ASCII fallback |
|---------|----------------|
| `█`     | `#`            |
| `░`     | `.`            |
| `····`  | `....` (four ASCII full stops) |
| `─`     | `-`            |
| `•`     | `*`            |

No mixing — either pure-Unicode or pure-ASCII for a given run. A
`TINA4_TEST_ASCII=1` env var forces the ASCII set.

**Column widths.** Fixed for both modes. Lengths are in display cells, not
bytes (every glyph above is single-cell width — no double-wide CJK chars
in the format itself).

| Column                                | Width | Mode      |
|---------------------------------------|------:|-----------|
| Left edge gutter (space)              |   1   | both      |
| Bar                                   |  20   | both      |
| Bar→filename gutter (spaces)          |   2   | both      |
| Filename                              |  50   | both (left-padded with spaces) |
| Filename→status gutter (spaces)       |   2   | normal — status on right       |
| Status (`PASS`/`FAIL`/`····`/`-`)     |   4   | normal — right-aligned in the 4-cell slot |
| Status before bar (per-file row)      |   4   | verbose — left, *before* bar  |
| Status→bar gutter (verbose)           |   2   | verbose                       |
| n/m count                             |   5   | verbose (right-aligned, e.g. ` 3/3 `, `13/13`) |
| count→time gutter                     |   3   | verbose                       |
| Time                                  |   6   | verbose (right-aligned, e.g. `0.02s`, `0.001s`)|

Total line widths come out to 82 cells normal, 82 cells verbose — keep
them equal so the separator rule below renders the same length in both.

**Bar fill rule.**

```
filled_cells = round(20 * tests_completed_in_file / tests_total_in_file)
empty_cells  = 20 - filled_cells
bar = "█" * filled_cells + "░" * empty_cells
```

Rounding is half-to-even (banker's rounding) — avoid surprise full bars
when one test in many is still pending. If `tests_total_in_file` is
unknown during collection, render `░` × 20 with status `-`.

**Status glyph rules.**

- `PASS` — every test in the file passed.
- `FAIL` — at least one test in the file failed OR errored (collection
  error counts as FAIL on the file row).
- `····` (four U+00B7) — file currently running, at least one test started.
- `-` — file not yet started (collected but waiting).
- Status string is exactly 4 cells; right-pad with spaces if any future
  status is shorter (e.g. `OK` would render as `OK  `, never `OK`).

**Right-alignment (normal mode).** The status column ends at cell 82 of
the line. Compute:

```
status_left_edge = 82 - 4 = 78
filename_right_edge = 78 - 2 = 76   # 2-cell gutter
```

Pad filename column with trailing spaces so its right edge sits at cell 76.
For the not-started rows, render `-` right-aligned in the 4-cell slot
(`   -`) — the same column as `PASS`/`FAIL` — so the rightmost column reads
cleanly top-to-bottom.

**Bottom printer line.** Single line, rewritten in place via ANSI
`\r` + `\x1b[2K` (carriage return + erase line). No newline at end while
running. Once the run completes, emit a newline and replace with the
final summary line. Format:

```
 [<bar32>]  <done>/<total>  •  <current_test_id>
```

Where `<bar32>` is 32 cells using the same `█`/`░` chars; `<done>` and
`<total>` are integers (no padding); `<current_test_id>` is
`file_stem::class::method` (no `tests/` prefix, no `.py` suffix), truncated
to fit terminal width minus the prefix using middle-ellipsis (e.g.
`test_ch18_routes::…::test_create_product`).

**Final summary line** (replaces the printer line on completion):

```
 [████████████████████████████████]  <p> passed  •  <f> failed  •  <T>s
```

Bar always full (32 `█`). `<p>` and `<f>` are integer counts; `<T>` is
total wall-clock seconds to 2 decimal places (e.g. `0.33`). Drop the
`• <f> failed` clause entirely when `<f> == 0`.

**Failure list** (appears after the summary line, when `<f> > 0`):

```
 Failures (<f>):
   FAIL  <file_stem>::<class>::<method>   <ExceptionType>: <single-line message>
   ...
```

Rules:
- `Failures (N):` heading line, exactly one space before `Failures`.
- Each failure row: 3-space indent, `FAIL  ` (status + 2 spaces),
  test ID, 3 spaces, exception class + colon + first line of message.
- Truncate the message to keep the row at ≤ 100 cells; suffix `…` if
  truncated. Full traceback available via `--verbose` or in a written
  log file at `logs/tina4-test-<timestamp>.log`.
- No blank line between failure rows. One blank line before the heading,
  one blank line after the last row.

**Time format.**

- Per-test time (verbose only): seconds to 3 decimals, e.g. `0.001s`,
  always 5 chars + `s` = 6 cells. Under 1ms shows `0.000s` (not `<0.001s`).
- Per-file time (verbose only): seconds to 2 decimals, e.g. `0.02s`,
  always 4 chars + `s` = 5 cells (allow up to 99.99s; over that, switch to
  `XXm` for whole minutes with no decimals).
- Total run time (summary): same as per-file but unbounded — render
  `0.33s`, `12.45s`, `1m23s`, `5m04s` as the magnitude requires.

**Colour scheme** (when stdout is a TTY and `NO_COLOR` env var is unset):

| Element                            | ANSI                                |
|------------------------------------|-------------------------------------|
| `PASS`                             | bright green (`\x1b[92m`)           |
| `FAIL`                             | bright red (`\x1b[91m`)             |
| `····` running                     | bright yellow (`\x1b[93m`)          |
| `-` not started                    | dim grey (`\x1b[2m\x1b[37m`)        |
| Bar filled cells                   | inherit terminal default (no colour) |
| Bar empty cells                    | dim grey                            |
| Bottom bar filled                  | inherit                             |
| Filename                           | inherit                             |
| Failure rows `FAIL` glyph + ID     | bright red                          |
| Failure exception line             | inherit                             |
| Run header / separator rules       | dim grey                            |

When `NO_COLOR` is set, or stdout is not a TTY, emit plain ASCII/Unicode
with no escape sequences. The fallback in this case is the same layout —
colour is decorative only.

**Indentation in verbose mode per-test rows.** 8 spaces (matches the
length of the per-file row's "status + gutter + bar start"), then 4-cell
`PASS`/`FAIL` (left-aligned), then 2-space gutter, then test name
(class-qualified), then padding to time column. Time format same as
per-file time but 3 decimals (per-test rule above).

**Things to NOT do (anti-patterns seen elsewhere):**

- Don't use ANSI cursor-up to overwrite the per-file rows — the running
  file's row gets its bar updated in place, but completed rows above
  must stay put. Use a single bottom-line cursor pattern only.
- Don't right-trim trailing whitespace on a row before emitting it —
  the trailing spaces are load-bearing for the right-aligned status
  column. Trimming breaks alignment in terminals that auto-trim.
- Don't print the run header until after collection completes — the
  count `26/59` in the printer line needs the total. Show a single-line
  "Collecting tests…" stub during collection, then redraw.
- Don't substitute the four middle dots `····` with three (`···`) or an
  ellipsis `…` — the running glyph is always exactly 4 cells to match
  `PASS`/`FAIL` width.
- Don't render the per-file bar live-updating cell-by-cell as each test
  finishes if the file completes in under 100 ms — the flicker reads as
  glitchy. Batch updates at 100 ms minimum cadence, or render the file
  row only on file completion if the whole file ran under that threshold.

---

### FIX-05 — Chapter 6 (ORM) should set up its own database

**Tags:** PY-06-01, PY-06-02
**Type:** Documentation
**Page:** `https://tina4.com/python/06-orm.html`
**Status:** proposed

**The problem in one sentence.** Chapter 6 teaches the ORM but never shows the
two things every example silently depends on — a connected database (PY-06-01)
and an existing table per model (PY-06-02) — so a reader who lands on this
chapter, or copies any section past S3, hits `No database bound` then
`relation "<table>" does not exist`.

**Proposed structure.** Add a short setup block at the very top of the chapter
(before S2 "Defining a Model"), then a one-line per-section reminder where new
models appear.

1. **Top-of-chapter setup section** — demonstrate the connection the chapter
   assumes, pointing back to Chapter 5:

   > **Before you start.** The ORM needs a database connection. Set
   > `TINA4_DATABASE_URL` in your `.env` (see Chapter 5) — the ORM auto-binds to
   > it. Each model maps to a table; create it with `Model.create_table()` (shown
   > below) or a migration before you query or save.

2. **Per-section table reminder** — every section that introduces a model
   (S6 Author/BlogPost, S8 Task, S12 Product, S13/14 blog) opens with a single
   line, e.g.:

   > *Assuming a database is connected and the `authors` and `posts` tables exist
   > (`Author.create_table()`, `BlogPost.create_table()`).*

3. **Self-contained exercise/solution.** The S14 solution (`src/routes/blog.py`)
   should either include the `create_table()` calls (app startup) or ship a
   migration for `authors`, `posts`, `comments` — as written it saves to three
   tables that no chapter step creates.

**Rationale.**

- Mirrors the actual dependency chain: connect DB → create table → query.
- Fixes both PY-06-01 (binding) and PY-06-02 (tables) at their root — the chapter
  omitting its own setup — rather than patching each example.
- A reader can follow Chapter 6 top-down, or jump to any section, and reach a
  working result without inferring the missing setup.

**Acceptance criteria.**

- A reader who has only completed Chapter 5 can run any Chapter 6 section's code
  and have it succeed (no `No database bound`, no `relation does not exist`).
- Every section that defines a model names the table it needs and how to create it.
- The S14 solution is runnable as shipped — the three tables it writes to are
  created by the chapter (startup `create_table()` or migration).

---

### FIX-06 — Strip Chapter 6 (ORM) to Python only

**Tags:** PY-06-03
**Type:** Documentation
**Page:** `https://tina4.com/python/06-orm.html`
**Status:** proposed

**The problem in one sentence.** The Python ORM chapter carries ~85 lines of
non-Python content — PHP/Ruby/Node.js model definitions and a four-language
comparison table (`06-orm.md:13-98`) — before the Python material proper begins.

**Proposed change.**

- Remove the PHP, Ruby, and Node.js code blocks from the "ORM at a Glance"
  section (`06-orm.md:37-78`).
- Drop the four-language "Common Query Operations" table (`06-orm.md:85-94`), or
  reduce it to the Python column only.
- Remove cross-language caveats in the surrounding prose (e.g. *"PHP needs
  `(new Post())`…"*, *"Ruby methods drop the parentheses"*).
- If the cross-language parity story is worth telling, move it to a shared
  overview page that sits above the per-language books — not inside the Python
  chapter.

**Rationale.**

- A reader in the Python book wants Python. Other-language code is noise that
  pushes the actual Python material down the page.
- The same applies to every Python chapter — check for and strip the same
  multi-language interludes elsewhere (this fix is scoped to Ch06; others get
  their own findings as they're walked).

**Acceptance criteria.**

- Chapter 6 contains only Python code and Python-relevant prose.
- No PHP/Ruby/Node.js code blocks or N-language comparison tables remain in the
  chapter body.

---

### FIX-07 — Lead the Quick Reference with an Installation / Update section; rename it "Getting Started / Quick Reference"

**Tags:** PY-01-10 (primary); relates to PY-01-09, PY-01-01
**Page:** the existing **Quick Reference** page — to be renamed **"Getting Started / Quick Reference"**. The broken landing quickstart (`/python/#installation`, PY-01-10) links here instead of carrying its own commands. Pattern repeats per language.
**Thread:** [#143](https://github.com/tina4stack/tina4-book/issues/143) — Tina4 Chapter Quick Reference (PY-01-10 report filed here 2026-06-19).
**Status:** proposed

**The problem in one sentence.** Install commands are scattered (a four-line quickstart on the landing page, a fuller flow in the Getting Started chapter) and no single place lists *every* command a from-zero reader runs, in order — and the landing quickstart is the broken one (PY-01-10): it shows `pip install tina4-python → tina4 init → cd → tina4 serve`, never installs the `tina4` CLI, so a brand-new reader dies at step 2 with `'tina4' is not recognized`.

**Proposed structure.** Don't add a new page. Make the existing **Quick Reference** the canonical home: add an **Installation / Update** block as its **first section**, and rename the page **"Getting Started / Quick Reference"** so a newcomer recognizes it as the entry point. A reader who has *only their OS* — no project, no CLI, no framework — follows that first section top-down and reaches a running server. Headings follow the dependency chain (Editorial principle 4); the CLI and the framework package stay in separate sub-sections (principle 3); other tools link out, never embedded (principle 1).

```
## Prerequisites   (Tina4 links out — it does not bundle these)
   Python 3.12+  — the runtime that executes your app.   → python.org/downloads
   uv            — manages your project's dependencies.   → docs.astral.sh/uv

## Install the Tina4 CLI   (one Rust binary; serves all four languages)
   What it is:   the tool that scaffolds and runs projects. NOT the Python
                 framework — that lives inside your project (next section).
   macOS:        brew install tina4stack/tap/tina4
   Linux/macOS:  curl -fsSL https://raw.githubusercontent.com/tina4stack/tina4/main/install.sh | bash
   Windows:      irm https://raw.githubusercontent.com/tina4stack/tina4/main/install.ps1 | iex
   Verify:       tina4 --version

## Create and run a project
   tina4 init python my-app
   cd my-app
   tina4 serve            # → http://localhost:7145

## Update   (returning users)
   tina4 update                       # upgrade the CLI
   uv pip install -U tina4-python     # upgrade the framework, inside a project
```

**What changes elsewhere.**

- **Landing "Get Started" becomes the *what*, not the *how*** — what Tina4 is, what you need (concepts), and "pick a language." It links to the Installation / Update section of **Getting Started / Quick Reference** instead of carrying its own command list.
- **Delete the broken four-line quickstart** (`pip install tina4-python → tina4 init → …`) from the landing page. Its `pip install tina4-python` lead is the trap: it yields the framework package + the `tina4python` script, not the `tina4` CLI the next line calls (and that script then crashes on a cp1252 Windows console — PY-01-09).
- **Bare `pip install tina4-python` appears only in the separate, clearly-labelled "Manual Setup (No CLI)" route** — the one that ends in `python app.py` and never invokes `tina4`. It must not lead any CLI-based flow.
- **The Getting Started chapter narrative references Getting Started / Quick Reference** rather than re-listing the commands, so setup commands live in exactly one place.

**Relationship to FIX-01.** FIX-01 restructures the Getting Started *chapter* in place (Prerequisites / Install the CLI / Create project). FIX-07 puts those same canonical commands in the first section of **Getting Started / Quick Reference** so they exist once and other pages link to them. Both share the three-concept model; FIX-07 supersedes the *install portion* of any page that currently re-lists commands.

**Acceptance criteria.**

- A reader with only their OS installed follows the Installation / Update section top-down and reaches a running server — no scroll-back, no missing-tool error, no missing-command error (`tina4 init` never runs before the CLI is installed).
- No page presents a CLI-based flow whose first command is `pip install tina4-python`. That command appears only in the "Manual Setup (No CLI)" route.
- The words "Tina4 CLI" and "tina4-python" each live in one heading scope, with an explicit "these are different things" call-out.
- An Update sub-section lets a returning user upgrade the CLI (`tina4 update`) and the framework package, each labelled for its target.
- The Quick Reference page is titled **"Getting Started / Quick Reference"** with Installation / Update as its first section; the landing page's old four-line quickstart no longer exists and links here instead.

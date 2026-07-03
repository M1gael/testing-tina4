# Coverage Ledger — Python · Chapter 6: ORM

Per-section proof-of-coverage for the chapter evaluation. This is the **canonical
coverage home** for Chapter 6 — the Evaluation Progress row for "06 — ORM" in
[`findings-log.md`](../findings-log.md) is a one-line status + a link here. A section is
never "complete", only **ledger-complete**: every snippet AND every named option marked
`✓ tested` / `⚠ diverges` / `⛔ blocked` / `⏸ deferred` / `n/a`, and **every sign-off
stamped with the date + the tina4 versions it was verified on**. See
[`readme.md`](../readme.md) → Workflow step 7.

- **Doc:** `documentation/tina4-book/book-1-python/chapters/06-orm.md` (glance + S2–S15 + QueryBuilder Integration)
- **Framework under test (READ-ONLY):** `pypy/.venv/Lib/site-packages/tina4_python/`
- **DB binding:** live PostgreSQL (`postgres:18` Docker, `tina4testingdb`) via `pypy/.env` + `pypy/conftest.py`. Most snippets are ORM-backed and raise `RuntimeError: No database bound` without it.
- **Tests:** `pypy/tests/test_ch06_*.py` (16 files) · **Live mock:** `GET /chapter/6` (served routes: `ch06_notes.py`, `ch06_blog.py`, `ch06_scopes.py`, `ch06_autocrud.py`, `blog.py`)

Legend: `✓` tested · `⚠` diverges (logged finding — its sentinel test IS the coverage) · `⛔` blocked (can't stand up here) · `⏸` deferred (USER) · `n/a` (no testable claim)

> **Latest full-suite stamp — 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51** (docs rev 7a4290b, confirmed latest). Ch06 = 16 test files; full suite 208 passed / 2 skipped / 4 xfailed (the 5 `test_issue_46_*` are the pre-existing BH-49 gap-sentinels, unrelated to Ch06). All 15 numbered sections + glance + QueryBuilder Integration exercised. PY-06-22 **FIXED in 3.13.39** (re-verified on our own probes 2026-06-22 — the two `test_ch06_cached.py` sentinels flipped and were rewritten to assert the corrected behaviour). Earlier section work (S2/S3/S4/S6/glance/S7/S8/S9/S10/S11) was first exercised 2026-06-17/18/19 on 3.13.30; S11 served on CLI 3.8.50 (port 7150). 27 findings logged (PY-06-01..27). The doc-fidelity audit (20-agent adversarial workflow, 2026-06-22) returned 0 confirmed impl-errors across all 12 audited section-units; the full 17-unit Ch06+Ch18 audit found + FIXED one impl-error (S14 `Author.name min_length=2`).

---

## Section sign-offs

### ORM at a Glance: Four Languages, One Shape
Sign-off: 2026-06-17 · tina4-python 3.13.30 · CLI 3.8.50 — FAITHFUL-with-findings
Verbatim glance `Post` model (`src/orm/post.py`) + the Python column of the "Common Query Operations" table.
- "Defining a Model" — Python `Post` field-class-instances snippet (06-orm.md:23-33) — `✓ tested` (model imported + `create_table()` in `test_ch06_glance.py::_schema`)
- PHP / Ruby / Node.js "Defining a Model" snippets (06-orm.md:37-78) — `⚠ diverges` (PY-06-03 — multi-language content in the Python book; non-Python, not implemented per single-language-docs stance)
- Common Query Operations — `Post.find_by_id(1)` — `✓ tested` (`test_ch06_glance.py::test_find_by_id`)
- Common Query Operations — `Post.find({"title": "x"})` — `✓ tested` (`::test_find_filter`)
- Common Query Operations — `Post.where("title = ?", ["x"])` — `✓ tested` (`::test_where`)
- Common Query Operations — `Post.create(title="x")` — `✓ tested` (`::test_create`)
- Common Query Operations — `post.save()` — `✓ tested` (`::test_save_instance`)
- Common Query Operations — `Post.all()` — `✓ tested` (`::test_all`)
- Common Query Operations — `post.delete()` — `✓ tested` (`::test_delete`)
- Common Query Operations — `Post.count()` — `✓ tested` (`::test_count`)
- glance `Post.body` `default=""` value (06-orm.md:31) — `⏸ deferred` (LOW — default value never asserted; see Open items)
- glance `Post` vs S6 `BlogPost` both `table_name="posts"` collision — `⚠ diverges` (PY-06-05 — module owns `posts` for its run)
- comparison table + "if you know the API in one book, you can read the others" prose — `n/a`

### S2 — Defining a Model
Sign-off: 2026-06-17 · tina4-python 3.13.30 · CLI 3.8.50 — FAITHFUL-with-findings · (aliases + auto_map coverage gaps closed 2026-06-22 · 3.13.39)
Verbatim `Note` model (`src/orm/note.py`). Field-mapping / utils examples defined inline in `test_ch06_field_mapping.py` (illustrative, no "Create src/orm/…" instruction; a standalone `user.py` collides with Ch18 `User.py` on a case-insensitive FS).
- `Note` model definition (06-orm.md:108-121) — `✓ tested` (imported + `create_table()` in `test_ch06_note_crud.py::_schema`)
- `table_name` maps to the table (06-orm.md:125) — `✓ tested` (implicit — `Note.table_name="notes"` used throughout `test_ch06_note_crud.py`)
- `table_name` omitted → lowercase class name derivation (06-orm.md:125) — `⏸ deferred` (LOW — default-derivation never exercised; see Open items)
- `primary_key=True` marks the PK (06-orm.md:127) — `✓ tested` (PK round-trips via `::test_save_insert_sets_pk`)
- `primary_key` defaults to `id` if none specified (06-orm.md:127) — `⏸ deferred` (LOW — default-to-id never exercised; see Open items)
- Field Types table — `IntegerField` / `StringField` / `BooleanField` / `DateTimeField` — `✓ tested` (all four on the `Note` model, `test_ch06_note_crud.py`)
- Field Types table — `NumericField` — `✓ tested` (S12 `Product.price`, `test_ch06_validation.py`) + `Field(float)` (S2 `Account.credit_limit`, `test_ch06_field_mapping.py::test_get_db_data`)
- Field Types table — `TextField` — `⏸ deferred` (AUD-06-1 — field type never exercised; see Open items)
- Field Types table — `BlobField` — `⏸ deferred` (AUD-06-1 — field type never exercised; see Open items)
- Field Types table — `ForeignKeyField` — `✓ tested` (S6 — `test_ch06_foreignkey.py`)
- short aliases `IntField` / `StrField` / `BoolField` "also work" (06-orm.md:142) — `✓ tested` (`test_ch06_field_mapping.py::test_short_field_aliases_resolve_to_verbose` + `::test_short_field_aliases_round_trip`)
- Field Options — `primary_key` / `required` / `default` / `max_length` / `min_length` / `min_value` / `max_value` / `choices` / `auto_increment` / `regex` — `✓ tested` (exercised via S12 validation, `test_ch06_validation.py`; `auto_increment` via every PK round-trip)
- Field Options — `validator` (callable) — `⏸ deferred` (AUD-06-2 — option never used; see Open items)
- Field Options — `max_value` upper bound / `max_length` upper bound — `⏸ deferred` (LOW — only lower bounds boundary-tested; see Open items)
- `field_mapping` translation on `save()`/`find_by_id()` (06-orm.md:165-201) — `✓ tested` (`test_ch06_field_mapping.py::test_field_mapping_roundtrip`)
- `field_mapping` translation on `select()` / `to_dict()` (06-orm.md:182) — `⏸ deferred` (AUD-06-3 — conversion via select()/to_dict() untested; see Open items)
- `_get_db_column()` (06-orm.md:207-209) — `✓ tested` (`::test_get_db_column`)
- `_get_db_data()` (06-orm.md:211-214) — `✓ tested` (`::test_get_db_data`)
- `find()` uses Python attr names / `where()` uses raw DB column names (06-orm.md:219-233) — `✓ tested` (`::test_find_uses_python_attr_names` + `::test_where_uses_db_column_names`)
- `auto_map` flag exists (no-op in Python) (06-orm.md:237) — `✓ tested` (`::test_auto_map_flag_present` — LOW: weak assert, presence only; see Open items)
- `snake_to_camel()` / `camel_to_snake()` utilities (06-orm.md:242-246) — `✓ tested` (`::test_snake_to_camel` + `::test_camel_to_snake`)
Live mock: `GET /chapter/6` (S2 block) — reachable under `tina4 serve`.

### S3 — create_table — Schema from Models
Sign-off: 2026-06-17 · tina4-python 3.13.30 · CLI 3.8.50 — FAITHFUL-with-findings
- `Note.create_table()` generates + runs CREATE TABLE from the model (06-orm.md:255) — `✓ tested` (every `test_ch06_*.py::_schema` fixture calls `create_table()` and rows persist)
- "use migrations for production" prose (06-orm.md:258) — `n/a`
- `tina4 shell` interactive `create_table()` flow (06-orm.md:260-264) — `⚠ diverges` (PY-06-16 — `tina4 shell` subcommand doesn't exist; real is `tina4 console`)
- `tina4 console` importing `src.*` for the documented flow — `⚠ diverges` (PY-06-17 — `tina4 console` can't import `src.*`: `No module named 'src'`; documented interactive flow unrunnable in the program)
- `create_table()` not re-shown after S3 (doc-completeness) — `⚠ diverges` (PY-06-02 — no `create_table` shown past S3; reader following S4+ has no table)
- DB-binding prerequisite never called out in Ch06 — `⚠ diverges` (PY-06-01 — no DB-binding callout; first ORM call raises `RuntimeError: No database bound`)

### S4 — CRUD Operations
Sign-off: 2026-06-17 · tina4-python 3.13.30 · CLI 3.8.50 — FAITHFUL-with-findings · route-handler HTTP driven under `tina4 serve`
Verbatim handlers in `src/routes/ch06_notes.py` (documented positional path-param signatures, no patch); model API in `test_ch06_note_crud.py`; handlers via the Test client in `test_ch06_routes.py`.
- `save()` — INSERT vs UPDATE, returns `self` on success (06-orm.md:272-288) — `✓ tested` (`test_ch06_note_crud.py::test_save_insert_sets_pk` asserts `is note` + `::test_save_update`)
- `create({...})` dict form (06-orm.md:294-300) — `✓ tested` (`::test_create_dict`)
- `create(title=…)` kwargs form (06-orm.md:304-306) — `✓ tested` (`::test_create_kwargs`)
- `find_by_id(id)` hit / `None` on miss (06-orm.md:310-324) — `✓ tested` (`::test_find_by_id_hit` + `::test_find_by_id_miss_returns_none`)
- `find_or_fail(id)` raises `ValueError` (06-orm.md:328-330) — `✓ tested` (`::test_find_or_fail_hit` + `::test_find_or_fail_miss_raises`)
- `find({...})` filter dict (06-orm.md:336-338) — `✓ tested` (`::test_find_filter_dict`)
- `find(..., limit=, order_by=)` pagination + ordering (06-orm.md:341) — `✓ tested` (`::test_find_pagination_and_order` — proves DESC with explicit out-of-order timestamps)
- `find()` no filter → all (06-orm.md:344) — `✓ tested` (`::test_find_no_filter_returns_all`)
- `where("category = ?", ["work"])` (06-orm.md:352) — `✓ tested` (`::test_where_basic`)
- `where(..., limit=, offset=)` pagination (06-orm.md:395) — `✓ tested` (`::test_where_pagination`)
- `all(limit=, offset=)` (06-orm.md:398) — `✓ tested` (`::test_all_pagination`)
- `select(SQL, [1], limit=, offset=)` SQL-first, verbatim (06-orm.md:401-404) — `⚠ diverges` (PY-06-08 — `[1]` bound to BOOLEAN `pinned` fails on PG: `operator does not exist: boolean = integer`; sentinel `::test_select_sql_first_verbatim_known_broken_on_pg`)
- `select(...)` with a real boolean param (method works) — `✓ tested` (`::test_select_sql_first_boolean_param_works`)
- `select_one(SQL, [...])` (06-orm.md:412) — `✓ tested` (`::test_select_one_works`)
- `select_one("… WHERE slug = ?", …)` verbatim (06-orm.md:412) — `⚠ diverges` (PY-06-04 — `slug` column not on the `Note` model; sentinel `::test_select_one_slug_verbatim_known_broken`)
- `load()` by PK (06-orm.md:421-424) — `✓ tested` (`::test_load_by_pk`)
- `load("slug = ?", …)` verbatim (06-orm.md:428) — `⚠ diverges` (PY-06-04 — no `slug` column; sentinel `::test_load_slug_verbatim_known_broken`)
- `count()` / `count("category = ?", ["work"])` (06-orm.md:436-437) — `✓ tested` (`::test_count`)
- `delete()` (06-orm.md:361-370) — `✓ tested` (`::test_delete`)
- Listing route (`where`/`all`) (06-orm.md:376-388) — `✓ tested` (Test client `test_ch06_routes.py::test_list_notes_ok` 200 + shape)
- path-param read handler (`get_note`) via Test client (06-orm.md:314-321) — `⚠ diverges` (PY-06-06 — positional `(id, request, response)` handler raises `TypeError` under the flat Test-client dispatch; sentinel `test_ch06_routes.py::test_get_note_path_param_py_06_06`)
- write route (`create_note` POST) — auth gate — `⚠ diverges` (PY-06-07 — Bearer-gated by default, 401 over `tina4 serve`, undocumented in Ch06)
- write route via Test client — 201 (client bypasses the gate) — `⚠ diverges` (PY-06-13 — serve 401 vs client 201; sentinel `::test_create_note_post_via_test_client_py_06_13`)
- S4/S6 handler snippets omit their imports — `⚠ diverges` (PY-06-09 — handler snippets omit imports)
Live mock: `GET /chapter/6` (S4 block) + served `/api/notes` (reads 200, write POST 401).

### S5 — to_dict, to_json, and Other Serialisation
Sign-off: 2026-06-17 · tina4-python 3.13.30 · CLI 3.8.50 — FAITHFUL-with-findings
- `to_dict()` → dict (06-orm.md:450-454) — `✓ tested` (`test_ch06_note_crud.py::test_to_dict`)
- `to_dict(include=["comments"])` literal (06-orm.md:460-461) — `⏸ deferred` (LOW — the S5 `note.to_dict(include=["comments"])` literal never run on `Note`; the include mechanism is covered on the blog models in S7; see Open items)
- `to_json()` → JSON string (06-orm.md:468-471) — `✓ tested` (`::test_to_json`)
- `to_assoc()` alias for `to_dict()` (06-orm.md:478) — `✓ tested` (`::test_to_assoc_and_to_object_alias_to_dict`)
- `to_object()` alias for `to_dict()` (06-orm.md:479) — `✓ tested` (`::test_to_assoc_and_to_object_alias_to_dict`)
- `to_json(include=None)` (06-orm.md:480) — `⏸ deferred` (LOW — `include=` arg on `to_json` never exercised; see Open items)
- `to_array()` → flat list of values (06-orm.md:481) — `✓ tested` (`::test_to_array_and_to_list` — LOW: shape assert is weak, `isinstance(list)` only; see Open items)
- `to_list()` alias for `to_array()` (06-orm.md:482) — `✓ tested` (`::test_to_array_and_to_list`)

### S6 — Relationships + ForeignKeyField
Sign-off: 2026-06-17 · tina4-python 3.13.30 · CLI 3.8.50 — FAITHFUL-with-findings
Verbatim `src/orm/author.py` + `src/orm/blog_post.py`; imperative relationships in `test_ch06_relationships.py`, FK auto-wiring in `test_ch06_foreignkey.py`.
- `ForeignKeyField(to=Author, related_name="posts")` auto-wires both sides (06-orm.md:499-528) — `✓ tested` (`test_ch06_foreignkey.py::test_belongs_to_accessor` + `::test_has_many_accessor`)
- ForeignKeyField DEFAULT `related_name` derivation (class-name + `s`) (06-orm.md:497) — `⏸ deferred` (AUD-06-4 — only explicit `related_name=` tested; see Open items)
- `has_many(BlogPost, "author_id")` (06-orm.md:577) — `✓ tested` (`test_ch06_relationships.py::test_has_many_returns_authors_posts` + `::test_has_many_empty`)
- `belongs_to(Author, "author_id")` (06-orm.md:620) — `✓ tested` (`::test_belongs_to_returns_parent_author`)
- `has_one(Profile, "user_id")` (06-orm.md:603) — `✓ tested` (imperative form exercised as `has_one(BlogPost, "author_id")` in `::test_has_one_returns_single_or_none`; single-or-None contract)
- `has_one` example refs undefined `Profile`/`user` (06-orm.md:603) — `⚠ diverges` (PY-06-10 — example references undefined models; verbatim snippet unrunnable as written)
- has_many route + JSON shape (06-orm.md:570-596) — `✓ tested` (handler logic in `test_ch06_relationships.py`; served via `ch06_blog.py`)
- belongs_to route + JSON shape (06-orm.md:613-642) — `✓ tested` (handler logic in `test_ch06_relationships.py`; served via `ch06_blog.py`)
Live mock: `GET /chapter/6` (S6 block) + served `/api/authors`, `/api/posts` reads.

### S7 — Eager Loading + Declarative Descriptors
Sign-off: 2026-06-17 · tina4-python 3.13.30 · CLI 3.8.50 — FAITHFUL-with-findings · comments paths unblocked once S14 `Comment` defined (2026-06-22 · 3.13.39)
Descriptors integrated onto `src/orm/author.py` (`posts`) + `blog_post.py` (`author`, `comments`). Tests: `test_ch06_eager_loading.py` (7 pass).
- imperative vs declarative styles prose (06-orm.md:488-493) — `n/a`
- `all(include=["posts"])` eager loading (06-orm.md:650-664) — `✓ tested` (`::test_eager_all_include_posts`)
- declarative `has_many("BlogPost", foreign_key="author_id")` lazy access (06-orm.md:684, 703-708) — `✓ tested` (`::test_lazy_has_many_posts`)
- declarative `belongs_to("Author", foreign_key="author_id")` lazy access (06-orm.md:695, 707-708) — `✓ tested` (`::test_lazy_belongs_to_author`)
- declarative `has_one` descriptor (06-orm.md:670) — `⏸ deferred` (AUD-06-6 — declarative `has_one` descriptor untested; only imperative `has_one` covered in S6; see Open items)
- `find_by_id(id, include=["author"])` (06-orm.md:718) — `✓ tested` (`::test_eager_find_by_id_include_author`)
- `find_by_id(id, include=["author","comments"])` (06-orm.md:718, 737-738) — `✓ tested` (`::test_include_comments_resolves_after_s14`)
- nested `include=["posts","posts.comments"]` (06-orm.md:727) — `✓ tested` (`::test_nested_posts_comments_resolves_after_s14`)
- lazy `post.comments` descriptor (06-orm.md:697) — `✓ tested` (`::test_lazy_comments_resolves_after_s14`)
- `to_dict(include=["author","comments"])` embeds related data (06-orm.md:734-753) — `✓ tested` (`::test_include_comments_resolves_after_s14`)
- S7 references a `Comment` model it never defines (first defined S14 :1150) — `⚠ diverges` (PY-06-12 — doc-ORDERING finding; a sequential S7 reader hits `ValueError: Related model 'Comment' not found`; original state preserved as isolated subprocess sentinel `::test_comments_blocked_without_comment_model_py_06_12`; stays OPEN)
- S7 eager example precedes descriptor declaration on the S6 model → silent no-op — `⚠ diverges` (PY-06-11)
- `include=` on `where()` / `select()` (06-orm.md:650) — `⏸ deferred` (AUD-06-5 — only `all()` / `find_by_id()` exercised; `where()`/`select()` include untested; see Open items)

### S8 — Soft Delete
Sign-off: 2026-06-18 · tina4-python 3.13.30 · CLI 3.8.50 — FAITHFUL-with-findings
Verbatim `Task` model (`src/orm/task.py`). Tests: `test_ch06_soft_delete.py`.
- `soft_delete = True` + `delete()` sets `is_deleted=1`, row stays, hidden (06-orm.md:762-789) — `✓ tested` (`::test_delete_is_soft`)
- `all()`/`where()`/`find_by_id()` filter out soft-deleted (06-orm.md:779) — `✓ tested` (`::test_standard_queries_exclude_deleted`)
- `restore()` → `is_deleted=0`, visible again (06-orm.md:792-798) — `✓ tested` (`::test_restore`)
- `force_delete()` permanently removes the row (06-orm.md:794) — `✓ tested` (`::test_force_delete`)
- `with_trashed()` includes soft-deleted (06-orm.md:806) — `✓ tested` (`::test_with_trashed_includes_deleted`)
- `with_trashed("completed = ?", [1])` verbatim (06-orm.md:809) — `⚠ diverges` (PY-06-14 — `[1]` on BOOLEAN `completed` fails on PG; sentinel `::test_with_trashed_filter_verbatim_known_broken_on_pg`)
- `with_trashed(filter)` with a real boolean (method works) — `✓ tested` (`::test_with_trashed_filter_works_with_boolean`)
- `count()` respects soft delete (06-orm.md:816-819) — `✓ tested` (`::test_count_respects_soft_delete`)
- `count("category = ?", ["work"])` verbatim (06-orm.md:820) — `⚠ diverges` (PY-06-15 — `category` column never defined on `Task` → UndefinedColumn; sentinel `::test_count_category_verbatim_known_broken`)
- "when to use soft delete" prose (06-orm.md:823-825) — `n/a`

### S9 — Auto-CRUD
Sign-off: 2026-06-18 · tina4-python 3.13.30 · CLI 3.8.50 — FAITHFUL-with-findings · (registration surfaces gap closed 2026-06-22 · 3.13.39)
`auto_crud=True` on `Task` (`src/orm/task.py`); `AutoCrud.register(Note, prefix="/api/v2")` (`src/routes/ch06_autocrud.py`). Tests: `test_ch06_autocrud.py` + `test_ch06_autocrud_registration.py` (isolated subprocesses — global route-table mutation).
- `auto_crud = True` registers on class load (06-orm.md:837-861, verbatim `Product` w/ `Field(float, default=0.0)`) — `✓ tested` (`test_ch06_autocrud_registration.py::test_auto_crud_flag_registers_on_load`)
- generated `GET /api/tasks` paginated list (06-orm.md:909-923) — `✓ tested` (`test_ch06_autocrud.py::AutoCrudTaskTest::test_list_paginated_shape` + `::test_list_reflects_rows`)
- generated `GET /api/tasks/{id}` (06-orm.md:878-884) — `✓ tested` (`::test_get_one_by_id`)
- generated `POST /api/tasks` create (06-orm.md:925-931) — `✓ tested` (`::test_create`)
- generated `PUT /api/tasks/{id}` update (06-orm.md:878-884) — `✓ tested` (`::test_update_by_id`)
- generated `DELETE /api/tasks/{id}` respects soft delete (06-orm.md:939) — `✓ tested` (`::test_delete_respects_soft_delete`)
- POST validation failure → 400 (06-orm.md:933-937) — `✓ tested` (`::test_create_validation_400`)
- `AutoCrud.register(Note)` DEFAULT prefix → `/api/notes` ("prefix derives from table name") (06-orm.md:865-891) — `✓ tested` (`test_ch06_autocrud_registration.py::test_register_default_prefix_derives_from_table`)
- `AutoCrud.register(Note, prefix="/api/v2")` (06-orm.md:888-890) — `✓ tested` (`test_ch06_autocrud.py::AutoCrudRegisterPrefixTest::test_v2_list_paginated` + `::test_v2_create`)
- `AutoCrud.discover("src/orm", prefix="/api")` (06-orm.md:893-901) — `✓ tested` (`test_ch06_autocrud_registration.py::test_discover_registers_src_orm_models`)
- `AutoCrud.models()` introspection (06-orm.md:949-952) — `✓ tested` (`test_ch06_autocrud.py::test_autocrud_models_introspection`)
- "custom routes take precedence over auto-CRUD" (06-orm.md:941-943) — `⚠ diverges` (PY-06-18 — FALSE via the `auto_crud=True` flag path: discovery imports `orm/` before `routes/` + first-match, so auto-CRUD shadows custom; captured under `tina4 serve`, not re-asserted as a persistent sentinel to avoid shadowing the S4/S6 custom routes)
- paginated payload key superset (06-orm.md:913-923) — `⚠ diverges` (PY-06-19 — served payload is a superset of the documented keys)
- validation-detail wording differs (06-orm.md:936) — `⚠ diverges` (PY-06-20)
Live mock: `GET /chapter/6` (S9 block) + served `/api/tasks`, `/api/v2/notes`.

### S10 — Cached Queries
Sign-off: 2026-06-18 · tina4-python 3.13.30 · CLI 3.8.50 (found) → re-verified 2026-06-22 · 3.13.39 · CLI 3.8.51 (PY-06-22 FIXED) — FAITHFUL-with-findings
Both documented calls run verbatim against live PG. S10 has no route in the chapter, so the live-program check is the ORM calls under the real DB binding. Tests: `test_ch06_cached.py`.
- `cached(SQL, [True], ttl=60, limit=20)` → `list[Note]`, honours filter/limit (06-orm.md:961-965) — `✓ tested` (`::test_cached_returns_note_list`)
- TTL cache serves STALE rows within the window for out-of-band writes — `✓ tested` (`::test_cached_serves_stale_within_ttl`)
- `clear_cache()` "clear the cache when data changes" (06-orm.md:968-971) — `⚠ diverges → FIXED` (**PY-06-22** — on 3.13.30 `clear_cache()` cleared only the module-level ORM cache, not the DB-layer `Database.fetch()` cache `cached()` reads; **FIXED in 3.13.39**, re-verified on our own probes; sentinels `::test_clear_cache_refreshes_cached` + `::test_clear_cache_rehits_db` flipped and now assert the corrected behaviour)
- ORM `.save()` auto-invalidates the query cache (undocumented) — `⚠ diverges` (PY-06-21 — undocumented; sentinel `::test_orm_save_auto_invalidates_cache`, still observed on 3.13.39)

### S11 — Scopes
Sign-off: 2026-06-19 · tina4-python 3.13.30 · CLI 3.8.50 — FAITHFUL-with-findings · served (port 7150) + pytest
S11 redefines `BlogPost` (`table_name="posts"`) with a different schema than S6 (PY-06-05 collision) → reproduced inline in `test_ch06_scopes.py`. Routes verbatim in `src/routes/ch06_scopes.py`.
- classmethod `published()` scope (06-orm.md:989-991) — `✓ tested` (`::test_published_scope`; served `GET /api/posts/published` 200, 2 posts)
- classmethod `drafts()` scope (06-orm.md:993-995) — `✓ tested` (`::test_drafts_scope`)
- classmethod `recent(days=7)` scope (06-orm.md:997-1002) — `⚠ diverges` (PY-06-23 — uses SQLite `datetime('now', ?)` → `UndefinedFunction` on PG; served `GET /api/posts/recent?days=7` 500; sentinel `::test_recent_scope_breaks_on_postgres`)
- scope route payloads (06-orm.md:1008-1017) — `✓ tested` (`::test_published_route_payload`)
- dynamic `scope("active", "status != ?", ["archived"])` → `active()` (06-orm.md:1022-1026) — `✓ tested` (`::test_dynamic_scope_active`)
Live mock: `GET /chapter/6` (S11 block) + served `/api/posts/published`.

### S12 — Input Validation
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings · pytest + served (port 7150)
Verbatim `Product` model. S12 `Product` reuses `table_name="products"` (PY-06-05 family) → save path runs against an isolated `products_s12_save` table. Tests: `test_ch06_validation.py` (6).
- `validate()` returns a list, one entry per failed constraint (06-orm.md:1035, 1067) — `✓ tested` (`::test_validate_returns_list_of_errors`)
- "checks every constraint" — catches `required`/`min_length`/`regex`/`min_value`/`choices` (06-orm.md:1035) — `✓ tested` (`::test_validate_catches_every_constraint` + `::test_validate_flags_missing_required_fields`)
- `validate()` → `[]` on valid input (06-orm.md:1067) — `✓ tested` (`::test_validate_passes_on_valid_input`)
- valid model persists via `save()` (06-orm.md:1063) — `✓ tested` (`::test_valid_product_saves`, isolated table)
- `min_length`/`max_length` on `name` boundary (06-orm.md:1044) — `⏸ deferred` (LOW — `min_length` lower bound tested via message sentinel; `max_length(name)` upper bound never boundary-tested; see Open items)
- `min_value`/`max_value` on `price` boundary (06-orm.md:1046) — `⏸ deferred` (LOW — `min_value` lower bound tested; `max_value(price)` upper bound never boundary-tested; see Open items)
- per-field error-message WORDING vs the doc's JSON example (06-orm.md:1070-1077) — `⚠ diverges` (PY-06-24 — behaviour faithful, wording differs; sentinel `::test_validate_message_format_py_06_24` asserts the ACTUAL format AND that the doc-claimed strings are absent)

### S13/S14 — Exercise: Build a Blog + Solution
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL (one impl-error found + FIXED) · pytest + served
Verbatim `src/orm/author.py` + `src/orm/blog_post.py` + new `src/orm/comment.py`; routes `src/routes/blog.py`. Handler-logic style (collision-immune — `get_author`/`get_post` share paths with `ch06_blog.py`, last-loaded wins, router.py:358). Tests: `test_ch06_blog_exercise.py` (12).
- `Author` model (id/name required/email required/bio/created_at) (06-orm.md:1113-1124) — `✓ tested` (`::test_create_author_valid` + `::test_create_author_invalid_returns_errors`)
- S14 `Author.name = StringField(required=True, min_length=2)` (06-orm.md:1120) — `✓ tested` (`::test_create_author_name_min_length`) — **impl-error FIXED 2026-06-22**: `src/orm/author.py` had carried only `required=True`; aligned to the S14 definition + boundary test added
- `BlogPost` model incl. `title max_length=300` + status choices (06-orm.md:1131-1146) — `✓ tested` (model round-trips; `::test_create_post_valid` + `::test_create_post_invalid_status_choice`)
- `BlogPost.title max_length=300` boundary (06-orm.md:1136) — `⏸ deferred` (LOW — `max_length=300` never boundary-tested; see Open items)
- `Comment` model (post_id/author_name/author_email/body min 5) (06-orm.md:1150-1162) — `✓ tested` (`::test_add_comment_valid` + `::test_add_comment_body_too_short`)
- `POST /api/authors` create_author + validation 400 (06-orm.md:1173-1185) — `✓ tested` (`::test_create_author_valid` / `::test_create_author_invalid_returns_errors`)
- `GET /api/authors/{id:int}` get_author with posts + 404 (06-orm.md:1188-1200) — `✓ tested` (`::test_get_author_with_posts` + `::test_get_author_not_found`)
- `POST /api/posts` create_post (verifies author, 404) (06-orm.md:1203-1224) — `✓ tested` (`::test_create_post_valid` + `::test_create_post_missing_author_is_404`)
- `GET /api/posts` list_posts (published + author) (06-orm.md:1227-1238) — `✓ tested` (`::test_list_posts_published_only_with_author`; served `GET /api/posts` 200)
- `GET /api/posts/{id:int}` get_post (author + comments + count) + 404 (06-orm.md:1241-1256) — `✓ tested` (`::test_get_post_with_author_and_comments` + `::test_get_post_not_found`)
- `POST /api/posts/{id:int}/comments` add_comment + validation (06-orm.md:1259-1277) — `✓ tested` (`::test_add_comment_valid` + `::test_add_comment_body_too_short`)
- S13/S14 POST routes Bearer-gated over serve — `⚠ diverges` (PY-06-07 — write routes 401 without a token)
- `GET /api/posts/{id}` shadowed by the S6 `ch06_blog.py` handler (last-loaded wins) — workspace artifact, not a doc divergence (serve boots clean, router.py:358)

### S15 — Gotchas (all 10)
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings
All ten gotcha behaviour claims checked against live PG. Tests: `test_ch06_gotchas.py` (11).
- Gotcha 1 — `save()` returns `self` / `False` (06-orm.md:1290) — `✓ tested` (`::test_g1_save_returns_self_on_success`)
- Gotcha 2 — `find_by_id()` `None` on miss + excludes soft-deleted (06-orm.md:1296) — `✓ tested` (`::test_g2_find_by_id_none_on_miss` + `::test_g2_find_by_id_excludes_soft_deleted`)
- Gotcha 3 — `find(42)` bare PK "unexpected" (06-orm.md:1300-1306) — `⚠ diverges` (PY-06-27 — INACCURATE: `find(bare_pk)` returns the single record, `find(dict)` returns a list; sentinel `::test_g3_find_bare_pk_actually_returns_record_py_06_27`)
- Gotcha 4 — circular top-level import → ImportError (06-orm.md:1308-1314) — `✓ tested` (`::test_g4_circular_top_level_import_fails`; framework's string-name descriptors sidestep it)
- Gotcha 5 — `to_dict()` includes all fields incl. sensitive (06-orm.md:1316-1322) — `✓ tested` (`::test_g5_to_dict_includes_all_fields`)
- Gotcha 6 — "`save()` does not validate" (06-orm.md:1324-1330) — `⚠ diverges` (PY-06-25 — FALSE: `save()` DOES validate + refuses invalid data, returns `False`, nothing persisted; sentinel `::test_g6_save_actually_validates_py_06_25`)
- Gotcha 7 — FK not enforced = "SQLite default" (06-orm.md:1332-1338) — `⚠ diverges` (PY-06-26 — MISLEADING: `ForeignKeyField` emits 0 FK constraints on PG too — engine-agnostic; sentinel `::test_g7_foreign_key_not_enforced_engine_agnostic_py_06_26`)
- Gotcha 8 — N+1 fix snippet (`select IN` + manual grouping) (06-orm.md:1340-1356) — `✓ tested` (`::test_g8_n_plus_1_fix_snippet_runs`)
- Gotcha 9 — auto-CRUD vs custom precedence (06-orm.md:1358-1364) — `⚠ diverges` (PY-06-18 — custom routes do NOT take precedence; auto-CRUD shadows; Gotcha 9 is also internally contradictory: Cause "first registered wins" vs Fix "custom take precedence")
- Gotcha 10 — soft delete requires flag + `is_deleted` field (06-orm.md:1366-1372) — `✓ tested` (`::test_g10_soft_delete_active_with_flag_and_field` + `::test_g10_without_flag_delete_is_hard`)

### QueryBuilder Integration
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL
Trailing section; the full builder (joins/grouping/having/Mongo) is deferred to Ch07. Tests: `test_ch06_querybuilder.py` (5).
- `Model.query()` returns a `QueryBuilder` (06-orm.md:1376-1380) — `✓ tested` (`::test_query_returns_querybuilder`)
- `.select().where().order_by().limit().get()` fluent chain (06-orm.md:1382-1387) — `✓ tested` (`::test_get_fluent_chain`)
- `.where().first()` (06-orm.md:1390-1392) — `✓ tested` (`::test_first_returns_match`)
- `.where().count()` (06-orm.md:1395-1397) — `✓ tested` (`::test_count`)
- `.where().exists()` (06-orm.md:1400-1402) — `✓ tested` (`::test_exists`)
- Note (no doc claim broken): `get()`/`first()` return `DatabaseResult`/`dict` rows, not ORM instances — return types are Ch07's scope. — `n/a`

---

## Open items

### Audit coverage gaps (tracked here; not yet exercised)
- **AUD-06-1** — `TextField` + `BlobField` field types (06-orm.md:138-139) never exercised. Missing-coverage. Add a model declaring both + round-trip TEXT/BLOB values.
- **AUD-06-2** — `validator=` callable field option (06-orm.md:159) never used. Untested-option. Add a field with a custom `validator` callable + assert it runs in `validate()`.
- **AUD-06-3** — `field_mapping` conversion via `select()` / `to_dict()` (06-orm.md:182 claims both directions) untested. Only `save()`/`find_by_id()` translation covered (`test_ch06_field_mapping.py`). Add a `select()`-through + `to_dict()` mapping assertion.
- **AUD-06-4** — `ForeignKeyField` DEFAULT `related_name` derivation (06-orm.md:497 — class-name lowercased + `s`) untested; only explicit `related_name="posts"` covered. Add an FK with no `related_name` + assert the derived accessor.
- **AUD-06-5** — `include=` on `where()` / `select()` (06-orm.md:650 lists all four) untested; only `all()` + `find_by_id()` exercised. Add eager-load assertions through `where()` and `select()`.
- **AUD-06-6** — declarative `has_one` descriptor (06-orm.md:670) untested; only imperative `has_one` (S6) covered. Add a class-attribute `has_one(...)` descriptor + lazy access.

### LOW / weak-assertion items
- `table_name` default-derivation (omitted → lowercase class name, 06-orm.md:125) never exercised.
- `primary_key` default-to-`id` (06-orm.md:127) never exercised.
- `max_value` / `max_length` UPPER bound (06-orm.md:152-153) never boundary-tested — only lower bounds asserted (S12/S14).
- `auto_map` no-op (06-orm.md:237) — weak assert: `test_ch06_field_mapping.py::test_auto_map_flag_present` checks presence only, not the no-op behaviour.
- `to_json(include=)` (06-orm.md:480) `include=` arg never exercised.
- `to_array()` / `to_list()` "flat list of values" shape (06-orm.md:481-482) — weak assert: `::test_to_array_and_to_list` checks `isinstance(list)` + alias-equality only, not the flat-values shape.
- S5 `note.to_dict(include=["comments"])` literal (06-orm.md:460-461) never run on `Note` (include mechanism covered on the blog models in S7 instead).
- glance `Post.body` `default=""` (06-orm.md:31) — default value never asserted.
- S12 `max_length(name)` (06-orm.md:1044) / `max_value(price)` (06-orm.md:1046) never boundary-tested.
- S14 `BlogPost.title max_length=300` (06-orm.md:1136) never boundary-tested.

### Doc-fidelity findings still OPEN (not fixed upstream)
- PY-06-01, 02, 04, 06, 07, 08, 09, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 23, 24, 25, 26, 27 — each with a sentinel test above (its sentinel IS the coverage). PY-06-05 is a workspace-collision family managed per-module (each collision-prone module owns `posts`/`products` for its run).
- Filing status (mine from findings-log): filed on tina4-book#142 — PY-06-01..05, 08, 13, 18, 22 (9). Unfiled batch — PY-06-06, 07, 09, 10, 11, 12, 14, 15, 16, 17, 19, 20, 21 (13) + the later PY-06-23..27.

## Resolved items
- **PY-06-22** (`clear_cache()` two-cache-layer defect) — FIXED in tina4-python **3.13.39**, re-verified on our own probes 2026-06-22 · CLI 3.8.51. The two `test_ch06_cached.py` sentinels (`::test_clear_cache_refreshes_cached`, `::test_clear_cache_rehits_db`) flipped red→green and were rewritten to assert the corrected behaviour (after out-of-band insert + `clear_cache()`, `cached()` reflects the new row; after `clear_cache()` + DROP TABLE, `cached()` re-hits the DB → `UndefinedTable`).
- **S14 `Author.name min_length=2` impl-error** — FIXED 2026-06-22 · 3.13.39. `src/orm/author.py` aligned to the S14 definition (06-orm.md:1120); boundary test `test_ch06_blog_exercise.py::test_create_author_name_min_length` added.
- **Coverage gaps CLOSED 2026-06-22 · 3.13.39** — (1) S2 short field aliases `IntField`/`StrField`/`BoolField` (`test_ch06_field_mapping.py`); (2) S9 registration surfaces — `auto_crud=True` on-load via verbatim `Product`, `AutoCrud.register(Note)` default prefix, `AutoCrud.discover('src/orm', prefix='/api')` (`test_ch06_autocrud_registration.py`). All work as documented.

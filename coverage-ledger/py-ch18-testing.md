There is no /chapter/18 live mock (only 7 and 12 are registered in explorer). So the chapter 18 tests are the coverage; no live mock exists for ch18. I have enough to build the ledger faithfully. The latest version stamp from history is 3.13.39 / CLI 3.8.51, but the prompt says use latest e.g. 3.13.47 / CLI 3.8.53. The history's actual stamp is 3.13.39 (re-verified 2026-06-22). I'll be faithful to the history: the section sign-offs stamp 3.13.39 / CLI 3.8.51 (that's what the history shows), noting the audit at 2026-06-22.

Now I'll write the ledger.

# Coverage Ledger — Python · Chapter 18: Testing

Per-section proof-of-coverage for the chapter evaluation. A section is never "complete" —
only **ledger-complete**: every snippet AND every named option marked `✓ tested` /
`⚠ diverges` / `⛔ blocked` / `⏸ deferred` / `n/a`, and **every sign-off stamped with the
date + the tina4 versions it was verified on**. See [`documentation-testing/readme.md`](../documentation-testing/readme.md) → Workflow
step 7.

**This file is the canonical coverage home for Chapter 18.** The `18 — Testing` row in the
Evaluation Progress table of [`findings-log.md`](../findings-log.md) is a one-line status +
a link here; the long run-on narrative that used to live in that cell has been migrated into
the section sign-offs below.

- **Doc:** `documentation/tina4-book/book-1-python/chapters/18-testing.md` (13 sections)
- **Framework under test (READ-ONLY):** `documentation-testing/pypy/.venv/Lib/site-packages/tina4_python/`
- **Tests:** `documentation-testing/pypy/tests/test_ch18_*.py` + `documentation-testing/pypy/tests/test_user_model.py`
- **Supporting routes (not in the chapter — added so verbatim tests can hit real handlers):** `src/routes/ch18_products.py`, `src/routes/ch18_auth.py`
- **Live mock:** none for Ch18 — the chapter explorer registers only Ch7 + Ch12 (`src/routes/chapter_explorer.py`); a `GET /chapter/18` page does **not** exist. The `test_ch18_*` suite under `tina4 test` IS the coverage surface.

Legend: `✓` tested · `⚠` diverges (logged finding — its sentinel test IS the coverage) · `⛔` blocked (can't stand up here) · `⏸` deferred (USER) · `n/a` (no testable claim)

> **Version basis.** Latest full re-verification: **2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51** — all persisted Ch18 tests green; doc-fidelity audit that day found ZERO confirmed impl-errors across S2–S7/S10 (verdict faithful / faithful-with-known-findings). PY-18-04, PY-18-07a, PY-18-08, PY-18-10 confirmed **fixed** (docs realigned in 3.13.4). Findings first logged on earlier stamps (3.13.2 / 3.13.30) carry their found-version inline; a probe tracks each fix. No blanket re-verify was run on the 3.13.47/.48 bumps.

---

## Section sign-offs

### S1 — Why Tests Matter More Than You Think
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL (concept prose)
- narrative + the `tina4 test` session-transcript illustration — `n/a` (prose; the transcript is illustrative, not a runnable claim)
- "Tina4 ships a `Test` class layered on top of pytest … `assert_equal`/`assert_true`/`assert_not_none` helpers" — `✓ tested` (exercised throughout S2/S3; import surface `from tina4_python.test import Test, assert_*`)

### S2 — Your First Test
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings
- `class BasicTest(Test)` + three `test_*` methods (`test_addition`, `test_string_contains`, `test_array_length`) run verbatim — `✓ tested` (`test_ch18_basic.py::BasicTest::test_addition`, `::test_string_contains`, `::test_array_length`)
- "Every `.py` file in `tests/` is auto-discovered by `tina4 test`" — `⚠ diverges` (**PY-18-04**, fixed) `tina4 test` wraps pytest whose default discovery needs the `test_*` filename prefix; the chapter's `test_basic.py` name is fine but the general auto-discovery-of-every-`.py` claim is why our files carry the `test_ch18_` prefix. Sentinel: file is named `test_ch18_basic.py` per the header note.
- "How It Works" step 2 — `test_addition` name "is converted to a readable label: `test_addition` stays as `test_addition`" — `⚠ diverges` (**PY-18-04**) the name→readable-label claim is unverified/vacuous as written (label == method name); subsumed by PY-18-04. LOW.

### S3 — Assertion Methods
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings
- `assert_equal(actual, expected, message)` PASS examples — `✓ tested` (`test_ch18_assertions.py::AssertEqualTest::test_equal_numbers`, `::test_equal_strings`)
- `assert_true(...)` PASS examples — `✓ tested` (`::AssertTrueTest::test_true_literal`, `::test_truthy_one`, `::test_truthy_string`)
- `assert_false(...)` PASS examples — `✓ tested` (`::AssertFalseTest::test_false_literal`, `::test_false_zero`, `::test_false_empty_string`)
- `assert_raises(callable, exception_class, message)` — `✓ tested` (`::AssertRaisesTest::test_raises_value_error`, `::test_raises_zero_division`)
- `assert_not_equal(...)` PASS example — `✓ tested` (`::AssertNotEqualTest::test_not_equal_strings`)
- `assert_none(...)` PASS example — `✓ tested` (`::AssertNoneTest::test_none_value`)
- `assert_not_none(...)` PASS example — `✓ tested` (`::AssertNotNoneTest::test_not_none_value`)
- documented 3-arg signatures `assert_true/false/none/not_none(actual, expected, message)` — `⚠ diverges` (**PY-18-01**) every chapter example (and the real runtime, a sentinel-default overload) uses the 2-arg form `assert_true(value, message)`; the 3-arg signature in the headings is inconsistent with the docs' own examples and the runtime. Sentinel: the 2-arg usage across `test_ch18_assertions.py`.
- FAIL examples (`assert_equal(4,5,…)`, `assert_true(False,…)`, `assert_true(0,…)`, etc.) — `n/a` (documented as expected-FAIL illustrations; running them to green would be test-rigging, and the negative path is covered by `assert_raises` semantics)

### S4 — Testing ORM Models (Product)
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings · DB-backed (SQLite `data/test.db`; `Product.create_table()` at module load)
- `test_create_product` — save → `id` not None and > 0 — `✓ tested` (`test_ch18_product.py::ProductTest::test_create_product`)
- `test_load_product` — `Product.find(id)` round-trips name/category/price — `✓ tested` (`::test_load_product`)
- `test_update_product` — mutate + re-save + reload — `✓ tested` (`::test_update_product`)
- `test_delete_product` — delete → `find()` is None — `✓ tested` (`::test_delete_product`)
- `test_select_with_filter` — `Product.where("category = ?", ["FilterCat"])` — `⚠ diverges` (**PY-18-07c**) chapter unpacks a 2-tuple `products, count = where(...)`, but `where()` returns a flat list by default; the tuple needs the never-documented `with_count=True`. Sentinel: `::test_select_with_filter` (PATCH adds `with_count=True`; remove it to reproduce `ValueError: too many values to unpack`).
- verbatim import `from src.orm.Product import Product` present in S4 — `✓ tested` (**PY-18-07a**, fixed in 3.13.4 — the import line now ships in the chapter; `test_ch18_product.py` uses it verbatim)
- "Test Database" subsection — `tina4 test` auto-binds a separate `data/test.db`, reset before each run — `⚠ diverges` (**PY-18-07b**) empirically false on two counts: (1) `tina4 test` does not load `.env`, so module-load `create_table()` hits "No database bound" even with `TINA4_DATABASE_URL` set; (2) with the env var set to a dev DB, the framework writes straight to it — no auto-swap to `test.db`. Sentinel: the PATCH block at the top of `test_ch18_product.py` (and `test_ch18_setup_teardown.py`).
- `TINA4_DATABASE_URL=sqlite:///data/test.db` `.env` snippet — `✓ tested` (set via the PY-18-07b PATCH; binds the suite)

### S5 — Testing Routes (+ Response Object + Test Client Methods)
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings · `/api/products` handlers supplied by `src/routes/ch18_products.py` (chapter never defines them — PY-18-11)
- `test_health_endpoint` — `GET /health` → 200, `body["status"]=="ok"`, `version` present — `✓ tested` (`test_ch18_routes.py::RouteTest::test_health_endpoint`) — holds **only on a clean error slate** (see PY-18-14 below)
- `test_get_products` — `GET /api/products` → 200, body has `data`/`products` — `✓ tested` (`::test_get_products`)
- `test_create_product` — `POST /api/products` json body → 201, echoes name/price — `✓ tested` (`::test_create_product`)
- `test_get_product_not_found` — `GET /api/products/99999` → 404 — `✓ tested` (`::test_get_product_not_found`)
- `test_create_product_validation` — `POST /api/products` `{}` → 400 — `✓ tested` (`::test_create_product_validation`)
- `test_delete_product` — create → `DELETE` → 204 → `GET` → 404 — `✓ tested` (`::test_delete_product`)
- "Tina4 provides a test client … without starting a server" + the `/api/products` etc. routes assumed to exist — `⚠ diverges` (**PY-18-11**) the chapter never shows how to define `/api/products`, `/api/auth/login`, `/api/profile`; only `/health` ships in a fresh `tina4 init python .` scaffold. Handlers added under `ch18_products.py` / `ch18_auth.py` so the verbatim tests can run.
- **Test Client Methods** — `self.get(path)` — `✓ tested` (`test_ch18_client_methods.py::ClientMethodsTest::test_get_request`)
- **Test Client Methods** — `self.get("…?category=Electronics&page=2")` (query params) — `⚠ diverges` (call-only, no assertion) `::test_get_with_query_parameters` (**AUD low**: exercises the call verbatim but asserts nothing about query-param handling)
- **Test Client Methods** — `self.post(path, json=…)` — `✓ tested` (`::test_post_with_json_body`)
- **Test Client Methods** — `self.put(path, json=…)` — `✓ tested` (`::test_put_with_json_body`)
- **Test Client Methods** — `self.patch(path, json=…)` — `✓ tested` (`::test_patch_with_json_body`)
- **Test Client Methods** — `self.delete(path)` — `✓ tested` (`::test_delete`)
- **Test Client Methods** — `self.get(path, headers={"Authorization": …})` — `✓ tested` (`::test_get_with_custom_headers`)
- keyword `json=` body form for post/put/patch — `✓ tested` (**PY-18-08a**, fixed in 3.13.4 — chapter no longer shows positional body; all client-method tests use `json=`)
- **Response Object** — `resp.status` (int) — `✓ tested` (used across every route test; **PY-18-10** doc regression, fixed in 3.13.4 — docs realigned to `.status`, not `.status_code`)
- **Response Object** — `resp.body` (raw bytes) — `✓ tested` (`json.loads(resp.body)` throughout; PY-18-10 — body documented as bytes now)
- **Response Object** — `resp.headers` (lowercased dict) — `⚠ diverges` (**AUD-18-2**, untested option) exercised **only** in the module-SKIPPED probe `test_ch18_response_object_probe.py` (dormant `pytest.skip(allow_module_level=True)`); no live assertion in the suite
- **Response Object** — `resp.content_type` — `⚠ diverges` (**AUD-18-2**) same dormant-probe-only status as `resp.headers`
- **Response Object** — `resp.text()` — `⚠ diverges` (**AUD-18-3**) covered only by `test_ch18_response_object_probe.py::ResponseObjectProbe::test_undocumented_text_helper_exists` (module-skipped/dormant)
- **Response Object** — `resp.json()` — `⚠ diverges` (**AUD-18-3**) same dormant-probe-only status; `::test_undocumented_json_helper_exists`

### S5 — `/health` contract (error-aware behaviour)
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings
- `/health` returns 200 + `{"status":"ok", "version":…}` — `⚠ diverges` (**PY-18-14**, found on 3.13.39) `/health` is error-aware: HTTP **503** + `status:"error"` when any unresolved error is recorded, file-backed in `data/.broken/` and persistent across restarts. The S5 health test's 200/"ok" holds **only on a clean error slate** (the version-bump 503 was stale recorded errors, not a regression). Sentinel: `test_ch18_health_probe.py::HealthContractTest::test_health_error_aware_contract` (asserts the ok↔200 / error↔503 mapping in both directions).

### S6 — Testing Authentication
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings · `/api/auth/login` + `/api/profile` handlers supplied by `src/routes/ch18_auth.py` (PY-18-11)
- `test_login_with_valid_credentials` — 200, `token` present, len > 50 — `✓ tested` (`test_ch18_auth.py::AuthTest::test_login_with_valid_credentials`)
- `test_login_with_invalid_password` — 401 — `✓ tested` (`::test_login_with_invalid_password`)
- `test_login_with_missing_fields` — status in (400, 401) — `✓ tested` (`::test_login_with_missing_fields`)
- `test_protected_route_without_token` — `GET /api/profile` → 401 — `✓ tested` (`::test_protected_route_without_token`)
- `test_protected_route_with_valid_token` — login → Bearer token → 200 + user email — `✓ tested` (`::test_protected_route_with_valid_token`)
- `test_protected_route_with_invalid_token` — bad Bearer → 401 — `✓ tested` (`::test_protected_route_with_invalid_token`)
- routes `/api/auth/login` + `/api/profile` assumed but undefined in chapter — `⚠ diverges` (**PY-18-11**, see S5)

### S7 — Setup and Teardown
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings · DB-backed (`User.create_table()` at module load)
- `set_up()` creates a user before each test; `self.user_id` visible in tests — `✓ tested` (`test_ch18_setup_teardown.py::UserTest::test_user_exists`)
- `tear_down()` deletes the user after each test — `✓ tested` (exercised implicitly by the two tests running isolated; `::test_user_exists` + `::test_update_user`)
- `test_update_user` — reload after save reflects the change — `✓ tested` (`::test_update_user`)
- "`set_up()`/`tear_down()` run before/after every method regardless of pass/fail" — `✓ tested` (covered by the two-test class each starting from a fresh `set_up`)
- chapter never imports `User` in the S7 snippet — `⚠ diverges` (**PY-18-12**) same defect class as PY-18-07a (S4 Product) pre-3.13.4; the parallel S7 import fix is missing → `NameError` on first use. Sentinel: PATCH `from src.orm.User import User` at top of `test_ch18_setup_teardown.py`.
- S7 snippet relies on the auto-test-DB claim — `⚠ diverges` (**PY-18-07b**, see S4) PATCH sets `TINA4_DATABASE_URL` + `create_table()` explicitly.

### S8 — Running Tests (CLI flags)
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings (documented-but-broken)
- `tina4 test` (run all) — `✓ tested` (the whole suite runs under it; PY-18-04 fixed)
- `tina4 test --file tests/test_product.py` — `⚠ diverges` (**PY-18-03**, re-verified open across S8) the `--file` flag is documented-but-broken. **Do-not-retest** (logged).
- `tina4 test --file … --method test_create_product` — `⚠ diverges` (**PY-18-03**) `--method` flag documented-but-broken. Do-not-retest.
- `tina4 test --verbose` — `⚠ diverges` (**PY-18-03**) `--verbose` flag documented-but-broken. Do-not-retest.
- "Failed Test Output" pytest FAILURES transcript — `n/a` (illustrative pytest formatting, not a runnable claim)

### S9 — pytest Integration + Code Coverage
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings (documented-but-broken)
- `uv add --dev pytest` + `pyproject.toml [tool.pytest.ini_options]` (`testpaths`/`python_files`/`python_classes`/`python_functions`) — `✓ tested` (the suite runs under both `tina4 test` and `python -m pytest`; the `*Test` class + `test_*` conventions are what the whole `test_ch18_*` set relies on)
- "your test files work with both `tina4 test` and `pytest` without modification" — `✓ tested` (verified running the same files both ways)
- `uv add --dev pytest-cov` + `tina4 test --cov=src --cov-report=term` — `⚠ diverges` (**PY-18-03**, re-verified open across S9) the `--cov*` flags passed through `tina4 test` are documented-but-broken. Do-not-retest.
- `tina4 test --cov=src --cov-report=html` (`htmlcov/index.html`) — `⚠ diverges` (**PY-18-03**) same broken CLI-flag passthrough. Do-not-retest.
- coverage-report transcript — `n/a` (illustrative output)

### S10 — Testing Best Practices
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL (S10 clean)
- "Test One Thing Per Test" — `test_create_product_returns_201` — `✓ tested` (`test_ch18_best_practices.py::BestPracticesTest::test_create_product_returns_201`)
- "Test One Thing Per Test" — `test_create_product_returns_created_product` — `✓ tested` (`::test_create_product_returns_created_product`)
- `test_everything` anti-pattern (`# Avoid:`) — `n/a` (labelled anti-example; intentionally not implemented)
- "Use Descriptive Assertion Messages" (Good/Bad) — `n/a` (text-only guidance, no runnable claim)
- "Isolate Tests" — Good pattern: create own data, delete, assert gone — `✓ tested` (`::test_delete_product`)
- "Isolate Tests" — Bad pattern (`Product.find(1)` dependency) — `n/a` (labelled anti-example)

### S11/S12 — Exercise + Solution: User Model
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — FAITHFUL-with-findings · 5/5 pass after 4 PATCH blocks · DB-backed
- `test_create_user` — save → id + fields correct — `✓ tested` (`test_user_model.py::UserModelTest::test_create_user`)
- `test_duplicate_email` — second same-email save rejected — `⚠ diverges` (**PY-18-13c** + **PY-18-13e**) no `unique=True`/`StringField` uniqueness kwarg exists and the chapter shows no migration → a manual `CREATE UNIQUE INDEX` is required (13c); and `ORM.save()` swallows the `IntegrityError` and returns `False` instead of raising, so the chapter's `assert_raises(..., Exception, ...)` can never fire (13e). Sentinel: `::test_duplicate_email` asserts `save() is False`.
- `test_update_user` — update + reload — `✓ tested` (`::test_update_user`)
- `test_delete_user` — delete → `find()` None — `✓ tested` (`::test_delete_user`)
- `test_select_users` — create 3, `User.where("1=1")`, count ≥ 3 — `⚠ diverges` (**PY-18-13d**) chapter unpacks `users, count = where("1=1")` but `where()` returns a flat list by default; needs `with_count=True` (undocumented) → `ValueError: too many values to unpack` as written. Sentinel: `::test_select_users` (PATCH adds `with_count=True`).
- chapter S12 never imports `User` — `⚠ diverges` (**PY-18-13a**, same class as PY-18-12) `NameError` on first use; PATCH `from src.orm.User import User`.
- S12 relies on auto-test-DB claim — `⚠ diverges` (**PY-18-07b**, see S4) PATCH sets env + `create_table()`.

### S11/S12 — Exercise + Solution: Auth Flow
Sign-off: **IN-PROGRESS** (not implemented) — see Open item **AUD-18-1**
- `test_register_new_user` — `POST /api/auth/register` → 201 — `⏸ deferred` (**AUD-18-1**, HIGH) test file absent; no `/api/auth/register` route exists (`ch18_auth.py` defines only login + profile)
- `test_register_duplicate_email` — second register → 409 — `⏸ deferred` (**AUD-18-1**)
- `test_login_success` — register → login → token — `⏸ deferred` (**AUD-18-1**)
- `test_login_failure` — wrong password → 401 — `⏸ deferred` (**AUD-18-1**)
- `test_access_protected_route` — token → `/api/profile` 200 + user data — `⏸ deferred` (**AUD-18-1**) — note the login/profile half is separately exercised in S6 (`test_ch18_auth.py`), but the register→login→profile flow the exercise mandates is not
- `test_access_with_expired_token` — crafted expired token → 401 — `⏸ deferred` (**AUD-18-1**)

### S13 — Gotchas
Sign-off: 2026-06-22 · tina4-python 3.13.39 · CLI 3.8.51 — n/a (guidance prose; no verbatim test artifact)
- Gotcha 1 Tests Run in Order — `n/a` (guidance; isolation is exercised behaviourally by S7 `set_up`/`tear_down` + S10 isolate tests)
- Gotcha 2 Test DB vs Dev DB — `n/a` (guidance; the underlying auto-test-DB claim it leans on is **PY-18-07b**, tracked in S4)
- Gotcha 3 Unique Constraint Failures (`uuid.uuid4().hex[:8]`) — `n/a` (guidance; the uuid technique is used verbatim in `test_user_model.py`)
- Gotcha 4 Test Method Not Discovered (`test`-prefix, case-sensitive) — `n/a` (guidance; corroborated by PY-18-04 discovery behaviour)
- Gotcha 5 Assertion Arguments Reversed (`assert_equal(actual, expected)`) — `n/a` (guidance; argument order used throughout the suite)
- Gotcha 6 Cannot Test Routes Requiring Auth Setup (`set_up()` + `create_table()` + `hash_password`) — `n/a` (guidance; the `create_table()` need is what PY-18-07b/PY-18-12 already document)
- Gotcha 7 Pass Locally, Fail in CI — `n/a` (environment guidance, no framework claim)

---

## Open items

- **AUD-18-1 (HIGH) — `tests/test_auth_flow.py` ENTIRELY MISSING.** S11/S12 mandates a 6-test auth-flow suite (register → 201, duplicate → 409, login → token, login fail → 401, protected route → 200, expired token → 401). Only `test_user_model.py` exists. Blocked in two ways: (1) no `test_auth_flow.py` file; (2) no `/api/auth/register` route — `src/routes/ch18_auth.py` defines only `POST /api/auth/login` and `GET /api/profile`. To close: add the register handler + the 6-test file. Login/profile mechanics are partially proven by the S6 `test_ch18_auth.py` suite, but the register→409-duplicate and expired-token paths are wholly untested.
- **AUD-18-2 — `resp.headers` / `resp.content_type` only in a dormant probe.** Both Response-Object properties are exercised solely inside `test_ch18_response_object_probe.py`, which is module-skipped (`pytest.skip(..., allow_module_level=True)`). No live assertion in the running suite. Untested-option; enable the probe (or add live asserts) to close.
- **AUD-18-3 — `resp.text()` / `resp.json()` same dormant-probe-only status.** Covered only by the skipped `test_ch18_response_object_probe.py` (`test_undocumented_text_helper_exists`, `test_undocumented_json_helper_exists`). Untested-option.
- **LOW — S5 GET-with-query-params is call-only.** `test_ch18_client_methods.py::test_get_with_query_parameters` issues the verbatim `self.get("…?category=Electronics&page=2")` call but asserts nothing about how query params are parsed/routed.
- **LOW — S2 name→readable-label claim unverified.** The "How It Works" step 2 label-conversion claim is vacuous as written (label equals method name) and not independently asserted; subsumed by **PY-18-04**.
- **PY-18-03 (do-not-retest) — S8/S9 CLI flags are documented-but-broken.** `tina4 test --file/--method/--verbose` (S8) and `--cov=src --cov-report=term|html` (S9) are logged broken and re-verified open across S8 + S9. Do not re-exercise; the finding stands.

## Resolved items

- **PY-18-04 — auto-discovery / `tina4 test` runs pytest** — verified fixed 2026-06-22 · 3.13.39. `tina4 test` cleanly wraps pytest against `tests/`; our `test_ch18_*` prefix satisfies default discovery. The name→readable-label sub-claim remains a LOW open note.
- **PY-18-07a — S4 missing `from src.orm.Product import Product`** — CLOSED (docs fixed in 3.13.4). The import line now ships in the chapter; `test_ch18_product.py` uses it verbatim. Re-confirmed 2026-06-22 · 3.13.39.
- **PY-18-08 (incl. -08a) — S5/S6 `resp.status_code` + positional POST body** — CLOSED (docs fixed in 3.13.4). Chapter now uses `resp.status` and keyword `json=` bodies; all route/auth/client-method tests run verbatim. Re-confirmed 2026-06-22 · 3.13.39.
- **PY-18-10 — S5 Response Object reference wrong** (`status_code`, "body is a string") — CLOSED (docs realigned in 3.13.4; framework unchanged). New S5 "Response Object" subsection correctly lists `status` (int), `body` (bytes), `text()`, `json()`, lowercased `headers`. Regression sentinel retained (dormant) in `test_ch18_response_object_probe.py`.
- **Ch18 doc-fidelity audit — 2026-06-22 · 3.13.39.** All section-units S2–S7 + S10 verdict faithful / faithful-with-known-findings; ZERO confirmed impl-errors. PY-18-07b/07c handled via cited PATCH blocks; PY-18-14 correctly left as a logged framework finding (not papered over in the verbatim health test).

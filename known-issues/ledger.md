# Known Issues — ledger

Cross-language ledger of confirmed issues in the Tina4 **documentation** and in **framework
code**, one row per issue.

**This is not the Known Issues Log.** `findings-log.md` → `## Known Issues Log` remains the
canonical record for `PY-NN-NN` doc-fidelity findings and `BH-<n>` bug hunts — 67 rows, Python
only, every one traced to a quoted documented claim tested inside `documentation-testing/`. This
ledger holds what that log deliberately excludes: issues found outside the chapter-walking
protocol, and issues in languages other than Python. Nothing appears in both. When a row here
earns a chapter-traced test, it graduates to the KI Log and its row is deleted from this file.

## Issue codes

`<SCOPE>-<KIND>-<NN>` — deliberately alphabetic in the middle so it can never collide with the
KI Log's numeric `PY-NN-NN`.

| Scope | | Kind | |
|---|---|---|---|
| `PY` | tina4-python | `DOC` | documentation: the page is wrong, incomplete, or contradicts itself |
| `PHP` | tina4-php | `FW` | framework code: the shipped code behaves wrongly |
| `RB` | tina4-ruby | | |
| `ND` | tina4-nodejs | | |
| `JS` | tina4-js (frontend) | | |
| `DLP` | tina4delphi | | |
| `CLI` | the Rust CLI, all languages | | |
| `SITE` | the docs site and its tooling | | |

Status: `open` · `fix-in-review` · `fixed` · `pending-retest` · `not-a-bug` · `wont-fix`

**Last reproduced on** is the version the behaviour was *actually observed on*, not the version
it was first found on. A row whose last-reproduced version has fallen behind the current release
is `pending-retest`, not `open` — an unverified age is how a fixed bug stays on a list for months.

## Ledger

| Code | Kind | Language | Last reproduced on | Date found | Status | Note | How to reproduce |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `PY-DOC-01` | documentation | python | tina4-python 3.13.98 (source read); site @`9d688d7` | 2026-08-12 | fix-in-review | Site printed `expect_equal` / `expect_raises` for the inline `@tests` builders. `tina4_python.Testing` exports `assert_equal`, `assert_raises`, `assert_true`, `assert_false`, `tests` — and no `expect_*` — so the snippet raised `NameError` on every released version. **Collateral damage:** upstream `10a1e3d` (issue 132) renamed `assertEqual`→`expectEqual` for **tina4-nodejs**, which is camelCase and presumably right there, and the same pass rewrote the Python page's snake_case names. PHP and Ruby were never touched. Corrected in docs PR 50; a maintainer still has to confirm Python was not meant to follow. Backlog G10. | `cd documentation-testing/pypy && .venv/bin/python -c "import tina4_python.Testing as T; print([n for n in dir(T) if not n.startswith('_')])"` — lists `assert_*`, no `expect_*` |
| `PY-DOC-02` | documentation | python | tina4-book @`2818c2f` | 2026-08-12 | open | Chapter 38 states "**97 built-in features**" in its opening line and "the same 97 features" at line 166, while its own feature tables carry **102** rows. Chapter 1 was aligned to the stated 97 (it previously said "70 other features", disagreeing with both). Three places disagreed; two now agree on a number that the table contradicts. The count is worth deriving from the framework rather than from the table. Backlog G11. | `cd tina4-book/book-1-python/chapters && awk '/^\|/ && !/^\| *Feature/ && !/^\|[- ]+\|/ {c++} END {print c}' 38-feature-list.md` — prints `102`; `grep -c "97" 38-feature-list.md` shows the stated figure |
| `PY-FW-01` | framework | python | 3.13.97 (behaviour); 3.13.98 (source) | 2026-08-07 | pending-retest | `@cached(max_age=N)` does not cache. The decorator only stamps `fn._cached` and `fn._cache_max_age`; nothing in the dev server reads them, so the handler runs on every request with or without `TINA4_CACHE_BACKEND` set. Behaviour last measured on 3.13.97 — the attribute-only implementation is still there in 3.13.98 by source read, but the end-to-end miss has not been re-run since. Deliberately **not** documented: the page states intended behaviour. Backlog G1. | Decorate a route returning `time.time()` with `@cached(max_age=120)`, `tina4 serve`, request it twice a second apart — bodies differ |
| `PY-FW-02` | framework | python | 3.13.97 (behaviour); 3.13.98 (signature) | 2026-08-07 | pending-retest | `ServiceRunner.register(name, instance)` accepts an object that merely has `run()` and then never runs it — zero invocations, nothing logged. `register_service()` is the working path for a class-based service. The signature annotates `handler: callable`, so an instance is the caller's error, but silent acceptance is the defect. Backlog G1. | `runner.register("x", MyService())` then `runner.start()`; the service's `run()` is never entered and no warning is logged. Contrast `runner.register_service("x", MyService())` |
| `PY-FW-03` | framework | python | tina4-python 3.13.94 and 3.13.98 | 2026-08-07 | open | `tina4_python.websocket` shadows the `@websocket` decorator. The top-level name resolves to the implementation *module*, so `@websocket("/ws")` fails with `'module' object is not callable` and takes the whole route file down with it. The decorator lives at `tina4_python.core.router`. Docs give the working import with no explanation, per the intended-behaviour rule. Backlog G1a item 5. | `cd documentation-testing/pypy && .venv/bin/python -c "import tina4_python as t; print(type(t.websocket).__name__, callable(t.websocket))"` — prints `module False` |
| `CLI-FW-01` | framework | all (Rust CLI) | CLI 3.8.67 · tina4-python 3.13.97 | 2026-08-11 | pending-retest | `.env` beats the command-line flag for the port, which is the opposite of the usual precedence. With `TINA4_PORT=7821` in `.env`, `tina4 serve --port 7899` serves on **7821**. The flag does beat a bare `PORT` variable. A reader whose `--port` is silently ignored has no way to tell why. Docs now show the three ways to set a port and claim no precedence. Backlog G1a item 1. | Put `TINA4_PORT=7821` in `.env`, run `tina4 serve --port 7899`, read the bound port from the banner |
| `CLI-FW-02` | framework | all (Rust CLI) | CLI 3.8.67 | 2026-08-11 | pending-retest | A busy port is taken, not avoided. `tina4 serve` logs `Port 7146 in use — killing existing process...` and terminates whatever holds the port, rather than failing or choosing the next free one. Convenient against your own stopped-but-not-dead server; destructive against an unrelated service on 7146. Backlog G1a item 2. | Bind 7146 with any process (`python3 -m http.server 7146`), then `tina4 serve` in a project — the other process is killed |
| `CLI-FW-03` | framework | all (Rust CLI) | CLI 3.8.67 | 2026-08-11 | pending-retest | `tina4 routes` in a scaffolded project prints the "must be started with the tina4 CLI" guard instead of listing routes. Omitted from the docs rather than described, since `/__dev` does the job. Backlog G1a item 3 / G4. | `tina4 init python demo && cd demo && tina4 routes` |
| `CLI-FW-04` | framework | all (Rust CLI) | CLI 3.8.67 · tina4-python 3.13.97 | 2026-08-11 | pending-retest | `tina4 test` fails `No module named pytest` on a freshly scaffolded project, because the scaffold installs no test runner. Documented as ordinary setup (`uv add pytest`) rather than as a defect. Whether the scaffold *should* ship a runner is the open question. Backlog G1a item 4 / G4. | `tina4 init python demo && cd demo && tina4 test` |
| `SITE-DOC-01` | documentation | all (site tooling) | tina4-documentation @`9d688d7` | 2026-08-13 | open | `scripts/audit-truth.py` cannot express a CLI-only environment variable. Its allow-list is built by scanning `getenv()` calls in the four framework source trees (`FRAMEWORK_SOURCES`), and the CLI is consulted only for subcommand grammar — so a real variable implemented in the Rust CLI is reported as a "fake env var" and fails the gate. `TINA4_INIT_NO_SERVE` is verified working and had to be left out of Chapter 1 for this reason. Fix is to add the CLI as an env-var source, or an explicit allow-list. | Add a line mentioning `TINA4_INIT_NO_SERVE` to any `docs/**/*.md`, then `python3 scripts/audit-truth.py` — it is listed under "fake env var(s)". Confirm it is real with `strings /usr/local/bin/tina4 \| grep TINA4_INIT_NO_SERVE` |

## Rules for a row

- **Reproduce before you write it.** The How-to-reproduce column is not optional and not prose —
  it is the command or the sequence, so the next person confirms in a minute instead of
  re-deriving. A row nobody can reproduce is a rumour.
- **Version-stamp what you actually observed.** If the row is carried forward from an older
  measurement, say which part is fresh (a source read) and which is not (the end-to-end
  behaviour), and set `pending-retest`.
- **Record, never fix.** The framework is read-only in this repo — `documentation-testing/readme.md`
  rules 10 to 12. A row here is evidence for someone else to act on.
- **Never document a fault on a page.** Framework defects are fixed in the framework; the
  documentation states intended behaviour. That rule is why several of these rows exist instead
  of paragraphs on tina4.com.
- **One home per fact.** The backlog (`outstanding-tasks.md`) tracks the *work*; this ledger
  tracks the *issue*. Each row names its backlog item so neither drifts.

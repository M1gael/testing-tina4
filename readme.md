# Tina4 Python Framework Evaluation

This project is dedicated to testing and evaluating different versions of the **Tina4 Python Framework**.

## Project Goal
The primary objective of this repository is to:
*   Perform systematic evaluations of the Tina4 stack across multiple languages (**Python** and **Ruby**).
*   Documentation Verification: Implement framework features exactly as they are provided from the official documentation.
*   Discrepancy Identification: Identify and document cases where the framework's actual behavior deviates from the documentation provided.
*   Regression Testing: Validate fixes and monitor issues across framework updates.

## Protocol: Chapter-Based Evaluation
The repository contains a `documentation/` folder with complete guides. The ASSISTANT MUST:
1.  **Wait for Direction**: Do NOT start working on any documentation file until the USER explicitly specifies which chapter (e.g., "Work on Chapter 3").
2.  **Strict Sequencing**: Implement chapters only in the order requested by the USER. No exceptions.
3.  **Implementation Fidelity**: Implement the provided code example exactly as documented within the target language project directory (`pypy/` for Python, `ruru/` for Ruby).
4.  **No Proactive Fixes**: Do NOT implement proactive fixes for framework bugs; the goal is to verify if the documentation works as-is.
5.  **Issue Reporting**: Report all discrepancies, errors, or points of confusion to the USER for issue tracking in plain-text code blocks as defined in the `reporting` skill.
6.  **Language-Specific Conversations**: Strictly only discuss one language per conversation. If a conversation is started for Python, it remains dedicated to Python and must never transition to Ruby (and vice-versa).

## Evaluation Progress
| Language | Chapter | Status | Key Issues Found |
| :--- | :--- | :--- | :--- |
| Ruby | 01 | Completed | See issues `RB-01-01`, `RB-01-02`, `RB-01-03` |
| Ruby | 02 | Completed | See issues `RB-02-01`, `RB-02-02`, `RB-02-03` |
| Ruby | 03 | Completed | See issues `RB-03-01`, `RB-03-02`, `RB-03-03`, `RB-03-04`, `RB-03-05` |
| Ruby | 04 | Completed | See issues `RB-04-01`, `RB-04-02`, `RB-04-03`, `RB-04-04` |
| Python | 01 | Completed | Path params in signature vs `params` dict. |
| Python | 02 | Completed | Wildcard key discrepancy; `@group` decorator missing. |
| Python | 03 | Completed | `request.files` empty; multipart in `request.body`. |
| Python | 04 | Completed | `tina4.css` missing from default project scaffold. |
| Python | 05 | Completed | `to_paginate` doesn't slice data; `migrate` CLI broken. |
| Python | 06 | In Progress | ORM issues: `ForeignKeyField` missing, `auto_now_add` error. |

## Project Structure
*   `pypy/`: The Python testing project and primary workspace.
*   `ruru/`: The upcoming Ruby testing project and workspace.
*   `.agents/`: Automation workflows, reporting skills, and agent-specific configurations.


## Standard Implementation Workflow
1.  **Isolation**: All test implementations occur within the current language's target project directory (e.g., `pypy/` or `ruru/`).

2.  **Organization**: Every documentation section should have a dedicated file in the appropriate routes/feature directory named after the feature (e.g., `chaining.py`).
3.  **Documentation Consistency**: 
    *   Implement exactly as documented first.
    *   Add lowercase, space-prefixed comments at the top of each file explaining the test case.
4.  **Verification**: 
    *   Test against the live `tina4 serve` process via CLI or browser.
    *   Continuously monitor `logs/tina4.log` for registration and execution errors.
5.  **Reporting**: Generate plain-text status reports as defined in the `reporting` skill.
6.  **Review**: Read the `reporting` skill before performing any `/commit` requested by the USER.

## Known Issues Log
All confirmed framework bugs and documentation discrepancies are tracked here. Status values: `open` | `fixed` | `workaround` | `pending-retest`.

| ID | Language | Chapter | Status | Date Found | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RB-01-01 | Ruby | 01 | open | 2026-03-31 | `webrick` gem is not listed as a dependency in the documentation but is required at runtime. Server fails to start without it. |
| RB-01-02 | Ruby | 01 | open | 2026-03-31 | Ternary operator syntax used in route documentation causes a Ruby parse error. The documented pattern is invalid Ruby. |
| RB-01-03 | Ruby | 01 | open | 2026-03-31 | POST endpoints return 401 Unauthorized when no auth is configured. Framework appears to apply a default auth guard to all non-GET routes. |
| RB-02-01 | Ruby | 02 | fixed | 2026-03-31 | Symbol keys (e.g. `params[:id]`) do not work for accessing route parameters. String keys must be used instead. |
| RB-02-02 | Ruby | 02 | open | 2026-03-31 | Route group prefixes are silently ignored at runtime. Routes registered inside a group resolve as if no prefix was applied. |
| RB-02-03 | Ruby | 02 | fixed | 2026-03-31 | Wildcard routes (e.g. `/docs/*`) now match correctly. Value available via `request.params['wildcard']`. |
| PY-02-05 | Python | 02 | open | 2026-04-01 | `@group` decorator is not exported from `tina4_python.core.router`, preventing documented decorator-style route groups. Only `Router.group()` (imperative) exists. |
| PY-03-05 | Python | 03 | open | 2026-04-01 | `request.files` is always empty for multipart uploads. Parsed file data is placed in `request.body` instead, contradicting documentation. |
| PY-05-04 | Python | 05 | open | 2026-04-01 | `DatabaseResult.to_paginate()` fails to slice the `records` list. It calculates metadata correctly but returns the full record set in the `data` key. |
| PY-05-05 | Python | 05 | open | 2026-04-01 | `DatabaseResult.column_info()` returns `UNKNOWN` for all types in SQLite when the table name cannot be reliably extracted from the SQL query via regex. |
| PY-04-06 | Python | 04 | open | 2026-04-01 | `tina4.css` documentation states it "ships with every project" but the file is missing from `public/css/` in scaffolded projects. |
| PY-06-07 | Python | 06 | open | 2026-04-01 | `ForeignKeyField` is missing from `tina4_python.orm`, causing import errors in documented ORM examples. |
| PY-06-08 | Python | 06 | open | 2026-04-01 | `Field.__init__()` in ORM throws `unexpected keyword argument 'auto_now_add'`, breaking documented timestamps. |
| PY-05-01 | Python | 05 | open | 2026-03-25 | `tina4 migrate` command fails with `ImportError` on `load_dotenv`. Migrations cannot be run via the CLI at all. |
| PY-05-02 | Python | 05 | open | 2026-03-25 | `DatabaseResult` methods `column_info()`, `to_list()`, and `to_paginate()` are documented but entirely absent from the implementation, yielding `AttributeError`. |
| PY-0506-03 | Python | 05-06 | open | 2026-03-25 | `Note.create_table()` and all schema-altering ORM operations deadlock with a SQLite `Resource Busy` error while `tina4 serve` is running. ORM integration via HTTP endpoints cannot be tested safely. |
| RB-03-01 | Ruby | 03 | open | 2026-03-31 | Header names are normalized to lowercase (e.g., `accept`) at runtime, contradicting documentation stating they "keep their original casing". |
| RB-03-02 | Ruby | 03 | open | 2026-03-31 | Usage of the `return` keyword within `Tina4::Router` blocks causes an `unexpected return` LocalJumpError and 500 status. `return` is used extensively in chapter 3 examples. |
| RB-03-03 | Ruby | 03 | open | 2026-03-31 | All POST routes return `401 Unauthorized` without any configured auth or session logic, making non-GET routes untestable as documented. |
| RB-03-04 | Ruby | 03 | open | 2026-03-31 | Content negotiation fails because manual header checks (`request.headers["Accept"]`) use Title-Case keys while the framework normalizes them to lowercase. |
| RB-03-05 | Ruby | 03 | open | 2026-03-31 | `tina4 serve` hangs or deadlocks when a route triggers an unhandled Ruby exception (e.g., the `LocalJumpError` from `return`) instead of cleanly returning a 500 error page. |
| RB-04-01 | Ruby | 04 | open | 2026-04-01 | Frond ternary operator `condition ? val1 : val2` returns the source object (e.g., an array) instead of the evaluated result when using complex expressions. |
| RB-04-02 | Ruby | 04 | open | 2026-04-01 | `{% include %}` tag does not inherit parent scope (e.g., loop variables), and the `with` keyword fails to pass any data to the partial. |
| RB-04-03 | Ruby | 04 | open | 2026-04-01 | Frond macros (`{% macro %}`) and special tags (`{% raw %}`, `{% spaceless %}`) are non-functional and currently produce no output or have no effect. |
| RB-04-04 | Ruby | 04 | open | 2026-04-01 | Boolean logic in `{% if %}` blocks fails when combined with filters (e.g., `items | length > 0` returns false for non-empty arrays). |
| RB-05-01 | Ruby | 05 | open | 2026-04-01 | `sqlite3` gem is not documented as a dependency but is required for the default database connection. Server fails to start on health checks. |
| RB-05-02 | Ruby | 05 | open | 2026-04-01 | `DatabaseResult#to_paginate` returns keys `data`/`page`/`per_page`/`total` instead of the documented `records`/`count`/`limit`/`offset`. |
| RB-05-03 | Ruby | 05 | open | 2026-04-01 | `Tina4.seed` is undefined by default. Requires an undocumented manual `require "tina4/seeder"` before use. |
| RB-05-04 | Ruby | 05 | open | 2026-04-01 | Documented curl examples fail with `401 Unauthorized` for POST/PUT/DELETE because write-routes are secure-by-default. Undocumented `.no_auth` chain method is required. |
| RB-05-05 | Ruby | 05 | open | 2026-04-01 | `request.body` returns raw string, not a Hash. Using `body["title"]` (as documented) silently returns the literal substring `"title"`, bypassing validations and inserting bad data. Requires `request.body_parsed` instead. |

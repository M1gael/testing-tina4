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
| Ruby | 05 | Completed | See issues `RB-05-01` to `RB-05-05`. `to_paginate` now provides dual-key support. |
| Python | 01 | Completed | Verified. Path parameters mirrored in `request.params`. |
| Python | 02 | Completed | Faulty. Path parameters match but NO auto-casting to `int/float` (`PY-02-06`). |
| Python | 03 | Completed | Faulty. POST routes secure-by-default (undocumented). Multipart handled in `request.body`. |
| Python | 04 | Completed | Faulty. `tina4.css` still missing from scaffold. |
| Python | 05 | Completed | Faulty. `tina4_migration` not recording runs (`PY-05-07`). Relative path needed for DB. |
| Python | 06 | Completed | Faulty. `auto_now_add` causes TypeError. `ForeignKeyField` FIXED. |
| Python | 07 | Completed | Faulty. `db.execute` returns bool, not object with `last_id` (`PY-07-01`). |
| Python | 08 | Completed | Verified. `@noauth()` and `@secured()` functional with correct nesting order. |
| Python | 09 | Completed | Verified. Session/Cookie APIs work; TTL default mismatch persists. |
| Python | 10 | Completed | Verified. Middleware chain and short-circuiting functional. |
| PHP | 01 | Completed | Basic GET/POST routes verified. |
| PHP | 02 | Completed | Chaining required for middleware; 2-arg `get()`. |
| PHP | 03 | Completed | File uploads and validation verified. |
| PHP | 04 | Completed | Frond templates and macros verified. |
| PHP | 05 | In Progress | Namespace/Class mismatch in `Database` usage. |

## Project Structure
*   `phph/`: The PHP testing project and workspace.
*   `pypy/`: The Python testing project and primary workspace.
*   `ruru/`: The Ruby testing project and workspace.
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
| PY-01-01 | Python | 01 | fixed | 2026-04-02 | Path parameters are now correctly mirrored in the `request.params` dictionary (Fixed in v3.10.50). |
| RB-01-03 | Ruby | 01 | open | 2026-03-31 | POST endpoints return 401 Unauthorized when no auth is configured. Framework appears to apply a default auth guard to all non-GET routes. |
| RB-02-01 | Ruby | 02 | fixed | 2026-03-31 | Symbol keys (e.g. `params[:id]`) do not work for accessing route parameters. String keys must be used instead. |
| RB-02-02 | Ruby | 02 | not-a-bug | 2026-03-31 | Not a bug. Using `Tina4::Router.get` inside a group bypasses the group context. Must use the block's DSL methods (`get`, `post`, etc.) to inherit the prefix. |
| RB-02-03 | Ruby | 02 | fixed | 2026-03-31 | Wildcard routes (e.g. `/docs/*`) now match correctly. Value available via `request.params['wildcard']`. |
| PY-02-03 | Python | 02 | fixed | 2026-04-02 | Wildcard route values are now correctly indexed by the key `"*"` in `request.params` (Fixed in v3.10.50). |
| PY-02-05 | Python | 02 | open | 2026-04-01 | `@group` decorator is not exported from `tina4_python.core.router`, preventing documented decorator-style route groups. Only `Router.group()` (imperative) exists. |
| PY-03-05 | Python | 03 | fixed | 2026-04-01 | `request.files` is now correctly populated for multipart uploads (Fixed in v3.10.50). |
| PY-05-04 | Python | 05 | fixed | 2026-04-01 | `DatabaseResult.to_paginate()` now successfully slices the record set based on page arguments (Fixed in v3.10.50). |
| PY-05-05 | Python | 05 | fixed | 2026-04-01 | `DatabaseResult.column_info()` now correctly identifies SQLite types (Fixed in v3.10.50). |
| PY-04-06 | Python | 04 | open | 2026-04-01 | `tina4.css` documentation states it "ships with every project" but the file is missing from `public/css/` in scaffolded projects. |
| PY-06-07 | Python | 06 | open | 2026-04-01 | `ForeignKeyField` is missing from `tina4_python.orm`, causing import errors in documented ORM examples. |
| PY-06-08 | Python | 06 | open | 2026-04-01 | `Field.__init__()` in ORM throws `unexpected keyword argument 'auto_now_add'`, breaking documented timestamps. |
| PY-05-01 | Python | 05 | fixed | 2026-03-25 | `tina4 migrate` command successfully executes migrations without the former `load_dotenv` ImportError. |
| PY-05-02 | Python | 05 | fixed | 2026-03-25 | `DatabaseResult` methods `column_info()`, `to_list()`, and `to_paginate()` are now present in the implementation. |
| PY-0506-03 | Python | 05-06 | open | 2026-03-25 | `Note.create_table()` and all schema-altering ORM operations deadlock with a SQLite `Resource Busy` error while `tina4 serve` is running. ORM integration via HTTP endpoints cannot be tested safely. |
| RB-03-01 | Ruby | 03 | open | 2026-03-31 | Header names are normalized to lowercase (e.g., `accept`) at runtime, contradicting documentation stating they "keep their original casing". |
| RB-03-02 | Ruby | 03 | open | 2026-03-31 | Usage of the `return` keyword within `Tina4::Router` blocks causes an `unexpected return` LocalJumpError and 500 status. `return` is used extensively in chapter 3 examples. |
| RB-03-03 | Ruby | 03 | not-a-bug | 2026-03-31 | Not a bug. ALL write routes (POST, PUT, PATCH, DELETE) require authentication by default in v3. Use `.no_auth` to open routes publicly. |
| RB-03-04 | Ruby | 03 | open | 2026-03-31 | Content negotiation fails because manual header checks (`request.headers["Accept"]`) use Title-Case keys while the framework normalizes them to lowercase. |
| RB-03-05 | Ruby | 03 | open | 2026-03-31 | `tina4 serve` hangs or deadlocks when a route triggers an unhandled Ruby exception (e.g., the `LocalJumpError` from `return`) instead of cleanly returning a 500 error page. |
| RB-04-01 | Ruby | 04 | open | 2026-04-01 | Frond ternary operator `condition ? val1 : val2` returns the source object (e.g., an array) instead of the evaluated result when using complex expressions. |
| RB-04-02 | Ruby | 04 | fixed | 2026-04-01 | Fixed in v3.10.91+. Included templates inherit parent context via duplication, and the `with` keyword is correctly parsed. |
| RB-04-03 | Ruby | 04 | fixed | 2026-04-01 | Fixed in v3.10.91+. Frond supports `handle_macro`, `handle_from_import`, `{% raw %}`, and `{% spaceless %}` blocks. |
| RB-04-04 | Ruby | 04 | open | 2026-04-01 | Boolean logic in `{% if %}` blocks fails when combined with filters (e.g., `items | length > 0` returns false for non-empty arrays). |
| RB-05-01 | Ruby | 05 | open | 2026-04-01 | `sqlite3` gem is not documented as a dependency but is required for the default database connection. Server fails to start on health checks. |
| RB-05-02 | Ruby | 05 | fixed | 2026-04-01 | `DatabaseResult#to_paginate` now returns BOTH documented (`records`/`count`) and extra (`data`/`total`) keys, ensuring compatibility. |
| RB-05-03 | Ruby | 05 | open | 2026-04-01 | `Tina4.seed` is undefined by default. Requires an undocumented manual `require "tina4/seeder"` before use. |
| RB-05-04 | Ruby | 05 | not-a-bug | 2026-04-01 | Not a bug. High-security by default. Write-routes require auth. Use `.no_auth` to bypass for public endpoints like webhooks. |
| RB-05-05 | Ruby | 05 | open | 2026-04-01 | `request.body` returns raw string, not a Hash. Using `body["title"]` (as documented) silently returns the literal substring `"title"`, bypassing validations and inserting bad data. Requires `request.body_parsed` instead. |
| PH-02-01 | PHP | 02 | open | 2026-04-07 | `Router::get()` and other route methods only accept 2 arguments (path, callback). Documentation states 3 arguments are supported (including middleware array), but this causes a "Too many arguments" error. Chaining `->middleware()` is required instead. |
| PH-02-02 | PHP | 02 | open | 2026-04-07 | PHP middleware callbacks do NOT receive a `$next` argument. Returning `true` continues the chain, while documentation incorrectly suggests calling `$next($request, $response)`. |
| PH-05-01 | PHP | 05 | open | 2026-04-07 | `Database` class is located in `Tina4\Database` namespace. Documentation incorrectly suggests `use Tina4\Database` followed by `Database::getConnection()`, which fails because it refers to the namespace. Correct usage is `use Tina4\Database\Database`. |
| PH-05-02 | PHP | 05 | open | 2026-04-07 | `Database::getDatabaseType()` method is missing from the PHP implementation but is featured prominently in Chapter 5 examples for schema inspection. |
| PH-01-01 | PHP | 01 | open | 2026-04-07 | `tina4 init` / `tina4php` CLI commands are not globally available in some environments; must use `./vendor/bin/tina4php` instead. |
| PH-04-01 | PHP | 04 | open | 2026-04-07 | Documentation uses `.twig` extension in Chapter 4 examples but `.html` in Chapter 1. Both appear to work, but the inconsistency can cause confusion regarding the preferred extension for Frond templates. |
| PY-06-09 | Python | 06 | open | 2026-04-07 | `@orm_bind` used as a class decorator fails by returning `None`, effectively deleting the model class and causing `AttributeError: 'NoneType' object has no attribute 'create_table'`. |
| PY-07-01 | Python | 07 | open | 2026-04-07 | `Database.execute()` returns `True` (bool) for write operations without `RETURNING`. Documentation erroneously suggests it returns a result object with a `last_id` attribute. |
| PY-08-01 | Python | 08 | open | 2026-04-07 | `Auth.get_token()` is implemented as an instance method, but documentation shows it being called as a class/static method (`Auth.get_token(payload)`). |
| PY-09-01 | Python | 09 | open | 2026-04-07 | `TINA4_SESSION_TTL` default value in code is `1800` (30m), but documentation states the default is `3600` (1hr). |
| PY-10-01 | Python | 10 | open | 2026-04-07 | `Router.group()` callback is documented as taking no arguments, but implementation passes a `RouteGroup` object, requiring the callback to accept one argument. |
| PY-02-06 | Python | 02 | open | 2026-04-13 | Path parameter type hints (e.g., `:int`) act as constraints but fail to perform auto-casting. Values remain strings. |
| PY-05-07 | Python | 05 | open | 2026-04-13 | Migration runner fails to record completed migrations in the `tina4_migration` table, causing duplicate-table errors on subsequent runs. |
| PY-06-07 | Python | 06 | fixed | 2026-04-01 | `ForeignKeyField` is now correctly exported from `tina4_python.orm` (Verified in v3.11.1). |

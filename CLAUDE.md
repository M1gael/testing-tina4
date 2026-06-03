# CLAUDE.md

Context for working in this repository. Read this first, then read `readme.md` (the
authoritative protocol + Known Issues Log).

## What this repo is

A **QA / evaluation harness for the Tina4 web framework**, not an app and not the framework
itself. The job is to implement the official Tina4 documentation *exactly as written*, in real
Tina4 projects, and record every place the framework's actual behaviour deviates from its docs.

The loop is:
1. Take a chapter from `documentation/tina4-book/`.
2. Implement its code examples verbatim in the language's project dir (`pypy/`, `phph/`, `ruru/`).
3. Run it against a live `tina4 serve` and observe.
4. Log discrepancies as issues in the **Known Issues Log** in `readme.md`.

This is **documentation-fidelity testing**: we verify whether a new user following the docs
would succeed. We are the new user.

## The Protocol — non-negotiable rules

These come from `readme.md`. Follow them strictly.

1. **Wait for direction.** Do NOT start on any chapter until the user explicitly says which one
   (e.g. "Work on Chapter 3"). Implement chapters only in the order requested.
2. **One language per conversation.** A Python session stays Python; never drift to Ruby/PHP
   (and vice-versa).
3. **Implement exactly as documented.** Code the example as written, first. Do not "fix" it.
4. **No proactive fixes.** We are verifying the docs, not patching the framework. Discover bugs
   the way a real user would.
5. **Blind implementation.** Do NOT read the Known Issues Log *while* implementing — implement
   from the docs cold, hit the bug naturally, document it, and only *then* cross-reference the
   log to see if it's already tracked or new.
6. **Stay inside the standard project structure.** All work happens in `src/routes/`,
   `src/orm/`, `src/templates/`, `migrations/`, `seeds/`. No throwaway scripts "next to app.py"
   unless a feature genuinely can't be tested any other way (e.g. CLI-internal logic).
7. **Report discrepancies as plain-text blocks** per the `reporting` skill (see Skills below),
   for the user to track. Read the `reporting` skill before any `/commit`.

## File & naming conventions

- **Chapter-prefixed, zero-padded filenames:** `ch01_`, `ch02_`, … e.g.
  `src/routes/ch01_routing.py`, `src/orm/ch06_author.rb`.
- One file per documentation feature/section, named after the feature.
- Top of each file: a lowercase, space-prefixed comment describing the test case.
- Migrations: numeric or timestamp prefix (`000001_create_notes_table.sql`,
  `20260409121000_create_auth_users_table.sql`).
- Seeds: numeric prefix (`001_notes.rb`).

## Language project directories

| Dir | Language | Tina4 version | Entry | Package manager | Notes |
|-----|----------|---------------|-------|-----------------|-------|
| `pypy/` | Python (primary workspace) | tina4-python **3.11.13** (`uv.lock`) | `app.py` | `uv` | has `.tina4/` agents |
| `phph/` | PHP | tina4php **3.12.10** (`composer.lock`) | `index.php` | composer | |
| `ruru/` | Ruby | tina4ruby `~> 3.0` (`Gemfile`) | `app.rb` | bundler | needs `webrick`, `sqlite3` gems |

Each follows the standard Tina4 layout: `src/{routes,orm,templates}/`, `migrations/`, `seeds/`.

### Running / testing
```
Python:  uv run tina4 serve     (or uv run pytest)
PHP:     ./vendor/bin/tina4php   (global tina4php may be unavailable — see PH-01-01)
Ruby:    bundle exec ...         (webrick required at runtime — see RB-01-01)
```
Watch `logs/tina4.log` (or `server.log` in ruru) for registration/execution errors while testing.

## Documentation source — `documentation/tina4-book/`

Seven "books", chapters as markdown under `book-N-*/chapters/NN-topic.md`:

| Book | Dir | Chapters |
|------|-----|----------|
| Understanding | `book-0-understanding` | 4 |
| Python | `book-1-python` | 38 |
| PHP | `book-2-php` | 38 |
| Ruby | `book-3-ruby` | 38 |
| Node.js | `book-4-nodejs` | 38 |
| JavaScript (frontend/Frond) | `book-5-javascript` | 16 |
| Delphi | `book-6-delphi` | 15 |

- `plan/` — API reference, brand guide, parity matrices. `plan/parity/` has per-subsystem parity
  audits (auth, database, orm, queue, router, session, sse, template, websocket).
- Chapters here are the **source of truth** for what to implement. The framework code is what's
  under test.

## Known Issues Log

Lives in `readme.md`. Issue IDs are `LANG-CH-NN` (e.g. `PY-05-11`, `RB-03-02`, `PH-02-01`,
`CLI-01-01`). Status values: `open` | `fixed` | `workaround` | `pending-retest` | `not-a-bug`.
When you confirm a new discrepancy, add a row; when retesting shows a fix, update the status with
the version it was fixed in.

## Skills, prompts & agents

- **`.agents/`** — gitignored. Holds the `reporting` and `verification` skills referenced by the
  protocol (not present in a fresh clone). The reporting skill defines the plain-text issue
  report format used for `/commit`.
- **`.prompts/` and `.skills/`** — three Tina4 guide docs each (`tina4-developer`, `tina4-js`,
  `tina4-maintainer`), in two formats. **The two directories are duplicates** of one another
  (content identical; only frontmatter `name` differs, underscore vs hyphen). These describe how
  to *build with* and *maintain* Tina4 — useful background, but the **Protocol above overrides
  them** (those guides say "fix bugs / be proactive"; here we explicitly do NOT).
- **`scratch/skills/`** — fuller copies of the same three skills, each with a `references/`
  subdir (routes-and-api, data-and-orm, templates-and-frontend, auth-and-services, signals,
  components, cli-and-deployment, subsystems, etc.). Good deep-reference material.
- **`pypy/.tina4/agents/`** — Tina4's own agent configs (coder, debug, planner, supervisor,
  vision, image-gen), each a `config.json` + `system.md`. Part of the framework under test, not
  our tooling.
- **`php-temp-test/`** — a scaffolded PHP app with the full tina4php (3.12.10) vendored in. A
  scratch/integration environment.

## Git

- Remote: `git@github.com:M1gael/testing-tina4.git`, default branch `main` (single branch).
- Commit messages in history are conventional-ish (`test(python):`, `docs:`, `chore:`,
  `feat(php):`) and frequently reference the tina4 version and issue IDs being verified.
- Read the `reporting` skill before any user-requested `/commit`.

## Doing work here — quick checklist

1. Confirm which **language** and which **chapter** the user wants. If unstated, ask.
2. Open the chapter md in `documentation/tina4-book/book-*/chapters/`.
3. Implement examples verbatim in the right `src/` location, chapter-prefixed, with no fixes.
4. Run `tina4 serve`, exercise the routes, watch the logs.
5. When behaviour ≠ docs: document the discrepancy (don't fix it), then check the Known Issues
   Log to classify it as existing or new.
6. Report in the plain-text format the `reporting` skill defines.

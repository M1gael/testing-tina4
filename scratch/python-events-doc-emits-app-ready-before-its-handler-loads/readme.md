# python ch13 §10 emits `app.ready` before its handler loads

Ledger row `d-misc-04`. Run 2026-11-02 against tina4-python v3 8fbc2254 (3.13.156), tina4-documentation
origin/main 2c09454, tina4-book origin/main 20b1006.

## Issue

`docs/python/13-events.md` §10 (and the book mirror `book-1-python/chapters/13-events.md`) registers
`@once("app.ready")` in `src/routes/user_events.py` and puts `emit("app.ready", {})` in `src/app.py`.
Booted with `python app.py`, "Application ready." never prints, in debug or production mode.

## Mechanism

`app.ready` is not a framework event in any port (no emit in py/php/rb/nd source); the user's emit is
the only one. Discovery imports `sorted(root.rglob("*.py"))` (`tina4_python/core/server.py:467`), so
`src/app.py` is imported before `src/routes/user_events.py`; the emit runs with no listener and the
`@once` handler registers afterwards. Documentation fault, not a framework fault: the sorted import
order is deterministic by design.

Control C1: the same two files with `src/app.py` renamed `src/zz_app.py` print once. Emitting from the
root `app.py` before `run()` also prints nothing (discovery runs inside `run()`); emitting above the
handler in the same file prints nothing.

## Fix

The emit moves to the bottom of `src/routes/user_events.py`, below the handler, plus one paragraph
saying why. Patches: `~/.cache/tina4-worktrees/dmisc04-tina4-{documentation,book}.fix.patch`.
In development, `POST /__dev/api/reload` re-imports a changed file, so editing it fires the event
again (seen: 2 prints after one reload). The added paragraph says so.

## Run

`./prove.sh` (default docs origin/main), `DOCS=<tree>`, `BOOK=<tree>`; `TINA4_PY=<tree with .venv>`.
Every python block in §10 goes to the path its lead-in prose names. Exit 2 = ERROR (no interpreter,
busy port, failed start), never a pass. Output: `run.log`.

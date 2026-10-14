# The test client cannot dispatch in a browser notebook

Ledger row: `f-rt-08`. Found 2026-10-14 while planning a Tina4 workshop that runs in JupyterLite.

Version: tina4-python v3 at `074fa2eb` (3.13.150). Wheel built from that tree. Pyodide 314.0.7 under
node 22, and JupyterLite 0.8.6 (pyodide-kernel 0.8.6, Pyodide v314.0.0, Python 3.14.2) in headless
Chromium.

## Behaviour (run)

```
sync-run TestClient FAIL: RuntimeError can't start new thread
direct await app: 200 b'{"hi":"Ann"}'
```

The same failure shows up in a real JupyterLite notebook (`jupyterlite-drive.mjs`, `make-probe-notebook.py`):
`TCFAIL RuntimeError can't start new thread`. A `RuntimeWarning: coroutine 'app' was never awaited` follows it.

## Mechanism (read)

`tina4_python/test_client/__init__.py:217-235`, in `TestClient._run`:
- When a loop is running, it hands `asyncio.run` to a `ThreadPoolExecutor`.
- In Pyodide a loop is always running, even under the synchronous `runPython`.
- WebAssembly has no threads, so `Thread.start` raises.

Awaiting `core.server.app` directly works.

So all of these work: routes, ORM, Frond and the ASGI app. Only the synchronous test-client wrapper fails.

## Not Tina4 (run)

In JupyterLite, a SQLite file on the notebook drive (`/drive`) fails:
- With WAL, which Tina4's adapter sets at `database/sqlite.py:85`: `disk I/O error`.
- With plain `sqlite3` in DELETE mode: `database disk image is malformed`.

`/tmp` and `:memory:` work under both journal modes. This is a JupyterLite DriveFS limitation, so it has no ledger row.

## Local Jupyter (run)

In a real ipykernel (Python 3.12, nbclient), all of these work:
- TestClient (it takes the thread path)
- a file SQLite DB
- the ORM through a route
- a `@noauth` POST returning 201
- a plain POST returning 401

## Re-run

`./prove.sh <tina4-python checkout>` runs the Pyodide half.

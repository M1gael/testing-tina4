# `results/`

One file per measurement run: `<date>-<language>.md`.

A run is only publishable if it records all of these. Anything missing makes the numbers
unreusable six weeks later, which is how the current site figures became wrong.

- **Date**, and the machine (OS, CPU class).
- **Versions** of every framework compared, and of the language runtime.
- **The verify output** for each app, or a statement that each passed
  `scripts/verify-app.sh`. Unverified apps are not counted; readme.md rule 2.
- **The counter's table**, produced by `scripts/count-lines.py --markdown`, not typed by hand.
- **The named package list per framework** — the argument, not a footnote; rule 5.
- **Judgement calls made**, and which way each was resolved. Where a call could have gone
  either way, rule 4 says it goes against Tina4, and the record says so.
- **What Tina4 lost on**; rule 9. A run with no losses listed has not been finished.
- **Capability gaps** — anything a framework could not do without more work.

## Runs

| Date | Language | Frameworks | Status |
|---|---|---|---|
| 2026-08-11 | Python | Tina4, Flask, FastAPI, Django | [Complete](2026-08-11-python.md) — all four passed 7/7 verification. Tina4 56 lines / 1 distribution / 3.4 MB against Flask 100 / 17 / 17.9 MB, FastAPI 86 / 18 / 24.7 MB, Django 76 / 16 / 30.6 MB |
| — | PHP, Ruby, Node.js | Tina4 + per-language comparatives | not yet run |

## Superseded figures

Kept so nobody re-quotes them.

| Figure | Where it came from | Why it is dead |
|---|---|---|
| Tina4 34 lines vs Flask 34, FastAPI 37, Django 39 | Scratch run, 2026-08-07 | Three routes, no database, no auth, no OpenAPI — the one shape where the comparatives need nothing extra. Not feature-matched, so it measures nothing. |
| Tina4 install 4.9 MB | Scratch run, 2026-08-06 | Inflated by `__pycache__` from a previous server run. A fresh 3.13.95 install is 3.9 MB across 105 `.py` files. |
| FastAPI 12 deps / 4.8 MB · Flask 6 / 4.2 MB · Django 20 / 25 MB | `tina4-documentation/docs/comparisons.md`, March 2026 | Spot-checked 2026-08-07 and wrong: Django installs 2 third-party distributions, not 20; FastAPI's `site-packages` measured 16 MB, not 4.8. Upstream has taken the Comparisons link off the home page pending re-benchmarking. |
| Throughput: Tina4 9 761 · Starlette 15 664 · FastAPI 11 523 · Flask 5 722 · Django 2 333 req/s | Same page, March 2026 | Apple Silicon; this machine cannot reproduce it, and `hey` is not installed. Not re-run, not quoted. Throughput needs its own spec and matched hardware. |

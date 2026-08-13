# `comparison-testing/`

Measurements of **how Tina4 compares to the frameworks it competes with** — a third
question, distinct from the rest of this repo. `documentation-testing/` asks *do the docs
work for a human reader*; `agent-testing/` asks *does the AI-facing context work for a
model*; this directory asks *what does a developer actually save, or lose, by choosing
Tina4*.

Nothing here ships. It produces numbers that the public site may then quote,
with a date and a method attached.

## Why this exists

The site already publishes a comparison table. Spot-checked on 2026-08-07, it was wrong:
Django listed at 20 installed dependencies against a real 2, FastAPI at 4.8 MB against a
real 16 MB. Upstream has since taken the Comparisons link off the home page "until the
benchmarking is done". This directory is that benchmarking.

A first attempt also went wrong in a more interesting way, and the rule it produced is the
whole point of this directory:

> "Functionality tested on comparatives needs to add packages to achieve what Tina4 has
> under the hood … if you need Swagger + auth + database = dependencies. Compare apples
> with apples." — Andre van Zuydam, 2026-08-07

That attempt built a three-route app with no database, no auth and no OpenAPI docs. Tina4
saved **zero** lines against Flask (34 vs 34) — because a hello-world app is precisely the
case where Flask needs nothing extra. The measurement was correct and the benchmark was
worthless. **A comparison only counts if every framework has to reach the same
capability.**

## The rules

Non-negotiable, because the output is meant to survive being challenged.

1. **Feature-matched or not published.** Every app implements the whole spec in
   [`spec/bookmarks-app.md`](spec/bookmarks-app.md) — database, JWT-protected write, and
   generated OpenAPI docs. Dropping a requirement to make an app look smaller invalidates
   the run.
2. **It must run before it counts.** Every app passes `scripts/verify-app.sh` — a live
   probe of all six acceptance checks — before a single line is counted. A count of code
   that never served a request is not evidence.
3. **Framework defaults, idiomatic and minimal.** Use what the framework's own docs
   recommend. No extra abstraction, no cleverness to shrink the count, and equally no
   deliberately clumsy code to inflate a competitor's.
4. **Err in the competitor's favour.** Where a framework offers a shorter route to the same
   capability, take it. If a judgement call could go either way, choose the one that makes
   Tina4 look worse, and record that you did.
5. **Name every added package.** The list of what Flask, FastAPI and Django must install to
   match is not a footnote — it *is* the argument. A bare count hides it.
6. **Measure fresh.** Install size is read from a clean virtual environment before the app
   is ever run. `__pycache__` from a single previous run inflated an earlier Tina4 figure
   from 3.9 MB to 4.9 MB, and that wrong number nearly shipped.
7. **Pin and date everything.** Framework versions, language version, date, machine. A
   figure without them is not reusable, and every published figure carries them.
8. **Counting is scripted, never hand-tallied.** `scripts/count-lines.py` encodes the rules
   so a re-run reproduces the number exactly.
9. **Publish the losses.** Whatever Tina4 is worse at goes in the results with the same
   prominence as what it is better at. A comparison that only flatters is marketing, and
   readers can smell it.

## What gets measured

Per framework, per language:

| Metric | Definition |
|---|---|
| Lines you write | Non-blank, non-comment lines in files the developer authored |
| Lines you must edit | Non-blank, non-comment lines changed inside generated boilerplate (Django's `settings.py`, `urls.py`) |
| Files touched | Files created or modified |
| Framework-wiring lines | Lines whose only job is framework setup, not application logic |
| Packages added | Third-party distributions beyond the framework itself, **named** |
| Distributions installed | Total in the virtual environment |
| Install size | `site-packages`, fresh, before first run |
| Capability gaps | Requirements the framework cannot meet without more work, described |

Throughput is deliberately **not** measured here yet. It needs matched hardware and a load
generator, and the existing published figures came from an Apple Silicon run this machine
cannot reproduce. Adding it is a separate exercise with its own spec.

## Layout

```
comparison-testing/
├── readme.md                  this file — the rules
├── spec/
│   └── bookmarks-app.md       the app every framework implements, exactly
├── apps/
│   └── python/
│       ├── tina4/             one directory per framework
│       ├── flask/
│       ├── fastapi/
│       └── django/
├── scripts/
│   ├── verify-app.sh          live probe of the six acceptance checks
│   └── count-lines.py         the counter, rules encoded
└── results/
    └── readme.md              dated measurement records, one per run
```

Languages get their own subtree under `apps/`. Python first; PHP, Ruby and Node.js follow
the same spec with their own comparatives (Laravel/Slim, Rails/Sinatra, Express/Nest).

## Running a measurement

```bash
# 1. Build each app to the spec, in its own directory with its own venv.

# 2. Prove each one works. Start the app, then:
scripts/verify-app.sh <port>            # exits non-zero on any failed check

# 3. Count, once every app has passed.
scripts/count-lines.py apps/python/tina4 apps/python/flask \
                       apps/python/fastapi apps/python/django

# 4. Write the run up in results/<date>-python.md, including versions,
#    the named package lists, and whatever Tina4 lost on.
```

## Relationship to the harness protocol

**These measurements are outside the doc-fidelity Protocol.** They do not walk chapters, so
they carry no quoted-documented-claim trace and are **not** eligible for the Known Issues
Log. If a run happens to expose a framework defect — the first attempt turned up `@cached`
not caching and `ServiceRunner.register()` silently never running a service — that defect
has to be re-tested inside `documentation-testing/` against a real chapter before it earns a
`PY-NN-NN` ID.

The framework stays **read-only** here too, exactly as in `documentation-testing/`. If Tina4
needs a patch to pass the spec, that is a finding, not a licence to edit it.

Consumers of these numbers: [`results/`](results/) is the record. **Nothing is published yet.**
The restructure that would have carried the table on `tina4.com/python/` was rejected on
2026-08-12, so no page quotes these figures today. The candidate home is
`tina4-documentation/docs/comparisons.md`, once it is re-benchmarked — that page is currently
de-linked from the site's home page for carrying stale March 2026 numbers.

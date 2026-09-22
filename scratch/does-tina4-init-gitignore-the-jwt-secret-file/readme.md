# Does `tina4 init` gitignore the JWT secret file?

**No — in none of the four backend languages.** The scaffolded `.gitignore` covers `.env`
but not `.env.local`, and `.env.local` is the file every Tina4 framework writes its
auto-minted JWT signing secret into. `git add -A` stages it without a word.

Pinned: Rust CLI `tina4` `origin/main` @ `2bb1418` = **v3.8.88**. Frameworks read at
`origin/v3`: tina4-python `76fee07`, tina4-php `e0df3a97`, tina4-ruby `17b7b20`,
tina4-nodejs `d89998c`. Linux, git 2.55, `core.excludesFile` neutralised in every
measurement. Runtimes present: Python 3.14.7, PHP 8.4.25, Ruby 3.4.10, Node 22.22.2.

> **This supersedes an earlier, narrower write-up.** The first pass fixed python only and
> also added unanchored `sessions/` and `*.db` lines that swallowed real source. Both
> errors are documented below, with the run that caught them. The independent
> verification that found them is preserved untouched in `verify/measurements.txt`.

## The defect

On its first dev run each framework mints a random signing secret and persists it so it
survives a restart. All four write it to `.env.local` in the project root:

| Framework | Writes the secret at | Reads |
|---|---|---|
| tina4-python | `tina4_python/auth/__init__.py:101` `ensure_dev_secret()` | `:44,57` |
| tina4-php | `Tina4/Auth.php:148` | via `App.php:252-262` |
| tina4-ruby | `lib/tina4/auth.rb:100` | `:109` |
| tina4-nodejs | `packages/core/src/auth.ts:108,117` `appendFileSync` | — |

Every one of them calls the file "gitignored" in its own docs. It is gitignored **in the
framework's own repository**. It is not gitignored in a project the CLI scaffolds, because
the template that project gets is written by the Rust CLI:

| Language | `src/init.rs` | Template as shipped |
|---|---|---|
| python | `:626` | `.venv/ __pycache__/ *.pyc *.pyo data/ logs/ secrets/ .env` |
| php | `:694` | `vendor/ data/ logs/ cache/ secrets/ .env` |
| ruby | `:815` | `.bundle/ vendor/ data/ logs/ .env Gemfile.lock` |
| nodejs | `:847` | `node_modules/ dist/ data/ logs/ .env` |

`.env` does not cover `.env.local` — different filename, no pattern relates them. Measured,
not assumed: `.env` returns rc 0 and `.env.local` rc 1 from the same `git check-ignore`
invocation, which is also what proves the instrument can emit both values.

tina4-php's `CLAUDE.md:528` states that "the scaffolded project's `.gitignore` exclude[s]
`.env.local`". That sentence is false against `src/init.rs:694`.

Dispatch is `src/init.rs:588-596`; the writer is `write_file` at `:1434`.

## Reproduction — stock, real binary, populated project

`./prove.sh`. It builds both trees, scaffolds a real project per language, drops a
realistic `.env.local`, and measures. rc 0 = ignored, rc 1 = not.

Stock (`2bb1418`, binary md5 `2907750cfbf944c9`) — identical in all four:

```
.env                        rc=0  .gitignore:8:.env
.env.local                  rc=1
>>> .env.local STAGED by git add -A: 1      <- the secret is committable
```

Fixed (md5 `0e2dce39864e521c`) — identical in all four:

```
.env.local                  rc=0  .gitignore:9:.env.local
>>> .env.local STAGED by git add -A: 0
.env.example                rc=1        (still tracked)
src/routes/sessions/get.py  rc=1        (still tracked)
src/orm/sessions/model.py   rc=1        (still tracked)
tests/fixtures/seed.db      rc=1        (still tracked)
```

## What the fix changes, and what it does not

One line added to each of the four backend templates: `.env.local`. Nothing else.

It deliberately does **not** add `sessions/` or `*.db`. The superseded patch added both to
"match the tina4-python template", and a run of a binary built from it shows what that
costs — these are real measurements from that tree, not a prediction:

```
src/routes/sessions/get.py   rc=0  <- .gitignore:7:sessions/
src/orm/sessions/model.py    rc=0  <- .gitignore:7:sessions/
docs/sessions/readme.md      rc=0  <- .gitignore:7:sessions/
tests/fixtures/seed.db       rc=0  <- .gitignore:9:*.db
```

`src/routes/` and `src/orm/` are directories the scaffolder itself creates
(`src/init.rs:557-568`) and are where a Tina4 project's code lives under file-based
routing. A route group called `sessions` is an ordinary thing to write, and `git add -A`
warns about none of it. `sessions/` is not even load-bearing: the session store defaults
to `data/sessions` (`tina4_python/session/__init__.py:104`) and `data/` was already in the
stock template. A control run — stock template plus `.env.local` alone — closes the leak
with none of these collisions, so the extra lines were never necessary.

`tina4js` is left alone: it writes no `.env`, mints no secret, and its scaffold is
`node_modules/ dist/ *.tsbuildinfo` (run).

## How the guard was established

`scaffold_gitignores_the_dev_secret_file` in `src/init.rs`, beside the existing
`scaffold_binds_a_default_sqlite_database`, which it mirrors. It calls `scaffold_project`
— the real dispatcher — once per language and asserts two things: a sentinel line unique
to that language's own template, and an exact `.env.local` line.

Mutation-tested, each mutation applied to a canonical copy and reverted immediately after:

| Mutation | Result |
|---|---|
| guard on stock templates (no template change) | **RED** |
| revert python / php / ruby / nodejs template, one at a time | **RED** (4 of 4) |
| reroute python / php / ruby / nodejs dispatch arm to another scaffold | **RED** (4 of 4) |
| none (canonical fix) | GREEN |

Suite: stock **221 passed**, fixed **222 passed**, 0 failed.

The sentinel exists because of an attack that succeeded. The first version of the guard
asserted only that a `.gitignore` containing `.env.local` had been written; rerouting the
php dispatch arm to `scaffold_python` left it **green**, because python's template also
satisfies that assertion. The guard was widened, not the fix.

## Residual — stated, not implied

- **An already-scaffolded project is never repaired.** `write_file` (`src/init.rs:1434-1443`)
  returns early when the file exists, printing `⚠ .gitignore already exists, skipping`.
  Run against a project with a pre-existing `.gitignore`: `.env.local` rc **1**, staged
  **1**. A template edit cannot reach these projects; only a check on the framework side,
  where the secret is written, can. That is a separate defect and has not been through a
  reproduction of its own.
- The npm-side node scaffolder (`packages/cli/src/commands/init.ts:112`) already writes
  `.env.local` and is untouched here — the two node scaffolders disagree. **read**
- Not visited: Windows path and case semantics, `.git/info/exclude`, CRLF templates, the
  `tina4 setup` wrapper (`TINA4_INIT_NO_SERVE=1` was used), `cargo test -- --ignored`,
  clippy. No framework was booted to watch `.env.local` appear — the minting is **read**
  from each port's `origin/v3`, not observed at runtime.
- `install_deps` is capped at 45s by the probe. Scaffolding completes before the cap, so
  the `.gitignore` under test is complete; a partially-installed dependency tree is not.

## Incidental, unpursued

- The scaffolder binds `TINA4_DATABASE_URL=sqlite:///app.db` (`src/init.rs:585`), so a dev
  database appears at the project root and no template ignores it. Not a secret, so it is
  not folded into this fix — it is its own question.

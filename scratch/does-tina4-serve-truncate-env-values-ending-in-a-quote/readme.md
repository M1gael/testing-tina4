# Does `tina4 serve` truncate `.env` values that end in a quote?

Yes. On the default-port path only. Reported as tina4stack/tina4#27 by @ChanBos.

Run against: **tina4 CLI 3.8.88** (released binary), CLI source at `origin/main` `3a4377d`,
tina4-php **3.13.134** (`origin/v3` `e0df3a97`).

## What happens

`tina4 serve` with no `-p`/`--port` parses `.env` itself and injects it into its own process
environment, which the language server inherits. Every value is passed through

```rust
let value = value.trim().trim_matches('"').trim_matches('\'');
```

`trim_matches` strips **every** matching character from both ends, not one wrapping pair. So a
value whose own content ends in `'` loses it — and loses a whole run of them.

```
.env                                              child process sees
TINA4_CSP="default-src 'self'; form-action 'self'" -> default-src 'self'; form-action 'self
PLAIN_TRAILING_SQ=form-action 'self'               -> form-action 'self
TRIPLE_SQ=abc'''                                   -> abc
QUOTED_EMPTY="''"                                  -> (empty)
SQ_WRAPPED='hello world'                           -> hello world          (correct)
DQ_WRAPPED="hello world"                           -> hello world          (correct)
ENDS_DQ='say "hi"'                                 -> say "hi"             (correct)
```

`ENDS_DQ` survives because the double-quote trim runs first, while the value is still wrapped in
single quotes and so has no bare `"` at either end. Only a trailing single quote is exposed.

End to end, through the real CLI against a real tina4-php app (`php-end-to-end/`):

```
tina4 serve            Content-Security-Policy: default-src 'self'; form-action 'self
tina4 serve -p 8795    Content-Security-Policy: default-src 'self'; form-action 'self'
```

`form-action 'self` is not a valid source expression, so the browser drops the directive and
falls back to blocking the form post. That is the login failure in the issue.

## Mechanism

| | |
|---|---|
| `tina4/src/main.rs:628` | serve's own `.env` parse. Inside the `port.unwrap_or_else(...)` closure opened at `:617`, so it runs **only when `--port` was omitted** |
| `tina4/src/env_config.rs:298` | `read_env()`, used by `tina4 env` — same expression, and this one writes back |
| `tina4/src/main.rs:985` | `read_dotenv_bool_from()` — same expression, but the value is lower-cased and compared against `true/1/yes`, so truncation cannot change the outcome |

## Two things the issue does not say

**1. `-p` does not merely avoid the truncation — it injects nothing at all.** Every `.env` key
is unset in the child on that path:

```
serve            TINA4_CSP=default-src 'self'; form-action 'self   SQ_WRAPPED=hello world ...
serve -p 8795    TINA4_CSP=<unset>                                 SQ_WRAPPED=<unset> ...
```

The two invocations hand the framework different environments. It only looks like a
one-character difference because tina4-php reads `.env` itself as a fallback; the inherited
value wins when there is one. A port flag deciding whether the CLI exports the project's
environment is its own contract question.

**2. `tina4 env --sync` persists the damage to disk, and it compounds.** `read_env()` truncates,
`write_env()` at `env_config.rs:306` writes `{key}={value}\n` with **no quoting**, and `--sync`
writes the whole file back — no `.env.bak` (only `tina4 env --migrate` makes one).

```
.env before       ENDS_DQ='say "hi"'     QUOTED_EMPTY="''"
after 1st --sync  ENDS_DQ=say "hi"       QUOTED_EMPTY=
after 2nd --sync  ENDS_DQ=say "hi        QUOTED_EMPTY=
```

A value that survived the read is written back unquoted, which exposes its trailing `"` to the
next read. Every run eats one more character. This is the more serious of the two: the serve
case is transient, this one edits the user's file.

## Reproduce

```
./prove.sh                       # CLI-only, no framework, no network. exit 0 = defect present
BIN=/path/to/tina4 ./prove.sh
```

`app.py` is a stand-in for the language server: `tina4 serve` spawns `python3 app.py --managed`,
and the child inherits the CLI's environment, so dumping that environment shows exactly what the
framework would have been handed. `requirements.txt` naming `tina4_python` is what makes
`detect::detect_language()` call this a Python project.

`php-end-to-end/` is the same defect observed on the wire: a real tina4-php app (framework
classes symlinked out of `gitdir/tinaforks/tina4-php`, nothing installed) served by the real
CLI, compared on the `Content-Security-Policy` response header.

## Bounds

- Reproduced on Linux. The parse is platform-independent; the issue reports it on Windows 11.
- Directly observed on the Python spawn path and end to end on the PHP one. Ruby and Node.js
  inherit the same process environment from the same closure — read, not run.
- Not tested: whether any port's own dotenv loader overrides an inherited value. tina4-php does
  not — that is what the header comparison above shows.

## The fix

Branch `fix/env-values-keep-their-own-trailing-quote` in `gitdir/tinaforks/tina4`, cut from
upstream `main` `3a4377d` (fork fast-forwarded onto it first). Worktree
`~/.cache/tina4-worktrees/fcli27`, uncommitted. `fix.patch` here is the diff.

Two helpers in `src/env_config.rs`, used at the two evidenced sites:

- `unquote_env_value` — strips at most one matching pair of wrapping quotes, where the old
  `trim().trim_matches('"').trim_matches('\'')` stripped every quote at both ends. A pair counts
  only when both ends are the SAME character, so `'say "hi"'` keeps its inner double quotes.
  Used at `src/main.rs:628` (serve) and `src/env_config.rs` `read_env` (`tina4 env`).
- `quote_env_value` — renders a value so that reading the file back yields it exactly. A value is
  quoted **only** when writing it bare would change it, which is exactly when
  `unquote_env_value` would alter it: surrounding whitespace, or a matching pair at both ends.
  `form-action 'self'` and `say "hi"` stay bare.

The wrapping quote is not a free choice, and getting this wrong was a hole found on cold read
rather than by a test. The frameworks read this file too: `Tina4/DotEnv.php` treats a
double-quoted value as escapable and interpolating (`\x` is `x`, `${VAR}` is substituted) and a
single-quoted value as literal. Wrapping ` say "hi" ` in double quotes would have been read by
PHP as ` say `. So a value carrying `"`, `\` or `${` is wrapped in single quotes instead. A value
that needs quoting *and* holds both quote characters cannot be represented without an escaping
scheme the readers do not all share — it is left bare, which is what happens today, and a test
pins that as the known limit.

**Deliberately not in the fix:** `src/main.rs:985`, the third copy of the same expression. Its
result is lower-cased and tested for membership of `{true, 1, yes}`, so truncation cannot change
the answer for any well-formed value; switching it would change what a malformed value means, and
no report covers that. A comment now says so at the site.

### What gates what

Every piece was reverted on its own against the shipped source and had to turn something red
alone. Restores were file copies — `git checkout --` restores upstream, which silently discards
the whole fix and makes the next "red" prove nothing.

| Reverted | Turns red |
|---|---|
| serve's call site (`main.rs:628`) | `serve_without_a_port_flag_exports_values_unharmed` only |
| `read_env`'s call site | `env_sync_leaves_every_value_exactly_as_it_found_it` only |
| `write_env`'s quoting | `env_sync_leaves_every_value_exactly_as_it_found_it` only |
| `unquote_env_value`'s body | 7 of 10 unit tests, and both entry-point tests |
| the wrapping-quote choice | `the_wrapping_quote_is_one_the_framework_parsers_read_literally`, `a_value_holding_both_quote_characters_is_left_bare` |

`tests/env_dotenv_values.rs` goes through the shipped binary at both entry points — `tina4 env
--sync` twice over on a real file, and a real `tina4 serve` whose language server is a stand-in
`python3` on a prepended PATH that dumps the environment it was handed. It reads `.env` back with
its own parser rather than the CLI's, since a test that shares the parser cannot see the parser be
wrong. Full suite: 231 unit + 8 integration, green.

### Residual gaps

- `tina4 env --sync` still rewrites and regroups the file, so quotes the user wrote around a value
  that does not need them are dropped. The value is unchanged and the second run is a fixed point;
  the formatting churn is pre-existing.
- A value containing a newline cannot be represented at all. Nothing in the CLI can produce one.
- The framework-parser reasoning is read from `Tina4/DotEnv.php`; the written files were not fed
  back through PHP, Python, Ruby or Node to confirm.
- `cargo fmt` and `clippy` are not installed in this environment, so neither was run.
- `tina4-python/tina4_python/dev_admin/__init__.py:1692` carries the same expression
  (`val.strip().strip('"').strip("'")`). Not investigated, not in this fix — a separate row.

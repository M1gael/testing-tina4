# Does `tina4 init` gitignore the file it writes the JWT secret into?

**No.** On the released Rust CLI the Python scaffold's `.gitignore` does not list
`.env.local`, which is exactly the file the framework mints the JWT signing secret into on
first dev run. A fresh project therefore stages and can commit its own signing secret.

Ledger: `f-cli-01` (was `CLI-FW-13`). Measured **2026-09-21**.

- **tina4 CLI (Rust):** `origin/main` @ `2bb1418`, `version = "3.8.88"` (`~/gitdir/tinaforks/tina4`).
- **tina4-python:** branch `v3`, current (`~/gitdir/tinaforks/tina4-python`).

The `.gitignore` is emitted by the **Rust CLI**, not by the Python package — so the guarantee
the Python source documents is not the guarantee the scaffolded user receives.

---

## Mechanism (to file:line)

1. **The scaffold writes an incomplete ignore file.** `tina4 init python <name>` calls
   `scaffold_python()` (`tina4/src/init.rs:599`), which writes a fixed `.gitignore` literal at
   **`src/init.rs:626-630`**:

   ```
   .venv/ __pycache__/ *.pyc *.pyo data/ logs/ secrets/ .env
   ```

   No `.env.local`. (READ + RUN — string read in source, and emitted verbatim by the built
   3.8.88 binary; see before/after below.)

2. **The framework then writes the secret into `.env.local`.** On first dev run
   `ensure_dev_secret()` (`tina4-python/tina4_python/auth/__init__.py:101`) mints a random
   `TINA4_SECRET` and persists it to `.env.local`; `Auth()` reads `TINA4_SECRET` from the
   environment to sign JWTs (`auth/__init__.py:44,57`). The framework asserts three times that
   this is safe *because the file is gitignored* — `auth/__init__.py:95` ("automatically into
   .env.local (gitignored)"), `:107`, `:117` ("only ever write to `.env.local` (gitignored) —
   never `.env`"). (READ, current `v3`.)

3. **`.env` does not cover `.env.local`.** A gitignore line `.env` matches only the path
   component `.env`, never `.env.local` — confirmed by `git check-ignore` (RUN), not by eye.

4. **The two scaffold templates disagree and the wrong one ships.** The Python package's own
   template is already correct — `tina4-python/tina4_python/cli/__init__.py:658-663` writes
   `.env\n.env.local\n__pycache__/\n*.pyc\n.venv/\ndata/\nlogs/\nsessions/\nsecrets/\n*.db\n`
   (has `.env.local`, plus `sessions/` and `*.db` the CLI omits) — but `tina4 init` uses the
   Rust template, which is missing all three. (READ, current `v3`.)

Note: the CLI writes `.gitignore` only when absent, so a project scaffolded once keeps the
unsafe file permanently.

---

## Before / after (real binaries, `git check-ignore`; rc 0 = ignored, rc 1 = NOT ignored)

Both runs: `tina4 init python probe`, then in the project a real `.env.local` (fake 64-hex
secret), a user-authored `.env.example`, an `app.db`, and `sessions/sess1` were created and
tested against the generated `.gitignore`.

| file | STOCK 3.8.88 | FIXED | meaning |
|---|---|---|---|
| `.env.local` (the secret) | **rc 1 — staged** | rc 0 — ignored | the leak, closed |
| `.env` | rc 0 | rc 0 | unchanged |
| `.env.example` (want tracked) | rc 1 | **rc 1** | not over-ignored |
| `app.py` (source) | rc 1 | rc 1 | not over-ignored |
| `app.db` | rc 1 | rc 0 | bonus gap closed |
| `sessions/sess1` | rc 1 | rc 0 | bonus gap closed |

STOCK `git add -An` staged `.env.local` (secret committed). FIXED did **not** stage
`.env.local`, and still staged `.env.example`, `app.py`, `pyproject.toml`.

---

## The fix (`fix.patch`, uncommitted in `~/.cache/tina4-worktrees/fcli01-fixed`)

`tina4/src/init.rs:626` — reconcile the Python scaffold template with the Python package's:

```
-        ".venv/\n__pycache__/\n*.pyc\n*.pyo\ndata/\nlogs/\nsecrets/\n.env\n",
+        ".venv/\n__pycache__/\n*.pyc\n*.pyo\ndata/\nlogs/\nsessions/\nsecrets/\n*.db\n.env\n.env.local\n",
```

Plus two regression guards:
- `src/init.rs` unit test `python_scaffold_gitignores_the_secret_file` — calls the real
  `scaffold_project("python", …)` and asserts the written `.gitignore` lists `.env.local`.
  Runs in normal CI (no network). **RED on stock (`rc 101`), GREEN on fixed.**
- `tests/scaffold.rs` — the existing gated `init_python_scaffolds_runnable_project` now also
  asserts the generated `.gitignore` covers `.env.local` (end-to-end, `--ignored`).

`cargo test --bin tina4`: **222 passed, 0 failed** (stock had 221; +1 is the new guard).

---

## Attacked

- **Over-ignore?** `.env.local` matches only that exact file; `.env.example` and `app.py`
  remain tracked on the fixed scaffold (RUN, table above). `sessions/` / `*.db` are dirs and a
  db-suffix — they do not hide any file the template's own project needs tracked.
- **Already fixed upstream?** No — reproduced on `origin/main` @ `2bb1418` (3.8.88), the
  current tip (RUN).
- **Does `.env` already cover it?** No — `git check-ignore .env.local` is rc 1 under the stock
  template while `.env` itself is rc 0 (RUN).
- **Does the secret really land in `.env.local`?** Yes on the Python path — documented and
  coded at `auth/__init__.py:101/117` (READ). Other ports (php/ruby/node) also omit `.env.local`
  from their templates, but whether their frameworks auto-mint into `.env.local` was **not**
  verified here — out of scope for `f-cli-01` (py-only). Flagged, not fixed.

## Sufficient?

Closes the leak for **newly** scaffolded Python projects. **Residual paths (not closed by a
template edit):**
1. Projects scaffolded before the fix keep the unsafe `.gitignore` (CLI writes it only if
   absent). The ledger's suggested belt-and-braces — have `ensure_dev_secret()` refuse/warn
   when the target's ignore rules don't actually cover `.env.local` — is the only thing that
   protects an already-scaffolded repo; it lives in tina4-python, not this patch.
2. php/ruby/node templates share the omission (see Attacked) — separate finding if their
   frameworks turn out to write a secret there.

## Reproduce

`./prove.sh` — reproduces stock (leak) and fixed (safe) from the exact template bytes via
`git check-ignore`, no build required, and prints a verdict. Set `TINA4_BIN=/path/to/tina4`
to additionally drive a real binary end-to-end.

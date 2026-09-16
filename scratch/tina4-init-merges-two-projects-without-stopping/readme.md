# `tina4 init` merges a second project into an existing one, silently

**Pinned:** tina4 CLI **3.8.87**, released `tina4-linux-amd64` (sha256 verified against the
release `SHA256SUMS`), upstream source `origin/main` **`6a9b68e`**. Linux, node v22.22.2,
npm 10.9.7, uv 0.11.14. Reported by @Caleb on Windows at the same CLI version.

`./prove.sh` — exit **1** reproduced, **0** fixed, **2** the proof itself could not run.

## The behaviour

`tina4 init <lang> <path>` where `<path>` already holds a Tina4 project of a *different*
language warns twice, proceeds anyway, and exits **0**:

```
⚠ Directory already exists: .../mixing-test — using it
⚠ .gitignore already exists, skipping
```

Both stacks then occupy one directory. Observed, this tree, stock 3.8.87:

```
app.py  pyproject.toml  uv.lock  .venv/          <- python
package.json  package-lock.json  node_modules/   <- tina4js
vite.config.ts  tsconfig.json  index.html
src/orm  src/public  src/scss  src/templates     <- python's src layout
src/components  src/pages  src/routes  main.ts   <- tina4js's src layout, same src/
```

## Mechanism

`src/init.rs:519-524` — the existing-directory branch warns and falls through. There is no
check for an existing project, no prompt, and `init` has no `--force`/`--yes` flag to gate
(`tina4 init --help`, run: only `-h`).

```rust
fn create_project_dir(path: &str) {
    let p = Path::new(path);
    if p.exists() {
        println!("  {} Directory already exists: {} — using it", icon_warn().yellow(), path);
    } else {
        ...
```

`scaffold_project` then writes on top. It has *file*-level collision awareness and no
*project*-level awareness.

## The sharp end: the second project loses its ignore rules

`.gitignore already exists, skipping` means the python project inherits the tina4js file.
Run, this tree — python's own `.gitignore` versus what the merged project actually has:

```
python alone            merged project
.venv/                  node_modules/
__pycache__/            dist/
*.pyc                   *.tsbuildinfo
*.pyo
data/
logs/
secrets/
.env
```

All eight python rules are gone, `.env` and `secrets/` among them. In the merged project
`git add -A` stages `.env`.

## Not reproduced / not covered

- Only the **js-then-python** order was run, which is @Caleb's order. The other five ordered
  pairs across python/php/ruby/nodejs/js were not visited.
- Same-language re-init (`python` onto a python project) was not tried.
- Windows was not tried here; @Caleb's screenshots show identical output and an identical
  merged tree, so the behaviour is not platform-specific.

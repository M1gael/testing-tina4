# `tina4 build` is documented as compiling to dist/; it builds a Docker image

Ledger row `d-cli-03`. Rebuilt 2026-10-29 (the 10-22 proof dir was lost).

Pinned to: docs `tina4-documentation` origin/main 01c4225, book `tina4-book` origin/main 20b1006,
tina4-nodejs b447252, tina4-ruby 74aa1f5, tina4-python efa826a3, tina4-php b321c1fc (origin/v3),
tina4 CLI ebb846b built with cargo (`tina4 3.8.112`). Docker is not installed on the host; a
`docker` shim on PATH records argv and exits 0.

## The pages and what they say

- nodejs 31-cli §14 and 34-deployment §3: "Compiles TypeScript to JavaScript", fake output
  `Compiled 47 TypeScript files / Output: dist/`, then `node dist/app.js`.
- nodejs 34-deployment §13: a plain-server `set -e` deploy script runs `tina4 build`.
- ruby 31-cli: `tina4 build  # Bundle and minify JavaScript` / `# Run all build steps`.
- ruby index: `tina4 build  # Compile SCSS, bundle assets for production`.
- general/cli.md: "Build production front-end assets."
- Book: the same text in book-3-ruby 31-cli and book-4-nodejs 31-cli, 34-deployment.

## Mechanism (read; line numbers at the pinned tips)

- tina4 `src/main.rs:569-581`: `Commands::Build` runs `scss::compile_dir("src/scss",
  "src/public/css", minify)` then `delegate_command(["build"])` (`:1790`), which runs the
  framework CLI (`resolve_cli`, `:1687`) and exits with its code.
- nodejs `packages/cli/src/commands/build.ts:64` `buildImage`; ruby `lib/tina4/cli.rb:1386`
  `cmd_build`; python `tina4_python/cli/__init__.py:1187` `_build`; php `bin/tina4php:5738`
  `tina4Build`. All four: no Dockerfile -> exit 1; no docker on PATH -> exit 1; else
  `docker build -t <cwd-name>:latest -f Dockerfile .`. None writes dist/.

## Run (`behaviour.sh`, output in `behaviour.log`)

nodejs and ruby, each through the framework CLI directly and through `tina4 build`:
no Dockerfile -> rc 1, docker never called; Dockerfile + shim -> rc 0, argv
`build -t <app>:latest -f Dockerfile .`; Dockerfile, no docker -> rc 1. dist/ absent in every
case. `tina4 build` also writes `src/public/css/app.min.css` first. The §13 `set -e` script on a
no-docker server stops at `tina4 build` (rc 1, migrate never reached). `tina4 deploy docker`
writes a Dockerfile that `tina4 build` then uses (`Run: docker run -p 7148:7148 ndapp:latest`).
python and php were read, not run.

## Doc check (`prove.sh`) and gate (`gate.sh`)

Stock docs FAIL wrong=13 missing=5; stock book FAIL wrong=11 missing=3; fixed docs and fixed
book PASS. Reverting each piece of the held patch alone (each file; each 34-deployment hunk)
turns it red: docs 6/6, book 4/4 (`gate-docs.log`, `gate-book.log`).

## Re-run

```bash
V=~/.cache/tina4-worktrees/verify-1029; W=$V/d-cli-03; P=~/.cache/tina4-worktrees
CLI=$V/target/release/tina4 ND=$W/nodejs-run RB=$V/fw-ruby WORK=$W ./behaviour.sh
DOCS=$W/stock-docs ./prove.sh; BOOK=$W/stock-book ./prove.sh     # rc 1
DOCS=$W/fixed-docs ./prove.sh; BOOK=$W/fixed-book ./prove.sh     # rc 0
KIND=docs FIXED=$W/fixed-docs PATCH=$P/docfix-dcli03-docs.fix.patch WORK=$W ./gate.sh
KIND=book FIXED=$W/fixed-book PATCH=$P/docfix-dcli03-book.fix.patch WORK=$W ./gate.sh
```

`$W/nodejs-run` is a copy of fw-nodejs with node_modules hard-linked from
`dcli04-stock-nodejs` (same b447252 tree and lockfile) and `packages/cli/dist/bin.js` built with
the package's own esbuild command.

## Left outside the fix

- nodejs 34-deployment §4 and 35-complete-app Dockerfiles `COPY dist/` and run `node dist/app.js`;
  nothing on the host writes dist/, and the fixed §3 points at §4's Dockerfile. systemd
  `ExecStart .../dist/app.js` and the cluster `node dist/app.js` lines have the same gap. The
  `tina4 deploy docker` template compiles inside the image instead.
- 34-deployment :142/:864/:888 and 35-complete-app :1302 run `tina4 build` and then
  `docker build`/`docker compose build`: two builds, redundant but not wrong.
- `tina4 --help` (`src/main.rs:214`) and the tina4-cli skill (`.claude/skills/tina4-cli/SKILL.md:110`,
  `references/commands.md:68`, also copied into docs `public/skills/3.13.146+`) still say
  "Build production front-end assets (SCSS minify + bundle)".

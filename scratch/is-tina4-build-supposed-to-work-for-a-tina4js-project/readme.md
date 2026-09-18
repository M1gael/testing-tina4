# Is `tina4 build` supposed to work for a tina4js project?

**Answer: yes for the CLI, no for the documentation — and they disagree.** The general CLI
reference promises `tina4 build` for every project type and names tina4-js as a supported one
two rows above; the tina4js book never mentions `tina4 build` and documents `npm run build`
instead. The command is reachable, advertised, and fails. It is a defect, but a narrower one
than "tina4js cannot be built" — the documented path works.

Pinned to tina4 CLI `2bb1418` = **3.8.88**, the current release. All runs on Linux, rustc
1.98.0, against `tina4-3.8.88-stock` in this directory — a binary built from `origin/main` with
no local changes, so no run here can silently use a patched tree. It is **gitignored**, being a 125 MB debug build; rebuild it with:

```console
$ cd ~/gitdir/tinaforks/tina4 && git stash && cargo build && git stash pop
$ cp target/debug/tina4 <this-dir>/tina4-3.8.88-stock
```

## What was run

Three fixtures under `fixtures/`, each the minimum that makes `detect_language()` pick that
language. Every run under `env PATH=/usr/bin:/bin` — **this machine has a global Vite at
`~/.npm-global/bin/vite` which masks the whole defect**, and the first attempt at this passed
for exactly that reason.

| fixture | `tina4 build` | reached the framework CLI? |
|---|---|---|
| `php/` | `TINA4PHP-STUB args=build`, exit 0 | yes |
| `ruby/` | `✗ No Dockerfile found.` …, exit 1 | yes — that text is the real `tina4ruby` gem's own refusal, not the CLI's; it is absent from `git grep` over `origin/main:src/` and reproduces identically under `bundle exec tina4ruby build` |
| `tina4js/` | `✗ Failed to run vite build: No such file or directory (os error 2)`, exit 1 | **no — never launched** |

So the delegate mechanism itself works. tina4js is the outlier, and "`tina4 build` is broken for
everyone" is dead.

### Both directions, in one directory

`fixtures/tina4js/` holds `node_modules/.bin/vite` — the real layout — and a `package.json`
whose `build` script is `vite build`, exactly what `tina4 init js` scaffolds.

```console
$ env PATH=/usr/bin:/bin npm run build
> vite build
VITE-STUB args=build                                          # exit 0

$ env PATH=/usr/bin:/bin ./tina4-3.8.88-stock build
✗ Failed to run vite build: No such file or directory (os error 2)   # exit 1
```

Same directory, same `PATH`, same Vite. Supply the cause and it fails; remove it — by launching
through npm, which prepends `node_modules/.bin` — and it succeeds. Necessary and sufficient.

## Mechanism

`resolve_cli` (`src/main.rs:1330`) has arms for php, python, ruby and nodejs and **no arm for
tina4js**, so a tina4js project falls to `_ => (info.cli_name().into(), vec![])`, and
`detect.rs:19` maps `tina4js` to `"vite"`. `delegate_command` (`src/main.rs:1394`) spawns that
name. Vite installs into `node_modules/.bin`, which is on `PATH` only inside an `npm run`
script — so the name cannot resolve, on any platform.

`Commands::Build` (`src/main.rs:472`) routes there deliberately: `delegate_command(vec!["build"])`.

**This is not the `f-cli-21` Windows shim problem and `console::resolve_cmd` does not fix it** —
there is nothing on `PATH` to find. Verified by running both binaries: identical output.

## Why this counts as a defect, not a decision

The codebase guards tina4js where it means to. `main.rs:446` routes `Commands::Ai` through
`is_tina4js_project()`; `main.rs:881` skips the reload watcher for it; `78d876a` gave serve its
own `tina4js_serve_command()`. `Commands::Build` has no such guard. The habit exists; this site
does not use it.

The author anticipated a delegate failure and documented the decision at `main.rs:479`:

> Try the language CLI's build subcommand; if the language doesn't have one, the delegate exits
> non-zero and we surface that to the user — they get to decide whether to wire one up.

That decision does **not** cover this case. It anticipates *the framework CLI having no `build`
subcommand* — a child that runs and exits non-zero. Here the child never runs, and Vite does
have a `build`; `tina4 init js` writes `"build": "vite build"` into the scaffold itself
(`init.rs:924`).

`79b1fc0` (v3.8.22, 2026-05-05), which wrote this body, is titled *"make 7 documented-but-fake
commands real"* and says every command in it *"was already promised somewhere in tina4-book /
tina4.com / release notes."* tina4js support predates it (`ce98a47`, 2026-04-02).

## What the documentation says

| where | says |
|---|---|
| `tina4-documentation/docs/general/cli.md:37` | `tina4 build` — "Build production front-end assets." No language qualifier. Two rows above, `tina4 init` — "Create a project for Python, PHP, Ruby, Node.js, or **tina4-js**." |
| clap, `src/main.rs:162` | "Build production assets (SCSS minify + bundle for the front-end)" |
| `docs/js/01-getting-started.md:357` | Production build — `npm run build` |
| `docs/js/16-vibe-coding-with-ai.md:36` | "Build and test commands — `npm run build`, `npm run test`, `tina4 serve`" — mixes them deliberately: serve via tina4, build via npm |
| `book-5-javascript` | same, `npm run build` throughout; `tina4 build` appears nowhere in it |

The js book and the general reference disagree. A tina4js user reading the general command map
— which names their project type in the same table — is told a command that cannot work.

The tina4-js **skill**'s `npm run build` is not evidence either way: `SKILL.md:28-31` is about
building the tina4-js *library's* IIFE bundle into `dist/`, not a user's app.

## Warrants

- **Run:** every row of both tables above; the stock-vs-fixed binary comparison; the ruby
  message's origin.
- **Read:** `resolve_cli`, `detect.rs:19`, `Commands::Build`, `init.rs:924`, the four doc
  sources, `79b1fc0`, `78d876a`.
- **Inferred:** on Windows this prints `program not found` rather than `No such file or
  directory (os error 2)` — Rust's Windows-only string, the same one `f-cli-20` reported. Not
  run. Confirmed by running `tina4 build` on a Windows tina4js project.

## Bounds

- **Not visited:** Windows, at all. The python and nodejs arms of `tina4 build` (php and ruby
  stand in for them). A project scaffolded by a real `tina4 init js` with a real Vite install —
  these fixtures are hand-made with a shell stub, which proves the `PATH` mechanism but not that
  real Vite builds.
- **Scope of the negative** "no documentation tells a tina4js user to run `tina4 build`":
  `grep -rn` for `tina4 build`, `npm run build`, `vite build` over `tina4-book/` and
  `tina4-documentation/` (`.md`, `.html`, `.twig`). tina4.com itself was not crawled — that is
  `documentation-testing/`'s job, not this one.
- **What would change the answer:** a tina4js arm in `resolve_cli`, or the general CLI table
  being scoped by language. Either one settles it in the opposite direction from the other.

## Found on the way, unpursued

- `install_production_server` (`main.rs:1010`) reports Vite "already installed" for tina4js and
  comments "uses vite build + preview", but `serve --production` then starts the **dev** server
  at `main.rs:1280`, not `vite preview`.
- `tina4-js` ships its own `bin/` — still never checked for the same bare-spawn pattern, which
  is the open `js:?` on `f-cli-20`.

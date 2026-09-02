# The js scaffold emits code its own tsconfig cannot type

`tina4 init js <name>` writes a `src/main.ts` that uses `import.meta.glob` and
`import.meta.env`, and a `tsconfig.json` that can type neither. A brand new project fails
`tsc --noEmit` on three lines the generator itself just wrote.

Ledger rows: **`f-cli-02`** (`src/main.ts`), **`f-cli-03`** (`vite.config.ts`), **`f-cli-04`**
(the second scaffolder still carries defects the first one fixed).

Reported 2026-09-02 by a developer scaffolding a throwaway project, who asked whether the
omission was deliberate before filing. It is not.

## Versions

Everything below was run on **2026-09-02** against:

| | |
|---|---|
| `tina4` CLI | **3.8.77** installed; source re-read at upstream **3.8.78** |
| `tina4js` | **1.7.0** (npm `latest`) |
| scaffolded | vite 8.2.2 · vitest 4.1.11 · typescript 5.9.3 |

`src/init.rs` is byte-identical between 3.8.77 and 3.8.78, and all nine literal templates in
`scaffold_tina4js()` extracted from upstream source match what the installed binary wrote. The
defect is live on the newest release.

## Run it

```
./prove.sh          # exit 0 = stock broken, fix closes it, fix does not leak
```

Self-contained: scaffolds into a temp directory with the `tina4` on `PATH`, never touches the
fork. Needs npm and network. Exit 2 means something stopped matching and the ledger rows need
re-reading before they are trusted.

## Mechanism

Vite adds `glob` and `env` to `ImportMeta`. TypeScript learns them only from `vite/client`,
which the scaffold never pulls in — `vite/client` and `vite-env` appear nowhere in the whole
upstream `tina4` tree, nor in tina4-js, tina4-documentation or tina4-book.

| what | where |
|---|---|
| writes `import.meta.glob` twice and `import.meta.env.DEV` once | `src/init.rs:1068-1069`, `:1074` |
| writes a tsconfig with no `types` and no `vite-env.d.ts` | `src/init.rs:946-962` |
| `"include": ["src/**/*.ts"]` — so `tsc` never opens `vite.config.ts` | `src/init.rs:961` |
| `defineConfig` from `vite`, then passes a vitest `test` block | `src/init.rs:975` |

**Why it shipped.** Nothing in a scaffolded project ever runs `tsc`. `"build"` is `vite build`,
which strips types through esbuild without checking them, and `"test"` is vitest. No CLI
subcommand runs it either. Contrast `scaffold_nodejs()`, whose `"build": "tsc"`
(`src/init.rs:860`) would have caught it. The errors were only ever editor squiggles.

## Before

```
src/main.ts(11,13): error TS2339: Property 'glob' does not exist on type 'ImportMeta'.
src/main.ts(12,13): error TS2339: Property 'glob' does not exist on type 'ImportMeta'.
src/main.ts(17,17): error TS2339: Property 'env' does not exist on type 'ImportMeta'.
```

and, in the inferred project an editor falls back to for `vite.config.ts`:

```
vite.config.ts(2,25): error TS2307: Cannot find module 'path' or its corresponding type declarations.
vite.config.ts(9,32): error TS2339: Property 'dirname' does not exist on type 'ImportMeta'.
vite.config.ts(12,3): error TS2769: No overload matches this call.
    Object literal may only specify known properties, and 'test' does not exist in type 'UserConfigExport'.
```

`npm run build` and `npm test` are **green** on all of that.

## After

```
$ npm run typecheck
> tsc --noEmit && tsc -p tsconfig.node.json --noEmit
$ echo $?
0
```

## Three fix sites, and why only one is right

**1. `"types": ["vite/client"]` in tsconfig.** Clears the errors. `types` is not additive, so
it also switches off automatic inclusion of every other `@types/*` package:

```
src/probe-node.ts(1,21): error TS2591: Cannot find name 'process'.
```

with `@types/node` installed. Rejected.

**2. `/// <reference types="vite/client" />` in `tina4js`'s own `dist/index.d.ts`.** Also
works — verified, exit 0 — and would fix every consumer at once. But it forces Vite's ambient
env and asset declarations on consumers that do not use Vite, and breaks them outright when
`vite` is absent:

```
node_modules/tina4js/dist/index.d.ts(1,23): error TS2688: Cannot find type definition file for 'vite/client'.
```

under `--skipLibCheck false`. A scaffold can guarantee `vite` is a devDependency; a library
cannot guarantee it of its consumers. Rejected.

**3. `src/vite-env.d.ts` + a second tsconfig.** Taken.

## The trap inside the fix

`vite.config.ts` imports `path` and uses `import.meta.dirname`, so it needs `@types/node`. Add
that to a single flat tsconfig and Node's globals become ambient in the browser tree, where
`setTimeout` stops being the DOM one:

```
src/probe-dom.ts(1,7): error TS2322: Type 'Timeout' is not assignable to type 'number'.
```

That is correct browser code failing to compile — the same class of side effect that rules out
fix 1, reintroduced by the fix for `f-cli-03`. Section 6 of `prove.sh` is the regression.

The split fixes it: the browser project sets `"types": []` and takes no ambient types, and
`vite.config.ts` moves to its own `tsconfig.node.json`, which does. **An explicit triple-slash
reference still resolves under `"types": []`** — that composition property is the whole reason
`src/vite-env.d.ts` works where a `types` array would not, and it is what makes the split
possible at all.

## Where the fix lives

Two scaffolders, not one:

| generator | repo | branch |
|---|---|---|
| `tina4 init js` | `gitdir/tinaforks/tina4` — `src/init.rs` | `fix/js-scaffold-typechecks-clean` |
| `npx tina4js create` | `gitdir/tinaforks/tina4-js` — `bin/tina4.js` | `fix/scaffold-typechecks-clean` |

Neither is pushed and neither is filed.

`f-cli-03` applies only to the first: the second's `vite.config.ts` carries no `test` block.
`f-cli-04` — that the two generators have drifted — is deliberately **not** in either branch.

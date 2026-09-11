# The agent listens on every interface, with no auth and a shell tool

`2026-09-11 · baseline-main v0.2.0-290-gd719fc3 · scratch v0.2.0-295-g9d159fe · node v22.22.2`

Ledger row: `sec-01` (harness, high, open since 2026-08-26).

## The behaviour

```ts
// app.ts:7430 on d719fc3
startServer({ basePath: HERE, port: SHELL_PORT });     // no host
```

No host means tina4-nodejs decides
(`node_modules/tina4-nodejs/packages/core/src/server.ts:404-411`):

```ts
const defaultHost = isTruthy(process.env.TINA4_DEBUG) ? "127.0.0.1" : "0.0.0.0";
const host = config?.host ?? process.env.TINA4_HOST ?? process.env.HOST ?? defaultHost;
```

The framework's default is loopback **only in dev mode**. DISTRIBUTION.md:106 runs production mode
deliberately, so the dev toolbar and `/__dev` assets stay out — which means `TINA4_DEBUG` is
unset, which means `0.0.0.0`.

There is no authentication anywhere (`grep -c 'Authorization\|bearer\|authenticate' app.ts` = 0;
README:150 *"no authentication and can execute shell commands"*), and `run_shell` executes
arbitrary commands. Anyone who can reach the port has code execution as the user, plus
`read_file` / `write_file` over the project tree.

## What the docs already say, and why it is still a defect

DISTRIBUTION.md:112 says *"Set `TINA4_HOST=127.0.0.1` before launching a distributed binary."*
So the exposure is known and documented.

It is documented as a **manual step**. A binary opened from Finder or the Dock — the exact launch
the `PATH` widening at `app.ts:143` exists to support — sets no environment at all, and gets the
open default. Safe requires a terminal; unsafe is what double-clicking does.

## Reproduce

```sh
./prove.sh                                                   # untouched main -> exit 1
./prove.sh …/tina4-simple-agent-work/scratch                 # patched        -> exit 0
./attack.sh …/tina4-simple-agent-work/scratch                # 8 cells
```

Everything runs inside `unshare -rn` — a network namespace with no route off this machine — so an
unauthenticated shell is never on a real LAN even for the seconds the probe needs. `10.99.0.1/32`
is added to `lo` purely as a non-loopback address to dial: a server bound to `127.0.0.1` refuses
it, a server bound to `0.0.0.0` answers it. `HOME`, `TINA4_STATE_DIR` and `TINA4_PROJECTS_ROOT`
are all redirected to a throwaway (`TINA4_STATE_DIR` alone does not isolate global secrets —
`sec-03`).

On `d719fc3`:

```
BIND      0.0.0.0:8796
LOOPBACK  200
OFF-LOOP  200
BODY      {"sessions":[]}
AUTHHDR   200
```

`OFF-LOOP 200` is the finding: a request from a non-loopback address, with no credentials, is
answered.

## The fix

`app.ts` — decide the host here instead of letting a framework default decide it:

```ts
const EXPOSE = /^(1|true|yes|on)$/i.test(String(process.env.TINA4_EXPOSE ?? ""));
const SHELL_HOST = process.env.TINA4_HOST ?? process.env.HOST ?? (EXPOSE ? "0.0.0.0" : "127.0.0.1");
startServer({ basePath: HERE, port: SHELL_PORT, host: SHELL_HOST });
```

Both env names the project already documents still win, so nothing that worked before stops
working. Exposure becomes an explicit `TINA4_EXPOSE=true`.

**One line beyond the strict minimum, flagged on purpose:** a `console.warn` when the resolved
host is not loopback. An opt-in with no signal is how this stayed invisible — the boot banner
prints `localhost` whatever it bound to (`up-02`). Drop it if it is unwanted; it is the only part
of the diff not strictly required to close the hole.

## Residual

- **The WebSocket is checked for upgrade (101), not driven.** A turn was never run against the
  patched build; that needs a model gateway.
- **`.env` is not consulted.** `startServer` loads `.env` / `.env.local` *inside* the call, after
  our read, so a `TINA4_HOST` in a `.env` file would no longer reach the bind. This repo ships no
  `.env` and documents none — checked — but it is a behaviour difference worth knowing.
- **Exploitability was demonstrated with a GET, not with `run_shell`.** That the API answers an
  unauthenticated off-loopback request is the property; actually executing a command through the
  hole was deliberately not done.
- The framework default itself is unchanged — this pins one app. `up-02` (banner says
  `localhost` regardless) is untouched.

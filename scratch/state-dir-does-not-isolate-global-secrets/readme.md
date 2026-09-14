# `TINA4_STATE_DIR` does not isolate global secrets — `sec-03`

2026-09-14 · reproduced on `v0.2.0-300-gd3e4b76` · fixed on `scratch` `b4c2f4e`

## The defect

`app.ts` says the variable "redirects the whole state dir to an ISOLATED location". It moved
`settings.json` and the trace log and nothing else. Four sites each joined `os.homedir()`
themselves, so any run with the variable set — a test, a probe, a second instance, CI — read **and
wrote** the operator's real credentials, and a colliding name would have overwritten one.

| site | what it does |
|---|---|
| `app.ts:582` | reads the Anthropic key out of the global store |
| `app.ts:1610` | `ensureGlobalSecretsDir()` — the write path |
| `src/app/tools.ts:540` | reads the vision provider key |
| `src/app/tools.ts:2227` | `get_secret`'s global candidate |

`src/app/tools.ts` had no knowledge of the state dir at all, which is why the row's "one line"
fix could not have worked.

## `repro.mjs`

Boots the app with the variable set **and a fake `HOME`**, saves a secret through
`POST /api/global-secrets`, then looks for the file in both places.

The fake `HOME` is not decoration. Overriding `HOME` is the only isolation that currently works,
so it is what keeps the probe out of Michael's real `~/.tina4-simple-agent/secrets/` — which is
exactly how this defect was found on 2026-09-09, the hard way. The probe lists the real store
before and after and **fails the run** if it changed.

```sh
npx tsx repro.mjs <tree>          # exit 1 = reproduces, 0 = isolated, 2 = could not run
```

| tree | result |
|---|---|
| shipped `d3e4b76` | `inState:false, inFakeHome:true` — **NOT ISOLATED** |
| fixed `b4c2f4e` | `inState:true, inFakeHome:false` — isolated |

## `gate.mjs`

Reverts each of the six pieces of the fix **on its own** and requires
`test/state-dir-isolation.mjs` to go red for that piece alone, restoring by checksum afterwards
and aborting the whole run if a restore fails. **6/6 gate.**

## What the fix deliberately does not move

The default workspace (`app.ts:140`), the context cache (`tools.ts:75`) and the downloaded tina4
binary (`tools.ts:692`) still resolve from the home directory. Same mechanism, different blast
radius. The binary is the one to think about first: pointing it at an isolated dir makes every
test run re-download it, which is a **new** failure on an offline machine.

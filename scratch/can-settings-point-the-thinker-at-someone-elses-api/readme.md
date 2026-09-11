# Can Settings point the thinker at someone else's API?

The question behind `w-20` — Michael, 2026-09-11: *"in the settings where you choose a thinker and
coder, id really like the option to add API keys for providers like openrouter or direct API keys
from deepseek etc"*, and Andre's own task #8, *easy thinker/coder swap with an API key*.

Trees: built on `scratch` (`v0.2.0-297-gc3b61d9`), measured against `baseline-main` (`main`
`d719fc3`). Nothing here is committed.

## What was already there — and what was not

`POST /api/model` has **always** accepted `thinkerEndpoint` / `thinkerModel` / `thinkerToken`
(`app.ts:1968-1971` on `main`). Sending a third-party endpoint returns **200**. It then does
nothing, because `reconcileVendorWiring()` (`app.ts:479`) runs afterwards and puts the gateway
back whenever the role's vendor is `tina4` — which it is, because `tina4` is the only vendor a
key-based provider could have been. So the absence is **not** "the server cannot talk to
OpenRouter". It is:

1. there is no **vendor that owns its own endpoint, model and key**, so any typed triple is
   reverted on the next save (`ground.mjs`, filed as `run-23`);
2. there is **no UI for the thinker at all** — one anonymous triple existed, and it wrote the
   *coder* (`public/app.js:3238-3255`), which is exactly Andre's task #8 sitting unfinished;
3. the key had nowhere safe to live: `settings.json` already held `token` / `thinkerToken` and
   was written **0644** (`sec-05`).

## The files

| | |
|---|---|
| `ground.mjs` | stage 1. Demonstrates the absence on untouched `main`: POST a third-party thinker triple, get 200, watch it revert |
| `gate.mjs` | the gate, written before the code. 8 server-side checks. **8/8** on the build, **1/8** on `main` |
| `gate-ui.mjs` | the same feature through the real Settings screen in Chromium. **10/10** on the build |
| `attack.mjs` | stage 5. 15 cells, the ones the gate does not think of — the second user. **15/15** on the build, **1/14** on `main` (14 cells at the time) — the single pass is the migration cell, which is meant to pass on both |
| `human-edit.mjs` | settles one question only: is a pre-filled endpoint box replaceable by a person? |
| `fake-provider.mjs` | a stand-in OpenAI-compatible provider for the UI gate. Enforces its key so a wrong one can be shown to fail |

Runners live in the session scratchpad: `uigate-w20.sh` (boots a tree + the fake provider, runs
`gate-ui.mjs`, kills both and verifies the ports are free), `w20-gate-components.py` (component
gating), `w20-testbutton.py` (the Test-button patch, kept so the build can be re-applied).

## Two probe bugs found here, both of which looked like product bugs

Worth reading before trusting any number in this directory.

**Triple-click does not select inside a bound input, under headless Chromium.** `gate-ui.mjs`
first reported check 4 failing with
`thinkerEndpointNow "https://mcp.tina4.com/v1http://127.0.0.1:8901/v1"` — the typed text
concatenated onto the seeded value. That reads as a field a user cannot edit. It is not.
`human-edit.mjs` drives three real gestures against a pre-filled box with no programmatic
clearing:

```
  seeded value       "https://mcp.tina4.com/v1"  (seeded by the probe)
  CLEAN    ctrlA      "http://127.0.0.1:8901/v1"
  CLEAN    backspace  "http://127.0.0.1:8901/v1"
  APPENDED tripleClk  "https://mcp.tina4.com/v1http://127.0.0.1:8901/v1"
  no revert          yes
```

Ctrl+A and Backspace — what people actually do — replace cleanly, and nothing re-asserts the old
value afterwards. Only `clickCount: 3` fails, and only in the probe. Fixed by clearing through the
native value setter and dispatching a real `input` event.

**A probe that measures nothing passes.** The first run of `human-edit.mjs` printed
`seeded value ""` and three CLEAN results: it had typed into an **empty** box and proved nothing
about replacing a pre-filled one. It now waits for the app to seed the field, seeds it itself if
the app does not, says which happened, and fails if the field cannot be seeded at all.

Same family as two earlier traps in this workspace — `unshare -r-m` silently running nothing, and
a cell satisfied by `undefined`. **A cell that cannot run must FAIL, never pass quietly.**

## Reproduce

```sh
# the absence, on untouched main
T4_TREE=…/baseline-main node ground.mjs

# the gate: 1/8 before, 8/8 after
T4_TREE=…/baseline-main node gate.mjs ; T4_TREE=…/scratch node gate.mjs

# the attack: 1/14 before, 15/15 after
T4_TREE=…/baseline-main node attack.mjs ; T4_TREE=…/scratch node attack.mjs

# the UI, in a real browser
…/scratchpad/uigate-w20.sh …/scratch 8795 8901
```

## Verified afterwards

Everything above was re-measured on 2026-09-11 in
`../do-the-w20-numbers-hold-when-re-measured/`. That pass found a **key-exfiltration hole this
build had introduced** (`POST /api/model/test` would post the stored key to any endpoint a caller
named), fixed it, and gated it as cell 15. It also corrected five wrong numbers in the write-ups
and widened cell 9 from 10 GET routes to all 14. One claim could not be closed by running: a coder
**chat** over a custom provider — the thinker's is settled, the coder's rests on reading.

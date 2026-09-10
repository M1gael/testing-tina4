# Is a secret typed in an unmaskable OS box?

Yes, it was. `ui-05` slice 2.

Trees: `main` **`v0.2.0-290-gd719fc3`** (before, on :8797) · fix on **`v0.2.0-295-g9d159fe`** (:8796).

## The behaviour

Replacing a stored secret — an API key — called a native browser dialog for the new value:

- `public/app.js:3064` project-scoped secrets (`<workspace>/.secrets/`)
- `public/app.js:3366` global secrets (`~/.tina4-simple-agent/secrets/`)

An OS box shows every character as it is typed and cannot be told to hide them. The clincher found
while grounding: the **add**-secret input two rows below each of those has always been
`type="password"`. The app already knew how to mask; only **replace** did not.

## Files

| File | What |
|---|---|
| `gate-secret.mjs` | The gate. 6 checks. **5 fail on `main`**, all 6 pass after. Exit 1 / 0 |
| `attack-secret.mjs` | 9 cells the gate does not visit, including the **global** list via Settings |
| `geom-secret.mjs` | Measures whether the `display: contents` entry does anything. It does |

Run:

```sh
# the fix must be served from the tree under test, with HOME redirected -- see sec-03 below
T4A=http://127.0.0.1:8796 SECRETS_DIR=/tmp/<root>/<proj>/.secrets node gate-secret.mjs
T4A=http://127.0.0.1:8796 SECRETS_DIR=... GLOBAL_DIR=$FAKEHOME/.tina4-simple-agent/secrets node attack-secret.mjs
```

## The check that matters

Not "a modal appeared" — that is decoration. With a value sitting in the field, the value must
appear nowhere:

```
inBodyText false · inValueAttribute false · inOuterHTML false
```

And the field opens **empty**. The old secret is never fetched back and re-displayed; the server has
no route that would return a secret's value at all.

## Three mistakes worth keeping

1. **The first gate passed three checks on the untouched tree.** `.modal` matched the project modal
   that was already open, and `input[type="password"]` matched the add-secret field that has always
   been masked — so "a masked input exists in a modal" was true *before* the feature existed. Two
   more were vacuous: nothing had been typed, so "the value never renders" could not fail, and
   "cancel wrote nothing" compared a value to itself. Rewritten to pin on `#secret-value`, which
   does not exist on `main`, and to fail rather than pass when a step could not run.

2. **A probe selector matched the wrong dialog.** `document.querySelectorAll(".modal-actions button")`
   found the *project modal's* buttons, rendered underneath, so Cancel never closed the secret
   dialog and two checks failed against a correct build. Scoped to
   `document.querySelector("#secret-value").closest(".modal")`. Probe bug, not a product bug — but
   it looked exactly like a product bug for one run.

3. **`display: contents` passed every functional gate when reverted**, which by the usual rule makes
   it dead weight. It is not. Measured instead of argued: without the line the element computes to
   `display: block`, takes a **1400×180** box, and pushes `.main` from top 44 to 224 (height 856 →
   676). The whole app shifts 180px behind the dialog and snaps back on close. `geom-secret.mjs`
   exists because a functional gate cannot see layout.

## `sec-03` — found by this probe biting

The first attack run wrote a secret into the **real** `~/.tina4-simple-agent/secrets/`, despite the
server being booted with `TINA4_STATE_DIR` pointed at `/tmp`.

`TINA4_STATE_DIR`'s own comment (`app.ts:423`) says it "redirects the whole state dir", but
`ensureGlobalSecretsDir()` (`app.ts:1594`) hardcodes
`path.join(os.homedir(), ".tina4-simple-agent", "secrets")` and never consults `APP_STATE_DIR`.

So **every** run with the isolation switch set — a test, a probe, CI, a second instance — reads and
writes the operator's real global secrets, and would overwrite a real credential on a name
collision. The only thing that isolates it is overriding `HOME` for the whole process, which is what
these probes now do. The stray file was removed and the directory re-read to confirm it was empty.

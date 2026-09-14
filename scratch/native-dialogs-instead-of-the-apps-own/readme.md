# 33 native browser dialogs — `ui-05` slice 3

2026-09-14 · before on `v0.2.0-300-gd3e4b76` · fixed on `scratch` `866bc87`

24 `alert`, 6 `confirm`, 3 `prompt` in `public/app.js`. Unstyled OS chrome — and, not cosmetically,
they **block the event loop** (a live turn's stream stops rendering while one is open) and a native
prompt **cannot mask** what is typed into it.

## `gate-ui.mjs` — the real UI, real Chromium, real server

```sh
cd <tree> && npx tsx <here>/gate-ui.mjs . 8933
```

**Two independent detectors, because either alone can lie:** puppeteer's `dialog` event (which
also has to dismiss the box, or the page wedges), and a tripwire installed *before any app script*
that records every call to `window.alert/confirm/prompt` whether or not anything is displayed.

| tree | result | native dialogs tripped |
|---|---|---|
| shipped `d3e4b76` | **3/17** | 5, by name |
| fixed `866bc87` | **17/17** | 0 |

The three that "pass" on the shipped tree are the *nothing-happened* cells (cancel keeps the
session, cancel keeps the secret, the app stays up) — each paired with a failing cell that proves
the dialog was the browser's.

Cells worth naming: a dialog raised **from inside Settings** must paint above it and take Escape
without closing it; **two oversize files** in one drop must raise two notices in order, not
overwrite; and the **Link** button must still insert `<a href>` around the selection — the one
call site where making the ask asynchronous can break the feature rather than the look.

## `gate-components.mjs`

Reverts each piece to what it replaced, alone, and requires the browser gate to go red. **5/5.**

## Two traps this probe fell into first

- **Cells that passed by absence.** "Confirming the delete deletes the session" checked for the
  *renamed* title — never present on a tree where the rename had failed. Keyed on the session id
  now. "The dialog closes after it is answered" had to prove it opened first.
- **Leaked servers.** `setsid` + `npx` + `tsx` puts the real server two processes down, and it did
  not always land in the group being signalled — six ports were still listening after a clean-looking
  run. A stale one makes the next run read the OLD code as a fresh pass. The probe now refuses to
  start on a busy port and kills by looking up who holds it; every number above was re-taken on
  clean ports afterwards.

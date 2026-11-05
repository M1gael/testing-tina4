# frond.form.collect keeps only the first option of a select multiple

Reported as tina4-php#348. Pinned: tina4-css `origin/main` fab8e67 (the source of frond.js);
ports' vendored copies are byte-identical builds of it (frond.js sha1 f400f6af09, frond.min.js
35c7e65500) on php v3 b82729b8, py v3 31f2e1aa, rb v3 b1d2ed7, nd v3 7ea02ba, all 2026-11-05.

## Mechanism

`src/js/frond.ts:415-416` (tina4-css): every element that is not file/checkbox/radio goes through
`fd.append(el.name, el.value)`. For `<select multiple>` `.value` is the first selected option, or
`""` when none is selected. So 2 picks send 1 value, and 0 picks send `name=""` (native sends nothing).

## Proof

- `node collect.mjs <tina4-css tree>`: frond.form.collect vs `new FormData(form)` in jsdom, per cell.
  Stock: 6 of 10 cells differ. Fix: 0.
- `./browser.sh <dir with frond.js>`: same in headless Chromium, incl. disabled options. jsdom's
  FormData wrongly keeps disabled options, so Chromium is the reference for those.
  Stock: `collect=[g[]=1]`. Fix: `[1,2]`, matching native.

## Fix (uncommitted)

Worktree `~/.cache/tina4-worktrees/css348` (detached on fab8e67), patch
`~/.cache/tina4-worktrees/css348.fix.patch` (src + test; rebuild dist with `npm run build:frond:dev && npm run build:frond`).
A `select-multiple` branch appends each selected option that is not disabled itself or by its optgroup.
Tests in `tests/frond.test.mjs`: 5 new (collect x4 + form.submit through a real server); 4 fail on stock, all
10 pass on the fix. Single mutants (no disabled skip, no optgroup skip, el.value, all options,
branch never taken, "" when none) each turn the suite red.

## Upstream state

Maintainer's tina4-php#349 (b0945122, open) patches only php's `src/public/js/frond.js` and the
example copy. Not covered there: `frond.min.js` (what `tina4php init` copies and base.twig loads, still
broken in Chromium), the tina4-css source (next asset refresh reverts it), py/rb/nd copies, and disabled
options (#349 sends them; native does not).

Not checked: disabled `<select>` and other disabled controls are sent by collect for every type
(pre-existing, not this fix). Server parsing of repeated `name[]` is f-rt-05 (merged 2026-10-13).

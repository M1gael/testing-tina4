# f-ai-08 — tina4-js `.cursor` skill cites references it does not ship

Observed 2026-08-26 against `tina4stack/tina4-js` `master` @ `f9cffcb`.
Read-only reproduction: `./reproduce.sh [checkout]`. Exit 1 while the defect is present.

## The defect

`.cursor/skills/tina4-js/SKILL.md` tells the assistant to open two files at four sites:

| line | text |
|---|---|
| 545 | ``Read `references/signals-and-reactivity.md` for the full API.`` |
| 584 | ``Read `references/html-and-components.md` for the full API.`` |
| 1094 | listed under the skill's own "what ships with this skill" section |
| 1097 | same |

`.cursor/skills/tina4-js/references/` does not exist. Only `.claude` ships those files.
The `.cursor` copy is byte-identical to `.claude`'s SKILL.md (53,204 bytes) — it was promoted
from an 828-byte stub to a full copy without the directory it depends on coming with it.

## Who reaches it

Not npm: `package.json:64-68` sets `"files": ["dist/", "bin/", "TINA4.md"]`, so no skill tree
is published to the registry.

Not the installer either, and this is the part worth knowing. `tina4/install-skills.sh:63`
builds every fetch as `${primary_root}/${repo}/${ref}/.claude/skills`, so **`TINA4_SKILLS_TARGET=cursor`
reads `.claude` and writes `~/.cursor/skills`** — the repo's own `.cursor` tree is never a source.
`tina4/src/doctor.rs:721` says the same thing in its own words: *"refresh writes ~/.cursor/skills
only - it never changes project .cursor/skills entrypoints"*.

That leaves one consumer: a developer who opens the tina4-js repo in Cursor and picks up the
project-scoped skill. Narrow, but it is the repo's own contributors, and the failure is silent —
the assistant follows the pointer, finds nothing, and answers from the summary instead of the
full API.

## Canonical is tina4-python, not tina4-js

`install-skills.sh:115`:

```sh
install_skill tina4-python  tina4-js  html-and-components.md signals-and-reactivity.md persistence.md rtc.md
```

The `tina4-js` skill everyone installs is fetched from **`tina4-python`**. tina4-js's own copy is
a second copy that nothing publishes. The two have drifted, in both directions:

- `SKILL.md` — tina4-python is **87 lines ahead** (an entire "Which flow? — pick the smaller one
  that fits" section: IIFE drop-in vs project scaffold). tina4-js has 9 unique lines.
- `references/html-and-components.md` — **tina4-js is 2 lines ahead**: it states history mode is
  canonical and shows `router.start({ mode: 'history' })`, where tina4-python still shows
  `mode: 'hash'`.

So "sync one direction" is the wrong instinct here. Recorded as its own finding; not fixed.

## Not defects, checked and dismissed

- `plan/MASTER.md` (SKILL.md:113) — reads as a dangling pointer, is not. Lines 213/215/219 show
  it describing the layout convention the skill teaches *the developer's project*, not a file in
  this repo. `plan/` exists here with `00-OVERVIEW.md`.
- `STORAGE.md` — exists at the repo root, and the skill says "at the repo root" (SKILL.md:1081).
- BOM / cp1252 mojibake — the `f-ai-03` defect. Present in my local checkout, **absent upstream**:
  fixed at `fab28b8`. My checkout was 12 commits behind when I first looked, which is the only
  reason it appeared live. Verified against `origin/master` after fetching.

## The fix

Copy the four reference files from `.claude/skills/tina4-js/references/` into
`.cursor/skills/tina4-js/references/`, byte-identical.

Deliberately **not** included: `evals/` and `tina4-js.skill`. The four language ports do carry
those under `.cursor`, because `sync-tina4-skills.sh` gates `.cursor` against `.claude` with a
full `diff -rq` and demands parity. tina4-js has no sync script, nothing demands parity here, and
the gate's own `GLOBAL_EXCLUDE=(-x evals -x '*.skill')` records that neither is part of what an
assistant consumes. Shipping the references is the smallest change that makes the existing
SKILL.md correct.

Branch: `fix/cursor-skill-ships-the-references-it-cites` in `gitdir/tinaforks/tina4-js`.
Uncommitted, unfiled.

## Verification

`./reproduce.sh` — FAIL (exit 1, 2 dangling) before, PASS (exit 0) after.
Copied files re-checked for BOM and mojibake: clean.
Run across all four ports on their PR branches: all PASS the dangling check, all four carry the
orphan pair below in all three trees.

## Second finding, not fixed — orphaned reference files

`references/persistence.md` (231 lines) and `references/rtc.md` (352 lines) ship in every tree of
every repo, and `install-skills.sh:115` installs both onto every user's machine. **No SKILL.md
cites either.** Grep for `persistence.md` / `rtc.md` across the skill text returns nothing — the
only `references/` pointers anywhere are the two above.

583 lines of API documentation that the assistant is never told to open. Present in canonical, so
every install has it. Logged as `f-ai-09`.

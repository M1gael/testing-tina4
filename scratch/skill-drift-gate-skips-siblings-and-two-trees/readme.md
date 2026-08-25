# skill-drift-gate-skips-siblings-and-two-trees

**`scripts/sync-tina4-skills.sh` guards one of the three skill trees it is meant to guard,
and reports `OK` for sibling repositories it never opened.**

Ledger rows: `f-ai-05` (the gate itself), `f-ai-03` (the corruption it cannot see),
`f-ai-07` (the drift it does not look for).

Pinned to `tina4-python` `origin/v3` @ `f5cd5cb`, script md5
`93e24f04394dec1f2dc1f72ca653e6d7`. All ten checkouts under `gitdir/tinaforks/`.

## Run it

```bash
./prove.sh                                   # stock  — 3 of 3 defects reproduce
./prove.sh candidate-sync-tina4-skills.sh    # fixed  — all 3 gated, clean tree still passes
```

No network, no framework install: the fixtures are synthetic repo trees built in `mktemp -d`,
with `HOME` redirected so the real `~/.claude/skills` can never leak into a measurement.

| File | What |
|---|---|
| `stock-sync-tina4-skills.sh` | byte-for-byte copy of the script at `origin/v3` |
| `candidate-sync-tina4-skills.sh` | the proposed replacement |
| `build-fixture.sh` | builds fixture A, B or C |
| `prove.sh` | runs all three, reports which defects are present |

## What the fixtures model

Every port repo carries **three** skill trees, and all three ship — `.claude/skills/` is read
by Claude Code, `.agents/skills/` by Codex, `.cursor/skills/` by Cursor. Measured in
`gitdir/tinaforks` on 2026-08-25, they hold three different kinds of file:

| Skill | `.claude` | `.agents` / `.cursor` | What "correct" means |
|---|---|---|---|
| `tina4-maintainer` | 79 139 B, the full skill | 755 B stub, all eight byte-identical | cross-repo, **tree against the same tree** |
| `tina4-js` | 52 960 B | 52 960 B, identical | cross-repo, per tree |
| `tina4-developer-<lang>` | full, plus 7 `references/` | smaller, **no `references/` at all** | intra-repo, `.claude` canonical |

`.agents` and `.cursor` legitimately differ from `.claude` for `tina4-maintainer` — they are
entrypoint stubs, not copies. Any gate that compares them against `.claude` is wrong. That is
why the fix compares tree to tree.

- **Fixture A** — `tina4-python` alone, no siblings on disk.
- **Fixture B** — all four repos; every `.claude` copy matches canonical exactly, the stubs
  carry the corruption, the developer skills have drifted inside each repo.
- **Fixture C** — negative control. Everything present, consistent, clean.

C is not decoration. Three new assertions are exactly the kind that produce false positives,
and a gate that fails on a clean tree gets switched off.

## Mechanism

**1. A sibling that is not on disk is dropped in silence.** `sync-tina4-skills.sh:44`

```bash
[ -d "$PARENT/$s/.claude/skills" ] && targets+=("$PARENT/$s/.claude/skills/$skill")
```

A bare `&&` with no `else`. The repo leaves the target list without a word, `drift` stays `0`,
and `--check` prints *"OK: every cross-repo Tina4 skill copy matches canonical"* and exits `0`.
The layout is load-bearing — `PARENT` is `$REPO_ROOT/..`, so moving `tina4-python` one
directory away from its siblings silently empties the gate — and nothing in the script says so.

**2. `CANON` is `.claude` only.** `sync-tina4-skills.sh:39`

```bash
CANON="$REPO_ROOT/.claude/skills/$skill"
```

`.agents` and `.cursor` are tracked, shipped, and never compared against anything.

**3. Neither gap is what let `f-ai-03` survive.** The eight corrupted stubs are byte-identical
to each other, so even a tree-to-tree diff reports them clean. Only an assertion on the bytes
themselves catches a defect that is uniform across every copy. This is the reason the fix adds
an encoding check that is independent of all the diffing.

## Before

```
=== FIXTURE A — tina4-python alone, no siblings on disk ===
    OK: every cross-repo Tina4 skill copy matches canonical (tina4-python).
    exit: 0
    DEFECT PRESENT  f-ai-05(1) absent siblings skipped in silence
      exit 0, three ungated repos, named in output: 0

=== FIXTURE B — siblings present; .claude clean, .agents/.cursor corrupt and drifted ===
    OK: every cross-repo Tina4 skill copy matches canonical (tina4-python).
    exit: 0
    DEFECT PRESENT  f-ai-03 / f-ai-05(2) BOM + mojibake in .agents/.cursor
      8 corrupt files planted, encoding mentioned in output: 0
    DEFECT PRESENT  f-ai-07 tina4-developer-<lang> drifted inside each repo
      4 drifted copies planted, tina4-developer mentioned in output: 0

VERDICT: 3 of 3 defects reproduce against this script.
```

## After

```
    gated          f-ai-05(1) absent siblings skipped in silence
      exit 1, three ungated repos, named in output: 18
    gated          f-ai-03 / f-ai-05(2) BOM + mojibake in .agents/.cursor
      8 corrupt files planted, encoding mentioned in output: 9
    gated          f-ai-07 tina4-developer-<lang> drifted inside each repo
      4 drifted copies planted, tina4-developer mentioned in output: 16
    clean tree accepted, exit 0. No false positive.

VERDICT: all 3 gated, and a clean tree still passes.
```

## What the fix changes

1. **Absent is reported, and counts.** `ABSENT [...] is not checked out — NOT compared`, and
   `--check` exits non-zero. `--siblings-optional` is there for a single-repo checkout, and
   says in its own output that the result is partial.
2. **All three trees are compared**, tree against the same tree for the shared skills.
3. **`tina4-developer-<lang>` is gated inside its own repo**, `.claude` canonical.
4. **An encoding assertion** over every tracked `.md`/`.txt` under all three trees: no UTF-8
   BOM, no cp1252 mojibake (`c3 a2 e2 82 ac`, `c3 82`). It runs in both modes and never
   auto-repairs — rewriting the bytes of a tracked file is a human's commit, not a side
   effect of a sync.
5. **The global install is compared with `-x evals -x '*.skill'`.** `tina4 ai` fetches
   `SKILL.md` and `references/` and never the eval fixtures or the packaged bundle, so
   without this the gate is permanently red — and a gate that can never say OK is one
   everybody learns to ignore. Scoped to the global target; repo-to-repo comparison is
   still total.

## What the first real run found

Run against `gitdir/tinaforks` on 2026-08-25, the fixed gate reported two things the ledger
did not have:

- **`tina4-js/SKILL.md` has drifted again, live.** `tina4-python` `origin/v3` carries
  `756d80c8…`; all three ports carry `ef7829e5…`, from upstream `f1424ce`, `6798556` and
  `7093020`. Exactly the drift the script exists to prevent, in the file it was written for.
- **`references/` is absent from `.agents` and `.cursor` entirely** — 7 files under `.claude`,
  0 under each of the other two, in all four repos. `f-ai-07` records this as a line-level
  drift of `SKILL.md`; the reference material is not drifted, it is missing.

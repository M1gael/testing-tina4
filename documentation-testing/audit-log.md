# Maintenance & Audit Log

**Not a bug log.** Confirmed issues live in [`../known-issues/ledger.md`](../known-issues/ledger.md). This file is version bumps, GitHub re-checks, fix re-verifications, and audit verdicts. The work backlog (`outstanding-tasks.md`) holds only open todo items.

### 2026-08-19 — `PY-FW-03` filed as PR #116

Fork `MichaelC8E/tina4-python`, branch `fix/websocket-decorator-shadowed` @ `de1b06e`, PR
[#116](https://github.com/tina4stack/tina4-python/pull/116) into `tina4stack/tina4-python` `v3`.
Ledger row `PY-FW-03` `open` → `fix-in-review`. Mix now **83 open**, 3 fix-in-review.
Still reproduces on released 3.13.105; do not mark `fixed` until merge.

`PY-FW-01` and `PY-FW-02` stay `open` — review said do not file those diffs as-is.

### 2026-08-19 — pull every repo, measure fork drift, verify the fixes end-to-end

**Pulled first, then worked** — the new standing rule (root `readme.md`, *Working against the
real repositories*). What the fetch found:

| Repo | Remote state | Action |
|---|---|---|
| `tina4-python` | `v3` == `origin/v3`; all four fix branches **1 ahead / 0 behind** | none needed — already on latest |
| `tina4-book` | only a `fork` remote (MichaelC8E) — **no `upstream`**; `fork/main` **19 behind** tina4stack, 0 ahead | added `upstream`; fork not pushed |
| `tina4-documentation` | same shape; `fork/main` **73 behind** tina4stack, 0 ahead | added `upstream`; fork not pushed |
| `tina4-js` | 7 behind `origin/master` | left; pull when next touched |
| `tina4-dev-admin` | 1 behind `origin/main` | left; pull when next touched |
| `testing-tina4` | level with `origin/main` | none |

Both doc forks are pure fast-forwards — 0 ahead of upstream, so syncing `main` loses nothing.
Both local `docs/python-consistency-fixes` branches sit 1 ahead of a base that is now 19 / 73
behind, and the fork's copy of each was force-updated to a different hash than the local one
(`5ebe35b` vs `82aaffe`; `6f176d9` vs `799dbef`). Left untouched — that divergence is somebody's
rewrite, not ours to resolve blind.

**Fix verification, end-to-end through the real CLI 3.8.77**, clone on `PYTHONPATH`, throwaway
project outside the workspace (no workspace `.venv` was touched):

- `CLI-FW-12` — installed `CLAUDE.md` is **82 965 bytes**, the packaged guide, not the ~2 KB stub.
- `CLI-FW-10` — writes `.cursorrules`; no `.cursorules` anywhere.
- `CLI-FW-05` — no `response({{` in any of the seven context files.
- `CLI-FW-08` — `tina4 ai --all` installs everything with no prompt. **The Rust CLI does forward
  the flag**; the defect was Python-side arg matching, and the fix closes it.
- `CLI-FW-07` — `tina4 ai </dev/null` prints the hint and exits `2`. No `EOFError`.
- `PY-FW-03` — `tina4_python.websocket` is callable; `core.router.websocket` still is.
- `PY-FW-02` — the chapter-27 pattern now raises a `TypeError` naming the working call. Which
  surfaced `PY-DOC-06`: **the chapter documents a contract the runner never had**, so the fix
  turns a silent no-op into a loud failure without making the documented code run. Direction is
  a decision, not a patch — logged, not resolved.

**Docs aligned to the framework** on branch `docs/ai-installer-behaviour` in both doc repos,
branched off `upstream/main` (not off the stale local branches). Python copies only — the
php / ruby / nodejs pages make the same claims about *their* implementations and those repos
are not cloned here, so they are a backlog item, not an assumption. Three new ledger rows:
`PY-DOC-04` (`websocket_route` does not exist), `PY-DOC-05` (eight tools / Antigravity vs the
seven in `AI_TOOLS`), `PY-DOC-06` (chapter 27's registration contract). Mix now **105 rows —
84 open**, 2 fix-in-review, 14 fixed, 1 closed, 3 not-a-bug, 1 wont-fix.

**Forks synced** (approved in-session): `git push fork upstream/main:main` on both doc repos —
`tina4-book` 2818c2f → 849d9e8, `tina4-documentation` 9d688d7 → 462f4bb. Both now measure
`0 0` against `upstream/main`. Fast-forwards; neither fork had a commit of its own on `main`.

`PY-DOC-06` (chapter 27) left open by decision — neither the chapter nor `register()` moves yet.

Nothing else pushed. No PR.

### 2026-08-19 — migrate the last issue records out of `bug-hunting/`

Ahead of a directory cleanup, every finding still living only in an investigation write-up was
moved into the ledger. Ten new rows, each rewritten to stand alone — root cause with
`file:line`, reproduction, and recommended fix all in the row — so no row depends on the source
directory surviving.

- **`bug-hunting/debug-false/README.md`** (551 lines, previously **zero** ledger IDs) → `PY-FW-09` (browser opens onto a 404 when `TINA4_DEBUG=false`), `PY-FW-10` (toolbar ✕ does not persist while the overlay's does), `PY-FW-11` (no `TINA4_NO_TOOLBAR`), `PY-FW-12` (footer vs dashboard route count differ by one; `/health` prefix filter misses `/__health`), `PY-FW-13` (route count unlabelled and undrillable), `PY-FW-14` (three route-listing paths that disagree), `PY-FW-15` (the reported 99 routes — **open question, deliberately not filed**: AutoCRUD was ruled out by the reporter, so the count has no known source), `SITE-DOC-02` (RAG index stores GitHub blob URLs), `SITE-DOC-03` (`md()` mangles `[text](<url>)` into a broken relative link).
- **`bug-hunting/serve-port/patches.md`** → `CLI-DOC-01` (`tina4 serve 7150` parsed as a project name; neither `-p`/`--port` nor the positional project launcher is documented).
- Mix now **102 rows — 83 open**, 14 fixed, 1 closed, 3 not-a-bug, 1 wont-fix.
- Not migrated, by decision: `agent-testing/unverified-leads.md` (discard — unverified agent observations, no quoted-doc trace) and `comparison-testing/results/` (measurements; that file records *"Capability gaps: None"*).
- `AUD-*` coverage gaps stay in `coverage-ledger/` — they track our missing tests, not Tina4 defects.

### 2026-08-19 — kill the second bug log

- Removed `known-issues/findings-log.md`. It mixed a duplicate Known Issues Log with coverage, `FIX-NN` proposals, and audit history.
- Issues: `known-issues/ledger.md` only.
- Coverage index: `coverage-ledger/README.md`.
- `FIX-NN` long-form: `known-issues/suggested-fixes.md`.
- This audit history: this file.

### 2026-08-19 — clean-room retest CLI 3.8.77 · tina4-python 3.13.105

- Fresh `tina4 init python` at `bug-hunting/2026-08-19/repro/`. Evidence: `bug-hunting/2026-08-19/NOTES.md`.
- Ledger restamped (24 rows). Mix now **72 open, 14 fixed, 1 closed, 3 not-a-bug, 1 wont-fix** (0 pending-retest, 0 fix-in-review).
- **Newly fixed:** `PY-DOC-01` (inline `expect_*` aligned), `PY-FW-05`/`PY-FW-06` (JWT alg + `TINA4_JWT_ALGORITHM`), `CLI-FW-03` (`tina4 routes` lists). `PY-FW-07` Python `nbf` now rejects; row stays **open** because PHP/Node were not re-run.
- **Still open, freshly reproduced:** `PY-FW-01` (`@cached` inert), `PY-FW-02` (register instance; now logs), `PY-FW-03`, `CLI-FW-01` (plus lying ready-line), `CLI-FW-02` (CLI still kills foreign holders), `CLI-FW-04`–`08`/`10`/`11`, `ALL-FW-01`, `PY-DOC-02`, `SITE-DOC-01` (env var real; `audit-truth.py` not re-run).
- **Holds:** `PY-FW-04` / `PY-DOC-03` not-a-bug, `PY-FW-08` wont-fix, `CLI-FW-09` empty `.cursor/`.

### 2026-07-02 — framework bump 3.13.49 + filing-candidate re-verification (PY-12-03, PY-06-06)

- **tina4-python 3.13.48 → 3.13.49** (`uv lock --upgrade-package tina4-python` + `uv sync`). CLI checked via `tina4 update`: 3.8.53 already latest. Upstream 48→49 diff: version bump, `public/js/tina4js.min.js`, docs/skills only — **no `queue/`, `test_client/`, or `core/server.py` changes.**
- Per the version-stamp policy, no blanket re-verify — only the two filing candidates probed:
  - **PY-12-03 STILL OPEN on 3.13.49** — brokers restarted (`tina4_rabbit`, `tina4_mongo`); `test_ch12_queue_backend_lifecycle.py` expectation suite green with 0 skips (live brokers reached); `size(status)` stubs byte-identical at the same lines.
  - **PY-06-06 STILL OPEN on 3.13.49, both sides** — direct-dispatch probe: `_invoke_handler` injects `id=42` into the documented positional handler (`{"got":42}`); Test client flat call unchanged → `test_ch06_routes.py` TypeError sentinels pass. (Server-side had been unverified since 3.13.30 — now closed.)
- Report bodies drafted in chat per report-brevity, adversarially verified (3-agent refute pass; PY-12-03 corrected on 3 points, PY-06-06 clean), and GitHub cross-checked for duplicates (371 comments + all bodies, both repos — none). **Both FILED 2026-07-02**: PY-12-03 → [#144](https://github.com/tina4stack/tina4-book/issues/144#issuecomment-4868451205), PY-06-06 → [#142](https://github.com/tina4stack/tina4-book/issues/142#issuecomment-4868455231). Unfiled count 30 → 28.

### 2026-07-02 — Ch12 audit coverage gaps closed (AUD-12-1/2/3/L)

- **Environment:** Docker recovered (`tina4_pg` up, healthy); the 3 queue brokers stay down — not needed (all Ch12 gaps are file-backend). tina4-python 3.13.48 · CLI 3.8.53.
- **AUD-12-1 (S8)** — NEW `documentation-testing/pypy/tests/test_ch12_orders_route_s8.py` (2 tests): in-process `tina4_python.test` client drives the registered `POST /api/orders` handler — exact fan-out payloads on emails/invoices/warehouse_sync, instant-201 body while all jobs still pending, 1:1 fan-out per request. Client bypasses the Bearer gate (PY-06-13 mechanics, disclosed); served 401 stays PY-12-10.
- **AUD-12-2 (S11/S12)** — NEW `documentation-testing/pypy/tests/test_ch12_email_routes_s12.py` (6 tests): all four email endpoints + the 400 branch both ways (one-missing → exactly that error; empty → all three). Retry test constructed with exactly 1 dead so the documented outcome and retry()'s one-per-call actual (PY-12-04) coincide, disclosed.
- **AUD-12-3 (S7)** — `retry_failed()` VERIFIED FAITHFUL (2 new tests in the S7 file): re-queues a dead job that is under a RAISED `max_retries` (the constructable "dead and under the limit" state); leaves at-limit jobs dead. The tautology concern is resolved — no doc-claim ambiguity, no finding.
- **AUD-12-L** — all four LOW items closed: `failed()` both exclusive bounds + pop()-path same-id re-delivery (S7 file), `job.retry()` default no-hold (S6 file), `TINA4_QUEUE_URL` own-knob selection (S9 file).
- **Runs:** new tests green ×2 (deterministic); full ch12 sweep **86 passed / 26 skipped**, 0 failed. **No new findings — every gap verified faithful.** Ledger closed-block + progress row updated; backlog rows removed.

### 2026-06-30 — framework bump + doc refresh + doc-system audit
- **tina4-python 3.13.47 → 3.13.48** (latest; released 2026-06-29). `uv lock --upgrade-package tina4-python` + `uv sync`; only `documentation-testing/pypy/uv.lock` changed. CLI stays 3.8.53. 3.13.48 = i18n interpolation hardening + swagger decorator-stacking fix (#59) + bundled-skill doc-truth; **none touch any open finding** — no re-verify per version-stamp rule.
- **Docs refreshed** (`tina4 books`): only `36-releases.md` changed vs the local copy; all implemented chapters (06/07/12/18) byte-identical → every line-ref still valid.
- **Coverage / fidelity audit** (12-agent workflow `wpr69vtjq`, Ch06/07/12/18): fidelity SOLID — **ZERO our-divergences**; every divergence-asserting test is a correct sentinel for a logged finding; no rigging. ~185 / 221 documented claims covered. Real coverage gaps found → **AUD-\*** (tracked in each chapter's ledger Open items). Empirical suite re-run blocked this session (Docker engine wedged; native PG-service start needs admin).
- **Doc-system audit + optimization** (7-agent workflow `wcb2k5all`): structure judged sound, drift fixed — created `coverage-ledger/_TEMPLATE.md`; backfilled `py-ch06-orm.md` + `py-ch18-testing.md` ledgers; slimmed the 4 Evaluation Progress cells (~31 KB of run-on narrative → one-line status + ledger link); relocated the FIX-04 spec to `notes/` (PY-18-04 is closed); consolidated memory (folded `upstream-labels` + `doc-reference-style` into `report-brevity`, regrouped MEMORY.md); reconciled the coverage legend to 5 states; fixed cross-file contradictions (phph workspace state, retired bracketed-title, superseded 3-section report shape, BH-46 stale re-check note).

### 2026-06-29 — maintenance check (update + GitHub responses + fix re-verify)
- CLI `tina4 update` 3.8.52 → **3.8.53**; framework `tina4-python` 3.13.47 already latest at the time.
- **GitHub:** no new maintainer activity on any filed thread. book #140 / #142 / #143 / #144 all OPEN (last comment MichaelC8E); py #46 CLOSED, #47 / #48 OPEN (maintainer "fixed in vX" replies), #49 OPEN.
- **Fix re-verify on 3.13.47** (6 issue probes, 32 passed / 4 xfailed): py #46 error-visibility, #47 driver ImportError, #48 schema-aware introspection all FIXED and stay fixed; BH-46/47/48/49 confirmed fixed/closed. The 4 xfails are drafted-patch-shape assertions the maintainer chose not to ship (not residual bugs, no XPASS).


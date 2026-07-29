# Coverage Ledger — <Lang> Ch<NN> <Topic>

<!-- Copy this file to `<lang>-ch<NN>-<topic>.md` (e.g. `py-ch12-queues.md`) and fill in.
     Every implemented chapter MUST have a ledger (documentation-testing/readme.md → Workflow step 7). The
     findings-log Evaluation Progress table links here and carries ONLY a one-line status. -->

Per-snippet / per-option coverage for the chapter. The canonical home for coverage detail —
the `findings-log.md` Evaluation Progress row for this chapter is a one-line status + a link here.

**Legend (5 states):**
- `✓ tested` — exercised faithfully; cite the test/probe function or the live-mock demo.
- `⚠ diverges` — framework behaves differently than documented; cite the finding ID (its sentinel test IS the coverage).
- `⛔ blocked` — cannot be stood up in this environment (broker/driver/service missing); state the reason. A logged blocker, never a silent skip.
- `⏸ deferred` — USER-deferred; add a pointer to where/why.
- `n/a` — nothing to test (concept-only prose, no code/option).

A section is **covered** only when every snippet AND every named option is `✓` / `⚠` / `⛔` / `⏸` / `n/a` — never a bare "complete".

---

## Section sign-offs

<!-- One block per section. Re-stamp (append, don't overwrite) when re-run on a newer version. -->

### S<n> <Section Name>
Sign-off: <YYYY-MM-DD> · tina4-python <framework-version> · CLI <cli-version> — <Verdict: FAITHFUL / FAITHFUL-with-findings / BLOCKED>
- <snippet or option> — `✓ tested` (`test_chNN_<topic>.py::<fn>`)
- <named option a> — `✓ tested` (...)
- <named option b> — `⚠ diverges` (PY-NN-NN — sentinel `...`)
- <named option c> — `⛔ blocked` (reason)
Live mock: `GET /chapter/<NN>` (block for S<n>) — reachable under `tina4 serve`.

---

## Option matrix (optional)

<!-- For sections naming multiple backends/engines/stores, a grid of option × operation.
     Ref: src/routes/queue_backend_matrix.py → GET /queue/backends. Delete if not applicable. -->

---

## Open items
- <anything not yet ✓ — with the reason and a pointer>

## Resolved items
- <item> — CLOSED <YYYY-MM-DD> · <version> — <how verified>

# `small-model-tiers/` — Tina4 Agent on small local models

Can the **built-in `.tina4/` agent**, driving a small local model (Qwen 27B–36B class),
build working Tina4 applications unassisted? Three difficulty tiers, one project directory
each, isolated so a tier's outcome can't be contaminated by another's state.

The subject under test is the **agent + the context Tina4 ships it** — not the model's raw
capability. A tier failing is a finding only where the cause traces to Tina4's agent
scaffolding, prompts, or shipped context.

## Tiers

| Dir | Tier | Exercises | State |
|---|---|---|---|
| `level-1-basic-routing/` | 1 — Easy | `@get` routing, Frond/Twig template rendering, dynamic variable injection | **Run** — agent transcript in `.tina4/chat/` |
| *(not created)* | 2 — Medium | REST microservice (`@get` + `@post`), JSON body parsing, interactive AJAX frontend | Not built |
| *(not created)* | 3 — Hard | SQLite ORM integration, full CRUD, visual feedback | Not built |

Prompt text for all three tiers is in [`prompts.md`](prompts.md) — verbatim, as handed to
the agent. Create tiers 2 and 3 as `level-2-rest-api/` and `level-3-orm-crud/` when run.

`level-1-basic-routing/src/routes/` is **empty** — the tier scaffolded and the agent ran
(25KB of transcript across `.tina4/chat/history.json`, `thoughts.json`,
`escalations.json`), but no route file was produced. Whether that is an agent failure or an
incomplete run is **not yet determined**; read the transcript before drawing a conclusion.

## Visual success requirement

Every generated app must render a top banner carrying (1) the program name, (2) the exact
prompt it was given, and (3) a verification checklist of feature badges. This exists so a
tier's outcome is judged by **looking at the running page**, not by reading the agent's
self-report — a small model will claim success it did not achieve.

## Rules

- **The assistant does not write code.** Only the Tina4 agent/model writes or modifies code
  in a tier directory. The assistant provides environment support, runs the agent, and
  documents outcomes. A tier where the assistant wrote code is void as evidence.
- **Target models**: Qwen variants, ~27B–36B parameters.
- **One directory per tier** — no shared `data/`, `.env`, or `__pycache__` between tiers.

## Findings

Observations from these runs are **not** eligible for
[`known-issues/ledger.md`](../../known-issues/ledger.md) — they carry no quoted-doc-claim trace (see
[`../readme.md`](../readme.md) → *Relationship to the harness protocol*). They go to
[`../unverified-leads.md`](../unverified-leads.md) and must be re-tested inside
`documentation-testing/` against a real chapter before earning a `PY-NN-NN` ID.

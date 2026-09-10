# The session token counter always reads zero

**Reported by Michael, 2026-09-08:** *"tokens used in my last session when i swapped thinker to
claude said 0 tokens."*

Trees: `main` **`v0.2.0-290-gd719fc3`** (before) · fix built on `scratch` at **`v0.2.0-293-gaee839e`**.

## 1. Reproduced, on untouched source

`repro.mjs` boots the app from a given tree against a fake OpenAI gateway that reports
`usage.total_tokens` on **every** call, drives two real turns over the WebSocket, and reads the
persisted session file.

```
                        gateway handed out   session totalTokens   session totalElapsedMs
main      d719fc3       548 across 4 calls   0                     37 ms
scratch   (fixed)       548 across 4 calls   548                   42 ms
```

`totalElapsedMs` is the control: written by the same function, one line apart, and it works.

Confirmed independently in Michael's own data — six real sessions across three projects, every one
`totalTokens: 0` with a real elapsed time (up to 364,164 ms):

```
claude-calc/mtsqr06j  0 tokens / 198075 ms      Tempooo/mtrejkxg  0 / 1098
mycalc/mtsqha4g       0 tokens / 364164 ms      Tempooo/mtrejwk0  0 / 45658
                                                Tempooo/mtseeu10  0 / 189093
                                                Tempooo/mtspm44n  0 / 328220
```

## 2. Mechanism, to file:line (line numbers on `d719fc3`)

**Nothing in the shipped turn path ever reads a token count, so the counter cannot be anything but
zero.** Three layers, each independently fatal:

| Layer | Where |
|---|---|
| **Nothing counts.** 17 thinker call sites hand-roll their own `fetch(settings.thinkerEndpoint…)` and read only `choices[0].message`; the `usage` block beside it is dropped. The streaming one (`app.ts:2917-2932`) parses only `choices[0].delta`, and `stream_options` appears **0 times** in the file, so an OpenAI-shaped gateway is never even asked to send usage on a stream. | `app.ts` ×17 |
| **The plumbing is inert.** `_inflightTokens` — the field whose own comment says it holds "tokens burned by the CURRENTLY RUNNING turn" — is only ever assigned `0`. `endTurn(reason, turnStartAt, tokensThisTurn, rounds)`, the one function that would pass a real count to `accumulateStats`, has **zero callers** (`grep -a endTurn` returns its comment and its definition, nothing else). | `:2674`, `:2472`, `:7306` |
| **The only reachable call passes a literal zero.** `runDeterministicTurn`'s `finally` — and `_runTurnBody` calls it "THE ONLY PATH" — is the sole reachable caller of `accumulateStats`, which is the sole writer of `session.totalTokens`. | `:7198`, `:6893-6896` |

The usage-normalising code that would have done this **exists and is dead**: `openaiStream` and
`anthropicStream` in `src/app/streamers.ts` set `stream_options:{include_usage:true}` and normalise
both vendors' shapes to `{prompt_tokens, completion_tokens, total_tokens}` (`streamers.ts:174`,
`:225`). They are imported at `app.ts:32` and **never called** — they went dead with the
tool-calling loop that `app.ts:7310` records as deleted.

**Only the coder is accounted for at all**, and not into the session: `recordUsage` (`:3062`,
`:3131`) writes `plan/cost/*.jsonl` and `COST.md`, per **project**. Michael's real ledgers confirm
the asymmetry — 67 calls, 162,067 tokens, **every row `role=coder`, not one thinker row**.

## 3. What the fix changes

One seam plus four wires, all in `app.ts`, +52 −18:

- `thinkerFetch(init)` — identical to `fetch()` except it reads `usage` off a **clone** and folds it
  in, so all 16 JSON call sites are one-token edits and their response handling is untouched.
- `thinkerStream` — asks for usage (`stream_options:{include_usage:true}`) and keeps the **last**
  usage frame, folding once after the stream (a gateway that repeats the block per chunk must not
  multiply).
- `coderStreamRaw` — one line; it already parses `usage` for the cost ledger.
- `runDeterministicTurn`'s `finally` — `accumulateStats(elapsed, this._inflightTokens)` instead of
  `0`, then resets the tally.

## 4. Files here

| File | What it does |
|---|---|
| `repro.mjs` | The reproduction. Exit 1 = defect present, 0 = counter moved, 2 = inconclusive |
| `where-do-the-tokens-go.mjs` | Two separate gateways (thinker/coder) — proves thinker usage lands nowhere |
| `attack.mjs` | 10 cells: absent / zero / negative / string / NaN / parts-only / anthropic-shaped usage, 3-turn accumulation, two sessions in one project |
| `gate-components.mjs` | Drives the **chat** lane (streaming thinker) and the **build** lane (coder) with per-role token values, so the arithmetic says which model contributed |

Every probe uses a throwaway `/tmp` projects root and a throwaway state dir, kills its own server,
and **re-reads** both directories afterwards to say out loud whether cleanup worked.

## Two mistakes this probe made, kept because they were nearly invisible

1. **The first reproduction measured a turn that had already given up.** The fake replied `"ok"` to
   everything; the app read that as an offline stub, fired `open-setup`, and aborted the turn in
   31 ms. The token numbers were still "correct" — 0 — so nothing looked wrong. Caught only by
   printing the frame types and seeing `open-setup`.
2. **"Turn 2" was turn 1's replay.** Each turn opened a new WebSocket; `attach()` replays the
   buffered frames, so the probe took turn 1's replayed `turn:done` as turn 2's result and reported
   "0 model calls" for a turn it had not sent. Fixed by holding one socket for the whole run.

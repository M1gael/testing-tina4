# Does the real gateway accept `stream_options: {include_usage: true}`?

2026-09-14 · `v0.2.0-300-gd3e4b76`

## The question

`run-20`'s fix (`mig-dev` `bdb4f57`) added `stream_options: {include_usage: true}` to every
streamed call — `app.ts:3002` (thinker stream: plan authoring, consultant reply) and
`src/app/streamers.ts:225` (coder). It had only ever been sent to a **fake** gateway. A real
gateway that rejects unknown body fields would break streaming for every user, and that risk
rode along with the shipped commit.

## What was run

`probe.mjs`, two cells per run against `https://mcp.tina4.com/v1/chat/completions`, token
`FREE-TOKEN`, prompt "Say OK.", `max_tokens: 32`:

- **A** — with `stream_options: {include_usage: true}`
- **B** — control, identical body with the field removed

A cell that cannot run fails; the abort cap is 90s and a blown cap is a named failure.
Deviation from the app: the app sends `max_tokens >= 16000`. Cap size cannot affect whether a
body field is accepted, and a small cap keeps the live spend at ~23 tokens per cell.

```sh
node probe.mjs                  # tina4-thinker  -> out.txt
MD=tina4-coder node probe.mjs   # tina4-coder    -> out-coder.txt
```

## Result — PASS, exit 0 both runs

| model | cell | status | chunks | usage |
|---|---|---|---|---|
| `tina4-thinker` | A with field | 200 | 4 | `{"prompt_tokens":21,"completion_tokens":2,"total_tokens":23}` |
| `tina4-thinker` | B control | 200 | 4 | same |
| `tina4-coder` | A with field | 200 | 5 | same |
| `tina4-coder` | B control | 200 | 5 | same |

**The field is accepted.** The gateway does not reject it, streams normally, and returns a
usage block with a positive total. `run-20`'s last unverified claim is closed by running.

## What the control changed

Cell B — the same request **without** the field — returned the same 200, the same chunk count
and the same usage block. So on `mcp.tina4.com` the field is **harmless but not load-bearing**:
usage arrives either way. It stays in the code because a strict OpenAI-shaped gateway (vLLM,
OpenRouter) omits usage on a stream unless asked, which is the case the line was written for.
**That case is still unverified** — nobody has streamed through a third-party gateway yet.
Without the control cell this probe would have "proved" the field was doing work it is not
doing here.

Total live spend: 4 completions, 92 tokens.

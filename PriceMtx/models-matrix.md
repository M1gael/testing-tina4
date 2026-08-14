# Model matrix — intelligence, cost, speed, factuality × how you buy it

Checked **2026-08-14**. Confidence: **[V]** vendor/benchmark page verified · **[S]** secondary
source only · **[gap]** not found.

Companion to [`matrix.md`](matrix.md) (seat bundles) and
[`pricing-2026-08-14.md`](pricing-2026-08-14.md) (subscription prices).

---

## 0. Read this before the tables

Four things make a naive model comparison wrong, and all four bite here.

**a. "Model" is not the unit — model + effort is.** Claude Opus 5 scores **63** on the AA
Intelligence Index at `max`/`xhigh` effort and **61** at `high` **[S]**. Same model, same
price per token, different intelligence *and* different token spend. Any row below that
doesn't name an effort level is approximate by construction.

**b. Price per token ranks wrong. Cost per task ranks right.** Artificial Analysis measured
**GPT-5.6 Sol (max) at $1.04 per Intelligence Index task** vs **Claude Fable 5 (max) at
~$3.12** — roughly 3× — even though Fable's output price is only 1.67× Sol's ($50 vs $30 per
MTok) **[V]**. The gap is *tokens emitted per task*, not the rate card. Sol used ~15,000
output tokens per task **[V]**. A cheap-per-token model that thinks twice as long is not cheap.

**c. Hallucination numbers here are not usable for picking a model.** AA's metric is
explicitly *"a display-only Artificial Analysis factuality metric for the rate of incorrect
answers among non-correct responses"* **[V]** — that is abstention-sensitive: a model that
declines more often moves on this metric without becoming more truthful. Vectara's HHEM
measures something else entirely (summarize-this-passage faithfulness) and its published
table is dominated by small models, last updated **2026-05-11** **[V]**. Secondary reports of
frontier hallucination rates **flatly contradict each other** (see §4). Treat §4 as "here is
why you can't answer this from public data", not as a ranking.

**d. Two rate cards below expire.** DeepSeek re-prices **2026-08-16 — two days from now**.
Gemini 3.7/3.6 Flash rates hold only to **2026-12-31**. See §5.

---

## 1. Intelligence

Artificial Analysis Intelligence Index, August 2026 snapshot, 163–177 models tested.

| Model | Index | Source note |
|---|---:|---|
| Claude Opus 5 (adaptive, max / xhigh) | **63.0** | [S] — 61 at `high` effort |
| Claude Fable 5 (adaptive, max) | 62.1 | [S] — AA's own GPT-5.6 article lists Fable 5 (max) at **60**; sources conflict |
| Grok 4.6 | 60.9 | [S] |
| Kimi K3 | 59.7 | [S] — a second source says **57**; conflict |
| GPT-5.6 Sol (max) | 58.9 | [S] — AA article says **59** |
| GPT-5.6 Terra (max) | 55 | [V] AA article |
| GPT-5.6 Luna (max) | 51 | [V] AA article |
| DeepSeek V4 | 44 | [S] |
| Gemini 3.1 Pro | — | **[gap]** no index score found |
| Gemini 3.7 / 3.6 Flash | — | **[gap]** on this index |

**Coding Agent Index** (separate, and the more relevant one for a software company) **[V]**:
GPT-5.6 Sol (max) **80** — leading · Terra **77** · Luna **75**. No Claude/Gemini/Grok/Kimi
rows captured. **[gap]** — this is the single most decision-relevant gap in the whole file.

Spread is narrow at the top: **2.1 points separates 1st from 3rd**. Kimi K3 at 59.7 sits
inside that band as an *open* model, which is what makes its price relevant rather than
academic.

## 2. Token prices — every named model

Per 1M tokens, USD.

| Model | Input | Cached input | Output | Context | Conf |
|---|---:|---:|---:|---|---|
| **Claude Fable 5** | 10.00 | 1.00 | 50.00 | 1M | [V] |
| **Claude Opus 5** | 5.00 | 0.50 | 25.00 | 1M | [V] |
| **Claude Sonnet 5** | 2.00 | 0.20 | 10.00 | 1M | [V] |
| **Claude Haiku 4.5** | 1.00 | 0.10 | 5.00 | 200k | [V] |
| **GPT-5.6 Sol** | 5.00 | 0.50 | 30.00 | ≤272k | [V] |
| **GPT-5.6 Terra** | 2.50 | — | 15.00 | — | [V] |
| **GPT-5.6 Luna** | 1.00 | — | 6.00 | — | [V] |
| **Grok 4.6** | 2.00 / 4.00¹ | 0.50 / 1.00 | 6.00 / 12.00 | 500k | [V] |
| **Grok 4.5** | 2.00 / 4.00¹ | 0.30 / 0.60 | 6.00 / 12.00 | 500k | [V] |
| **Grok 4.3 / 4.20** | 1.25 / 2.50¹ | 0.20 / 0.40 | 2.50 / 5.00 | 1M | [V] |
| **Grok Build 0.1** | 1.00 / 2.00¹ | 0.20 / 0.40 | 2.00 / 4.00 | 256k | [V] |
| **Gemini 3.7 Flash** | 0.75² | 0.075 | 3.75² | — | [V] |
| **Gemini 3.6 Flash** | 0.75² | 0.075 | 3.75² | — | [V] |
| **Gemini 3.1 Pro Preview** | 2.00³ | 0.20 | 12.00³ | — | [V] |
| **Gemini 2.5 Flash-Lite** | 0.10 | 0.01 | 0.40 | — | [V] |
| **DeepSeek V4 Flash** (until 08-16) | 0.14 | **0.0028** | 0.28 | 1M | [V] |
| **DeepSeek V4 Pro** (until 08-16) | 0.435 | 0.003625 | 0.87 | 1M | [V] |
| **Kimi K3** | 3.00 | 0.30 | 15.00 | 1M | [S] |

¹ Grok bills **all** tokens at the higher rate once a request crosses the long-context
threshold — not a marginal rate. A single long request re-prices itself entirely.
² Holds through **2026-12-31**, increases 2027-01-01.
³ Scales by prompt length (≤200k vs >200k).

Standouts:

- **DeepSeek V4 Flash cache-hit input at $0.0028/MTok is ~180× cheaper than Opus 5's cache
  read** ($0.50). On cache-heavy repeated-prefix work the gap is not incremental.
- **Kimi K3 at $3/$15 buys index ~59.7 — inside 3.3 points of Opus 5 at $5/$25.** On paper the
  best intelligence-per-dollar among the named frontier models. Price is [S] though.
- **Gemini 3.7 Flash at $0.75/$3.75 is the cheapest fast frontier-adjacent option**, and the
  only one with a verified speed number (§3).

## 3. Output speed

Thinnest data in this file. AA publishes it; I could not extract a consolidated table.

| Model | Output t/s | Conf |
|---|---:|---|
| Gemini 3.7 Flash | ~340 | [S] — "nearly 3× GPT-5.6 Terra and GLM-5.2" |
| Gemini 3.6 Flash | ~303 | [S] — a second source says **135**; conflict |
| Qwen3.7 Flash | 199 | [S] |
| Grok 4.5 | ~70 | [S] |
| Claude Opus 5 / Fable 5 | — | **[gap]** |
| GPT-5.6 Sol / Terra / Luna | — | **[gap]** |
| Kimi K3, DeepSeek V4 | — | **[gap]** |

Non-frontier speed reference: Celeris-1 **1560 t/s**, Mercury 2 **820 t/s** **[V]**. Lowest
latency measured: Gemini 2.5 Flash-Lite **0.29s** TTFT **[V]**.

For interactive coding, TTFT and t/s matter more than index points. **This gap should be
closed on Artificial Analysis directly before any speed-sensitive choice.**

## 4. Factuality / hallucination — why there is no clean answer

**AA-Omniscience hallucination rate**, dated 2026-08-14, 163 models, lower is better.
Definition: *rate of incorrect answers among non-correct responses* — **display-only**, and
excluded from BenchLM's own model rankings **[V]**.

| Rank | Model | Rate |
|---:|---|---:|
| 1 | Command A+ | 14.2% |
| 2 | MiniMax M3 | 18.4% |
| 3 | MiMo-V2.5-Pro | 24.7% |
| 4 | **Grok 4.3** | 25.0% |
| 5 | Qwen3.7 Max | 25.6% |
| 6 | GLM-5.2 | 26.3% |
| 7 | Qwen3.7 Plus | 27.7% |
| 8 | Nemotron 3 Ultra | 29.7% |
| 9 | GLM-5.1 | 29.9% |
| 10 | MiMo-V2-Pro | 30.0% |
| … | (worst: Ling 2.6 Flash) | 96.7% |

Note what that top-10 is: **almost none of the frontier models are in it.** Cheap and
mid-tier models dominate. That alone should stop anyone using this metric as a proxy for
"trustworthy".

**Secondary reports of frontier rates, which contradict each other [S]:**

- One source: Claude Opus 5 **60.8%**, Grok 4.5 **54.1%**, GPT-5.1 **51.9%**, Gemini 3.1 Pro **50.9%**.
- Another source: Claude Opus 4.7 **36%** vs GPT-5.5 **86%**, calling it a 50-point gap.

Those cannot both be right about Claude. And the second source itself notes Claude gets its
number **"by declining to answer more often, not by being smarter at every question"** —
which is exactly the abstention artefact the metric definition warns about.

**Vectara HHEM** (different task — faithfulness when summarizing a supplied passage), last
updated **2026-05-11** **[V]**: finix_s1_32b 1.8% · gpt-5.4-nano 3.1% · gemini-2.5-flash-lite
3.3% · Phi-4 3.7% · Llama-3.3-70B 4.1%. **No frontier rows.** Useful if our workload is
document summarization; irrelevant to agentic coding.

**Conclusion for this column: do not buy on it.** If factuality matters for a specific
workload, the defensible move is to run our own eval on our own data. That is cheap compared
to a wrong seat decision, and it is the only number that would actually be about us.

---

## 5. Two rate cards that expire

### DeepSeek — re-prices **2026-08-16** (two days out) **[V]**

Peak hours **01:00–04:00 and 06:00–10:00 UTC**; off-peak is 50% of peak.

| Model | Now: in (miss) / out | From 08-16 peak | From 08-16 off-peak |
|---|---:|---:|---:|
| V4 Flash | 0.14 / 0.28 | **0.44 / 1.32** | 0.22 / 0.66 |
| V4 Pro | 0.435 / 0.87 | **1.32 / 3.96** | 0.66 / 1.98 |

Cache-hit input also moves: Flash **$0.0028 → $0.014** peak / $0.007 off-peak.

That is roughly a **3× increase at peak, 1.6× off-peak** on output. Any business case built on
today's DeepSeek numbers is wrong from Sunday. Off-peak-only batch scheduling keeps most of
the advantage — and the off-peak windows are UTC, so from **UTC+2 (SAST)** the peak bands are
03:00–06:00 and 08:00–12:00 local, meaning a normal SA working afternoon already sits
off-peak. Worth confirming against the vendor's own timezone wording before relying on it.

### Gemini 3.7 / 3.6 Flash — hold to **2026-12-31**, rise **2027-01-01** **[V]**

Anything built on $0.75/$3.75 needs a re-baseline before January.

---

## 6. The three ways to buy the same capability

This is the distinction the seat matrix didn't cover.

| Shape | What you get | Usable in third-party clients? | Cost control |
|---|---|---|---|
| **A. Seat with app quota, no key** | Vendor's own apps/CLI only | **No** | Fixed monthly, quota-limited |
| **B. Subscription that *is* a key** | Key/endpoint + a quota, not a token balance | **Yes** | Fixed monthly, quota-limited |
| **C. Metered key top-up** | Raw token billing | Yes | Prepaid credit or arrears |

### A — seats whose quota you cannot export

| Plan | Price | Quota shape | Conf |
|---|---|---|---|
| Claude Team standard / premium | $20 / $100 seat/mo (annual) | Usage tiers; **includes Claude Code**, no API key | [V] |
| Claude Max 5× | from $100/mo | 5×/20× Pro usage | [V] |
| ChatGPT / Codex — Free, Go, Plus, Pro, Business | $0 / $8 / $20 / from $100 / $20 seat annual ($25 mo) | Codex included on **every** tier; per-message pricing retired **2026-04-02**, now token-based credits | [S] |

**Claude subscriptions and ChatGPT both bill API usage separately from the seat.** The seat
quota does not become an API key. That is the structural difference from category B.

Reported reality check on Codex: OpenAI is quoted saying Codex averages **~$100–200 per
developer per month** with high variance by model, parallel instances, automations and Fast
mode **[S]**. If true, a $20 Plus/Business seat is an entry price, not the run rate — the
credits are what actually meter.

### B — subscriptions that behave like an API key

This is the category with the best headline value-for-money, and the most hidden terms.

**GLM Coding Plan (Z.ai)** **[S]** — the archetype:

| Tier | List | Intro (−30%) | Quota | MCP calls/mo |
|---|---:|---:|---|---:|
| Lite | $18/mo | $12.60 | ~80 prompts/5h, ~400/week | 100 |
| Pro | $72/mo | $50.40 | ~400 prompts/5h, ~2,000/week | 1,000 |
| Max | $160/mo | $112.00 | ~1,600 prompts/5h, ~8,000/week | 4,000 |

Works inside **Claude Code, Cline, Roo Code, OpenClaw and 20+ clients** **[S]** — i.e. it
substitutes for an Anthropic API key in our existing tooling.

**The catch is the quota unit.** GLM-5.2 and GLM-5-Turbo consume **3× quota in the
14:00–18:00 UTC+8 peak window and 2× off-peak**, with a 1× off-peak promo through end of
September **[S]**. So "2,000 prompts/week" is really 666–1,000 prompts/week of the good model,
and drops again when the promo lapses. **A "prompt" is also not a defined unit of work** — one
agent turn can be many prompts. This is not comparable to a token budget without measuring.
From **UTC+2**, that UTC+8 peak window is 08:00–12:00 local — the middle of our morning.

**Kimi app tiers** **[S]**: $19 / $39 / $99 / $199 per month. **Only the $99 (Allegro) and
$199 (Vivace) tiers include K3's full 1M context.** The API is separate and
OpenAI-compatible (`kimi-k3`, `MOONSHOT_API_KEY`, custom base URL) — so Kimi is reachable from
any OpenAI-compatible client via category C regardless of the app tier.

**GitHub Copilot credits** **[V]** — dollar-denominated credits ($15 / $70 / $200 at $10 /
$39 / $100) spendable across the model menu, but **only inside Copilot surfaces**. Nominally
2× face value at Pro+ and Max; a Copilot credit-dollar has no published token equivalent, so
that 2× is unverified and the crossover in `matrix.md` cannot be computed for it.

### C — metered top-up, and the gateways

**opencode Zen** **[V]** — pay-as-you-go gateway, prices mirroring the providers:

- Opus 5 $5/$25 · GPT-5.5 $5/$30 · DeepSeek V4 Flash $0.14/$0.28 — i.e. **no gateway markup
  observed** on these rows.
- **Free model tier** includes DeepSeek V4 Flash Free, MiMo-V2.5 Free, Nemotron 3 Ultra Free,
  Big Pickle, Hy3 Free, Laguna S 2.1 Free.
- Controls that matter for a fixed budget: **per-workspace and per-member monthly spend
  limits**, auto-reload ($20 when balance drops below $5, adjustable or off).
- Card processing passed through at cost: **4.4% + $0.30** per transaction — real, and it
  favours fewer larger top-ups.
- **BYOK for OpenAI and Anthropic**, billed direct by the provider, while still reaching other
  models through Zen. Team workspaces **free during beta**.

**Direct vendor keys** — Anthropic, OpenAI, xAI, Google, DeepSeek, Moonshot all sell raw
metered keys at the §2 rates. Anthropic adds **batch −50%** and **cache read at 0.1×**, which
stack **[V]**; Google and DeepSeek also publish batch/off-peak discounts.

### BYOK compatibility — which client accepts which key

| Client | Accepts your key for | Restrictions | Conf |
|---|---|---|---|
| **Cursor** | OpenAI (non-reasoning chat), Anthropic (all Claude), Google Gemini, Azure OpenAI, AWS Bedrock | **Chat models only** — tab completion stays on Cursor's models. BYOK in Agent/Ask needs **Pro or higher ($20+)**. Shared team keys via admin dashboard on **Enterprise only**. Requests still traverse Cursor infra, so team spend limits can block a BYOK call. | [S] |
| **opencode / Zen** | OpenAI, Anthropic direct; everything else via Zen credits | — | [V] |
| **Claude Code, Cline, Roo Code, OpenClaw + 20 others** | GLM Coding Plan endpoint | Quota-metered, not token-metered | [S] |
| Any OpenAI-compatible client | Kimi (`kimi-k3`), DeepSeek, Grok | Base-URL swap | [V]/[S] |

**Cursor BYOK is weaker than it sounds:** paying Cursor $20–40/seat *and* your own token bill,
while tab completion still runs on Cursor's models and shared keys need Enterprise. Nobody
saves money buying Cursor purely as a BYOK shell.

---

## 7. What this changes for the 10-seat decision

The seat recommendation in [`matrix.md`](matrix.md) (Claude Team standard ×10 + capped metered
pool, $400/mo) survives, but this file adds three moves worth pricing:

1. **Put the metered pool on cheap models, not frontier ones.** The pool exists for CI,
   batch and automation — where DeepSeek V4 off-peak, Gemini 3.7 Flash, or Kimi K3 do the work
   at a fraction of Opus 5. That makes a $200/mo cap go 5–20× further.
2. **Trial one GLM Coding Plan Pro seat ($50.40 intro / $72 list) against one Claude Team
   premium seat ($100)** on the same developer's real work for a month. Both drive Claude
   Code. If the GLM quota holds up under the 2–3× multiplier, it is roughly half the price for
   the heavy-user tier. Measure prompts-to-quota-exhaustion, not vibes.
3. **Use opencode Zen as the metered pool's spend gate**, not as a model source per se — the
   per-member monthly limits and prepaid auto-reload are exactly the hard-cap shape a fixed
   per-employee budget needs, and there was no markup on the rows checked. Weigh against the
   4.4% + $0.30 card fee and beta-stage team features.

Do **not** act on §1/§3/§4 rankings for a model choice yet — the Coding Agent Index is missing
for everything except GPT-5.6, speeds are missing for most frontier models, and the
factuality data is unusable as published.

## 8. Gaps, ranked by how much they'd change the answer

| # | Gap | Why it matters |
|---|---|---|
| 1 | **Coding Agent Index for Claude / Gemini / Grok / Kimi** | Only GPT-5.6 rows captured. For a software company this index outranks the general one |
| 2 | **Output t/s + TTFT for Opus 5, GPT-5.6, K3, DeepSeek V4** | Interactive coding is latency-bound; these are simply absent |
| 3 | **Cost per task beyond Sol and Fable 5** | The only cost metric that ranks correctly; AA has it, I have two rows |
| 4 | GLM "prompt" definition + real quota burn | Whole category-B business case rests on an undefined unit |
| 5 | Kimi K3 price verified at source | Currently [S]; it's the best intelligence-per-dollar candidate |
| 6 | OpenAI plan prices at source | Vendor pages 403'd; Codex/ChatGPT tiers all [S] |
| 7 | Gemini 3.1 Pro intelligence index | No score found at all |
| 8 | Whether Copilot credit-dollars ≈ API dollars | Determines if Pro+/Max 2× credit ratio is real value |

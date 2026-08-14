# The matrix — 10 seats, $100/seat/month ceiling

Priced 2026-08-14 from [`pricing-2026-08-14.md`](pricing-2026-08-14.md). Read that file for
sources and confidence markers.

## Inputs used

| Input | Value | Status |
|---|---|---|
| Headcount | 10 | given |
| Budget ceiling | **$100 per employee per month** → **$1,000/mo, $12,000/yr total** | given |
| Role split | assumed **7 engineering / 3 non-engineering** | **assumed — not confirmed** |
| Billing | annual where a discount exists | assumption |
| Currency | USD, **excluding VAT and FX** | see caveat below |
| Measured usage | none | **missing — see crossovers** |

Everything below is ex-VAT and ex-FX. If the $100 is a gross rand-equivalent budget, the
real USD room per seat is lower — VAT and card FX have to come off the top first. Google is
the only vendor here that quotes us in ZAR.

> The $100 was read as a **budget ceiling per employee per month**. If it was instead a
> statement of what we already spend, the analysis is unchanged — the question just becomes
> "can we beat $100/seat" instead of "what fits under $100/seat", and the same table answers it.

---

## Bundles priced at 10 seats

Annual-billing rates. `%` is share of the $1,000/mo ceiling consumed.

| # | Bundle | $/mo | $/yr | % of cap | Coverage |
|---|---|---:|---:|---:|---|
| 1 | Claude Team, 10 standard seats | **200** | 2,400 | 20% | Frontier chat + Claude Code for all 10 |
| 2 | ChatGPT Business, 10 seats **[S]** | 200 | 2,400 | 20% | Frontier chat for all 10; no terminal coding agent at this price |
| 3 | Copilot Pro, 10 seats | 100 | 1,200 | 10% | In-IDE completions + $15/user credits — thin for agentic work |
| 4 | **Claude Team standard ×10 + metered API pool (capped $200)** | **400** | **4,800** | **40%** | All 10 covered + budgeted automation/CI headroom |
| 5 | Copilot Pro+, 10 seats | 390 | 4,680 | 39% | Multi-model in-IDE, $70/user credits |
| 6 | Cursor Teams, 10 seats | 400 **+ arrears overage** | 4,800+ | 40%+ | Full IDE agent; **overage not capped** |
| 7 | Claude Team, 7 premium + 3 standard | 760 | 9,120 | 76% | Heavy coding tier for engineers, chat for the rest |
| 8 | Claude Team, 10 premium seats | 1,000 | 12,000 | **100%** | Everyone on 5× usage — exactly at the cap |
| 9 | Copilot Max, 10 seats | 1,000 | 12,000 | **100%** | $200/user credits — exactly at the cap |
| 10 | Two-vendor hedge: Claude Team std ×10 + ChatGPT Business ×10 | 400 | 4,800 | 40% | Both frontier families; **duplicate chat capability** |

The headline finding: **$100/seat/month is a generous budget for 10 people.** Full coverage
for all 10 starts at 20% of it. The risk here is not underfunding, it is overbuying — and
specifically buying the same capability twice.

## The single biggest waste to avoid

**Do not buy two agentic coding tools per developer.** A Claude Team seat already includes
Claude Code. Stacking Cursor Teams ($40) or Copilot Pro+ ($39) on top of a Claude premium
seat ($100) means paying twice for "an agent that edits my repo", and both are fronting
overlapping frontier models. Pick one primary coding agent per developer; add a second only
where a named workflow genuinely needs it, and record which workflow.

## Seat vs. token — where the crossover sits

A flat seat is worth buying when the user's metered spend would exceed the seat price. At
Anthropic's published rates, this is what each seat price has to displace per user per month:

| Seat price | Opus 5 input | Opus 5 output | Opus 5 cache reads | Sonnet 5 input | Sonnet 5 output |
|---|---:|---:|---:|---:|---:|
| $20 standard | 4 MTok | 0.8 MTok | 40 MTok | 10 MTok | 2 MTok |
| $100 premium | 20 MTok | 4 MTok | 200 MTok | 50 MTok | 10 MTok |

How to read it: a **$20 standard seat pays for itself the moment a user generates more than
~0.8M Opus-5 output tokens a month** — a low bar for anyone running a coding agent daily. A
**$100 premium seat needs ~4M Opus-5 output tokens** to beat metered billing, which is real
heavy-agent usage, not casual use.

Consequences:

- **Light users (occasional chat, no agent loops):** metered API would cost single-digit
  dollars — but there is no per-seat admin/SSO on a raw API key, and a $20 seat is cheap
  enough that the governance is worth more than the arbitrage. Buy the standard seat.
- **Heavy users (agentic coding most of the day):** flat seats win decisively, and the
  premium seat is the cheapest way to buy that ceiling. This is the opposite of the usual
  "metered is cheaper" instinct, and it is why per-seat plans exist at $100.
- **Automation and CI (no human at the keyboard):** metered, always. Batch API at 50% off
  plus prompt caching at 0.1× input make unattended work far cheaper per unit of work than
  any seat, and a seat can't be shared with a pipeline anyway.

Caveat that applies to this whole section: **these are theoretical crossovers.** No measured
token volumes exist yet, so we don't know which of our 10 people are heavy and which are
light. That is the one input that would make this exact instead of directional.

## Recommendation

**Buy bundle #4: Claude Team, 10 standard seats, annual, plus a metered Claude API account
with a hard spend cap — $400/mo, $4,800/yr, 40% of the ceiling.**

Why it wins:

1. **Full coverage at 20% of budget.** All 10 people get frontier chat *and* Claude Code on
   a $20 standard seat. No other bundle covers both capabilities that cheaply.
2. **It has a documented upgrade path that cannot breach the cap.** Standard and premium
   seats mix inside one Team. Upgrade only the users who actually hit their limits, at $100
   each. Worst case — all 10 upgrade — lands at exactly $1,000/mo, still inside budget. No
   other bundle can absorb a 5× usage increase without a renegotiation.
3. **The metered pool covers what seats can't.** CI, batch jobs, and scripted work get token
   billing with batch and caching discounts, on a spend cap we set.
4. **Team tier carries the governance we need at 10 people** — SSO, central billing,
   2–150 seat range.

Runner-up: **Copilot Pro+ ×10 at $390/mo.** It wins if the team is GitHub-native and values
one multi-model surface inside the IDE. It loses on two points: the $70/user credit
allowance is an opaque ceiling — a "credit dollar" has no published token equivalent, so we
cannot compute the crossover above for it — and the Business/Enterprise admin tier we would
actually buy at company scale is not priced on the public page.

Why the others lost:

- **Cursor Teams (#6)** — $40/seat is competitive, but overage is *billed in arrears* with
  no published hard cap. For a fixed per-employee budget, an uncapped arrears line is the
  wrong risk shape. Reconsider if Cursor exposes a hard org spend limit.
- **ChatGPT Business alone (#2)** — same $20/seat as Claude Team standard but, at that
  price, no equivalent terminal coding agent included. Also our weakest-sourced price.
- **Google AI plans** — the ZAR billing is genuinely attractive (no FX, local invoicing) and
  worth keeping for non-engineering staff, but no per-seat business tier with admin controls
  surfaced, so it can't be the backbone of a company buy yet.
- **#8 / #9 (everyone at $100)** — both sit exactly at the ceiling on day one, with zero
  headroom for a price rise, a new hire, or a usage spike. Buying the top tier before
  measuring is the definition of overbuying here.

### First 30 days

1. Buy 10 Claude Team standard seats, annual.
2. Open the metered API account, set a hard monthly cap (start $200) and per-key budgets.
3. Measure: who hits usage limits, and what the metered pool actually consumes.
4. Upgrade *only* the limit-hitters to premium seats. Re-price this matrix with the real
   numbers.

### Revisit triggers

- Any vendor announces a price change (Gemini Flash rates rise **2027-01-01**; Sonnet 5 and
  ChatGPT Business both moved during 2026).
- Headcount crosses ~15, or the engineering/non-engineering split changes materially.
- Three consecutive months where the metered pool exceeds its cap — that means work should
  move onto seats, or the cap is set wrong.
- A client contract imposes a data-residency or retention requirement (US-only inference
  carries a documented 1.1× multiplier).

## What is still assumed, and what it would change

| Assumption | If wrong |
|---|---|
| 7 engineers / 3 non-engineering | Changes only bundle #7's mix, not the recommendation — #4 is role-agnostic |
| $100 is a ceiling, not current spend | No change to the ranking |
| No client data-residency constraints | US-only pinning adds 1.1× to metered tokens; some cheaper options may be vetoed outright |
| VAT and FX absorbed outside this budget | If the $100 is gross, every USD figure needs grossing up before comparison to the cap |
| Nobody needs two coding agents | Adding a second agent per dev roughly doubles the per-dev tool line |

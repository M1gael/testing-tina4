# PriceMtx — AI tooling value-for-money matrix

## Why this directory exists

We have to buy AI tooling for **every employee at the software company**, and we do not yet
know which combination of products gives the most capability per rand spent. This directory
is the working space for answering that question with numbers instead of vibes.

The goal is **not** "pick the best AI tool". It is to find the best *combination* — the seat
subscriptions, the API keys, the free tiers, and the self-hosted options — that together cover
what each role actually does, at the lowest total monthly cost.

## The question, stated precisely

> For a team of N people in known role mixes, which bundle of AI subscriptions and API keys
> covers the required workloads at the lowest total cost per month, and where are the cliffs
> where a different bundle becomes cheaper?

Sub-questions this directory must answer:

1. **Seat vs. token.** Where does a flat per-seat subscription beat metered API billing, and at
   what usage volume does the crossover happen? (Heavy users subsidise light users on flat
   plans; the reverse on metered.)
2. **Overlap.** Which products duplicate each other, so we are paying twice for the same
   capability (e.g. an IDE assistant plus a CLI agent plus a chat plan, all fronting the same
   frontier models).
3. **Role fit.** Not everyone needs a frontier-model coding agent. Which roles need what, and
   what is the cheapest adequate tier per role rather than one blanket plan for all.
4. **Bring-your-own-key.** Which tools accept our own API keys, letting us consolidate spend
   onto one metered account with volume/committed-use discounts instead of many seat fees.
5. **Cost controls.** Which options support hard spend caps, per-user budgets, prompt caching,
   batch pricing, and cheaper-model routing — the levers that change the bill without changing
   the tool.
6. **Non-price constraints that can veto a cheap option.** Data residency, training-on-our-data
   terms, retention windows, client contractual restrictions, SSO/audit requirements, and
   procurement friction (card vs. invoice, ZAR vs. USD, VAT treatment, FX exposure).

## Definition of "value for money"

A candidate bundle is scored on:

- **Total monthly cost** at our real headcount and usage, in ZAR, VAT and FX included — not
  headline USD list price.
- **Coverage** — what fraction of the required workloads it actually handles, per role.
- **Ceiling** — whether it caps out (rate limits, message quotas, context limits) during normal
  work, forcing a second purchase anyway.
- **Switching cost** — how locked in we become, and what it costs to leave.
- **Risk** — terms, compliance, and vendor stability.

Cheapest bundle that fully covers a role wins. A bundle that is cheaper but leaves gaps is only
comparable once the cost of filling those gaps is added to it.

## Method

1. **Inventory the work.** List the actual AI-assisted workloads by role (code authoring,
   review, docs, test generation, support triage, design, data work, meeting/admin overhead).
2. **Inventory the market.** Per-seat products, metered APIs, and self-hosted/open-weight
   options. Record list price, billing unit, limits, and terms — with a source link and a
   date-checked stamp on every number, because this pricing moves.
3. **Measure our usage.** Pull real token/request volumes from whatever we already run, so the
   model is fed measured numbers, not guesses. Where no data exists, state the assumption
   explicitly and mark it as an assumption.
4. **Build the matrix.** Bundles × roles × cost, with the crossover points calculated.
5. **Sensitivity-check.** Re-run at ±50% usage and at a different headcount. A bundle that only
   wins in one narrow scenario is not the answer.
6. **Recommend**, with the runner-up and the reason it lost, so the decision can be revisited
   when prices change.

## Ground rules

- **Every price carries a source and a date.** No remembered or inferred pricing. Vendor pricing
  pages and official docs only.
- **Model the bill, not the sticker.** Include minimums, annual-vs-monthly deltas, seat floors,
  overage rates, tax, and FX.
- **State assumptions inline.** Any number we invented gets labelled as invented.
- **No vendor advocacy.** The output is a comparison, not a pitch.

## Inputs

Known:

- [x] **Headcount: 10.**
- [x] **Budget ceiling: $100 per employee per month** → $1,000/mo, $12,000/yr total.

Still needed (the matrix is directional, not exact, until these land):

- [ ] Role split — currently **assumed** 7 engineering / 3 non-engineering.
- [ ] Which AI tools/subscriptions we already pay for, and current monthly spend.
- [ ] Measured usage volumes for anything already metered — this is the one input that
      turns the seat-vs-token crossovers from theoretical into decisive.
- [ ] Compliance/contractual constraints from clients on where data may go.
- [ ] Procurement constraints — billing currency, invoice vs. card, approval threshold.
      (Note: Google quotes us in ZAR; Anthropic, OpenAI, GitHub and Cursor quote USD.)

## Layout

| Path | What |
|---|---|
| `readme.md` | This charter — the question, the scoring rules, the method |
| `pricing-2026-08-14.md` | Dated pricing snapshot, per vendor, with sources and confidence markers |
| `matrix.md` | Ten bundles priced at 10 seats, seat-vs-token crossovers, recommendation, revisit triggers |
| `models-matrix.md` | Per-model intelligence / token price / speed / factuality, plus the three acquisition shapes (app-quota seat, subscription-as-API-key, metered top-up) and BYOK compatibility |
| *(to be added)* | Workload/role inventory, once the role split is confirmed |
| *(to be added)* | Measured usage baseline |

## Scope note

This directory is a procurement/evaluation workspace. It is unrelated to the Tina4 QA harness
that occupies the rest of this repository, and nothing here is governed by that harness's
testing protocol.

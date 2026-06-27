# SPICE — Architecture, Hero Demo & 48h Build Plan

*Built real end-to-end: real quant engine, real on-chain execution (testnet / paper), lean local frontend.*

---

## Architecture

```
  DATA (synthetic, we generate it)  ANALYSE (the brain)         EXECUTION (programmable money)
  ────────────────────────────────  ─────────────────────       ───────────────────────────────
   - synthetic financials           Forecasting (commodity   ┌─▶ Alpaca options on commodity ETFs
   - cost ledger                      history)                │    (HERO, paper) — calls/puts on
   - wallet                          Cost-center decomposition│    WEAT / UNG / USO …
        │                             (budget share, variance,│    └ Hyperliquid = on-chain fallback
        ▼                              cost of insurance)      ├─▶ Aave / Morpho (testnet) — yield /
   ORCHESTRATOR + specialists        Propagation & MacroRisk   │    borrow to fund premiums
   (Claude Opus 4.8, plain SDK) ───────────────────────────── ├─▶ Escrow contract — parametric
                                                               │    insurance, pays out on trigger
                                                               └─▶ x402 / Polymarket / Bridge (stretch)

                          FRONT DEMO (lean, local Next.js):
                          Opportunity → Wedge/GTM → Big model (data moat) → Tech & live demo
```

**The spine:** ordinary financials in → the engine finds hidden commodity exposure and forecasts the margin hit → the orchestrator decides the hedge mix → executes across venues → re-forecast shows the risk collapsed. The brain is deep and real; the venues are thin-but-real.

**Demo vs production scope:** the hackathon demo runs on **synthetic data + testnet/paper venues, no real funds.** The production product adds the real-money rails — **Open Banking**, bank/wallet connections, custody, KYC — which are pitch/vision, not weekend scope.

---

## The hero demo — "The bakery that hedges like a trading desk"

A continuous ~2-minute story. Real engine output, real testnet/paper execution, one live dramatic payout.

**Client (synthetic):** *Maison Levain*, a Lyon bakery, ~€1.4M revenue. Real, relatable, and secretly a commodity book: flour (wheat), oven (gas), ovens + fridges (electricity), butter (fats).

**The flow:**
1. **Ingest** the bakery's accounting (synthetic data we generate) + cash position. ~30s.
2. **The engine thinks out loud** (agent activity feed): it **decomposes the cost structure** — "41% of your costs are wheat, 22% energy (gas + power), 11% fats" — forecasts a wheat + gas spike from commodity history, and **propagates** it to margin: "net margin falls from 11% to 4% over the next quarter." This is the quant "holy shit": a bakery's P&L re-expressed as a commodity portfolio with a VaR.
3. **The orchestrator proposes a hedge** and reasons through it, then executes across three venues:
   - **Alpaca options on ETFs (hero, paper):** buys calls on a wheat ETF + a gas ETF (e.g. WEAT, UNG) to offset the input-cost exposure. Hyperliquid is the on-chain fallback if Alpaca's API is blocked.
   - **Escrow / parametric insurance:** takes a policy that pays out if an energy-price index crosses a trigger.
   - **Aave/Morpho (testnet):** sweeps idle cash into yield to fund the hedge premiums, recallable.
4. **Re-forecast:** the margin distribution tightens, VaR drops. Before/after risk curve, side by side.
5. **Live beat:** trigger the price spike on stage → the options hedge gains and the escrow pays out → the bakery's margin holds while an unhedged peer's collapses. The AI didn't predict the risk, it *pre-bought protection that just paid out*.
6. **The vision close:** "Multiply this by a million ordinary businesses and you don't just have a hedging tool — you have the real-time micro-map of the entire real economy. That's what we sell to hedge funds and central banks."

**Why it beats the room:** real quant + real on-chain execution + the most ordinary imaginable business. Everyone else demos a chat box over a spreadsheet. Spice turns a boulangerie into a hedge fund and shows the macro endgame.

---

## The pitch order (from your schema)

1. **Opportunity** — every ordinary business is an unhedged commodity trader; the rails to fix it just arrived.
2. **Problem → Solution** — they're blind and exposed; Spice sees, forecasts, and hedges autonomously.
3. **Rising market** — Stripe (Bridge) and Circle cracked stablecoin payments but stopped there; nobody cracked the **real-world risk layer**. That's the frontier, and it's the YC stablecoin RFS.
4. **How it works** — the live demo above.
5. **The big model** — cash + data pooling → the macro intelligence central banks can't get → the décacorn.

---

## Build plan — 48h, team of 5

### Stack
- **Engine (quant):** Python. Forecasting on commodity price history (the "T0" model or an AI black-box agent), cost-center decomposition (budget share, variance, cost of insurance), shock propagation to margin, before/after VaR. Real math, bounded scope.
- **Agents:** **Claude Opus 4.8**, plain Anthropic SDK tool-calling (no graph framework). One **orchestrator** + specialists: **Risk/Analysis**, **Hedging** (options + escrow insurance), **Placement** (Aave/Morpho yield). Tools: `decompose_costs`, `forecast_commodity`, `propagate_shock`, `hedge_options`, `lend_aave`, `take_escrow_policy`, `recall_cash`.
- **Execution:** Alpaca options on commodity ETFs (paper) as the derivatives hero, Hyperliquid as on-chain fallback; Aave/Morpho on testnet (lending, trivial `sendFrom`); an Escrow contract (parametric payout). x402 / Polymarket / Bridge.xyz are optional stretch.
- **Frontend (3 screens, demo-only — in production the agent runs headless):** lean local **Next.js + Tailwind**, nicely made but not load-bearing. (1) **Dashboard** — enterprise KPI tiles + AI status. (2) **Analyse** — cost decomposition, forecast, before/after VaR, and the AI's recommendations (*conseils*). (3) **Execution** — the specialist agents (Hedging, Placement) acting live across the options + on-chain venues, with the activity feed. No auth, no onboarding. *(Detailed design → `/plan-design-review`.)*
- **Data:** synthetic + benchmark. The founders build the commodity→input mapping KB + 2–3 synthetic businesses (bakery hero, trucking, plastics shop) and a commodity price history feed.

### Who builds what
- **Quant:** the analysis engine end to end (decomposition → forecast → propagation → VaR). *Owns the depth.*
- **Blockchain/fullstack dev:** the three on-chain venues (Hyperliquid hedge, Aave/Morpho lend, Escrow payout) + x402 wiring. *Owns credibility.*
- **Frontend/data + fullstack:** the Next.js front demo, agent activity feed, synthetic data generation. *Owns the show.*
- **Founder 1 (you):** orchestrator + specialist agents, the venue-routing logic, integration glue. *Owns the brain's behavior.*
- **Founder 2 (Sara):** commodity→input mapping KB, synthetic businesses + scenarios, the quant↔agent bridge, and the pitch narrative. *Owns the story + the data.*

### Timeline (48h)
- **H0–6:** freeze the hero script; define the commodity→input mapping + synthetic bakery; scaffold Next.js; deploy Escrow + testnet tokens; stub the 7 agent tools with realistic returns; confirm Alpaca options (paper) access, Hyperliquid fallback ready.
- **H6–18:** quant engine real (decomposition → forecast → propagation → VaR); orchestrator produces a coherent narrated hedge plan over the synthetic bakery.
- **H18–30:** wire real execution — Alpaca options hedge (paper), Aave lend, Escrow policy + payout; explorer / fill links in the UI.
- **H30–42:** front demo (risk dashboard + before/after curve + activity feed); choreograph the 2-minute flow + the live trigger/payout beat.
- **H42–48:** rehearse to death. Pre-fund wallets, paper/testnet only, recorded fallback. Lock the pitch order above.

### Risks & mitigations
- **Three venue integrations in 48h** → the brain is the priority; if a venue slips, Alpaca options + Escrow are the two that must be live, Aave is the easy third, x402/Polymarket/Bridge are cut first.
- **Live trigger flakiness** → controllable mock oracle for the escrow + pre-warmed positions; recorded backup of the exact tx flow.
- **Alpaca API access** → if Alpaca's options API is blocked or slow, fall back to Hyperliquid (on-chain, open API) for the derivatives leg. Decide in H0–6.
- **Quant scope creep** → bound it: decomposition + one forecast + one propagation + one before/after VaR. No multi-factor model, no full backtest engine for the demo.

---

## Verification — before stage
1. **Engine:** changing the synthetic bakery's cost mix changes the decomposition and the VaR correctly (not hardcoded).
2. **Execution:** the Alpaca options fill (paper), the Aave deposit, and the Escrow payout are all visible on the venue / on-chain with the agent as actor.
3. **Live beat:** triggering the price spike makes the hedge gain and the escrow pay out, on stage, repeatably (≥5 clean runs + recorded fallback).
4. **Agents:** the activity feed shows real tool calls and reasoning; changing a seed changes the hedge plan.

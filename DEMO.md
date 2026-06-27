# SPICE — Architecture, Hero Demo & 48h Build Plan

*Built real end-to-end: real quant engine, real on-chain execution (testnet / paper), lean local frontend.*

---

## Architecture

```
  PME (data in)            ANALYSE (the brain)              PROGRAMMATIC MONEY (execution)
  ───────────────          ─────────────────────            ──────────────────────────────
  Pennylane         ┐                                  ┌──▶ Hyperliquid   leveraged commodity
  Open Banking      ├──▶  Forecasting (commodity hist) │     (HERO)        hedge (call/put/perp),
  Enterprise data   │     Cost-center decomposition    │                   leverage = low capital
  (annual accounts) │     (budget share + variance     │
  Wallet            ┘      + cost of insurance)         ├──▶ Aave / Morpho  idle cash → yield /
                          Propagation & MacroRisk       │     (testnet)      borrow to fund premiums
                                  │                      │
                                  ▼                      ├──▶ Escrow         parametric insurance,
                          ORCHESTRATOR AGENT  ──x402──▶  │     contract       pays out on trigger
                          + specialist agents            │
                          (Claude Opus 4.8,              ├──▶ Polymarket     real-world event hedge
                           plain SDK tool-calling)       │     (stretch)
                                                         └──▶ Bridge.xyz     fiat on/off-ramp (stretch)

                          FRONT DEMO (lean, local Next.js):
                          Opportunity → Wedge/GTM → Big model (data moat) → Tech & live demo
```

**The spine:** ordinary financials in → the engine finds hidden commodity exposure and forecasts the margin hit → the orchestrator decides the hedge mix → executes across venues via x402 → re-forecast shows the risk collapsed. The brain is deep and real; the venues are thin-but-real.

---

## The hero demo — "The bakery that hedges like a trading desk"

A continuous ~2-minute story. Real engine output, real testnet/paper execution, one live dramatic payout.

**Client (synthetic):** *Maison Levain*, a Lyon bakery, ~€1.4M revenue. Real, relatable, and secretly a commodity book: flour (wheat), oven (gas), ovens + fridges (electricity), butter (fats).

**The flow:**
1. **Ingest** the bakery's accounting (synthetic Pennylane-style export) + bank data. ~30s.
2. **The engine thinks out loud** (agent activity feed): it **decomposes the cost structure** — "41% of your costs are wheat, 22% energy (gas + power), 11% fats" — forecasts a wheat + gas spike from commodity history, and **propagates** it to margin: "net margin falls from 11% to 4% over the next quarter." This is the quant "holy shit": a bakery's P&L re-expressed as a commodity portfolio with a VaR.
3. **The orchestrator proposes a hedge** and reasons through it, then executes across three venues:
   - **Hyperliquid (hero):** opens a small leveraged long on wheat + gas to offset the input-cost exposure — little capital because of leverage.
   - **Escrow / parametric insurance:** takes a policy that pays out if an energy-price index crosses a trigger.
   - **Aave/Morpho (testnet):** sweeps idle cash into yield to fund the hedge premiums, recallable.
4. **Re-forecast:** the margin distribution tightens, VaR drops. Before/after risk curve, side by side.
5. **Live beat:** trigger the price spike on stage → the Hyperliquid hedge gains and the escrow pays out → the bakery's margin holds while an unhedged peer's collapses. The AI didn't predict the risk, it *pre-bought protection that just paid out*.
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
- **Agents:** **Claude Opus 4.8**, plain Anthropic SDK tool-calling (no graph framework). One **orchestrator** + specialists (risk, derivatives, lending, insurance). Tools: `decompose_costs`, `forecast_commodity`, `propagate_shock`, `hedge_hyperliquid`, `lend_aave`, `take_escrow_policy`, `recall_cash`.
- **Execution:** Hyperliquid (derivatives), Aave/Morpho on testnet (lending, trivial `sendFrom`), an Escrow contract (parametric payout). **x402** as the agent payment rail. Polymarket + Bridge.xyz are stretch.
- **Frontend:** lean local **Next.js + Tailwind** — pitch-shaped flow, a risk dashboard (cost decomposition + before/after VaR), and the agent activity feed. No auth, no onboarding.
- **Data:** synthetic + benchmark. The founders build the commodity→input mapping KB + 2–3 synthetic businesses (bakery hero, trucking, plastics shop) and a commodity price history feed.

### Who builds what
- **Quant:** the analysis engine end to end (decomposition → forecast → propagation → VaR). *Owns the depth.*
- **Blockchain/fullstack dev:** the three on-chain venues (Hyperliquid hedge, Aave/Morpho lend, Escrow payout) + x402 wiring. *Owns credibility.*
- **Frontend/data + fullstack:** the Next.js front demo, agent activity feed, data-connector mocks (Pennylane/Open Banking). *Owns the show.*
- **Founder 1 (you):** orchestrator + specialist agents, the venue-routing logic, integration glue. *Owns the brain's behavior.*
- **Founder 2 (Sara):** commodity→input mapping KB, synthetic businesses + scenarios, the quant↔agent bridge, and the pitch narrative. *Owns the story + the data.*

### Timeline (48h)
- **H0–6:** freeze the hero script; define the commodity→input mapping + synthetic bakery; scaffold Next.js; deploy Escrow + testnet tokens; stub the 7 agent tools with realistic returns; confirm Hyperliquid + x402 access.
- **H6–18:** quant engine real (decomposition → forecast → propagation → VaR); orchestrator produces a coherent narrated hedge plan over the synthetic bakery.
- **H18–30:** wire real execution — Hyperliquid hedge, Aave lend, Escrow policy + payout; x402 connecting brain → venues; explorer links in the UI.
- **H30–42:** front demo (risk dashboard + before/after curve + activity feed); choreograph the 2-minute flow + the live trigger/payout beat.
- **H42–48:** rehearse to death. Pre-fund wallets, paper/testnet only, recorded fallback. Lock the pitch order above.

### Risks & mitigations
- **Three venue integrations in 48h** → the brain is the priority; if a venue slips, Hyperliquid + Escrow are the two that must be live, Aave is the easy third, Polymarket/Bridge are cut first.
- **Live trigger flakiness** → controllable mock oracle for the escrow + pre-warmed positions; recorded backup of the exact tx flow.
- **API access (IBKR/Alpaca blocked)** → Hyperliquid is the answer (onchain, open API). Confirmed in H0–6, no Plan B needed on the derivatives leg.
- **Quant scope creep** → bound it: decomposition + one forecast + one propagation + one before/after VaR. No multi-factor model, no full backtest engine for the demo.

---

## Verification — before stage
1. **Engine:** changing the synthetic bakery's cost mix changes the decomposition and the VaR correctly (not hardcoded).
2. **Execution:** the Hyperliquid hedge, the Aave deposit, and the Escrow payout are all visible on-chain / on the venue with the agent wallet as actor.
3. **Live beat:** triggering the price spike makes the hedge gain and the escrow pay out, on stage, repeatably (≥5 clean runs + recorded fallback).
4. **Agents:** the activity feed shows real tool calls and reasoning; changing a seed changes the hedge plan.

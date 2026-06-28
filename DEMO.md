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

## Eng-review decisions (locked 2026-06-27)

**D1 — On-stage P&L comes from the scenario engine, not live quotes.** The quant engine outputs a position-level P&L under the triggered shock; the UI shows that as the live number. Real venue artifacts (order id, tx hash) sit next to it as proof. Never wire the climax to live option prices (options barely move in 2 min and thin ETF options may not quote).

**D2 — Three processes, boundaries on language lines.** One Python service = orchestrator + quant engine (in-process modules). The existing Alpaca FastAPI stays its own service. One Node service = blockchain (Aave/Morpho + Escrow, viem/Solidity). The Next.js frontend talks ONLY to the orchestrator (REST + WebSocket for the activity feed). No separate quant HTTP service.

**D3 — Weekend reality (markets closed Sat+Sun): the live settlement beat is on-chain.**
- **Aave deposit + Escrow payout (testnet) are the live "real money moves" beat** — they run 24/7 and actually settle on stage tomorrow.
- **Alpaca stays real without a fill:** the agent resolves a real OCC option contract (`/chain` works market-closed) and submits a real paper order that queues (status `accepted`, fills Monday) for a real order id. **2-min check today:** submit one test paper option order; if it returns an order id, the queued-order proof is live; if it rejects, show "contract resolved + order prepared" instead.
- **Hyperliquid dropped as the derivatives fallback** — it has crypto perps, not commodity exposure, so it can't hedge wheat/gas. The derivatives leg is Alpaca-only.

**Jury calibration:** on-chain is the rail, not the thesis. Lead with real-economy risk + serious quant; present on-chain as "programmable, 24/7, instant, low-minimum," not a crypto bet. The jury knows stablecoins exist but won't be crypto-bullish ex ante.

**Code-quality notes (Alpaca backend, already built — `alpaca-backend/`):**
- Solid, keep: `client`/`service`/`contracts` split, the FR+EN exposure registry + word-boundary inference (`infer_exposures`), error handling, tests.
- Fix (~5 min): `alpaca/client.py` imports `from ibkr.config import alpaca_settings` — move shared settings to a neutral `config.py` so Alpaca doesn't depend on the `ibkr` namespace.
- Defer: README + FastAPI titles say "YIELD"/"ibkr-backend" → rename to Spice. The dead IBKR module is harmless once config is extracted.

**Test priority (right-sized for 48h):** the one path that must be correct is the **quant scenario P&L math** (decomposition → shock → position P&L → VaR) — the demo's believability rests on it. Unit-test that + the inference mapping. Smoke-test orchestrator tool-routing and the on-chain settlement call. Skip exhaustive coverage.

---

## Design decisions (locked 2026-06-27, plan-design-review)

Full system in `DESIGN.md`. Aesthetic: **premium fintech, épuré** — calm, money-grade,
not a generic SaaS dashboard. The quant is the proof; the design is the believability layer.

- **DR1 — Direction:** light, refined, one deep-green accent, terracotta for risk only.
  Borderless cards on warm paper, quiet status dots (no filled pills), generous air.
  Type: **Satoshi** + **Spline Sans Mono** (tabular numerics). Picked over a dark
  trading-desk variant and an editorial-brand variant.
- **DR2 — Projection:** keep the light UI; tune contrast + min type (≥12.5px) for the
  room; verify on the real projector at rehearsal (H42–48). Warm off-white (`#F4F3EF`),
  not pure white, to cut glare.
- **DR3 — Language:** fully English chrome ("Recommendations", "Bakery", "Run risk
  analysis"); keep the proper noun *Maison Levain*.
- **DR4 — Motion:** choreographed but safe — count-up numbers, feed types in event-by-event
  over SSE, margin-collapse transition, climax banner slides in. Timing from the scenario
  clock (deterministic, D1) → repeatable across ≥5 runs; recorded fallback if a venue hangs.
- **Two hero visuals carry the demo:** the **margin collapse** on Analyse (11.0% → 3.3%,
  terracotta) and the **deep-ink payout banner** on Execution (VaR 13.1% → 2.0%, margin
  held 11% vs peer 3.3%, +€107.5k). Everything else stays calm so these land.
- **Interaction states** (loading / empty / settled / error+fallback) are specified per
  surface in `DESIGN.md` — the demo *is* the live SSE stream, so states are load-bearing.

### Approved mockups
Built as real HTML (Satoshi + Spline Sans Mono), convertible straight to Next.js + Tailwind.

| Screen | Mockup |
|--------|--------|
| Dashboard | `~/.gstack/projects/briacSck-spice-finance-YC-hack/designs/dashboard-variants-20260627/variant-B2.png` |
| Analyse | `~/.gstack/projects/briacSck-spice-finance-YC-hack/designs/analyse-20260627/analyse-v2.png` |
| Execution | `~/.gstack/projects/briacSck-spice-finance-YC-hack/designs/execution-20260627/execution-v2.png` |
| 3-screen board | `~/.gstack/projects/briacSck-spice-finance-YC-hack/designs/spice-3screen-board.html` |

### NOT in scope (deferred, with rationale)
- **Responsive / mobile** — demo is fixed 1280×832; production runs headless. No viewport work.
- **Dark theme** — single light theme; revisit only if the rehearsal projector glares badly.
- **Auth / onboarding / settings** — demo has none; out of the 48h.
- **Real charting lib** — the donut + bars are hand-rolled CSS; no D3/Recharts dependency for the demo.

---

## The hero demo — "The bakery that hedges like a trading desk"

A continuous ~2-minute story. Real engine output, real testnet/paper execution, one live dramatic payout.

**Client (synthetic):** *Maison Levain*, a Lyon bakery, ~€1.4M revenue. Real, relatable, and secretly a commodity book: flour (wheat), oven (gas), ovens + fridges (electricity), butter (fats).

**The flow:**
1. **Ingest** the bakery's accounting (synthetic data we generate) + cash position. ~30s.
2. **The engine thinks out loud** (agent activity feed): it **decomposes the cost structure** — "41% of your costs are wheat, 22% energy (gas + power), 11% fats" — forecasts a wheat + gas spike from commodity history, and **propagates** it to margin: "net margin falls from 11% to 4% over the next quarter." This is the quant "holy shit": a bakery's P&L re-expressed as a commodity portfolio with a VaR.
3. **The orchestrator proposes a hedge** and reasons through it, then executes across three venues:
   - **Alpaca options (real contract, paper):** resolves a real commodity-ETF option (e.g. UNG/USO) and submits a real paper order; markets are closed this weekend so it queues (real order id, fills Monday). The hedge's P&L is shown from the scenario engine (D1), not a live fill.
   - **Escrow / parametric insurance (testnet):** takes a heatwave policy that pays out automatically if a regional heat index crosses a trigger — protection against an aléa the options can't touch (lost footfall + broken refrigeration are not a tradeable price).
   - **Aave/Morpho (testnet):** sweeps idle cash into yield to fund the hedge premiums, recallable.
4. **Re-forecast:** the margin distribution tightens, VaR drops. Before/after risk curve, side by side.
5. **Live beat (on-chain, settles on stage):** trigger the heatwave → the heat index crosses the trigger, the Escrow parametric policy pays out and the Morpho position is recalled, **live on testnet** (24/7, works this weekend) → the scenario engine shows the bakery's margin holding while an unhedged peer's collapses. The AI didn't predict the risk, it *pre-bought protection that just paid out* — and a traditional insurer would still be sending an adjuster. **One 2026 heatwave hit this bakery three ways — spiked input prices (options), stranded idle cash (Morpho yield), and collapsed footfall + broke refrigeration (parametric payout) — and Spice caught all three.**
6. **The vision close:** "Multiply this by a million ordinary businesses and you don't just have a hedging tool — you have the real-time micro-map of the entire real economy. That's what we sell to hedge funds and central banks."

**Why it beats the room:** real quant + real on-chain execution + the most ordinary imaginable business. Everyone else demos a chat box over a spreadsheet. Spice turns a boulangerie into a hedge fund and shows the macro endgame.

---

## The pitch order (from your schema)

1. **Opportunity** — every ordinary business is an unhedged commodity trader; the rails to fix it just arrived.
2. **Problem → Solution** — they're blind and exposed; Spice sees, forecasts, and hedges autonomously.
3. **Rising market** — Stripe (Bridge) and Circle cracked stablecoin payments but stopped there; nobody cracked the **real-world risk layer**: using programmable rails to let an ordinary business hedge, insure, and finance itself. That's the frontier. *(Lead with the real-economy value; the rails are plumbing, not a crypto thesis.)*
4. **How it works** — the live demo above.
5. **The big model** — cash + data pooling → the macro intelligence central banks can't get → the décacorn.

---

## Build plan — 48h, team of 5

### Stack
- **Engine (quant):** Python. Forecasting on commodity price history (the "T0" model or an AI black-box agent), cost-center decomposition (budget share, variance, cost of insurance), shock propagation to margin, before/after VaR. Real math, bounded scope.
- **Agents:** **Claude Opus 4.8**, plain Anthropic SDK tool-calling (no graph framework). One **orchestrator** + specialists: **Risk/Analysis**, **Hedging** (options + escrow insurance), **Placement** (Aave/Morpho yield). Tools: `decompose_costs`, `forecast_commodity`, `propagate_shock`, `hedge_options`, `lend_aave`, `take_escrow_policy`, `recall_cash`.
- **Execution:** Alpaca options on commodity ETFs (paper) for the derivatives leg (real contract + queued order this weekend); Aave/Morpho on testnet (lending, trivial `sendFrom`); an Escrow contract (parametric payout) — the on-chain legs are the live settlement beat. Hyperliquid dropped (crypto perps, no commodity exposure). x402 / Polymarket / Bridge.xyz are optional stretch.
- **Frontend (3 screens, demo-only — in production the agent runs headless):** lean local **Next.js + Tailwind**, premium-fintech aesthetic (épuré), legible on a projector. (1) **Dashboard** — client identity + the "74% of costs are unhedged commodities" hook + agent status. (2) **Analyse** — exposure donut, the margin-collapse hero (11.0% → 3.3%), VaR, and Spice's recommended 3-venue hedge. (3) **Execution** — the specialist agents (Hedging, Placement) acting live across the options + on-chain venues, the activity feed, and the on-chain payout climax. No auth, no onboarding. **Design system + approved mockups locked in `DESIGN.md` (plan-design-review, 2026-06-27).**
- **Data:** synthetic + benchmark. The founders build the commodity→input mapping KB + 2–3 synthetic businesses (bakery hero, trucking, plastics shop) and a commodity price history feed.

### Who builds what
- **Quant:** the analysis engine end to end (decomposition → forecast → propagation → VaR). *Owns the depth.*
- **Blockchain/fullstack dev:** the Node blockchain service — Aave/Morpho lend + Escrow policy/payout (testnet), exposed to the orchestrator over localhost. *Owns the live on-chain settlement.*
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
- **Live trigger flakiness** → a controllable scenario clock drives the shock + the displayed P&L (D1); the escrow reads a settable mock oracle; pre-deploy + pre-fund testnet wallets; recorded backup of the exact tx flow.
- **Markets closed all weekend** → no options fill is possible Sat/Sun. The live settlement beat is on-chain (Escrow + Aave, testnet, 24/7); Alpaca shows a real resolved contract + a real queued order (verify weekend orders are accepted with a 2-min test submit today).
- **Quant scope creep** → bound it: decomposition + one forecast + one propagation + one before/after VaR. No multi-factor model, no full backtest engine for the demo.

---

## Verification — before stage
1. **Engine:** changing the synthetic bakery's cost mix changes the decomposition and the VaR correctly (not hardcoded).
2. **Execution:** the Aave deposit and Escrow payout settle on testnet (visible by tx hash, agent wallet as actor); the Alpaca leg shows a real resolved contract + a real queued order id.
3. **Live beat:** triggering the scenario shock fires the Escrow payout + Aave recall on-chain and updates the displayed P&L, on stage, repeatably (≥5 clean runs + recorded fallback).
4. **Agents:** the activity feed shows real tool calls and reasoning; changing a seed changes the hedge plan.

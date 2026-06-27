# SPICE — Team Brief

> **The autonomous hedging & risk desk for traditional businesses.**
> An AI that finds the commodity, FX, and cash risks hiding in an ordinary SMB's books — and hedges them across programmable markets, the way only a trading desk could.

**For:** YC hackathon (luma.com/8ucy347o) · jury incl. Nicolas Dessaigne (Algolia, YC) · décacorn track · YC interview as prize.
**Team:** 5 — one quant, two founders (worked on YIELD), one frontend/data + fullstack, one fullstack + blockchain.

---

## The one-liner

Spice ingests an ordinary business's financials, finds the **hidden commodity exposure** buried in its cost structure, forecasts the margin hit before it lands, and **hedges it autonomously** across onchain derivatives, lending, and parametric insurance — settled on stablecoin rails. A bakery gets risk management that today only a Fortune 500 treasury desk has.

---

## The non-obvious insight: every SMB is a commodity trader who doesn't know it

A bakery thinks it buys flour, butter, and electricity. It is actually **long wheat, long gas, long fats, long power** — massively exposed, completely unhedged, and blind to it. A trucking company is long oil. A small plastics shop is long oil. A foundry is long electricity and copper. None of them can see it, price it, or hedge it, because hedging has always required a desk, a broker, and size.

Spice maps each business's cost structure down to the **tradeable commodities underneath**, then hedges those — automatically, in the small sizes an SMB needs, on rails that didn't exist two years ago.

### The exposure map (the "real-world" translation layer)

| Commodity (hedgeable) | Hidden inside these SMB inputs |
|---|---|
| **Oil** | plastics/polymers (PVC, polystyrene, polyurethane), bitumen, synthetic rubber, transport & logistics, off-road diesel (GNR) for machinery |
| **Electricity** | aluminium ("solidified electricity"), glass, partly electric steel |
| **Gas** | cement, glass, nitrogen fertilizers (ammonia from gas), part of chemicals |
| **Wheat** | flour, bread, animal feed (→ part of meat) |
| **Fats** | butter, cream |
| **Copper, Wood, …** | electrical, construction, packaging |

This translation layer is the product's brain and the start of its moat. Nobody else connects "a boulangerie in Lyon" to "long wheat + gas" and acts on it.

---

## Why now (the rising market Stripe and Circle opened but didn't finish)

Stripe (Bridge) and Circle cracked **stablecoin payments** — moving dollars programmatically. But they stopped at payments. **Nobody cracked the real-world risk layer**: using those same programmable rails to let an ordinary business *hedge, insure, and finance* itself. That's the open frontier.

- **Options on commodity ETFs (Alpaca) and on-chain derivatives (Hyperliquid)** make small, capital-light commodity hedges possible for the first time.
- **x402** (agentic stablecoin payments) lets an AI agent pay for and execute these actions natively.
- **Lending (Aave/Morpho), prediction markets (Polymarket), and escrow** give an agent a full toolkit: yield, event hedges, parametric insurance — all programmable, all 24/7.
- The programmable rails (onchain derivatives, escrow, stablecoin settlement) now run 24/7 at low minimums — the plumbing that makes micro-hedging viable. *(We sell the real-economy outcome, not crypto; the rails are an implementation detail.)*

---

## The beachhead: every traditional small & mid business

Bakeries, transport firms, small factories, agri-food, builders — the millions of ordinary SMBs (3M+ in France, ~24M in the EU) that are commodity-exposed and completely unhedged. Turnkey, short sales cycle, huge volume. Low ARPU per business is the point, not the problem — because the real asset compounds at scale (below).

---

## The moat: cash pooling + data pooling → the macro intelligence nobody else has

Per-business, Spice is a useful hedging tool. **At scale, it becomes something no one can replicate:**

- **Cash pooling** — pooled SMB liquidity gives better hedge pricing and execution than any single small business could get.
- **Data pooling** — Spice sees the real cost structures, margins, and commodity exposures of millions of ordinary businesses, **in real time, at the micro level**. That is a live, ground-truth picture of the real economy.
- **The endgame** — that dataset is worth more to **hedge funds and central banks** than the SaaS ever will be. They forecast the real economy from lagging surveys and aggregates; Spice would have the micro-level, real-time truth they structurally cannot get. The wedge sells hedging to SMBs; the company sells the real economy's nervous system to the people who move markets.

---

## Open decisions for the team
- **Name:** **Spice** (full brand "The Exotic Asset Company"). Tagline candidate: *"the spice must flow"* (≈ commodities/cash must keep moving). Lock before logo/UI.
- **Hero demo business:** bakery (most relatable, exposed to wheat + gas + power + fats) vs trucking (clean single oil exposure). Recommendation: **bakery** for the contrast, mention trucking + a plastics shop for breadth.

See `COMPETITION.md` for whitespace and `DEMO.md` for the architecture, hero demo, and 48h build plan.

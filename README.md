# 🌶️ Spice — the autonomous commodity-hedging desk for ordinary businesses

*The Exotic Asset Company.*

> Every ordinary business is an unhedged commodity trader and doesn't know it.
> A bakery is **short wheat, short gas, short power, short fats**. A trucking firm is
> **short oil**. A foundry is **short electricity and copper**. None can see it,
> price it, or hedge it — because hedging always required a desk, a broker, and size.
>
> **Spice maps a business's cost structure down to the tradeable commodity
> underneath, forecasts the margin hit before it lands, and hedges it
> autonomously** across options, on-chain lending, and parametric insurance.
> A bakery gets the risk desk only a Fortune 500 treasury had.

Built for a YC hackathon (décacorn track).

---

## The shape

```
  DATA (synthetic)      QUANT ENGINE              AGENTS              EXECUTION
  ───────────────       ─────────────             ──────             ─────────
  company financials ─▶ decompose cost      ─▶  orchestrator    ─┬─▶ Alpaca options (paper)
                        forecast commodity       + specialists   ├─▶ Aave / Morpho (testnet)
                        propagate shock          (Opus 4.8)      └─▶ Escrow insurance (testnet)
                        margin VaR
```

## Repo

| Path | What |
|---|---|
| [`BRIEF.md`](BRIEF.md) | The idea, insight, beachhead, moat |
| [`COMPETITION.md`](COMPETITION.md) | Competitive whitespace map |
| [`DEMO.md`](DEMO.md) | Architecture, hero demo, 48h build plan, locked decisions |
| [`quant-engine/`](quant-engine/) | Quant engine (runnable) + orchestrator + [API contract](quant-engine/API_CONTRACT.md) |
| [`alpaca-backend/`](alpaca-backend/) | Commodity-ETF options service (FastAPI, paper) + the exposure-inference registry |

## Quickstart — see the brain run (zero deps)

```bash
cd quant-engine
python run_analysis.py
```

Re-expresses the synthetic bakery *Maison Levain* as a commodity book and prints:
decomposition → a commodity shock → **net margin 11% → 3.3%** → the recommended
hedge → **margin restored to 11%** → **margin VaR 13.1% → 2.0%**.

## Hero demo, one line

*The bakery that hedges like a trading desk*: ingest the books → the AI finds the
hidden wheat/gas exposure → forecasts the margin hit → hedges across real venues →
trigger the shock live and the protection pays out on-chain, on stage.

# spice-backend

Orchestrator + quant engine for Spice (the autonomous commodity-hedging desk).

## Quant engine (runnable now, zero deps)

```bash
cd spice-backend
python run_analysis.py
```

Re-expresses a synthetic business as a commodity book and prints the
decomposition, a scenario shock, the margin hit, the recommended hedge, and the
before/after VaR — the numbers the agent narrates and the frontend renders.

- `spice/schema.py` — `Company` / `CostLine` data model + `load_company`
- `spice/commodities.py` — hedgeable-commodity registry (ticker, vol)
- `spice/quant.py` — `decompose`, `propagate`, `recommend_hedges`, `hedge_pnl`, `var`
- `spice/data/maison_levain.json` — the synthetic bakery hero
- `run_analysis.py` — end-to-end CLI

The displayed P&L comes from this engine under a chosen scenario, never from a
live fill (eng-review decision D1). The quant lane deepens the models here.

## Orchestrator (next)

Claude Opus 4.8 agent loop (plain Anthropic SDK), tools call the quant engine +
the Alpaca service + the Node blockchain service. The Next.js frontend talks
only to this service (REST + WebSocket activity feed). See `../DEMO.md`.

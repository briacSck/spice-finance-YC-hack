---
name: spice-quant
description: Use to analyze a Spice company — decompose costs into hidden commodity exposures, apply a price shock to net margin, recommend hedges, and compute margin Value-at-Risk. Pure in-process engine (no network, no keys). Run when you need the numbers behind the demo or to add a new company.
---

# spice-quant — commodity decomposition, shock, VaR

In-process deterministic engine. No network, no API keys. Lives in
`backend/quant-engine/spice/`.

## Quick run
```bash
cd backend/quant-engine
python run_analysis.py        # prints decomposition → shock → hedge → before/after VaR
```

## Data model (`spice/schema.py`)
A `Company` = `revenue`, `cash`, `cost_lines[]` where each `CostLine(label, annual_amount, commodity)`.
`commodity` is a hedgeable ticker (`WEAT/SOYB/UNG/XLU/USO/...`) or `None` (labour, rent).
Companies are JSON in `spice/data/*.json` (e.g. `maison_levain.json`).

## Core functions (`spice/quant.py`, pure over a Company)
- `decompose(company)` → `[Exposure(commodity, name, amount, share_of_cost, share_of_revenue, vol)]`, biggest first.
- `propagate(company, shock)` → margin before/after a `{ticker: fractional_move}` shock + added cost.
- `recommend_hedges(company, coverage=1.0)` → long notional per commodity.
- `hedge_pnl(hedges, shock)` → P&L of the hedge book under the shock.
- `var(company, z=1.65, residual_basis=0)` → annual margin VaR (€ + % revenue). `residual_basis=0.15` models a hedged book.

## Add a company
Drop a JSON in `spice/data/`, then `load_company(path)` (schema.py). Tag each cost line's
`commodity` with a ticker the venues can trade (see spice-alpaca registry) or `None`.

## Example
```python
from spice.schema import load_company
from spice import quant
co = quant  # noqa
c = load_company("spice/data/maison_levain.json")
print([(e.commodity, e.amount) for e in quant.decompose(c)])
print(quant.var(c).pct_revenue)                      # unhedged
print(quant.var(c, residual_basis=0.15).pct_revenue) # hedged
```

The orchestrator exposes this analysis via the `analyze_exposure` / `run_shock` agent tools.

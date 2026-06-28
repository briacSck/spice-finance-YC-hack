---
name: spice-alpaca
description: Use to hedge a commodity exposure with options on commodity ETFs via the Spice Alpaca backend (paper) — map an exposure to its ETF, browse the option chain, buy protective calls (single-leg) or a collar (multi-leg). Covers the FastAPI on :8001, the ETF registry, invoice→ETF inference, and env keys.
---

# spice-alpaca — commodity-ETF option hedges (paper)

Alpaca has **no futures** — commodity exposure is hedged via **options on commodity ETFs**.
A business is *long* its input commodity (price up = cost up), so the hedge is a **long call**
on the mapped ETF. Path: `backend/alpaca-backend`. See `ALPACA_API.md` there.

## Run
```bash
cd backend/alpaca-backend
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env   # set ALPACA_KEY / ALPACA_SECRET (paper keys, PK… prefix)
uvicorn app_alpaca:app --port 8001    # docs: http://localhost:8001/docs
```
Paper vs live = host + keys only (`ALPACA_TRADING_URL=https://paper-api.alpaca.markets`).

## ETF registry (commodity → tradeable ETF)
USO=Pétrole · UNG=Gaz · WEAT=Blé · CORN=Maïs · SOYB=Mat.grasse · CPER=Cuivre · XLU=Électricité · WOOD=Bois · DBB=Métaux(alu/zinc) · SLX=Acier.
For the quant tickers, the commodity code usually **is** the ETF ticker (WEAT/UNG/USO…).

## Endpoints (:8001)
| Method | Path | Use |
|---|---|---|
| GET | `/account` | status, options approval level, cash |
| GET | `/instruments` | the ETF registry |
| POST | `/infer` `{line_items:[...]}` | invoice/AP lines → exposed ETFs |
| GET | `/chain/{ticker}?right=C&expiration_date_gte=YYYY-MM-DD` | option contracts |
| POST | `/hedge/option` | single-leg (buy protective call) |
| POST | `/hedge/collar` | multi-leg (L3) collar |
| GET | `/positions` · `/orders` · DELETE `/orders/{id}` | manage |

## Buy a protective call
```bash
curl -s localhost:8001/hedge/option -H 'content-type: application/json' -d '{
  "ticker":"WEAT","right":"C","quantity":10,"strike":22,
  "expiration":"2026-10-16","limit_price":1.58}'
```
`strike`/`expiration` are targets — the nearest available contract is auto-picked.

## Sizing a hedge (rule of thumb)
1 contract = 100 shares ≈ `strike×100` USD notional. Contracts ≈ `eur_notional×1.08 / (strike×100)`.
Premium (cash needed = max loss) ≈ **~7% of notional** for a ~3–6mo ATM call at ~25–30% IV.
Read live premiums from `/chain` (bid/ask) or option snapshots before quoting.

## Notes
- Market closed (weekend) → quotes are indicative; mid is better than ask.
- Orchestrator calls this via the `hedge_options` agent tool (degrades to a queued ref if down).
- Single-commodity ag ETFs (WEAT/CORN/SOYB) and CPER have thin option liquidity; USO/UNG/XLU/DBB/SLX fill better.

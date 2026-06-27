# ibkr-backend

Python backend for the YIELD AI-CFO **commodity-hedging** agent. Wraps the IBKR
**Client Portal Web API** (see `../IBKR_API.md`) and exposes clean, agent-facing
intents over FastAPI. **US-only, paper trading.**

## What it does
- Maps an SMB's invoice / AP line-items → the commodity it's silently exposed to
  (`/infer`, the demo's "unfair depth").
- Resolves the right futures / futures-option `conid` via `secdef` and places the
  hedge, auto-handling IBKR's reply-confirm prompts.

## Instruments (US liquid set)
| Root | Name | Exchange | Micro |
|---|---|---|---|
| CL | WTI Crude Oil | NYMEX | MCL |
| NG | Henry Hub NatGas | NYMEX | MNG |
| ZW | Wheat | ECBOT | — |
| ZC | Corn | ECBOT | — |
| ZL | Soybean Oil | ECBOT | — |
| HG | Copper | COMEX | MHG |

## Prereqs
1. **IBKR Pro** account, fully open + funded (required even for paper).
2. **Client Portal Gateway** running locally, logged in with **paper** creds.
   Default base URL `https://localhost:5000/v1/api` (self-signed TLS).
3. Python 3.11+.

## Setup
```bash
cd ibkr-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # set IBKR_ACCOUNT_ID to your DU... paper account
```

## Verify contracts (do this first)
Resolves real conids + checks option availability against your paper gateway:
```bash
python scripts/verify_contracts.py
python scripts/verify_contracts.py --month SEP26
```
Use this to confirm the **futures-option** resolution before trusting it — the
Web API's options-on-futures path is under-documented (see `ibkr/contracts.py`).

## Run the API
```bash
uvicorn app:app --reload --port 8000
# Swagger UI: http://localhost:8000/docs
```

### Key endpoints
| Method | Path | Purpose |
|---|---|---|
| GET | `/session` | prime + check brokerage session |
| GET | `/instruments` | the US root registry |
| POST | `/infer` | line-items → exposed roots |
| GET | `/strikes/{root}/{month}` | option strikes for a month (MMMYY) |
| POST | `/hedge/future` | place a futures hedge |
| POST | `/hedge/option` | place a defined-risk option hedge |
| GET | `/positions` | current positions |
| GET | `/orders` | live orders |
| DELETE | `/orders/{id}` | cancel |

### Example — infer then hedge wheat
```bash
curl -s localhost:8000/infer -H 'content-type: application/json' \
  -d '{"line_items":["Farine T65 50kg","Diesel livraison","Cuivre câblage"]}'
# -> {"ZW":["Farine T65 50kg"],"CL":["Diesel livraison"],"HG":["Cuivre câblage"]}

curl -s localhost:8000/hedge/future -H 'content-type: application/json' \
  -d '{"root":"ZW","month":"SEP26","side":"BUY","quantity":1,"order_type":"MKT"}'
```

## Layout
```
ibkr-backend/
  app.py                 FastAPI surface (agent calls this)
  ibkr/
    config.py            env settings
    contracts.py         US registry + exposure keywords + conid resolution
    client.py            async Web API client + reply-confirm loop
    service.py           high-level hedge intents
  scripts/
    verify_contracts.py  empirical conid/option check on paper
```

## Alpaca backend (commodity-ETF options, paper)

Alternative venue — **no gateway needed**, just API keys. Trades **options on
commodity ETFs** (Alpaca has no futures). See `../ALPACA_API.md`.

Setup: keys live in `.env` (`ALPACA_KEY`/`ALPACA_SECRET`, paper). Run:
```bash
uvicorn app_alpaca:app --reload --port 8001   # docs: http://localhost:8001/docs
```

ETF registry (commodity → Alpaca options ticker):
| Commodité | Ticker |
|---|---|
| Pétrole | USO |
| Gaz | UNG |
| Blé | WEAT |
| Maïs | CORN |
| Matière grasse | SOYB |
| Cuivre | CPER |
| Électricité | XLU |
| Bois | WOOD |

Endpoints: `/account` `/instruments` `/infer` `/chain/{ticker}` `/positions`
`/hedge/option` (single-leg) `/hedge/collar` (L3 multi-leg) `/orders`.

```bash
# infer then buy a protective put on oil exposure
curl -s localhost:8001/infer -H 'content-type: application/json' \
  -d '{"line_items":["Diesel livraison","Farine T65","Facture électricité"]}'
# -> {"USO":["Diesel livraison"],"WEAT":["Farine T65"],"XLU":["Facture électricité"]}

curl -s localhost:8001/hedge/option -H 'content-type: application/json' \
  -d '{"ticker":"USO","right":"P","quantity":1,"strike":75,"expiration":"2026-09-18","limit_price":1.20}'
```

## Honest caveats
- **Futures options over the Web API** are under-documented; `resolve_option` is
  best-effort. Run the verify script; if strikes don't return, options on that
  root may need the futures contract's own conid or a different secType.
- **Hedging derivatives for an SMB is regulated** (MiFID-style advice/dealing).
  This backend is a hackathon paper-trading prototype, not a production trade rail.
- Session drops if `/tickle` isn't called < every 60s; the agent loop or a
  background task should ping it during a live demo.
```

---
name: spice
description: Use to understand or boot the Spice stack — the autonomous commodity-hedging desk for SMBs. Overview of the orchestrator + venue backends + quant engine + frontend, their ports, env vars, and boot order. Start here, then use spice-quant / spice-alpaca / spice-morpho / spice-escrow for a specific tool.
---

# Spice — stack overview & boot

Spice re-expresses an SMB's costs as a hidden commodity book, forecasts the margin
hit, and hedges it across options + on-chain lending + parametric insurance.

## Architecture & ports
```
spice-frontend (Next.js)  ──HTTP/SSE──▶  orchestrator :8000 (spice.server)
                                              │ agent tools call venues:
                                              ├─▶ alpaca-backend  :8001  (option hedges)
                                              ├─▶ morpho-backend  :8002  (idle-cash yield)
                                              └─▶ escrow-backend  :8003  (parametric insurance)
   quant-engine (spice.*)  = in-process analysis (decompose / shock / VaR)
```

| Service | Path | Run | Port |
|---|---|---|---|
| Orchestrator | `backend/quant-engine` | `uvicorn spice.server:app --port 8000` | 8000 |
| Alpaca venue | `backend/alpaca-backend` | `uvicorn app_alpaca:app --port 8001` | 8001 |
| Morpho venue | `backend/morpho-backend` | `uvicorn app:app --port 8002` | 8002 |
| Escrow venue | `backend/escrow-backend` | `uvicorn app:app --port 8003` | 8003 |
| Frontend | `spice-frontend` | `npm run dev` | 3000 |

## Orchestrator API (frontend ↔ server, see `backend/quant-engine/API_CONTRACT.md`)
- `GET /api/company` — hero company + decomposition
- `POST /api/run[?mock=true]` — start a run → `{run_id}` (`mock=true` = deterministic, no LLM/network)
- `GET /api/run/{id}/events` — SSE stream (agent_message / tool_call / analysis / execution / done)
- `POST /api/run/{id}/trigger` — fire the climax (operator-controlled)

## Agent tools (orchestrator-internal, `spice/tools.py`)
`analyze_exposure` · `run_shock` · `hedge_options`→Alpaca · `lend_morpho`→Morpho · `take_escrow_policy`→Escrow.
Venue tools degrade gracefully to a fabricated ref if a backend is down, so the demo never hard-fails.

## Env
- Each backend: own `.env` (gitignored) from its `.env.example`. Never commit keys.
- Orchestrator venue URLs: `ALPACA_URL` / `MORPHO_URL` / `ESCROW_URL` (default `localhost:800x`).
- Live agent loop needs `ANTHROPIC_API_KEY`; `mock=true` needs nothing.

## Boot order (per backend: `python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt && cp .env.example .env`)
1. Start venues 8001 / 8002 / 8003.
2. Start orchestrator 8000.
3. Start frontend 3000 (`spice-frontend`).
4. Safe demo with no keys: `POST /api/run?mock=true`.

## Which skill
- Analyze a company / VaR / shock → **spice-quant**
- Hedge a commodity (options) → **spice-alpaca**
- Place/recall idle cash (yield) → **spice-morpho**
- Parametric heat policy → **spice-escrow**

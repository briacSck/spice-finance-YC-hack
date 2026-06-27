# Orchestrator API contract (frontend ↔ orchestrator)

The Next.js frontend talks **only** to the orchestrator (eng-review D2). REST for
state, a stream for the live activity feed. This is the contract the frontend
lane builds against; the orchestrator implements it. Stable shapes below — mock
them in the frontend until the server is live.

Base: `http://localhost:8000`

## REST

### `GET /api/company`
Returns the loaded business + its decomposition (Dashboard + Analyse screens).
```json
{
  "name": "Maison Levain",
  "revenue": 1400000,
  "cash": 180000,
  "net_margin": 0.11,
  "exposures": [
    { "commodity": "WEAT", "name": "Blé", "amount": 300000,
      "share_of_revenue": 0.214, "vol": 0.30 }
  ]
}
```

### `POST /api/run`
Starts an agent run over the loaded company. Returns a run id; the reasoning +
executions stream over the events channel below.
```json
{ "run_id": "r_abc123" }
```

## Stream — `GET /api/run/{run_id}/events` (Server-Sent Events)

Each event is `data: {json}\n\n`. Event shapes (discriminated by `type`):

| `type` | payload | screen |
|---|---|---|
| `agent_message` | `{ "text": "..." }` | Execution (activity feed) |
| `tool_call` | `{ "tool": "propagate_shock", "input": {...} }` | Execution |
| `tool_result` | `{ "tool": "...", "output": {...} }` | Execution |
| `analysis` | `{ "decomposition": [...], "margin_before": 0.11, "margin_after": 0.033, "var_before": 0.131, "var_after": 0.020 }` | Analyse |
| `execution` | `{ "venue": "alpaca\|aave\|escrow", "action": "...", "status": "accepted\|settled", "ref": "<order id / tx hash>", "explorer_url": "..." }` | Execution |
| `done` | `{ "summary": "...", "hedge_pnl": 107500, "margin_with_hedge": 0.11 }` | all |

## Agent tools (orchestrator-internal, names are stable)

`decompose_costs` · `forecast_commodity` · `propagate_shock` · `recommend_hedges`
· `compute_var` · `hedge_options` (→ Alpaca) · `lend_aave` (→ chain) ·
`take_escrow_policy` (→ chain) · `recall_cash` (→ chain)

Analysis tools resolve in-process against `spice.quant`. Venue tools call the
Alpaca FastAPI (`:8001`) and the Node chain service (`:300x`); on the closed
market this weekend, `hedge_options` returns a resolved contract + a queued order
ref (eng-review D3).

## Modes
- `POST /api/run?mock=true` → deterministic scripted run (no LLM, no live venues):
  the guaranteed-safe demo fallback. Same event stream, canned timing.
- default → real Opus 4.8 agent loop + live venue calls.

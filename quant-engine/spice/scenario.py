"""The hardcoded hero scenario + the mock (no-LLM) event stream.

The shock is scripted (markets-closed-proof). The numbers match the engine's hero
output and the frontend mockData. `mock_pre()` / `mock_post()` are the deterministic
fallback run; the live agent narrates the same spine with real tool artifacts.

Events are exactly the `RunEvent` union in spice-frontend/lib/types.ts.
"""

from __future__ import annotations

BUSINESS = "Maison Levain"
HERO_DATASET = "maison_levain.json"

# Scripted shock — NOT live market data. Root cause: a 2026 heatwave/drought that
# spikes wheat + energy prices AND collapses footfall / breaks refrigeration.
SHOCK = {"WEAT": 0.38, "UNG": 0.25, "XLU": 0.25}
SHOCK_LABEL = "2026 heatwave · +38% wheat · +25% gas"

# Hero exposures, grouped for the UI (gas+power -> Energy); matches the frontend.
HERO_EXPOSURES = [
    {"commodity": "WEAT", "name": "Wheat", "amount": 300000, "share_of_revenue": 0.214, "vol": 0.30},
    {"commodity": "ENERGY", "name": "Energy", "amount": 161000, "share_of_revenue": 0.115, "vol": 0.45},
    {"commodity": "FATS", "name": "Fats", "amount": 80000, "share_of_revenue": 0.057, "vol": 0.25},
]

MARGIN_BEFORE = 0.11
MARGIN_SHOCK = 0.033   # unhedged under the shock
VAR_BEFORE = 0.131
VAR_AFTER = 0.02       # after the hedge
HEDGE_PNL = 107500
MARGIN_HELD = 0.11


def _analysis(margin_after: float, var_after: float) -> dict:
    return {
        "type": "analysis",
        "decomposition": HERO_EXPOSURES,
        "margin_before": MARGIN_BEFORE,
        "margin_after": margin_after,
        "var_before": VAR_BEFORE,
        "var_after": var_after,
    }


def mock_pre() -> list[dict]:
    """Events streamed up to the operator trigger (the climax pause)."""
    return [
        {"type": "agent_message", "who": "Orchestrator",
         "text": "Maison Levain — let me see what this bakery is really exposed to."},
        {"type": "tool_call", "who": "Risk agent", "tool": "analyze_exposure",
         "input": {"business": BUSINESS}},
        _analysis(MARGIN_BEFORE, VAR_BEFORE),
        {"type": "agent_message", "who": "Risk agent",
         "text": "74% of cost is commodities. Wheat alone is the biggest line. This bakery is silently long wheat, gas and power."},
        {"type": "tool_call", "who": "Risk agent", "tool": "run_shock",
         "input": {"shock": SHOCK_LABEL}},
        _analysis(MARGIN_SHOCK, VAR_BEFORE),
        {"type": "agent_message", "who": "Orchestrator",
         "text": f"Under a {SHOCK_LABEL} shock, net margin collapses 11% → 3.3%. Routing to both specialists."},
        {"type": "tool_call", "who": "Hedging agent", "tool": "hedge_options",
         "input": {"ticker": "WEAT", "right": "C", "qty": 3}},
        {"type": "execution", "venue": "alpaca", "action": "Buy WEAT + UNG calls",
         "status": "accepted", "ref": "id 6f2a…b1", "amount": 3900},
        {"type": "tool_call", "who": "Hedging agent", "tool": "take_escrow_policy",
         "input": {"trigger": "heat_index", "premium": 1240, "payout": 84000}},
        {"type": "execution", "venue": "escrow", "action": "Parametric heatwave policy minted",
         "status": "accepted", "ref": "0x9c…4e", "explorer_url": "#", "amount": 1240},
        {"type": "tool_call", "who": "Placement agent", "tool": "lend_morpho",
         "input": {"amount": 180000}},
        {"type": "execution", "venue": "morpho", "action": "Supply idle cash to vault",
         "status": "settled", "ref": "0x21…af", "explorer_url": "#", "amount": 180000},
        {"type": "agent_message", "who": "Orchestrator",
         "text": "Hedges placed, premiums self-funded from idle cash. Watching the heat-index oracle."},
    ]


def mock_post() -> list[dict]:
    """Events streamed after the trigger fires (the payout climax)."""
    return [
        {"type": "agent_message", "who": "Scenario · trigger",
         "text": "Heat index hit 41°C — trigger crossed. Firing payout + cash recall."},
        {"type": "execution", "venue": "escrow", "action": "Parametric payout settled to the bakery wallet",
         "status": "settled", "ref": "0x9c…4e", "explorer_url": "#", "amount": 84000, "pnl": 84000},
        {"type": "execution", "venue": "morpho", "action": "Recall idle cash",
         "status": "settled", "ref": "0x21…af", "explorer_url": "#", "amount": 180000},
        _analysis(MARGIN_HELD, VAR_AFTER),
        {"type": "done",
         "summary": "Margin held at 11% while an unhedged peer fell to 3.3%. The hedge paid out €84k, settled on-chain.",
         "hedge_pnl": HEDGE_PNL, "margin_with_hedge": MARGIN_HELD},
    ]

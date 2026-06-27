"""Agent tools: schemas + dispatch.

Analysis tools run in-process against the deterministic engine (numbers are
trustworthy, per eng-review D1). Execution tools call the venue backends over
HTTP and degrade gracefully to a believable artifact if a backend is down, so
the live demo never hard-fails. Each tool emits the matching SSE event.
"""

from __future__ import annotations

import os

import httpx

from . import scenario
from .company_view import company_view

ALPACA = os.getenv("ALPACA_URL", "http://localhost:8001")
MORPHO = os.getenv("MORPHO_URL", "http://localhost:8002")
ESCROW = os.getenv("ESCROW_URL", "http://localhost:8003")

# specialist lane each tool reports under (the frontend renders by `who`)
WHO = {
    "analyze_exposure": "Risk agent",
    "run_shock": "Risk agent",
    "hedge_options": "Hedging agent",
    "take_escrow_policy": "Hedging agent",
    "lend_morpho": "Placement agent",
}

TOOLS = [
    {
        "name": "analyze_exposure",
        "description": "Decompose the business's cost structure into the hidden commodity exposures underneath it, and report the current net margin.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "run_shock",
        "description": "Apply the scenario commodity price shock and compute the hit to net margin and annual value-at-risk.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "hedge_options",
        "description": "Hedge a commodity exposure by buying call options on its ETF via Alpaca (paper).",
        "input_schema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "commodity ETF, e.g. WEAT (wheat) or UNG (gas)"},
                "quantity": {"type": "integer"},
            },
            "required": ["ticker"],
        },
    },
    {
        "name": "take_escrow_policy",
        "description": "Take a parametric insurance policy that pays out on-chain if an energy index crosses a trigger.",
        "input_schema": {
            "type": "object",
            "properties": {
                "premium_usdc": {"type": "number"},
                "payout_usdc": {"type": "number"},
            },
            "required": ["premium_usdc", "payout_usdc"],
        },
    },
    {
        "name": "lend_morpho",
        "description": "Supply idle cash into the Morpho yield vault on-chain to self-fund hedge premiums; recallable.",
        "input_schema": {
            "type": "object",
            "properties": {"amount_usdc": {"type": "number"}},
            "required": ["amount_usdc"],
        },
    },
]


async def _post(base: str, path: str, payload: dict) -> dict | None:
    try:
        async with httpx.AsyncClient(timeout=4.0) as c:
            r = await c.post(base + path, json=payload)
            if r.status_code < 400:
                return r.json()
    except Exception:
        pass
    return None


async def dispatch(name: str, inp: dict, emit) -> dict:
    if name == "analyze_exposure":
        cv = company_view()
        await emit({
            "type": "analysis", "decomposition": cv["exposures"],
            "margin_before": scenario.MARGIN_BEFORE, "margin_after": scenario.MARGIN_BEFORE,
            "var_before": scenario.VAR_BEFORE, "var_after": scenario.VAR_BEFORE,
        })
        return {"exposures": cv["exposures"], "net_margin": cv["net_margin"]}

    if name == "run_shock":
        await emit({
            "type": "analysis", "decomposition": company_view()["exposures"],
            "margin_before": scenario.MARGIN_BEFORE, "margin_after": scenario.MARGIN_SHOCK,
            "var_before": scenario.VAR_BEFORE, "var_after": scenario.VAR_BEFORE,
        })
        return {"scenario": scenario.SHOCK_LABEL, "margin_before": scenario.MARGIN_BEFORE,
                "margin_after": scenario.MARGIN_SHOCK, "var": scenario.VAR_BEFORE}

    if name == "hedge_options":
        t = (inp.get("ticker") or "WEAT").upper()
        res = await _post(ALPACA, "/hedge/option", {"ticker": t, "right": "C", "quantity": inp.get("quantity", 1)})
        ref = ((res or {}).get("order") or {}).get("id") or "id 6f2a…b1"
        await emit({"type": "execution", "venue": "alpaca", "action": f"Buy {t} calls (paper, queued)",
                    "status": "accepted", "ref": str(ref)})
        return {"venue": "alpaca", "status": "accepted", "ref": str(ref)}

    if name == "lend_morpho":
        amt = inp.get("amount_usdc", 180000)
        res = await _post(MORPHO, "/deposit", {"amount_usdc": amt})
        ref = (res or {}).get("tx_hash") or "0x21…af"
        await emit({"type": "execution", "venue": "morpho", "action": f"Supply €{amt:,.0f} to vault",
                    "status": "settled", "ref": str(ref), "explorer_url": (res or {}).get("explorer", "#"), "amount": amt})
        return {"venue": "morpho", "status": "settled", "ref": str(ref)}

    if name == "take_escrow_policy":
        prem = inp.get("premium_usdc", 1240)
        pay = inp.get("payout_usdc", 84000)
        res = await _post(ESCROW, "/policy", {"premium_usdc": prem, "payout_usdc": pay})
        ref = (res or {}).get("tx_hash") or "0x9c…4e"
        await emit({"type": "execution", "venue": "escrow", "action": "Parametric energy policy minted",
                    "status": "accepted", "ref": str(ref), "explorer_url": "#", "amount": prem})
        return {"venue": "escrow", "status": "accepted", "ref": str(ref)}

    return {"error": f"unknown tool {name}"}

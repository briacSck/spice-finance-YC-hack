"""GET /api/company — the real engine's hero output, shaped for the frontend.

Runs the deterministic engine on the hand-tuned hero dataset and groups gas+power
into one "Energy" exposure so the shape matches spice-frontend/lib/types.ts.
"""

from __future__ import annotations

from pathlib import Path

from . import commodities, quant
from .schema import load_company

DATA = Path(__file__).parent / "data" / "maison_levain.json"

# UI grouping: gas + power -> "Energy"; SOYB -> the frontend's "FATS" id.
_GROUP = {"UNG": "ENERGY", "XLU": "ENERGY", "SOYB": "FATS"}
_GROUP_META = {"ENERGY": ("Energy", 0.45), "FATS": ("Fats", 0.25)}


def company_view() -> dict:
    co = load_company(DATA)
    agg: dict[str, dict] = {}
    for e in quant.decompose(co):
        gid = _GROUP.get(e.commodity, e.commodity)
        name, vol = _GROUP_META.get(gid, (commodities.en_name(e.commodity), e.vol))
        slot = agg.setdefault(gid, {"commodity": gid, "name": name, "amount": 0.0, "vol": vol})
        slot["amount"] += e.amount
    exposures = sorted(agg.values(), key=lambda x: x["amount"], reverse=True)[:3]
    for x in exposures:
        x["share_of_revenue"] = round(x["amount"] / co.revenue, 4) if co.revenue else 0.0
        x["amount"] = round(x["amount"])
    return {
        "name": co.name,
        "revenue": co.revenue,
        "cash": co.cash,
        "net_margin": round(co.net_margin, 4),
        "exposures": exposures,
    }

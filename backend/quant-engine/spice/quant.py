"""Quant engine: a business as a commodity portfolio.

Pure functions over a Company. Bounded scope for the demo (locked in the eng
review): decomposition -> shock propagation -> hedge P&L -> before/after VaR.
No live market data; the shock is a scenario the orchestrator/agent chooses, and
the displayed P&L comes from here (eng-review decision D1), never from a live fill.

    decompose ──▶ propagate(shock) ──▶ recommend_hedges ──▶ hedge_pnl(shock)
                          │                                        │
                          └────────────── var(before/after) ───────┘
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from . import commodities
from .schema import Company


# --- decomposition -----------------------------------------------------------
@dataclass(frozen=True)
class Exposure:
    commodity: str
    name: str
    amount: float          # annual € spent on this commodity input
    share_of_cost: float
    share_of_revenue: float
    vol: float


def decompose(company: Company) -> list[Exposure]:
    """Aggregate cost lines into per-commodity exposure, biggest first."""
    by_ticker: dict[str, float] = {}
    for line in company.commodity_lines():
        by_ticker[line.commodity] = by_ticker.get(line.commodity, 0.0) + line.annual_amount
    out = [
        Exposure(
            commodity=t,
            name=commodities.name(t),
            amount=amt,
            share_of_cost=amt / company.total_cost if company.total_cost else 0.0,
            share_of_revenue=amt / company.revenue if company.revenue else 0.0,
            vol=commodities.vol(t),
        )
        for t, amt in by_ticker.items()
    ]
    out.sort(key=lambda e: e.amount, reverse=True)
    return out


# --- shock propagation -------------------------------------------------------
@dataclass(frozen=True)
class Propagation:
    margin_before: float
    margin_after: float
    added_cost: float
    detail: list[tuple[str, float]]  # (commodity, added € cost)


def propagate(company: Company, shock: dict[str, float]) -> Propagation:
    """Apply a price shock (ticker -> fractional move) to input costs -> new margin."""
    detail: list[tuple[str, float]] = []
    added = 0.0
    for e in decompose(company):
        move = shock.get(e.commodity, 0.0)
        delta = e.amount * move
        if delta:
            detail.append((e.commodity, delta))
        added += delta
    new_profit = company.net_profit - added
    return Propagation(
        margin_before=company.net_margin,
        margin_after=new_profit / company.revenue if company.revenue else 0.0,
        added_cost=added,
        detail=detail,
    )


# --- hedging -----------------------------------------------------------------
@dataclass(frozen=True)
class Hedge:
    commodity: str
    notional: float  # € of long commodity exposure taken on (offsets input cost)


def recommend_hedges(company: Company, coverage: float = 1.0) -> list[Hedge]:
    """Long each commodity at `coverage` x its input exposure, so a price rise that
    raises input cost is offset by the hedge's gain."""
    return [Hedge(e.commodity, e.amount * coverage) for e in decompose(company)]


def hedge_pnl(hedges: list[Hedge], shock: dict[str, float]) -> tuple[list[tuple[str, float]], float]:
    """P&L of the hedge book under the shock: long notional gains notional * move."""
    rows = [(h.commodity, h.notional * shock.get(h.commodity, 0.0)) for h in hedges]
    return rows, sum(p for _, p in rows)


# --- value at risk -----------------------------------------------------------
@dataclass(frozen=True)
class VaR:
    eur: float
    pct_revenue: float


def var(company: Company, z: float = 1.65, residual_basis: float = 0.0) -> VaR:
    """Parametric annual margin VaR from commodity exposures (assumed independent).

    residual_basis in [0,1] models imperfect hedging: 0 = unhedged, 0.15 = a hedged
    book with 15% leftover basis risk. Returns the z-level VaR in € and % of revenue.
    """
    var_sq = 0.0
    for e in decompose(company):
        eff = e.amount * (residual_basis if residual_basis else 1.0)
        var_sq += (eff * e.vol) ** 2
    std = math.sqrt(var_sq)
    eur = z * std
    return VaR(eur=eur, pct_revenue=eur / company.revenue if company.revenue else 0.0)

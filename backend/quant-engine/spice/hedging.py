"""Hedge program: real exposure recommendations -> per-commodity human approval ->
a 12-month rolling call-option ladder sized to real monthly spend, plus a
monthly excess-cash sweep into Morpho lending.

This is a deterministic state machine, not an LLM agent loop: once a human has
approved a proposal, every subsequent action (ladder build, monthly roll, cash
sweep) is mechanical. So this module is called directly from server.py's REST
endpoints, bypassing agent.py's Opus tool-calling loop entirely.

    Exposure (real analysis)  ->  HedgeProposal  ->  [human approve/reject]
                                                            |
                                                            v
                                          HedgeLadder (12 rungs, Alpaca calls)
                                                            |
                                          advance_month(): +1 rung/month, + Morpho sweep

Reuses tools.py's graceful-degradation HTTP helper (_post) and venue base URLs
so a missing Alpaca/Morpho backend degrades to a fabricated ref instead of
hard-failing, exactly like the existing agent tools.
"""

from __future__ import annotations

import os
import statistics
import uuid
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import httpx

from . import commodities, quant
from . import exposure as exposure_mod
from .company_view import DATA as HERO_DATA
from .schema import load_company
from .tools import ALPACA, ESCROW, MORPHO, _post

COVERAGE_MONTHS = 12

# Parametric heatwave tail — the leg the option ladder can't cover (lost footfall +
# broken refrigeration are not a tradeable price). One program-level policy, sized to
# the demo narrative and kept consistent with scenario.py / agent.py.
ESCROW_TICKER = "HEAT"
ESCROW_PREMIUM_USDC = 1240.0
ESCROW_PAYOUT_USDC = 84000.0
ESCROW_TRIGGER_INDEX = 38      # heat-index threshold (°C); the demo settles at 41


# --- data model ----------------------------------------------------------------
@dataclass
class HedgeProposal:
    proposal_id: str
    ticker: str
    underlying: str
    monthly_notional: float
    explanation: str
    score: int
    status: str = "pending"  # pending | approved | rejected
    kind: str = "option"     # option (Alpaca call ladder) | escrow (parametric policy)


@dataclass
class LadderRung:
    month_index: int          # offset from the month the ladder was built
    target_month: str         # "YYYY-MM"
    contract_symbol: str | None
    quantity: int
    strike: float | None
    status: str               # bought | degraded
    order_ref: str | None


@dataclass
class HedgeLadder:
    ticker: str
    underlying: str
    rungs: list[LadderRung] = field(default_factory=list)
    built_at_month_index: int = 0


@dataclass
class Program:
    program_id: str
    company_name: str
    monthly_excess_cash: float
    current_month_index: int = 0
    proposals: dict[str, HedgeProposal] = field(default_factory=dict)
    ladders: dict[str, HedgeLadder] = field(default_factory=dict)
    sweep_log: list[dict] = field(default_factory=list)
    escrow_policies: list[dict] = field(default_factory=list)


# --- Exposure -> HedgeProposal ---------------------------------------------------
def _explanation_for(e: exposure_mod.Exposure, report: exposure_mod.Report) -> str:
    decisions = (report.llm or {}).get("hedge_decisions") if report.llm else None
    if isinstance(decisions, list):
        for d in decisions:
            if isinstance(d, dict) and d.get("ticker") == e.ticker and d.get("reasoning"):
                return d["reasoning"]
    return (
        f"{e.underlying} is {e.expense_share * 100:.0f}% of costs with "
        f"{e.price_volatility * 100:.0f}% annualised price volatility - a 20% price "
        f"shock would cost ~{e.shock20_margin_points_lost:.1f} margin points."
    )


def build_proposals(report: exposure_mod.Report) -> list[HedgeProposal]:
    proposals = []
    for e in report.exposures:
        if e.recommendation != "Hedge recommended":
            continue
        proposals.append(
            HedgeProposal(
                proposal_id=f"prop_{e.ticker}",
                ticker=e.ticker,
                underlying=e.underlying,
                monthly_notional=e.average_monthly_spend,
                explanation=_explanation_for(e, report),
                score=e.score,
            )
        )
    # The parametric heatwave tail — one program-level escrow policy, approved like
    # any other proposal but minted (not laddered) on approval.
    proposals.append(
        HedgeProposal(
            proposal_id="prop_escrow",
            ticker=ESCROW_TICKER,
            underlying="Heatwave parametric cover",
            monthly_notional=ESCROW_PREMIUM_USDC,
            explanation=(
                f"Premium ~€{ESCROW_PREMIUM_USDC:,.0f} -> payout ~€{ESCROW_PAYOUT_USDC:,.0f} "
                f"if the regional heat index crosses {ESCROW_TRIGGER_INDEX}°C. Covers the tail "
                f"options can't: lost footfall + broken refrigeration."
            ),
            score=90,
            kind="escrow",
        )
    )
    return proposals


def _report_from_company_view() -> exposure_mod.Report:
    """Demo-safe fallback: build a Report-shaped object straight off the hero
    dataset (maison_levain.json) so the proposal flow always has something to
    show, even with no cashplan CSV and no LLM key configured."""
    company = load_company(HERO_DATA)
    exposures: list[exposure_mod.Exposure] = []
    for e in quant.decompose(company):
        exposures.append(
            exposure_mod.Exposure(
                ticker=e.commodity,
                underlying=commodities.en_name(e.commodity),
                total_spend=e.amount,
                expense_share=e.share_of_cost,
                revenue_share=e.share_of_revenue,
                mapping_confidence=1.0,
                average_monthly_spend=e.amount / 12,
                monthly_volatility=0.0,
                price_volatility=e.vol,
                price_vol_source="registry (demo fallback)",
                shock20_margin_points_lost=round(e.amount * 0.20 / company.revenue * 100, 2) if company.revenue else 0.0,
                hedge_notional=e.amount,
                score=round(min(e.share_of_cost / 0.30, 1.0) * 50 + min(e.vol / 0.50, 1.0) * 50),
                rank=0,
                recommendation="Hedge recommended",
            )
        )
    exposures.sort(key=lambda e: e.score, reverse=True)
    for i, e in enumerate(exposures, start=1):
        e.rank = i
    return exposure_mod.Report(
        business={"name": company.name, "months_analyzed": 12},
        financial_summary={
            "average_monthly_revenue": round(company.revenue / 12, 2),
            "average_monthly_expenses": round(company.total_cost / 12, 2),
        },
        exposures=exposures,
        unmapped={},
        var={},
        llm=None,
    )


def _load_report() -> tuple[exposure_mod.Report, float]:
    """Returns (report, monthly_excess_cash). Tries a real cashplan file first
    (SPICE_CASHPLAN_PATH env var), falls back to the hero dataset."""
    cashplan_path = os.getenv("SPICE_CASHPLAN_PATH")
    if cashplan_path and Path(cashplan_path).exists():
        exposure_mod.load_local_env()
        rows = exposure_mod.load_input(cashplan_path)
        report = exposure_mod.analyze(rows)
        report = exposure_mod.smooth_with_llm(report, "auto", None)
    else:
        report = _report_from_company_view()

    revenue = report.financial_summary.get("average_monthly_revenue", 0.0)
    expenses = report.financial_summary.get("average_monthly_expenses", 0.0)
    monthly_excess_cash = max(0.0, revenue - expenses)
    return report, monthly_excess_cash


def create_program() -> Program:
    report, monthly_excess_cash = _load_report()
    proposals = build_proposals(report)
    program = Program(
        program_id=f"prog_{uuid.uuid4().hex[:8]}",
        company_name=report.business.get("name", "Business"),
        monthly_excess_cash=monthly_excess_cash,
        proposals={p.ticker: p for p in proposals},
    )
    return program


# --- sizing + Alpaca order placement --------------------------------------------
def _month_label(month_index: int) -> str:
    """month_index 1 = next month from "now" (month_index 0)."""
    today = date.today()
    year = today.year + (today.month - 1 + month_index) // 12
    month = (today.month - 1 + month_index) % 12 + 1
    return f"{year:04d}-{month:02d}"


async def size_and_resolve_rung(ticker: str, monthly_notional: float, target_month: str) -> LadderRung:
    """Resolve a strike via Alpaca's option chain, size a quantity off
    notional/strike (not premium - per spec), and place a market-order call buy.
    Degrades to a fabricated ref if the chain can't be resolved."""
    target_date = f"{target_month}-01"
    try:
        async with httpx.AsyncClient(timeout=4.0) as c:
            r = await c.get(f"{ALPACA}/chain/{ticker}", params={"right": "C", "expiration_date_gte": target_date})
            r.raise_for_status()
            chain = r.json()
        contracts = chain.get("option_contracts", [])
        strikes = sorted({float(ct["strike_price"]) for ct in contracts if ct.get("tradable", True)})
        if not strikes:
            raise ValueError("no tradable strikes in chain")
        strike = strikes[len(strikes) // 2]
    except Exception:
        # chain unresolved: stand-in strike, skip the order call entirely
        strike = max(1.0, monthly_notional / (100 * 10))
        quantity = max(1, round(monthly_notional / (strike * 100)))
        return LadderRung(
            month_index=0,  # filled in by caller
            target_month=target_month,
            contract_symbol=None,
            quantity=quantity,
            strike=round(strike, 2),
            status="degraded",
            order_ref=f"sim-{ticker}-{target_month}",
        )

    quantity = max(1, round(monthly_notional / (strike * 100)))
    res = await _post(
        ALPACA,
        "/hedge/option",
        {"ticker": ticker, "right": "C", "quantity": quantity, "expiration": target_date, "order_type": "market"},
    )
    if res:
        resolved = res.get("resolved") or {}
        order_ref = ((res.get("result") or {}).get("id")) or f"sim-{ticker}-{target_month}"
        return LadderRung(
            month_index=0,
            target_month=target_month,
            contract_symbol=resolved.get("symbol"),
            quantity=quantity,
            strike=float(resolved.get("strike_price", strike)),
            status="bought",
            order_ref=str(order_ref),
        )
    return LadderRung(
        month_index=0,
        target_month=target_month,
        contract_symbol=None,
        quantity=quantity,
        strike=round(strike, 2),
        status="degraded",
        order_ref=f"sim-{ticker}-{target_month}",
    )


async def build_ladder(program: Program, ticker: str) -> HedgeLadder:
    proposal = program.proposals[ticker]
    ladder = HedgeLadder(ticker=ticker, underlying=proposal.underlying, built_at_month_index=program.current_month_index)
    for month_index in range(1, COVERAGE_MONTHS + 1):
        target_month = _month_label(program.current_month_index + month_index)
        rung = await size_and_resolve_rung(ticker, proposal.monthly_notional, target_month)
        rung.month_index = month_index
        ladder.rungs.append(rung)
    program.ladders[ticker] = ladder
    return ladder


# --- parametric escrow (the heatwave tail leg) ----------------------------------
async def mint_escrow_policy(program: Program) -> dict:
    """Mint the one program-level parametric heatwave policy via the escrow venue.
    Pre-funds the payout and records the premium for display (premium is not pulled
    on-chain in the demo). Degrades to a fabricated ref if the escrow backend is down,
    exactly like compute_and_sweep / the option ladder."""
    res = await _post(
        ESCROW,
        "/policy",
        {
            "premium_usdc": ESCROW_PREMIUM_USDC,
            "trigger_index": ESCROW_TRIGGER_INDEX,
            "payout_usdc": ESCROW_PAYOUT_USDC,
        },
    )
    ref = (res or {}).get("tx_hash") or f"sim-escrow-{program.current_month_index}"
    entry = {
        "ticker": ESCROW_TICKER,
        "underlying": "Heatwave parametric cover",
        "premium_usdc": ESCROW_PREMIUM_USDC,
        "payout_usdc": ESCROW_PAYOUT_USDC,
        "trigger_index": ESCROW_TRIGGER_INDEX,
        "policy_id": (res or {}).get("policy_id"),
        "ref": str(ref),
        "status": "minted" if res else "degraded",
    }
    program.escrow_policies.append(entry)
    return entry


async def roll_ladder(program: Program, ladder: HedgeLadder) -> LadderRung:
    """Buy exactly one new rung at the new far end (current_month + 12), keeping
    the ladder's active coverage at a constant 12 months ahead."""
    proposal = program.proposals[ladder.ticker]
    new_month_index = program.current_month_index + COVERAGE_MONTHS
    target_month = _month_label(new_month_index)
    rung = await size_and_resolve_rung(ladder.ticker, proposal.monthly_notional, target_month)
    rung.month_index = new_month_index
    ladder.rungs.append(rung)
    return rung


# --- monthly excess cash sweep ---------------------------------------------------
async def compute_and_sweep(program: Program) -> dict:
    res = await _post(MORPHO, "/deposit", {"amount_usdc": program.monthly_excess_cash})
    ref = (res or {}).get("tx_hash") or f"sim-sweep-{program.current_month_index}"
    status = "settled" if res else "degraded"
    entry = {
        "month_index": program.current_month_index,
        "amount_usdc": program.monthly_excess_cash,
        "ref": str(ref),
        "status": status,
    }
    program.sweep_log.append(entry)
    return entry


async def advance_month(program: Program) -> dict:
    program.current_month_index += 1
    rungs_bought = []
    for ladder in program.ladders.values():
        rung = await roll_ladder(program, ladder)
        rungs_bought.append({"ticker": ladder.ticker, **rung.__dict__})
    sweep = await compute_and_sweep(program)
    return {"month_index": program.current_month_index, "rungs_bought": rungs_bought, "sweep": sweep}

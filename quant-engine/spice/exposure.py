"""Exposure extractor: ordinary monthly accounting (CSV) -> commodity exposure
map + hedge priorities.

Implements EXPOSURE_AGENT_PLAN.md. Reads the tidy CSV emitted by cashplan
(scripts/export_cost_csv.py), reuses spice.quant for cost-share, margin stress
and VaR, and adds mapping confidence, monthly volatility, a hedge-priority score,
evidence rows, and a JSON + Markdown report.

    CSV in (cashplan)  ->  map -> metrics -> stress -> score  ->  JSON + Markdown
                              (reuses spice.commodities, spice.quant)

CLI:  python -m spice.exposure <costs.csv> [--json out.json] [--md out.md]
"""

from __future__ import annotations

import argparse
import csv
import json
import statistics
import sys
from dataclasses import dataclass, field
from pathlib import Path

from . import commodities, quant
from .schema import Company, CostLine

# Scoring calibration (EXPOSURE_AGENT_PLAN weights: 40/35/15/10).
COST_SHARE_FULL = 0.30      # 30% of cost base -> full cost-share points
MARGIN_POINTS_FULL = 5.0    # 5 margin points lost @ +20% -> full margin points
VOL_FULL = 0.50             # 50% annual price vol -> full volatility points
SHOCK = 0.20                # the headline stress shock


# --- ingestion ---------------------------------------------------------------
@dataclass
class Row:
    business: str
    archetype: str
    month: str       # YYYY-MM
    kind: str        # expense | revenue
    category: str
    line: str
    underlying_raw: str
    amount: float
    source_row: int


def load_rows(csv_path: str | Path) -> list[Row]:
    rows: list[Row] = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for i, r in enumerate(csv.DictReader(f), start=2):  # row 1 = header
            try:
                amount = float(r.get("amount") or 0.0)
            except ValueError:
                amount = 0.0
            rows.append(
                Row(
                    business=(r.get("business") or "").strip(),
                    archetype=(r.get("archetype") or "").strip(),
                    month=(r.get("period_month") or "").strip(),
                    kind=(r.get("kind") or "expense").strip().lower(),
                    category=(r.get("category") or "").strip(),
                    line=(r.get("line") or "").strip(),
                    underlying_raw=(r.get("underlying") or "").strip(),
                    amount=amount,
                    source_row=i,
                )
            )
    return rows


# --- mapping -----------------------------------------------------------------
@dataclass
class Mapping:
    ticker: str | None
    confidence: float
    rule: str


def map_row(r: Row) -> Mapping:
    """Trust the underlying tag first; fall back to keyword inference."""
    t = commodities.ticker_for_underlying(r.underlying_raw)
    if t:
        return Mapping(t, 0.95, f"tag '{r.underlying_raw}' -> {t}")
    t = commodities.infer_ticker(f"{r.line} {r.category}")
    if t:
        return Mapping(t, 0.75, f"keyword -> {t}")
    return Mapping(None, 0.0, "unmapped")


# --- analysis ----------------------------------------------------------------
@dataclass
class Exposure:
    ticker: str
    underlying: str
    total_spend: float
    expense_share: float
    revenue_share: float
    mapping_confidence: float
    monthly_volatility: float       # coefficient of variation of monthly spend
    price_volatility: float         # annualised commodity price vol (registry)
    shock20_margin_points_lost: float
    hedge_notional: float
    score: int
    recommendation: str
    evidence: list[dict] = field(default_factory=list)


@dataclass
class Report:
    business: dict
    financial_summary: dict
    exposures: list[Exposure]
    unmapped: dict
    var: dict


def _band(score: int) -> str:
    if score >= 80:
        return "Hedge priority"
    if score >= 60:
        return "Hedge recommended"
    if score >= 40:
        return "Monitor"
    return "Do not hedge yet"


def analyze(rows: list[Row]) -> Report:
    expenses = [r for r in rows if r.kind == "expense"]
    revenues = [r for r in rows if r.kind == "revenue"]
    months = sorted({r.month for r in rows if r.month})
    n_months = max(1, len(months))
    years = n_months / 12.0

    total_expense = sum(r.amount for r in expenses)
    total_revenue = sum(r.amount for r in revenues)
    margin = total_revenue - total_expense
    margin_pct = margin / total_revenue if total_revenue else 0.0

    # aggregate expenses by ticker
    by_ticker_spend: dict[str, float] = {}
    by_ticker_monthly: dict[str, dict[str, float]] = {}
    by_ticker_conf: dict[str, float] = {}
    by_ticker_rows: dict[str, list[Row]] = {}
    unmapped_total = 0.0
    unmapped_rows: list[Row] = []

    for r in expenses:
        m = map_row(r)
        if not m.ticker:
            unmapped_total += r.amount
            unmapped_rows.append(r)
            continue
        by_ticker_spend[m.ticker] = by_ticker_spend.get(m.ticker, 0.0) + r.amount
        monthly = by_ticker_monthly.setdefault(m.ticker, {})
        monthly[r.month] = monthly.get(r.month, 0.0) + r.amount
        by_ticker_conf[m.ticker] = max(by_ticker_conf.get(m.ticker, 0.0), m.confidence)
        by_ticker_rows.setdefault(m.ticker, []).append(r)

    # build a Company (annualised) so we can reuse quant.var + recommend_hedges
    cost_lines = [
        CostLine(label=commodities.en_name(t), annual_amount=spend / years, commodity=t)
        for t, spend in by_ticker_spend.items()
    ]
    if unmapped_total:
        cost_lines.append(CostLine("Other (labour, rent, …)", unmapped_total / years, None))
    company = Company(
        name=rows[0].business if rows else "Business",
        revenue=total_revenue / years if total_revenue else 0.0,
        cash=0.0,
        cost_lines=cost_lines,
    )
    hedges = {h.commodity: h.notional for h in quant.recommend_hedges(company)}

    exposures: list[Exposure] = []
    for t, spend in sorted(by_ticker_spend.items(), key=lambda kv: kv[1], reverse=True):
        series = [by_ticker_monthly[t].get(m, 0.0) for m in months]
        mean = statistics.fmean(series) if series else 0.0
        monthly_vol = (statistics.pstdev(series) / mean) if mean else 0.0
        price_vol = commodities.vol(t)
        # +20% shock on this commodity only -> margin points lost
        extra_cost = spend * SHOCK
        points_lost = (extra_cost / total_revenue * 100) if total_revenue else 0.0

        score = round(
            40 * min((spend / total_expense) / COST_SHARE_FULL, 1.0)
            + 35 * min(points_lost / MARGIN_POINTS_FULL, 1.0)
            + 15 * min(max(price_vol, monthly_vol) / VOL_FULL, 1.0)
            + 10 * by_ticker_conf.get(t, 0.0)
        )
        evidence = [
            {
                "source_row": r.source_row,
                "description": r.line,
                "amount": round(r.amount, 2),
                "matched_rule": map_row(r).rule,
            }
            for r in sorted(by_ticker_rows[t], key=lambda r: r.amount, reverse=True)[:3]
        ]
        exposures.append(
            Exposure(
                ticker=t,
                underlying=commodities.en_name(t),
                total_spend=round(spend, 2),
                expense_share=round(spend / total_expense, 4) if total_expense else 0.0,
                revenue_share=round(spend / total_revenue, 4) if total_revenue else 0.0,
                mapping_confidence=round(by_ticker_conf.get(t, 0.0), 2),
                monthly_volatility=round(monthly_vol, 4),
                price_volatility=price_vol,
                shock20_margin_points_lost=round(points_lost, 2),
                hedge_notional=round(hedges.get(t, 0.0), 2),
                score=score,
                recommendation=_band(score),
                evidence=evidence,
            )
        )

    var_before = quant.var(company)
    var_after = quant.var(company, residual_basis=0.15)

    return Report(
        business={
            "name": company.name,
            "period_start": months[0] if months else None,
            "period_end": months[-1] if months else None,
            "months_analyzed": len(months),
        },
        financial_summary={
            "average_monthly_revenue": round(total_revenue / n_months, 2),
            "average_monthly_expenses": round(total_expense / n_months, 2),
            "average_margin_pct": round(margin_pct, 4),
            "mapped_expense_share": round(
                (total_expense - unmapped_total) / total_expense, 4
            ) if total_expense else 0.0,
        },
        exposures=exposures,
        unmapped={
            "expense_share": round(unmapped_total / total_expense, 4) if total_expense else 0.0,
            "top_rows": [
                {"source_row": r.source_row, "description": r.line, "amount": round(r.amount, 2)}
                for r in sorted(unmapped_rows, key=lambda r: r.amount, reverse=True)[:5]
            ],
        },
        var={
            "annual_margin_var_pct_before": round(var_before.pct_revenue, 4),
            "annual_margin_var_pct_after_hedge": round(var_after.pct_revenue, 4),
            "eur_before": round(var_before.eur, 2),
            "eur_after": round(var_after.eur, 2),
        },
    )


# --- outputs -----------------------------------------------------------------
def to_json(report: Report) -> str:
    payload = {
        "business": report.business,
        "financial_summary": report.financial_summary,
        "exposures": [e.__dict__ for e in report.exposures],
        "unmapped": report.unmapped,
        "var": report.var,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def to_markdown(report: Report) -> str:
    b, fs = report.business, report.financial_summary
    lines = [
        f"# Commodity exposure report — {b['name']}",
        "",
        f"Period {b['period_start']} to {b['period_end']} ({b['months_analyzed']} months). "
        f"Avg monthly revenue €{fs['average_monthly_revenue']:,.0f}, "
        f"avg margin {fs['average_margin_pct'] * 100:.1f}%, "
        f"{fs['mapped_expense_share'] * 100:.0f}% of expenses mapped to a commodity.",
        "",
        "## Hedge priorities",
        "",
        "| Underlying | Cost share | Rev share | +20% shock (margin pts) | Score | Recommendation |",
        "|---|--:|--:|--:|--:|---|",
    ]
    for e in report.exposures:
        lines.append(
            f"| {e.underlying} ({e.ticker}) | {e.expense_share * 100:.0f}% | "
            f"{e.revenue_share * 100:.0f}% | {e.shock20_margin_points_lost:.1f} | "
            f"{e.score} | {e.recommendation} |"
        )
    lines += [
        "",
        f"Annual margin VaR: {report.var['annual_margin_var_pct_before'] * 100:.1f}% of revenue "
        f"unhedged → {report.var['annual_margin_var_pct_after_hedge'] * 100:.1f}% hedged.",
        "",
        "## Evidence (top contributing lines)",
        "",
    ]
    for e in report.exposures:
        lines.append(f"**{e.underlying}** — confidence {e.mapping_confidence:.2f}")
        for ev in e.evidence:
            lines.append(f"- row {ev['source_row']}: {ev['description']} (€{ev['amount']:,.0f}) — {ev['matched_rule']}")
        lines.append("")
    if report.unmapped["top_rows"]:
        lines.append(f"## Unmapped ({report.unmapped['expense_share'] * 100:.0f}% of expenses)")
        for ev in report.unmapped["top_rows"]:
            lines.append(f"- row {ev['source_row']}: {ev['description']} (€{ev['amount']:,.0f})")
        lines.append("")
    lines.append("> Risk analysis, not financial advice. v1 maps direct inputs only, no multi-hop supply chain.")
    return "\n".join(lines)


# --- CLI ---------------------------------------------------------------------
def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")  # Windows console is cp1252
    except Exception:
        pass
    ap = argparse.ArgumentParser(description="Spice exposure extractor")
    ap.add_argument("csv", help="tidy cost CSV from cashplan")
    ap.add_argument("--json", dest="json_out", default=None)
    ap.add_argument("--md", dest="md_out", default=None)
    args = ap.parse_args()

    report = analyze(load_rows(args.csv))
    js = to_json(report)
    md = to_markdown(report)

    if args.json_out:
        Path(args.json_out).write_text(js, encoding="utf-8")
    if args.md_out:
        Path(args.md_out).write_text(md, encoding="utf-8")
    if not args.json_out and not args.md_out:
        print(md)
        print("\n--- JSON ---\n")
        print(js)


if __name__ == "__main__":
    main()

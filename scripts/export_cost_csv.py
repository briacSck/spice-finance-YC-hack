"""Emit a tidy monthly cost + revenue CSV from a cashplan BusinessProfile.

Sibling to cashplan (does NOT modify Sara's files). Reproduces the workbook's
per-line monthly computation in Python, because the generated .xlsx is
formula-driven and openpyxl does not evaluate formulas (data_only reads None on
a workbook never opened in Excel). This CSV is the contract the exposure
extractor consumes.

    python scripts/export_cost_csv.py "boulangerie artisanale" --name "Maison Levain" --out bakery_costs.csv
    cd quant-engine && python -m spice.exposure ../bakery_costs.csv
"""

from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # repo root on path

from cashplan.business_profiles import infer_business_profile, slugify

HEADER = ["business", "archetype", "period_month", "kind", "category", "line", "underlying", "amount"]


def build_rows(profile, business_label: str, start_year: int, years: int) -> list[tuple]:
    season = profile.seasonality
    season_sum = sum(season) or 1.0
    rows: list[tuple] = []
    for yi in range(years):
        year = start_year + yi
        growth = (1 + profile.annual_revenue_growth) ** yi
        infl = (1 + profile.purchase_inflation) ** yi
        for mi in range(12):
            month = f"{year:04d}-{mi + 1:02d}"
            # revenue: annual_revenue * stream.share * normalized seasonal weight * growth
            weight = season[mi] / season_sum
            for s in profile.revenue_streams:
                amt = profile.annual_revenue * s.share * weight * growth
                rows.append((business_label, profile.archetype, month, "revenue", "Revenue", s.name, "", round(amt, 2)))
            # expenses: monthly_quantity * seasonality (raw, or 1 if not linked) * unit_price * inflation
            for line in profile.cost_lines:
                seas = season[mi] if line.seasonality_linked else 1.0
                amt = line.monthly_quantity * seas * line.unit_price * infl
                rows.append(
                    (business_label, profile.archetype, month, "expense",
                     line.category, line.name, line.underlying or "", round(amt, 2))
                )
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description="Emit a tidy monthly cost CSV from a business description")
    ap.add_argument("business", help="e.g. 'boulangerie artisanale', 'transport routier'")
    ap.add_argument("--name", default=None, help="display name for the business (default: archetype description)")
    ap.add_argument("--annual-revenue", type=float, default=None)
    ap.add_argument("--start-year", type=int, default=2026)
    ap.add_argument("--years", type=int, default=3)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    profile = infer_business_profile(args.business, args.annual_revenue)
    label = args.name or profile.business_type
    rows = build_rows(profile, label, args.start_year, args.years)

    out = Path(args.out or f"{slugify(label)}_costs.csv")
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(HEADER)
        w.writerows(rows)
    print(f"wrote {len(rows)} rows for '{label}' ({profile.archetype}) -> {out}")


if __name__ == "__main__":
    main()

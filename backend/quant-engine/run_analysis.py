"""Runnable demo of the Spice quant engine over the synthetic bakery.

    python run_analysis.py

Zero dependencies (stdlib only). Prints the decomposition, a commodity shock,
its hit to margin, the recommended hedge, and the before/after VaR — i.e. the
numbers the agent narrates and the frontend renders.
"""

from __future__ import annotations

from pathlib import Path

from spice import quant
from spice.schema import load_company

DATA = Path(__file__).parent / "spice" / "data" / "maison_levain.json"

# A scenario the agent picks (not live data): wheat + gas + power + diesel rise.
SHOCK = {"WEAT": 0.20, "UNG": 0.30, "XLU": 0.10, "USO": 0.15, "SOYB": 0.05}


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def eur(x: float) -> str:
    return f"€{x:,.0f}"


def main() -> None:
    co = load_company(DATA)
    print(f"\n=== {co.name} — revenue {eur(co.revenue)}, net margin {pct(co.net_margin)} ===\n")

    print("Hidden commodity book (cost decomposition):")
    for e in quant.decompose(co):
        print(f"  {e.commodity:5} {e.name:14} {eur(e.amount):>12}"
              f"  {pct(e.share_of_revenue):>6} of revenue   vol {pct(e.vol)}")

    prop = quant.propagate(co, SHOCK)
    print(f"\nScenario shock: {', '.join(f'{k} +{int(v*100)}%' for k, v in SHOCK.items())}")
    print(f"  added input cost: {eur(prop.added_cost)}")
    print(f"  net margin: {pct(prop.margin_before)}  ->  {pct(prop.margin_after)}  "
          f"(unhedged)")

    hedges = quant.recommend_hedges(co, coverage=1.0)
    rows, total = quant.hedge_pnl(hedges, SHOCK)
    hedged_profit = co.net_profit - prop.added_cost + total
    print(f"\nRecommended hedge (long each commodity at its input exposure):")
    for h in hedges:
        print(f"  long {h.commodity:5} notional {eur(h.notional)}")
    print(f"  hedge P&L under shock: {eur(total)}")
    print(f"  net margin with hedge: {pct(hedged_profit / co.revenue)}  (restored)")

    v_before = quant.var(co, residual_basis=0.0)
    v_after = quant.var(co, residual_basis=0.15)
    print(f"\nAnnual margin VaR (95%):")
    print(f"  unhedged: {eur(v_before.eur)}  ({pct(v_before.pct_revenue)} of revenue)")
    print(f"  hedged:   {eur(v_after.eur)}  ({pct(v_after.pct_revenue)} of revenue)")
    print()


if __name__ == "__main__":
    main()

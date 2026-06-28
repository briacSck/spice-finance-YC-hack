"""Core data model: a business re-expressed as a commodity book.

    Company
      ├─ revenue
      ├─ cash
      └─ cost_lines: [CostLine(label, annual_amount, commodity)]
                      commodity is a hedgeable ticker (WEAT/UNG/…) or None (labour, rent)

Everything downstream (decomposition, shock propagation, VaR, hedge P&L) is a
pure function of a Company. Synthetic instances live in spice/data/*.json.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class CostLine:
    label: str
    annual_amount: float
    commodity: str | None = None  # hedgeable ticker, or None for non-commodity cost


@dataclass(frozen=True)
class Company:
    name: str
    revenue: float
    cash: float
    cost_lines: list[CostLine] = field(default_factory=list)

    @property
    def total_cost(self) -> float:
        return sum(c.annual_amount for c in self.cost_lines)

    @property
    def net_profit(self) -> float:
        return self.revenue - self.total_cost

    @property
    def net_margin(self) -> float:
        return self.net_profit / self.revenue if self.revenue else 0.0

    def commodity_lines(self) -> list[CostLine]:
        return [c for c in self.cost_lines if c.commodity]


def load_company(path: str | Path) -> Company:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    lines = [CostLine(**ln) for ln in data["cost_lines"]]
    return Company(
        name=data["name"],
        revenue=float(data["revenue"]),
        cash=float(data["cash"]),
        cost_lines=lines,
    )

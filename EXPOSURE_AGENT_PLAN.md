# Spice Exposure Agent Plan

## Goal

Build the first Spice agent: given an Excel file containing monthly business
revenues and expenses over several years, identify which commodity underlyings
the company should consider hedging.

The agent does not execute hedges yet. Its job is to turn ordinary accounting
data into an explainable commodity exposure map and a hedge priority list.

## Product Principle

Hedge when a commodity-linked cost is both:

1. A meaningful share of the company's cost base.
2. Capable of materially damaging margins under a plausible price shock.

This first version should be simple, auditable, and demo-ready. It should not try
to infer deep supply-chain relationships yet.

## Underlyings In Scope

The first version maps expenses only to these commodity underlyings:

| Underlying | Direct business inputs to map |
| --- | --- |
| Oil | Plastics, polymers, PVC, polystyrene, polyurethane, bitumen, synthetic rubber, transport, logistics, off-road diesel, diesel, fuel |
| Electricity | Electricity, aluminium, glass, partially electric steel, electric ovens, refrigeration |
| Gas | Gas, cement, glass, nitrogen fertilizers, ammonia, parts of chemicals |
| Wheat | Flour, bread, wheat, animal feed, part of meat when explicitly visible |
| Fats | Butter, cream, fats, dairy fats |
| Copper | Copper, wiring, electrical components, copper piping |
| Steel / iron ore proxy | Carbon steel, galvanized steel substrate, rebar, sheet, tubes, profiles |
| Aluminium | Aluminium profiles, sheets, frames, castings, aluminium-heavy components |
| Zinc | Galvanization, zinc coating, plated fasteners, die-cast zinc hardware |
| Nickel | Stainless steel, nickel alloying inputs, specialty alloys |
| Tin | Solder, tinplate, electronics-adjacent consumables |
| Lead | Batteries, shielding, lead components where explicitly visible |
| Wood | Wood, pallets, wood packaging, timber, carpentry, construction wood |

Out of scope for v1:

- Multi-hop supply-chain inference.
- Automatic mapping from obscure suppliers to their underlying input costs.
- Real hedge execution.
- Options pricing or portfolio optimization.
- Real-time market data.

Note: for industrial SMBs, v1 should avoid a single generic "metal" bucket. It
should preserve material-level exposure whenever the accounting labels make it
visible: steel, aluminium, copper, zinc, nickel/stainless, tin and lead should be
separate underlyings or proxies.

## Expected Input

The agent should accept an Excel workbook with one or more sheets. The ideal
input is a transaction-level or monthly accounting export containing:

| Field | Required | Notes |
| --- | --- | --- |
| Date or month | Yes | Used to build monthly time series |
| Amount | Yes | Signed or accompanied by a direction/type column |
| Direction/type | Preferred | Expense, revenue, debit, credit, etc. |
| Category/account | Preferred | Accounting category or chart-of-accounts label |
| Description/label | Preferred | Used for commodity matching |
| Vendor/supplier | Optional | Used as supporting evidence, not deep inference |

If the file is already summarized monthly by category, the agent should still
work. If the schema is ambiguous, the agent should return a clear column-mapping
request rather than guessing silently.

## Processing Pipeline

### 1. Load and Normalize

Parse the Excel file and produce a normalized table:

```text
month
amount
direction
category
description
vendor
source_sheet
source_row
```

Normalize dates to calendar months, amounts to positive expense/revenue values,
and labels to lowercase searchable text.

### 2. Separate Revenues and Expenses

Aggregate by month:

- revenue
- total expenses
- mapped commodity-linked expenses
- unmapped expenses
- approximate margin

Margin can start simple:

```text
margin = revenue - total_expenses
margin_pct = margin / revenue
```

If revenue is unavailable, the agent should still rank cost exposures but should
not claim margin impact.

### 3. Map Expense Lines to Underlyings

Use a deterministic keyword/rule layer first. Each matched line should include:

- underlying
- matched keyword or rule
- confidence score
- source rows
- amount

Recommended confidence:

| Confidence | Meaning |
| --- | --- |
| 0.90-1.00 | Direct explicit match, e.g. "flour" -> Wheat |
| 0.70-0.89 | Strong category match, e.g. "transport" -> Oil |
| 0.40-0.69 | Ambiguous match needing review |
| < 0.40 | Unmapped |

A later version can use an LLM fallback for ambiguous rows, but v1 should keep
the rule layer as the source of truth so the demo is explainable.

### 4. Compute Exposure Metrics

For each underlying, compute:

- total mapped spend
- share of total expenses
- share of revenue
- monthly spend time series
- month-over-month variability
- trend over the available period
- number of supporting rows
- top contributing categories/vendors/descriptions
- mapping confidence

The key first-order metric is cost share. The key business metric is margin
sensitivity.

### 5. Stress Test Margin

For each underlying, simulate price shocks:

```text
+10%, +20%, +30%
```

For each shock, estimate:

```text
extra_cost = underlying_spend * shock_pct
stressed_margin = margin - extra_cost
stressed_margin_pct = stressed_margin / revenue
margin_points_lost = base_margin_pct - stressed_margin_pct
```

This gives the demo its "risk desk" moment: the agent can say, for example,
"Wheat-linked spend is 18% of costs. A 20% wheat-linked cost shock would reduce
margin by 3.6 percentage points."

### 6. Score Hedge Priority

Recommended v1 score out of 100:

| Component | Weight |
| --- | ---: |
| Share of cost base | 40 |
| Margin impact under +20% shock | 35 |
| Historical volatility or upward trend | 15 |
| Mapping confidence | 10 |

Suggested recommendation bands:

| Score | Recommendation |
| ---: | --- |
| 80-100 | Hedge priority |
| 60-79 | Hedge recommended |
| 40-59 | Monitor |
| 0-39 | Do not hedge yet |

Suggested initial hard triggers:

- Hedge candidate if the underlying is more than 10% of expenses.
- Hedge candidate if a +20% shock costs more than 2 margin points.
- Monitor if exposure is 5-10% of expenses or the trend is rising quickly.

These thresholds are intentionally simple and should be easy to tune.

### 7. Produce Outputs

The agent should produce both a structured JSON output and a human-readable
Markdown report.

#### JSON Shape

```json
{
  "business": {
    "name": "Maison Levain",
    "period_start": "2023-01",
    "period_end": "2025-12",
    "months_analyzed": 36
  },
  "financial_summary": {
    "average_monthly_revenue": 116000,
    "average_monthly_expenses": 103000,
    "average_margin_pct": 0.112,
    "mapped_expense_share": 0.47
  },
  "exposures": [
    {
      "underlying": "Wheat",
      "total_spend": 420000,
      "expense_share": 0.18,
      "revenue_share": 0.13,
      "mapping_confidence": 0.94,
      "shock_20_margin_points_lost": 3.6,
      "score": 87,
      "recommendation": "Hedge priority",
      "evidence": [
        {
          "source_row": 42,
          "description": "Flour supplier invoice",
          "amount": 12500,
          "matched_rule": "flour -> Wheat"
        }
      ]
    }
  ],
  "unmapped": {
    "expense_share": 0.53,
    "top_rows": []
  }
}
```

#### Markdown Report

The report should include:

1. Executive summary.
2. Top hedge priorities.
3. Underlying-by-underlying exposure table.
4. Margin stress test table.
5. Evidence rows from the Excel file.
6. Unmapped/low-confidence rows that need human review.
7. Out-of-scope warning: this is risk analysis, not financial advice.

## Agent Behavior

The agent should behave like a junior risk analyst with perfect spreadsheet
hygiene:

- Be explicit about what it knows from the file.
- Never hide low confidence.
- Cite the rows or labels behind every recommendation.
- Distinguish "large cost exposure" from "hedgeable risk".
- Avoid pretending it can infer supplier supply chains in v1.

## Demo Narrative

For the bakery demo:

1. Upload monthly Excel export.
2. Agent identifies flour, gas, electricity, butter/cream.
3. Agent maps them to Wheat, Gas, Electricity, Fats.
4. Agent shows that Wheat and Gas are large enough to threaten margin.
5. Agent recommends hedge priority on Wheat, hedge recommended on Gas, monitor
   Electricity and Fats.
6. The next Spice module can then propose execution routes.

## Open Questions

1. Is the expected Excel file transaction-level, monthly category-level, or both?
2. Should v1 always require revenue data, or should it support expense-only mode?
3. Should the first output be optimized for frontend consumption, human report,
   or both?
4. Should ambiguous rows use an LLM fallback in v1, or stay rule-only for
   explainability?
5. What exact thresholds should trigger "hedge priority" for the hackathon demo?

## Suggested Build Order

1. Create a synthetic Excel file for the hero bakery.
2. Implement Excel ingestion and schema detection.
3. Implement the static commodity mapping rules.
4. Compute exposure metrics and margin stress tests.
5. Generate JSON output.
6. Generate Markdown report.
7. Add a CLI wrapper for local demo use.
8. Connect JSON output to the frontend later.

# Commodity exposure report — Transport Routier

Period 2021-01 to 2023-12 (36 months). Avg monthly revenue €73,341, avg margin 0.6%, 40% of expenses mapped to a commodity.

## Hedge priorities (ranked by score)

| Rank | Underlying | Cost share | Price vol | Vol source | +20% shock (margin pts) | Score | Recommendation |
|--:|---|--:|--:|---|--:|--:|---|
| 1 | Oil (USO) | 40% | 41% | INSEE BDM BRENT (10y monthly) | 8.0 | 91 | Hedge recommended |

Annual margin VaR: 23.1% of revenue unhedged → 3.5% hedged.

<details><summary>How the score and recommendation are computed</summary>

Score (0-100) is a weighted sum, each term capped at its max:
- 50 pts: cost share, capped at 30% of total expenses
- 50 pts: annualised price volatility of the underlying commodity, capped at 50%

Price volatility is computed from real INSEE BDM monthly price series (std of month-over-month returns, annualised) when a series is mapped for that ticker - no other external source (Alpha Vantage, World Bank, synthetic) is used. If INSEE has no series for a ticker or the fetch/cache both fail, it falls back to a static registry estimate, flagged in the 'Vol source' column.

This score sets the ranking only. The final Recommendation per line is decided by the LLM narrative layer (see Hedge decisions below), which can deviate from the ranking when the underlying numbers justify it. Without an LLM call (--llm not set or no API key), the Recommendation stays 'Pending LLM decision'.

</details>

## Hedge decisions (AI reasoning)

- **USO** — Hedge recommended: With an expense share of 40.32% and a potential loss of 8.02 margin points translating to roughly -€740/month, hedging against oil price increases is advisable to protect your already thin margins.

## Evidence (top contributing lines)

**Oil** — confidence 0.95
- row 6: Diesel fuel (€45,742) — tag 'Oil' -> USO
- row 6: Diesel fuel (€44,587) — tag 'Oil' -> USO
- row 6: Diesel fuel (€40,099) — tag 'Oil' -> USO

## Unmapped (60% of expenses)
- row 14: Drivers payroll and charges (€25,500)
- row 14: Drivers payroll and charges (€25,500)
- row 14: Drivers payroll and charges (€25,500)
- row 14: Drivers payroll and charges (€25,500)
- row 14: Drivers payroll and charges (€25,500)

## Findings explained (AI)

**Executive Angle**: As the owner of Transport Routier, understanding your exposure to commodity prices is crucial for maintaining your thin profit margins. With the current economic climate, fluctuations in oil prices can significantly impact your bottom line, especially given that diesel fuel is a major cost driver for your operations.

**Owner Message**: This report outlines how changes in oil prices could affect your finances, particularly focusing on diesel fuel, which is a significant part of your expenses. By understanding these impacts, you can make informed decisions about whether to lock in prices now or wait.

**Demo Script**: Let's break down your exposure to oil prices. Diesel fuel accounts for a substantial portion of your costs, specifically 40.32% of your expenses. If oil prices were to jump by 20%, you would lose approximately 8.02 margin points. Given your average monthly revenue of €73,341.42, this translates to about -€740 per month. This is a significant amount, especially considering your already thin margin of just 0.6%. It's important to note that other expenses, like driver payroll, are not linked to commodity prices, which limits our analysis to just the mapped expenses. This means we need to be particularly cautious about fluctuations in oil prices, as they can have a direct and immediate impact on your profitability.

**Ambiguity Notes**: The unmapped expenses, which account for 59.68% of total expenses, include fixed costs like salaries and rent that do not fluctuate with commodity prices. This means that while we can analyze the impact of oil price changes on your variable costs, we cannot account for how these changes might affect your overall financial health when fixed costs are considered.

> Risk analysis, not financial advice. v1 maps direct inputs only, no multi-hop supply chain.
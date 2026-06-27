# Commodity exposure report — Boulangerie Artisanale

Period 2021-01 to 2023-12 (36 months). Avg monthly revenue €26,485, avg margin 1.9%, 38% of expenses mapped to a commodity.

## Hedge priorities (ranked by score)

| Rank | Underlying | Cost share | Price vol | Vol source | +20% shock (margin pts) | Score | Recommendation |
|--:|---|--:|--:|---|--:|--:|---|
| 1 | Gas (UNG) | 4% | 65% | INSEE BDM NATURAL_GAS (10y monthly) | 0.7 | 56 | Do not hedge yet |
| 2 | Wheat (WEAT) | 14% | 23% | INSEE BDM WHEAT (10y monthly) | 2.8 | 46 | Hedge recommended |
| 3 | Fats (SOYB) | 13% | 6% | INSEE BDM DAIRY_FATS (10y monthly) | 2.5 | 27 | Hedge recommended |
| 4 | Wood (WOOD) | 4% | 20% | INSEE BDM WOOD (4y monthly) | 0.7 | 26 | Do not hedge yet |
| 5 | Electricity (XLU) | 4% | 7% | INSEE BDM ELECTRICITY (10y monthly) | 0.8 | 14 | Do not hedge yet |

Annual margin VaR: 9.4% of revenue unhedged → 1.4% hedged.

<details><summary>How the score and recommendation are computed</summary>

Score (0-100) is a weighted sum, each term capped at its max:
- 50 pts: cost share, capped at 30% of total expenses
- 50 pts: annualised price volatility of the underlying commodity, capped at 50%

Price volatility is computed from real INSEE BDM monthly price series (std of month-over-month returns, annualised) when a series is mapped for that ticker - no other external source (Alpha Vantage, World Bank, synthetic) is used. If INSEE has no series for a ticker or the fetch/cache both fail, it falls back to a static registry estimate, flagged in the 'Vol source' column.

This score sets the ranking only. The final Recommendation per line is decided by the LLM narrative layer (see Hedge decisions below), which can deviate from the ranking when the underlying numbers justify it. Without an LLM call (--llm not set or no API key), the Recommendation stays 'Pending LLM decision'.

</details>

## Hedge decisions (AI reasoning)

- **UNG** — Do not hedge yet: Gas represents only 3.59% of your costs, and a 20% price increase would lead to a loss of 0.7 margin points, which is about -€740/month; this is manageable compared to other exposures.
- **WEAT** — Hedge recommended: Wheat accounts for 14.01% of your costs, and a 20% price jump would cost you 2.75 margin points, approximately -€730/month, which significantly impacts your thin margin.
- **SOYB** — Hedge recommended: Fats make up 12.9% of your costs, and a 20% price increase would result in a loss of 2.53 margin points, around -€670/month, which is substantial given your low overall margin.
- **WOOD** — Do not hedge yet: Wood represents only 3.64% of your costs, and a 20% price increase would lead to a loss of 0.71 margin points, about -€190/month, which is less impactful than other exposures.
- **XLU** — Do not hedge yet: Electricity accounts for 4.23% of your costs, and a 20% price increase would cost you 0.83 margin points, roughly -€220/month, which is manageable compared to the risks from wheat and fats.

## Evidence (top contributing lines)

**Gas** — confidence 0.95
- row 25: Gas for heating (€2,645) — tag 'Gas' -> UNG
- row 25: Gas for heating (€2,256) — tag 'Gas' -> UNG
- row 25: Gas for heating (€2,082) — tag 'Gas' -> UNG

**Wheat** — confidence 0.95
- row 6: Wheat flour T55/T65 (€5,488) — tag 'Wheat' -> WEAT
- row 6: Wheat flour T55/T65 (€5,211) — tag 'Wheat' -> WEAT
- row 6: Wheat flour T55/T65 (€4,848) — tag 'Wheat' -> WEAT

**Fats** — confidence 0.95
- row 8: Tourage butter (€2,752) — tag 'Fats' -> SOYB
- row 8: Tourage butter (€2,610) — tag 'Fats' -> SOYB
- row 8: Tourage butter (€2,408) — tag 'Fats' -> SOYB

**Wood** — confidence 0.95
- row 20: Packaging (€1,241) — tag 'Packaging' -> WOOD
- row 20: Packaging (€1,144) — tag 'Packaging' -> WOOD
- row 20: Packaging (€1,129) — tag 'Packaging' -> WOOD

**Electricity** — confidence 0.95
- row 23: Electricity for ovens and refrigeration (€1,530) — tag 'Electricity' -> XLU
- row 23: Electricity for ovens and refrigeration (€1,367) — tag 'Electricity' -> XLU
- row 23: Electricity for ovens and refrigeration (€1,323) — tag 'Electricity' -> XLU

## Unmapped (62% of expenses)
- row 29: Employee salary and charges (€5,600)
- row 29: Employee salary and charges (€5,600)
- row 29: Employee salary and charges (€5,600)
- row 29: Employee salary and charges (€5,600)
- row 29: Employee salary and charges (€5,600)

## Findings explained (AI)

**Executive Angle**: This report highlights the key commodity exposures for Boulangerie Artisanale, focusing on how fluctuations in raw material prices can impact your profit margins. Understanding these exposures will help you make informed decisions about whether to lock in prices now or wait.

**Owner Message**: As a bakery owner, it's crucial to know how the prices of your key ingredients can affect your bottom line. This report breaks down the potential financial impact of price changes in gas, wheat, fats, wood, and electricity, helping you decide if you should hedge against these risks.

**Demo Script**: Let's look at the key commodities that affect your business. First, we have Gas, which accounts for 3.59% of your costs. If the price jumps by 20%, you could lose 0.7 margin points, which translates to about -€740 per month on your average revenue of €26,485. Next is Wheat, making up 14.01% of your expenses. A 20% price increase would cost you 2.75 margin points, roughly -€730 monthly. Fats, at 12.9% of costs, could lead to a loss of 2.53 margin points, about -€670 monthly. Wood, representing 3.64% of your expenses, would result in a loss of 0.71 margin points, or about -€190 monthly. Lastly, Electricity, at 4.23% of costs, could cost you 0.83 margin points, around -€220 monthly. These figures show how vulnerable your margins are to price changes in these commodities.

**Ambiguity Notes**: The analysis does not include salaries and rent, which are significant costs but not directly linked to commodity prices. This means that while we can assess the impact of commodity price changes, we must also consider that other fixed costs will still apply regardless of commodity price fluctuations.

> Risk analysis, not financial advice. v1 maps direct inputs only, no multi-hop supply chain.
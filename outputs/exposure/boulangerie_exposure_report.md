# Commodity exposure report — Boulangerie Artisanale

Period 2021-01 to 2023-12 (36 months). Avg monthly revenue €26,485, avg margin 1.9%, 38% of expenses mapped to a commodity.

## Hedge priorities

| Underlying | Cost share | Rev share | +20% shock (margin pts) | Score | Recommendation |
|---|--:|--:|--:|--:|---|
| Wheat (WEAT) | 14% | 14% | 2.8 | 56 | Hedge recommended |
| Fats (SOYB) | 13% | 13% | 2.5 | 52 | Hedge recommended |
| Electricity (XLU) | 4% | 4% | 0.8 | 27 | Do not hedge yet |
| Wood (WOOD) | 4% | 4% | 0.7 | 27 | Do not hedge yet |
| Gas (UNG) | 4% | 4% | 0.7 | 34 | Do not hedge yet |

Annual margin VaR: 9.4% of revenue unhedged → 1.4% hedged.

## Evidence (top contributing lines)

**Wheat** — confidence 0.95
- row 6: Wheat flour T55/T65 (€5,488) — tag 'Wheat' -> WEAT
- row 6: Wheat flour T55/T65 (€5,211) — tag 'Wheat' -> WEAT
- row 6: Wheat flour T55/T65 (€4,848) — tag 'Wheat' -> WEAT

**Fats** — confidence 0.95
- row 8: Tourage butter (€2,752) — tag 'Fats' -> SOYB
- row 8: Tourage butter (€2,610) — tag 'Fats' -> SOYB
- row 8: Tourage butter (€2,408) — tag 'Fats' -> SOYB

**Electricity** — confidence 0.95
- row 23: Electricity for ovens and refrigeration (€1,530) — tag 'Electricity' -> XLU
- row 23: Electricity for ovens and refrigeration (€1,367) — tag 'Electricity' -> XLU
- row 23: Electricity for ovens and refrigeration (€1,323) — tag 'Electricity' -> XLU

**Wood** — confidence 0.95
- row 20: Packaging (€1,241) — tag 'Packaging' -> WOOD
- row 20: Packaging (€1,144) — tag 'Packaging' -> WOOD
- row 20: Packaging (€1,129) — tag 'Packaging' -> WOOD

**Gas** — confidence 0.95
- row 25: Gas for heating (€2,645) — tag 'Gas' -> UNG
- row 25: Gas for heating (€2,256) — tag 'Gas' -> UNG
- row 25: Gas for heating (€2,082) — tag 'Gas' -> UNG

## Unmapped (62% of expenses)
- row 29: Employee salary and charges (€5,600)
- row 29: Employee salary and charges (€5,600)
- row 29: Employee salary and charges (€5,600)
- row 29: Employee salary and charges (€5,600)
- row 29: Employee salary and charges (€5,600)

> Risk analysis, not financial advice. v1 maps direct inputs only, no multi-hop supply chain.
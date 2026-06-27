# Spice Cash-Plan Generator

## What It Does

`scripts/generate_cash_plan.py` generates a Spice-style monthly cash-plan workbook
for a business description such as:

- `boulangerie artisanale`
- `transport routier`
- `atelier de plasturgie injection PVC`
- `restaurant`
- `entreprise de construction`
- `atelier metal / electricien`
- any generic SMB description

The workbook follows the structure of the bakery reference model:

1. `Hypotheses`
2. `Revenus`
3. `Depenses detaillees`
4. `Plan de tresorerie`
5. `Market data`
6. `Benchmarks & sources`

It creates realistic revenue streams, expense lines, quantities, unit prices,
seasonality, purchase inflation, VAT, cash timing, and commodity-linked market
price movements.

## Basic Usage

```powershell
python scripts\generate_cash_plan.py "boulangerie artisanale"
```

With explicit revenue and output path:

```powershell
python scripts\generate_cash_plan.py "atelier de plasturgie injection PVC" `
  --annual-revenue 1200000 `
  --start-year 2026 `
  --years 3 `
  --output C:\tmp\plasturgie_cash_plan.xlsx
```

Reference the existing bakery model without modifying it:

```powershell
python scripts\generate_cash_plan.py "boulangerie artisanale" `
  --template C:\Users\saraf\Downloads\Plans_Tresorerie\Boulangerie_Plan_Tresorerie.xlsx `
  --output C:\tmp\boulangerie_cash_plan.xlsx
```

## API Modes

Default mode is offline and deterministic. It uses synthetic monthly commodity
series shaped like market data, so the demo always works.

Online mode:

```powershell
python scripts\generate_cash_plan.py "transport routier" --online
```

Online mode tries:

1. Alpha Vantage, if `--alpha-vantage-key` is provided.
2. World Bank Pink Sheet monthly commodity workbook.
3. Synthetic fallback if the API/network/cache is unavailable.

Example with Alpha Vantage:

```powershell
@"
ALPHA_VANTAGE_API_KEY=your_key_here
"@ | Set-Content .env

python scripts\generate_cash_plan.py "entreprise de construction" `
  --online
```

You can also pass `--alpha-vantage-key`, but prefer `.env` or an environment
variable so the key does not appear in shell history.

## INSEE

INSEE support is intentionally configurable rather than guessed. The exact INSEE
BDM series depends on the sector, region, index, and benchmark question.

You can pass a full INSEE SDMX URL:

```powershell
python scripts\generate_cash_plan.py "restaurant" `
  --online `
  --insee-sdmx-url "https://bdm.insee.fr/series/sdmx/data/..."
```

The response is cached in `.cache/cashplan/`. The current workbook records the
INSEE source but does not yet automatically map INSEE series into sector ratios.

Official sources used by the generator:

- INSEE BDM / SDMX: https://www.insee.fr/fr/information/2862759
- INSEE API catalog: https://www.insee.fr/fr/information/8184146
- World Bank Commodity Markets: https://www.worldbank.org/en/research/commodity-markets
- Alpha Vantage API docs: https://www.alphavantage.co/documentation/

## Current Archetypes

The generator has first-pass archetypes for:

| Archetype | Commodity links |
| --- | --- |
| Bakery | Wheat, fats, gas, electricity, oil-linked packaging |
| Trucking/logistics | Oil, synthetic rubber/oil-linked tires, depot electricity |
| Plastics manufacturing | Oil-linked polymers, electricity, wood packaging |
| Construction | Gas-linked cement, wood, electricity-linked steel, oil, copper |
| Restaurant | Fats, wheat, gas, electricity |
| Metal/electrical workshop | Copper, aluminium/electricity, electricity, oil |
| Generic SMB | Conservative fallback plus keyword-triggered commodity lines |

Industrial SME costs are generated from the dedicated module
`cashplan/industrial_costs.py`. It contains revenue-share drivers for raw
materials, energy, payroll, machine leases, maintenance, logistics and overhead,
then converts those drivers into realistic monthly quantities and unit prices.

## Design Notes

- The workbook is formula-driven so users can edit blue assumption cells.
- Commodity API values are normalized to the model's unit price. This preserves
  real time-series movement without breaking units such as USD/tonne vs EUR/kg.
- The generator is not financial advice. It creates a plausible operating model
  for analysis, demo, and the next Spice exposure agent.

## Next Improvements

1. Add a real LLM profile builder that returns a validated JSON business profile.
2. Add curated INSEE/NAF benchmark mappings for revenue, margin, wage, and input
   ratios by sector.
3. Add tests that compare generated workbooks against the bakery template logic.
4. Feed generated workbooks into the exposure agent from `EXPOSURE_AGENT_PLAN.md`.

# Spice Cash-Plan Generator

## What It Does

`data-generation/scripts/generate_cash_plan.py` generates a Spice-style monthly cash-plan workbook
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
python data-generation\scripts\generate_cash_plan.py "boulangerie artisanale"
```

With explicit revenue and output path:

```powershell
python data-generation\scripts\generate_cash_plan.py "atelier de plasturgie injection PVC" `
  --annual-revenue 1200000 `
  --start-year 2026 `
  --years 3 `
  --output C:\tmp\plasturgie_cash_plan.xlsx
```

Reference the existing bakery model without modifying it:

```powershell
python data-generation\scripts\generate_cash_plan.py "boulangerie artisanale" `
  --template C:\Users\saraf\Downloads\Plans_Tresorerie\Boulangerie_Plan_Tresorerie.xlsx `
  --output C:\tmp\boulangerie_cash_plan.xlsx
```

## API Modes

Default mode is offline and deterministic. It uses synthetic monthly commodity
series shaped like market data, so the demo always works.

Online mode:

```powershell
python data-generation\scripts\generate_cash_plan.py "transport routier" --online
```

Online mode tries:

1. INSEE BDM commodity series from `IPPMP-NF` for mapped raw-material codes.
2. ENTSO-E France day-ahead electricity prices, if `--entsoe-token` is provided.
3. Alpha Vantage, if `--alpha-vantage-key` is provided.
4. World Bank Pink Sheet monthly commodity workbook.
5. Synthetic fallback if the API/network/cache is unavailable.

Example with Alpha Vantage:

```powershell
@"
ALPHA_VANTAGE_API_KEY=your_key_here
ENTSOE_SECURITY_TOKEN=your_token_here
"@ | Set-Content .env

python data-generation\scripts\generate_cash_plan.py "entreprise de construction" `
  --online
```

You can also pass `--alpha-vantage-key`, but prefer `.env` or an environment
variable so the key does not appear in shell history.

## INSEE

INSEE support has two modes. For raw materials, the generator automatically uses
curated INSEE BDM `IPPMP-NF` series when `--online` is enabled. The values are
normalized to the model's unit price, so the workbook keeps its business units
while using the historical INSEE price movement.

Mapped INSEE-backed codes include:

| Model code | INSEE IDBANK | Source idea |
| --- | --- | --- |
| `WHEAT` | `010002046` | Wheat futures, proxy for flour movement |
| `BUTTER` | `010763694` | Butter producer-price index |
| `CREAM` | `010763691` | Cream producer-price index |
| `DAIRY_FATS` | `010763706` | Dairy products for wholesalers/restaurants |
| `EGGS` | `010776696` | Monthly agricultural producer-price index for eggs |
| `YEAST` | `010763751` | Other food products proxy |
| `SALT` | `010766282` | Salt producer-price index |
| `FOOD_PRODUCTS` | `010763739` | Other food products producer-price index |
| `SUGAR` | `010002069` | Sugar contract no. 11 |
| `COCOA` | `010002048` | Cocoa futures |
| `NATURAL_GAS` | `010767333` | TTF natural gas, EUR/MWh |
| `ELECTRICITY` | `010777317` | IPAMPA electricity fallback when no ENTSO-E token is provided |
| `DIESEL` | `010002076` | Diesel/gazole, EUR/tonne |
| `BRENT` | `010002078` | Brent spot, EUR/barrel |
| `COPPER` | `010767327` | Copper LME, EUR/tonne |
| `ALUMINUM` | `010002041` | Aluminium LME, USD/tonne |
| `IRON_ORE` | `010002059` | Iron ore 62% Fe |
| `NICKEL` | `010767326` | Nickel LME, EUR/tonne |
| `ZINC` | `010002072` | Zinc LME |
| `LEAD` | `010002064` | Lead LME |
| `TIN` | `010002035` | Tin LME |
| `WOOD` | `010762320` | Lumber futures |
| `PACKAGING_PAPER` | `010763805` | Corrugated paper/cardboard packaging |
| `RUBBER` | `010763822` | Synthetic rubber |
| `WATER` | `001634676` | Retail water distribution price series |
| `LABOR_*` | `010761999`, `010762002`, `010762004`, `010762008`, `010762009` | Labor-cost indices by sector |
| `RENT_COMMERCIAL` | `001532540` | Commercial rent index |
| `EQUIPMENT_RENTAL` | `010766451` | Machinery/equipment leasing services |
| `RENT_EQUIPMENT_CONSTRUCTION` | `010766449` | Construction equipment rental |
| `MAINTENANCE` | `010777481` | Maintenance and repair proxy |
| `ACCOUNTING_SERVICES` | `010766437` | Accounting/audit/tax advisory services |
| `ADMIN_SERVICES` | `010766756` | Combined administrative services |
| `CONSTRUCTION_COST` | `011800507` | Construction production-cost index |

For sector benchmarks, INSEE remains configurable. The exact INSEE BDM series
depends on the sector, region, index, and benchmark question.

You can pass a full INSEE SDMX URL:

```powershell
python data-generation\scripts\generate_cash_plan.py "restaurant" `
  --online `
  --insee-sdmx-url "https://bdm.insee.fr/series/sdmx/data/..."
```

The response is cached in `.cache/cashplan/`. The current workbook records the
INSEE source but does not yet automatically map INSEE series into sector ratios.

Official sources used by the generator:

- INSEE BDM / SDMX: https://www.insee.fr/fr/information/2862759
- INSEE API catalog: https://www.insee.fr/fr/information/8184146
- ENTSO-E Transparency Platform: https://transparency.entsoe.eu/
- World Bank Commodity Markets: https://www.worldbank.org/en/research/commodity-markets
- Alpha Vantage API docs: https://www.alphavantage.co/documentation/

## Electricity France

When `--online` is enabled and an ENTSO-E token is configured, `ELECTRICITY`
uses French day-ahead spot prices from the ENTSO-E Transparency Platform:

```powershell
python data-generation\scripts\generate_cash_plan.py "restaurant" `
  --online `
  --entsoe-token "your_token_here"
```

The generator requests `documentType=A44` for bidding zone France
`10YFR-RTE------C`, then aggregates hourly prices into monthly averages.
These values are market prices in EUR/MWh before supplier margin, network costs,
taxes, and contract-specific adjustments.

## Current Archetypes

The generator has first-pass archetypes for:

| Archetype | Commodity links |
| --- | --- |
| Bakery | Wheat, fats, gas, electricity, oil-linked packaging |
| Trucking/logistics | Oil, synthetic rubber/oil-linked tires, depot electricity |
| Plastics manufacturing | Oil-linked polymers, electricity, wood packaging |
| Construction | Cement/gas proxy, wood, carbon steel/iron ore proxy, diesel/oil, copper |
| Restaurant | Fats, wheat, gas, electricity |
| Metal/electrical workshop | Carbon steel, galvanized steel, stainless/nickel, aluminium, copper, zinc, tin, electricity, diesel/oil |
| Generic SMB | Conservative fallback plus keyword-triggered commodity lines |

Industrial SME costs are generated from the dedicated module
`data-generation/cashplan/industrial_costs.py`. It contains revenue-share drivers for raw
materials, energy, payroll, machine leases, maintenance, logistics and overhead,
then converts those drivers into realistic monthly quantities and unit prices.

The industrial presets now use a precise material taxonomy from
`data-generation/cashplan/materials.py`. Instead of one generic "metal" bucket, the model can
separate:

- carbon steel and galvanized steel, proxied by iron ore in v1;
- stainless steel, proxied by nickel exposure;
- aluminium;
- copper;
- zinc;
- tin;
- lead where relevant;
- polymer resin and polyurethane;
- wood/panels/packaging;
- electricity, gas and diesel.

World Bank Pink Sheet is the preferred no-key source for detailed base metals
such as aluminium, copper, lead, nickel, tin, zinc and iron ore. Alpha Vantage is
kept for supported direct commodity endpoints such as copper and aluminium.

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

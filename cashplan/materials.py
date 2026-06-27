from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Material:
    key: str
    label: str
    family: str
    underlying: str
    market_code: str | None
    default_unit: str
    default_unit_price: float
    volatility: float
    source: str
    note: str


MATERIALS: dict[str, Material] = {
    "carbon_steel": Material(
        key="carbon_steel",
        label="Carbon steel sheet and profiles",
        family="ferrous_metals",
        underlying="Steel",
        market_code="IRON_ORE",
        default_unit="kg",
        default_unit_price=0.95,
        volatility=0.07,
        source="World Bank Pink Sheet iron ore proxy",
        note="Steel is proxied by iron ore in v1; finished steel prices also include scrap, energy and conversion margin.",
    ),
    "galvanized_steel": Material(
        key="galvanized_steel",
        label="Galvanized steel sheet",
        family="ferrous_metals",
        underlying="Steel",
        market_code="IRON_ORE",
        default_unit="kg",
        default_unit_price=1.10,
        volatility=0.07,
        source="World Bank Pink Sheet iron ore proxy",
        note="Main exposure is steel substrate; zinc coating is modeled separately when material intensity matters.",
    ),
    "stainless_steel": Material(
        key="stainless_steel",
        label="Stainless steel",
        family="ferrous_metals",
        underlying="Nickel",
        market_code="NICKEL",
        default_unit="kg",
        default_unit_price=3.20,
        volatility=0.11,
        source="World Bank Pink Sheet nickel proxy",
        note="Stainless is represented by nickel as the volatile alloying component; chromium is out of scope for v1.",
    ),
    "aluminium": Material(
        key="aluminium",
        label="Aluminium profiles and sheets",
        family="base_metals",
        underlying="Aluminium",
        market_code="ALUMINUM",
        default_unit="kg",
        default_unit_price=2.60,
        volatility=0.06,
        source="World Bank Pink Sheet / Alpha Vantage aluminum",
        note="Aluminium is treated as a direct base-metal exposure and also an electricity-heavy input.",
    ),
    "copper": Material(
        key="copper",
        label="Copper wire, bars and busbars",
        family="base_metals",
        underlying="Copper",
        market_code="COPPER",
        default_unit="kg",
        default_unit_price=8.20,
        volatility=0.08,
        source="World Bank Pink Sheet / Alpha Vantage copper",
        note="Direct copper exposure for wiring, electrical assemblies and plumbing components.",
    ),
    "zinc": Material(
        key="zinc",
        label="Zinc coating, zinc die-cast parts and galvanization",
        family="base_metals",
        underlying="Zinc",
        market_code="ZINC",
        default_unit="kg",
        default_unit_price=2.80,
        volatility=0.08,
        source="World Bank Pink Sheet zinc",
        note="Used for galvanization, zinc die-cast hardware and anti-corrosion components.",
    ),
    "nickel": Material(
        key="nickel",
        label="Nickel alloying input",
        family="base_metals",
        underlying="Nickel",
        market_code="NICKEL",
        default_unit="kg",
        default_unit_price=18.00,
        volatility=0.11,
        source="World Bank Pink Sheet nickel",
        note="Used for stainless steel and specialty alloys; very volatile relative to steel substrate.",
    ),
    "tin": Material(
        key="tin",
        label="Tin solder and tinplate exposure",
        family="base_metals",
        underlying="Tin",
        market_code="TIN",
        default_unit="kg",
        default_unit_price=28.00,
        volatility=0.10,
        source="World Bank Pink Sheet tin",
        note="Relevant for solder, tinplate packaging and electronics-adjacent manufacturing.",
    ),
    "lead": Material(
        key="lead",
        label="Lead components and shielding",
        family="base_metals",
        underlying="Lead",
        market_code="LEAD",
        default_unit="kg",
        default_unit_price=2.20,
        volatility=0.07,
        source="World Bank Pink Sheet lead",
        note="Relevant for batteries, shielding and some legacy industrial components.",
    ),
    "polymer_resin": Material(
        key="polymer_resin",
        label="PVC / polymer resin",
        family="petrochemicals",
        underlying="Oil",
        market_code="WTI",
        default_unit="kg",
        default_unit_price=1.55,
        volatility=0.09,
        source="Oil-linked polymer resin proxy",
        note="Polymer resin is treated as oil-linked in v1; exact resin grade is not modeled yet.",
    ),
    "polyurethane": Material(
        key="polyurethane",
        label="Polyurethane additives",
        family="petrochemicals",
        underlying="Oil",
        market_code=None,
        default_unit="kg",
        default_unit_price=2.80,
        volatility=0.06,
        source="Oil-linked chemical input estimate",
        note="Chemical input with oil/gas feedstock exposure; no direct commodity series in v1.",
    ),
    "wood_panels": Material(
        key="wood_panels",
        label="Timber, boards and panels",
        family="wood",
        underlying="Wood",
        market_code="WOOD",
        default_unit="m3",
        default_unit_price=420.00,
        volatility=0.05,
        source="World Bank wood/logs proxy",
        note="Used for furniture, carpentry, pallets and packaging.",
    ),
    "cardboard_packaging": Material(
        key="cardboard_packaging",
        label="Cardboard packaging and pallets",
        family="packaging",
        underlying="Wood",
        market_code="WOOD",
        default_unit="unit",
        default_unit_price=7.50,
        volatility=0.04,
        source="Wood/pulp packaging proxy",
        note="Packaging is represented by wood/pulp exposure unless plastic packaging is explicit.",
    ),
    "industrial_electricity": Material(
        key="industrial_electricity",
        label="Industrial electricity",
        family="energy",
        underlying="Electricity",
        market_code="ELECTRICITY",
        default_unit="kWh",
        default_unit_price=0.16,
        volatility=0.05,
        source="Industrial electricity tariff proxy",
        note="Electricity-heavy inputs include aluminium, glass, CNC, injection molding and machine tools.",
    ),
    "process_gas": Material(
        key="process_gas",
        label="Process gas or heating gas",
        family="energy",
        underlying="Gas",
        market_code="NATURAL_GAS",
        default_unit="kWh",
        default_unit_price=0.10,
        volatility=0.08,
        source="Natural gas market proxy",
        note="Gas exposure for heating, curing, drying, cement/mineral processes and chemistry.",
    ),
    "diesel": Material(
        key="diesel",
        label="Diesel and logistics fuel",
        family="energy",
        underlying="Oil",
        market_code="WTI",
        default_unit="L",
        default_unit_price=1.62,
        volatility=0.08,
        source="Oil-linked fuel proxy",
        note="Fuel/logistics exposure maps to oil in v1.",
    ),
}


def material(key: str) -> Material:
    return MATERIALS[key]


def material_source_notes() -> list[tuple[str, str, str, str]]:
    return [
        (
            "Industrial metals coverage",
            "Aluminium, copper, iron ore, lead, nickel, tin, zinc",
            "https://www.worldbank.org/en/research/commodity-markets",
            "World Bank Pink Sheet is the primary no-key monthly source for detailed base metals.",
        ),
        (
            "Base metal index components",
            "Aluminium, copper, lead, nickel, tin, zinc",
            "World Bank Commodity Markets Chapter 4",
            "World Bank documentation describes the base metal index as covering these metals.",
        ),
    ]


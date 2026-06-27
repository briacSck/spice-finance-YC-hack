from __future__ import annotations

from dataclasses import dataclass
import random
import re


@dataclass(frozen=True)
class IndustrialCostItem:
    category: str
    name: str
    monthly_quantity: float
    unit: str
    unit_price: float
    source: str
    underlying: str | None = None
    market_code: str | None = None
    volatility: float = 0.03
    seasonality_linked: bool = True


@dataclass(frozen=True)
class IndustrialCostDriver:
    category: str
    name: str
    annual_revenue_share: float
    unit: str
    unit_price: float
    source: str
    underlying: str | None = None
    market_code: str | None = None
    volatility: float = 0.03
    seasonality_linked: bool = True
    min_monthly_quantity: float = 1.0


@dataclass(frozen=True)
class IndustrialCostPreset:
    key: str
    label: str
    description: str
    drivers: tuple[IndustrialCostDriver, ...]


INDUSTRIAL_PRESETS: dict[str, IndustrialCostPreset] = {
    "plastics_injection": IndustrialCostPreset(
        key="plastics_injection",
        label="Plastics injection / polymer workshop",
        description="Industrial SME turning oil-linked polymers into plastic parts.",
        drivers=(
            IndustrialCostDriver("Raw materials", "PVC / polymer resin", 0.279, "kg", 1.55, "Oil-linked polymer benchmark", "Oil", "WTI", 0.09),
            IndustrialCostDriver("Raw materials", "Polyurethane additives", 0.067, "kg", 2.80, "Chemical input benchmark", "Oil", None, 0.06),
            IndustrialCostDriver("Energy", "Electricity for injection molding", 0.067, "kWh", 0.16, "Industrial electricity tariff proxy", "Electricity", None, 0.05),
            IndustrialCostDriver("Raw materials", "Cardboard and wood pallets", 0.068, "unit", 7.50, "Packaging and pallet benchmark", "Wood", None, 0.04),
            IndustrialCostDriver("Personnel", "Production payroll and charges", 0.335, "monthly package", 1.0, "Industrial SMB payroll ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Workshop rent", 0.082, "monthly package", 1.0, "Industrial lease ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Machine leases and maintenance", 0.098, "monthly package", 1.0, "Equipment lease and maintenance ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Insurance, quality, admin", 0.052, "monthly package", 1.0, "Industrial overhead ratio", None, None, 0.00, False),
        ),
    ),
    "metalwork": IndustrialCostPreset(
        key="metalwork",
        label="Metalworking / electrical components workshop",
        description="Industrial SME using copper, aluminium, electricity and workshop labor.",
        drivers=(
            IndustrialCostDriver("Raw materials", "Copper wiring and bars", 0.234, "kg", 8.20, "Copper market proxy", "Copper", "COPPER", 0.08),
            IndustrialCostDriver("Raw materials", "Aluminium profiles", 0.088, "kg", 2.60, "Aluminium market proxy", "Electricity", "ALUMINUM", 0.06),
            IndustrialCostDriver("Energy", "Electricity for machines", 0.046, "kWh", 0.16, "Industrial electricity tariff proxy", "Electricity", None, 0.05),
            IndustrialCostDriver("Fuel and mobility", "Transport and delivery fuel", 0.030, "L", 1.62, "Oil-linked fuel proxy", "Oil", "WTI", 0.08),
            IndustrialCostDriver("Personnel", "Workshop payroll and charges", 0.335, "monthly package", 1.0, "Industrial SMB payroll ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Workshop rent", 0.080, "monthly package", 1.0, "Industrial lease ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Machine maintenance and consumables", 0.065, "monthly package", 1.0, "Maintenance benchmark", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Insurance, admin, accounting", 0.046, "monthly package", 1.0, "Industrial overhead ratio", None, None, 0.00, False),
        ),
    ),
    "woodworking": IndustrialCostPreset(
        key="woodworking",
        label="Woodworking / furniture workshop",
        description="Industrial SME making wood products, furniture, packaging or carpentry.",
        drivers=(
            IndustrialCostDriver("Raw materials", "Timber and panels", 0.260, "m3", 420.0, "Wood and panel benchmark", "Wood", None, 0.05),
            IndustrialCostDriver("Raw materials", "Glue, varnish and oil-linked chemicals", 0.040, "kg", 5.40, "Chemical input benchmark", "Oil", None, 0.05),
            IndustrialCostDriver("Raw materials", "Hardware, hinges and metal fittings", 0.055, "unit basket", 100.0, "Hardware benchmark", "Copper", "COPPER", 0.05),
            IndustrialCostDriver("Energy", "Electricity for CNC, saws and dust extraction", 0.045, "kWh", 0.16, "Industrial electricity tariff proxy", "Electricity", None, 0.05),
            IndustrialCostDriver("Fuel and mobility", "Delivery fuel", 0.025, "L", 1.62, "Oil-linked fuel proxy", "Oil", "WTI", 0.08),
            IndustrialCostDriver("Personnel", "Workshop payroll and charges", 0.310, "monthly package", 1.0, "Industrial SMB payroll ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Workshop rent", 0.075, "monthly package", 1.0, "Industrial lease ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Machine maintenance, blades and tooling", 0.050, "monthly package", 1.0, "Maintenance benchmark", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Insurance, admin, accounting", 0.045, "monthly package", 1.0, "Industrial overhead ratio", None, None, 0.00, False),
        ),
    ),
    "light_manufacturing": IndustrialCostPreset(
        key="light_manufacturing",
        label="Light manufacturing",
        description="Generic industrial SME with purchased goods, machine power, labor and overhead.",
        drivers=(
            IndustrialCostDriver("Raw materials", "Purchased components and inputs", 0.240, "unit basket", 100.0, "Generic manufacturing input ratio", None, None, 0.04),
            IndustrialCostDriver("Raw materials", "Packaging and pallets", 0.045, "unit", 7.50, "Packaging benchmark", "Wood", None, 0.04),
            IndustrialCostDriver("Energy", "Industrial electricity", 0.060, "kWh", 0.16, "Industrial electricity tariff proxy", "Electricity", None, 0.05),
            IndustrialCostDriver("Energy", "Process gas or heating", 0.020, "kWh", 0.10, "Gas tariff proxy", "Gas", "NATURAL_GAS", 0.08),
            IndustrialCostDriver("Fuel and mobility", "Logistics and delivery fuel", 0.035, "L", 1.62, "Oil-linked logistics proxy", "Oil", "WTI", 0.08),
            IndustrialCostDriver("Personnel", "Production payroll and charges", 0.300, "monthly package", 1.0, "Industrial SMB payroll ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Workshop rent and facilities", 0.075, "monthly package", 1.0, "Industrial lease ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Machine leases, maintenance and tooling", 0.085, "monthly package", 1.0, "Equipment cost ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Insurance, quality, software, admin", 0.050, "monthly package", 1.0, "Industrial overhead ratio", None, None, 0.00, False),
        ),
    ),
}


def infer_industrial_preset_key(business_description: str) -> str | None:
    text = _normalize(business_description)
    if re.search(r"plast|polymer|pvc|injection|polyurethane", text):
        return "plastics_injection"
    if re.search(r"metal|usinage|fonderie|foundry|aluminium|aluminum|copper|cuivre|electricien|electrical|cable", text):
        return "metalwork"
    if re.search(r"wood|bois|menuis|furniture|mobilier|palette|timber", text):
        return "woodworking"
    if re.search(r"factory|atelier|manufact|industrial|industrie|machine|production|usine", text):
        return "light_manufacturing"
    return None


def build_industrial_cost_items(
    annual_revenue: float,
    preset_key: str = "light_manufacturing",
    seed: int = 42,
    jitter: float = 0.04,
) -> list[IndustrialCostItem]:
    preset = INDUSTRIAL_PRESETS[preset_key]
    rng = random.Random(f"industrial:{preset_key}:{seed}:{annual_revenue}")
    items: list[IndustrialCostItem] = []

    for driver in preset.drivers:
        monthly_budget = annual_revenue * driver.annual_revenue_share / 12
        if driver.unit == "monthly package":
            unit_price = round(monthly_budget, 2)
            quantity = 1.0
        else:
            unit_price = driver.unit_price
            quantity = max(driver.min_monthly_quantity, monthly_budget / max(unit_price, 0.01))

        quantity *= rng.uniform(1 - jitter, 1 + jitter)
        items.append(
            IndustrialCostItem(
                category=driver.category,
                name=driver.name,
                monthly_quantity=round(quantity, 4),
                unit=driver.unit,
                unit_price=round(unit_price, 4),
                source=driver.source,
                underlying=driver.underlying,
                market_code=driver.market_code,
                volatility=driver.volatility,
                seasonality_linked=driver.seasonality_linked,
            )
        )

    return items


def industrial_benchmark_notes(preset_key: str) -> list[tuple[str, str, str, str]]:
    preset = INDUSTRIAL_PRESETS[preset_key]
    return [
        (
            "Industrial cost preset",
            preset.label,
            "cashplan/industrial_costs.py",
            preset.description,
        ),
        (
            "Industrial ratio method",
            "Revenue-share driver model",
            "local generator",
            "Each cost line starts from an annual revenue share, unit price and realistic monthly quantity.",
        ),
    ]


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


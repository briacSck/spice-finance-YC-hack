from __future__ import annotations

from dataclasses import dataclass
import random
import re

from cashplan.materials import material, material_source_notes


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
    material_key: str | None = None


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
    material_key: str | None = None


@dataclass(frozen=True)
class IndustrialCostPreset:
    key: str
    label: str
    description: str
    drivers: tuple[IndustrialCostDriver, ...]


def material_driver(
    category: str,
    material_key: str,
    annual_revenue_share: float,
    name: str | None = None,
    unit: str | None = None,
    unit_price: float | None = None,
    source: str | None = None,
    seasonality_linked: bool = True,
) -> IndustrialCostDriver:
    mat = material(material_key)
    return IndustrialCostDriver(
        category=category,
        name=name or mat.label,
        annual_revenue_share=annual_revenue_share,
        unit=unit or mat.default_unit,
        unit_price=unit_price if unit_price is not None else mat.default_unit_price,
        source=source or mat.source,
        underlying=mat.underlying,
        market_code=mat.market_code,
        volatility=mat.volatility,
        seasonality_linked=seasonality_linked,
        material_key=material_key,
    )


INDUSTRIAL_PRESETS: dict[str, IndustrialCostPreset] = {
    "plastics_injection": IndustrialCostPreset(
        key="plastics_injection",
        label="Plastics injection / polymer workshop",
        description="Industrial SME turning oil-linked polymers into plastic parts.",
        drivers=(
            material_driver("Raw materials", "polymer_resin", 0.245, "PVC / polymer resin granulate"),
            material_driver("Raw materials", "polyurethane", 0.055, "Polyurethane additives and oil-linked chemicals"),
            material_driver("Raw materials", "carbon_steel", 0.028, "Steel mold inserts and tooling wear parts"),
            material_driver("Raw materials", "aluminium", 0.018, "Aluminium fixtures and light tooling"),
            material_driver("Energy", "industrial_electricity", 0.067, "Electricity for injection molding"),
            material_driver("Raw materials", "cardboard_packaging", 0.060, "Cardboard packaging and wood pallets"),
            IndustrialCostDriver("Personnel", "Production payroll and charges", 0.335, "monthly package", 1.0, "Industrial SMB payroll ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Workshop rent", 0.082, "monthly package", 1.0, "Industrial lease ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Machine leases and maintenance", 0.098, "monthly package", 1.0, "Equipment lease and maintenance ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Insurance, quality, admin", 0.052, "monthly package", 1.0, "Industrial overhead ratio", None, None, 0.00, False),
        ),
    ),
    "metalwork": IndustrialCostPreset(
        key="metalwork",
        label="Metalworking / electrical components workshop",
        description="Industrial SME using steel, stainless/nickel, zinc, copper, aluminium and workshop labor.",
        drivers=(
            material_driver("Raw materials", "carbon_steel", 0.115, "Carbon steel sheet, tubes and profiles"),
            material_driver("Raw materials", "galvanized_steel", 0.045, "Galvanized steel sheet"),
            material_driver("Raw materials", "stainless_steel", 0.055, "Stainless steel parts and sheet"),
            material_driver("Raw materials", "aluminium", 0.055, "Aluminium profiles and plates"),
            material_driver("Raw materials", "copper", 0.080, "Copper wiring, bars and busbars"),
            material_driver("Raw materials", "zinc", 0.020, "Zinc coating, plated fasteners and die-cast hardware"),
            material_driver("Raw materials", "tin", 0.010, "Tin solder and tinplate consumables"),
            material_driver("Energy", "industrial_electricity", 0.046, "Electricity for CNC and machine tools"),
            material_driver("Fuel and mobility", "diesel", 0.030, "Transport and delivery fuel"),
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
            material_driver("Raw materials", "wood_panels", 0.240, "Timber, boards and panels"),
            material_driver("Raw materials", "polyurethane", 0.035, "Glue, varnish and oil-linked finishing chemicals", unit_price=5.40),
            material_driver("Raw materials", "carbon_steel", 0.020, "Steel screws, brackets and structural hardware"),
            material_driver("Raw materials", "zinc", 0.012, "Zinc-plated hinges, fasteners and handles"),
            material_driver("Raw materials", "aluminium", 0.012, "Aluminium rails and light fittings"),
            material_driver("Energy", "industrial_electricity", 0.045, "Electricity for CNC, saws and dust extraction"),
            material_driver("Fuel and mobility", "diesel", 0.025, "Delivery fuel"),
            IndustrialCostDriver("Personnel", "Workshop payroll and charges", 0.310, "monthly package", 1.0, "Industrial SMB payroll ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Workshop rent", 0.075, "monthly package", 1.0, "Industrial lease ratio", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Machine maintenance, blades and tooling", 0.050, "monthly package", 1.0, "Maintenance benchmark", None, None, 0.00, False),
            IndustrialCostDriver("Fixed costs", "Insurance, admin, accounting", 0.045, "monthly package", 1.0, "Industrial overhead ratio", None, None, 0.00, False),
        ),
    ),
    "light_manufacturing": IndustrialCostPreset(
        key="light_manufacturing",
        label="Light manufacturing",
        description="Generic industrial SME with precise metal, polymer, energy and logistics exposures.",
        drivers=(
            material_driver("Raw materials", "carbon_steel", 0.070, "Carbon steel bought-in parts"),
            material_driver("Raw materials", "galvanized_steel", 0.025, "Galvanized sheet and zinc-coated components"),
            material_driver("Raw materials", "aluminium", 0.035, "Aluminium parts and profiles"),
            material_driver("Raw materials", "copper", 0.030, "Copper wiring and connectors"),
            material_driver("Raw materials", "zinc", 0.014, "Zinc-plated hardware"),
            material_driver("Raw materials", "tin", 0.006, "Tin solder or tinplate inputs"),
            material_driver("Raw materials", "polymer_resin", 0.040, "Plastic housings and polymer components"),
            material_driver("Raw materials", "cardboard_packaging", 0.035, "Packaging and pallets"),
            material_driver("Energy", "industrial_electricity", 0.060, "Industrial electricity"),
            material_driver("Energy", "process_gas", 0.020, "Process gas or heating"),
            material_driver("Fuel and mobility", "diesel", 0.035, "Logistics and delivery fuel"),
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
    if re.search(r"metal|usinage|fonderie|foundry|aluminium|aluminum|copper|cuivre|electricien|electrical|cable|hardware|zinc|acier|steel|inox|stainless|galvani|chaudronnerie", text):
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
                material_key=driver.material_key,
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
    ] + material_source_notes()


def _normalize(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()

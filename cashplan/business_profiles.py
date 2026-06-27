from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
import random
import re
import unicodedata

from cashplan.industrial_costs import (
    build_industrial_cost_items,
    industrial_benchmark_notes,
    infer_industrial_preset_key,
)


@dataclass(frozen=True)
class RevenueStream:
    name: str
    share: float


@dataclass(frozen=True)
class CostLine:
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
class BusinessProfile:
    business_type: str
    archetype: str
    description: str
    annual_revenue: float
    vat_sales: float
    vat_purchases: float
    opening_cash: float
    owner_social_quarterly: float
    loan_monthly: float
    annual_revenue_growth: float
    purchase_inflation: float
    seasonality: list[float]
    revenue_streams: list[RevenueStream]
    cost_lines: list[CostLine]
    benchmark_notes: list[tuple[str, str, str, str]] = field(default_factory=list)


MONTHLY_SEASONALITY_DEFAULT = [
    1.02,
    0.96,
    0.98,
    1.00,
    1.02,
    1.03,
    1.04,
    0.88,
    1.03,
    1.05,
    1.02,
    1.07,
]


UNDERLYING_LABELS = {
    "oil": "Oil",
    "electricity": "Electricity",
    "gas": "Gas",
    "wheat": "Wheat",
    "fats": "Fats",
    "copper": "Copper",
    "wood": "Wood",
}


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"\s+", " ", ascii_text.lower()).strip()


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", normalize_text(value)).strip("-")
    return slug or "business"


def _industrial_cost_lines(
    annual_revenue: float,
    preset_key: str,
    seed: int = 42,
) -> list[CostLine]:
    return [
        CostLine(
            category=item.category,
            name=item.name,
            monthly_quantity=item.monthly_quantity,
            unit=item.unit,
            unit_price=item.unit_price,
            source=item.source,
            underlying=item.underlying,
            market_code=item.market_code,
            volatility=item.volatility,
            seasonality_linked=item.seasonality_linked,
        )
        for item in build_industrial_cost_items(annual_revenue, preset_key, seed)
    ]


def infer_business_profile(
    business_type: str,
    annual_revenue: float | None = None,
    seed: int = 42,
) -> BusinessProfile:
    text = normalize_text(business_type)
    rng = random.Random(seed)

    if any(word in text for word in ["boulanger", "bakery", "patisserie", "bread"]):
        return _scale_profile(_bakery_profile(), annual_revenue)
    if any(word in text for word in ["transport", "trucking", "logistique", "livraison"]):
        return _scale_profile(_trucking_profile(), annual_revenue)
    if any(word in text for word in ["plast", "polymer", "pvc", "injection"]):
        return _scale_profile(_plastics_profile(), annual_revenue)
    if any(word in text for word in ["construction", "btp", "builder", "macon"]):
        return _scale_profile(_construction_profile(), annual_revenue)
    if any(word in text for word in ["restaurant", "traiteur", "cafe", "brasserie"]):
        return _scale_profile(_restaurant_profile(), annual_revenue)
    if any(word in text for word in ["metal", "usinage", "foundry", "fonderie", "electricien"]):
        return _scale_profile(_metalwork_profile(), annual_revenue)
    industrial_preset_key = infer_industrial_preset_key(text)
    if industrial_preset_key:
        return _industrial_generic_profile(
            business_type,
            annual_revenue or 650_000,
            industrial_preset_key,
            seed,
        )

    return _generic_profile(business_type, annual_revenue or 420_000, rng)


def _scale_profile(profile: BusinessProfile, annual_revenue: float | None) -> BusinessProfile:
    if not annual_revenue:
        return profile

    scale = annual_revenue / profile.annual_revenue
    # Quantities scale sublinearly so the model does not imply perfect linear
    # operating leverage for every input.
    quantity_scale = math.pow(scale, 0.92)
    cash_scale = math.pow(scale, 0.75)
    cost_lines = [
        replace(line, monthly_quantity=round(line.monthly_quantity * quantity_scale, 4))
        for line in profile.cost_lines
    ]
    return replace(
        profile,
        annual_revenue=float(annual_revenue),
        opening_cash=round(profile.opening_cash * cash_scale, 2),
        owner_social_quarterly=round(profile.owner_social_quarterly * cash_scale, 2),
        loan_monthly=round(profile.loan_monthly * cash_scale, 2),
        cost_lines=cost_lines,
    )


def _bakery_profile() -> BusinessProfile:
    return BusinessProfile(
        business_type="boulangerie artisanale",
        archetype="bakery",
        description="Artisanal bakery and pastry shop.",
        annual_revenue=310_000,
        vat_sales=0.055,
        vat_purchases=0.11,
        opening_cash=12_000,
        owner_social_quarterly=3_200,
        loan_monthly=480,
        annual_revenue_growth=0.025,
        purchase_inflation=0.03,
        seasonality=[1.08, 0.97, 0.98, 1.03, 1.00, 0.97, 0.95, 0.75, 1.02, 1.05, 1.02, 1.18],
        revenue_streams=[
            RevenueStream("Bread", 0.45),
            RevenueStream("Viennoiserie", 0.20),
            RevenueStream("Pastry", 0.15),
            RevenueStream("Snacking and catering", 0.15),
            RevenueStream("Drinks and other", 0.05),
        ],
        cost_lines=[
            CostLine("Raw materials", "Wheat flour T55/T65", 5000, "kg", 0.56, "Market proxy: WHEAT", "Wheat", "WHEAT", 0.08),
            CostLine("Raw materials", "Tourage butter", 280, "kg", 6.20, "Wholesale BVP estimate", "Fats", None, 0.04),
            CostLine("Raw materials", "Incorporation butter", 110, "kg", 5.10, "Wholesale BVP estimate", "Fats", None, 0.04),
            CostLine("Raw materials", "Baker's yeast", 65, "kg", 3.60, "Supplier estimate", None, None, 0.02),
            CostLine("Raw materials", "Salt", 55, "kg", 0.65, "Supplier estimate", None, None, 0.01),
            CostLine("Raw materials", "Eggs", 2200, "unit", 0.25, "Food wholesaler estimate", None, None, 0.03),
            CostLine("Raw materials", "Cream", 160, "L", 3.60, "Food wholesaler estimate", "Fats", None, 0.04),
            CostLine("Raw materials", "Packaging", 13000, "unit", 0.06, "Packaging supplier estimate", "Oil", None, 0.03),
            CostLine("Energy", "Electricity for ovens and refrigeration", 5800, "kWh", 0.17, "Electricity market/pro tariff proxy", "Electricity", None, 0.05),
            CostLine("Energy", "Gas for heating", 2600, "kWh", 0.10, "Natural gas market proxy", "Gas", "NATURAL_GAS", 0.08),
            CostLine("Personnel", "Owner net compensation", 1, "monthly package", 3400, "Artisan benchmark", None, None, 0.00, False),
            CostLine("Personnel", "Employee salary and charges", 1, "monthly package", 3000, "Bakery collective agreement estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Commercial rent", 1, "monthly package", 3200, "Local lease estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Insurance", 1, "monthly package", 250, "Professional insurance estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Maintenance", 1, "monthly package", 350, "Equipment maintenance estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Accountant", 1, "monthly package", 500, "Accounting firm estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Water", 1, "monthly package", 150, "Utility estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Bank fees and payment terminal", 1, "monthly package", 150, "Bank tariff estimate", None, None, 0.00, False),
        ],
        benchmark_notes=_default_source_notes(),
    )


def _trucking_profile() -> BusinessProfile:
    return BusinessProfile(
        business_type="transport routier",
        archetype="trucking",
        description="Small trucking and logistics company.",
        annual_revenue=850_000,
        vat_sales=0.20,
        vat_purchases=0.20,
        opening_cash=45_000,
        owner_social_quarterly=5_800,
        loan_monthly=5_200,
        annual_revenue_growth=0.035,
        purchase_inflation=0.035,
        seasonality=[0.94, 0.96, 1.02, 1.03, 1.05, 1.02, 0.96, 0.82, 1.08, 1.12, 1.08, 0.92],
        revenue_streams=[
            RevenueStream("Regional transport contracts", 0.62),
            RevenueStream("Spot deliveries", 0.25),
            RevenueStream("Warehousing and handling", 0.13),
        ],
        cost_lines=[
            CostLine("Fuel and mobility", "Diesel fuel", 10500, "L", 1.62, "Fuel market proxy: oil", "Oil", "WTI", 0.08),
            CostLine("Fuel and mobility", "Tires and rubber consumables", 12, "unit", 420, "Synthetic rubber proxy", "Oil", None, 0.04),
            CostLine("Maintenance", "Truck maintenance and parts", 1, "monthly package", 6200, "Fleet maintenance estimate", "Oil", None, 0.03, False),
            CostLine("Personnel", "Drivers payroll and charges", 1, "monthly package", 25500, "Transport payroll benchmark", None, None, 0.00, False),
            CostLine("Fixed costs", "Vehicle leases", 1, "monthly package", 10200, "Truck lease estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Insurance and permits", 1, "monthly package", 3600, "Fleet insurance estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Depot rent and utilities", 1, "monthly package", 4200, "Depot operating estimate", "Electricity", None, 0.02, False),
            CostLine("Fixed costs", "Admin, software, bank fees", 1, "monthly package", 2500, "SMB overhead estimate", None, None, 0.00, False),
        ],
        benchmark_notes=_default_source_notes(),
    )


def _plastics_profile() -> BusinessProfile:
    annual_revenue = 1_200_000
    preset_key = "plastics_injection"
    return BusinessProfile(
        business_type="plasturgie",
        archetype="plastics",
        description="Small plastic parts manufacturer.",
        annual_revenue=annual_revenue,
        vat_sales=0.20,
        vat_purchases=0.20,
        opening_cash=70_000,
        owner_social_quarterly=6_500,
        loan_monthly=7_800,
        annual_revenue_growth=0.04,
        purchase_inflation=0.035,
        seasonality=MONTHLY_SEASONALITY_DEFAULT,
        revenue_streams=[
            RevenueStream("Contract manufacturing", 0.72),
            RevenueStream("Prototype runs", 0.16),
            RevenueStream("Tooling and engineering services", 0.12),
        ],
        cost_lines=_industrial_cost_lines(annual_revenue, preset_key),
        benchmark_notes=_default_source_notes() + industrial_benchmark_notes(preset_key),
    )


def _construction_profile() -> BusinessProfile:
    return BusinessProfile(
        business_type="construction",
        archetype="construction",
        description="Small construction and renovation contractor.",
        annual_revenue=950_000,
        vat_sales=0.10,
        vat_purchases=0.20,
        opening_cash=50_000,
        owner_social_quarterly=6_000,
        loan_monthly=3_200,
        annual_revenue_growth=0.03,
        purchase_inflation=0.04,
        seasonality=[0.82, 0.88, 1.02, 1.08, 1.12, 1.10, 0.96, 0.72, 1.12, 1.12, 1.04, 0.92],
        revenue_streams=[
            RevenueStream("Renovation projects", 0.55),
            RevenueStream("Small structural works", 0.30),
            RevenueStream("Maintenance contracts", 0.15),
        ],
        cost_lines=[
            CostLine("Raw materials", "Cement and concrete inputs", 95, "t", 115, "Cement benchmark estimate", "Gas", None, 0.05),
            CostLine("Raw materials", "Timber and panels", 38, "m3", 420, "Wood benchmark estimate", "Wood", None, 0.05),
            CostLine("Raw materials", "Steel and metalwork", 18, "t", 880, "Steel electricity-linked estimate", "Electricity", None, 0.06),
            CostLine("Fuel and mobility", "Diesel for machinery and vehicles", 4200, "L", 1.62, "Fuel market proxy: oil", "Oil", "WTI", 0.08),
            CostLine("Raw materials", "Copper electrical wiring", 480, "kg", 8.10, "Copper market proxy", "Copper", "COPPER", 0.08),
            CostLine("Personnel", "Site payroll and charges", 1, "monthly package", 27500, "Construction payroll estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Tools, equipment rental, depot", 1, "monthly package", 12500, "Contractor overhead estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Insurance, admin, accounting", 1, "monthly package", 5200, "SMB overhead estimate", None, None, 0.00, False),
        ],
        benchmark_notes=_default_source_notes(),
    )


def _restaurant_profile() -> BusinessProfile:
    return BusinessProfile(
        business_type="restaurant",
        archetype="restaurant",
        description="Independent restaurant.",
        annual_revenue=520_000,
        vat_sales=0.10,
        vat_purchases=0.12,
        opening_cash=24_000,
        owner_social_quarterly=4_400,
        loan_monthly=1_200,
        annual_revenue_growth=0.025,
        purchase_inflation=0.035,
        seasonality=[0.90, 0.92, 0.98, 1.02, 1.05, 1.08, 1.12, 0.82, 1.00, 1.04, 1.06, 1.01],
        revenue_streams=[
            RevenueStream("Lunch service", 0.38),
            RevenueStream("Dinner service", 0.44),
            RevenueStream("Drinks", 0.12),
            RevenueStream("Takeaway and catering", 0.06),
        ],
        cost_lines=[
            CostLine("Raw materials", "Food purchases", 1, "monthly package", 12700, "Restaurant COGS estimate", None, None, 0.04),
            CostLine("Raw materials", "Butter, cream and dairy fats", 320, "kg/L", 4.20, "Food wholesaler estimate", "Fats", None, 0.04),
            CostLine("Raw materials", "Bread and flour-based inputs", 1, "monthly package", 2500, "Bakery supplier estimate", "Wheat", "WHEAT", 0.06),
            CostLine("Energy", "Cooking gas", 5200, "kWh", 0.105, "Natural gas proxy", "Gas", "NATURAL_GAS", 0.08),
            CostLine("Energy", "Electricity for kitchen and refrigeration", 7600, "kWh", 0.17, "Electricity tariff proxy", "Electricity", None, 0.05),
            CostLine("Personnel", "Kitchen and service payroll", 1, "monthly package", 14500, "Restaurant payroll estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Rent", 1, "monthly package", 5200, "Commercial lease estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Insurance, accounting, software", 1, "monthly package", 2400, "SMB overhead estimate", None, None, 0.00, False),
        ],
        benchmark_notes=_default_source_notes(),
    )


def _metalwork_profile() -> BusinessProfile:
    annual_revenue = 780_000
    preset_key = "metalwork"
    return BusinessProfile(
        business_type="metal workshop",
        archetype="metalwork",
        description="Small metalworking and electrical components shop.",
        annual_revenue=annual_revenue,
        vat_sales=0.20,
        vat_purchases=0.20,
        opening_cash=40_000,
        owner_social_quarterly=5_500,
        loan_monthly=4_000,
        annual_revenue_growth=0.03,
        purchase_inflation=0.035,
        seasonality=MONTHLY_SEASONALITY_DEFAULT,
        revenue_streams=[
            RevenueStream("Custom fabrication", 0.58),
            RevenueStream("Electrical assemblies", 0.27),
            RevenueStream("Repairs and maintenance", 0.15),
        ],
        cost_lines=_industrial_cost_lines(annual_revenue, preset_key),
        benchmark_notes=_default_source_notes() + industrial_benchmark_notes(preset_key),
    )


def _industrial_generic_profile(
    business_type: str,
    annual_revenue: float,
    preset_key: str,
    seed: int,
) -> BusinessProfile:
    return BusinessProfile(
        business_type=business_type,
        archetype=preset_key,
        description="Industrial SME profile inferred from the business description.",
        annual_revenue=annual_revenue,
        vat_sales=0.20,
        vat_purchases=0.20,
        opening_cash=round(annual_revenue * 0.055, 2),
        owner_social_quarterly=round(annual_revenue * 0.018, 2),
        loan_monthly=round(annual_revenue * 0.010, 2),
        annual_revenue_growth=0.03,
        purchase_inflation=0.035,
        seasonality=MONTHLY_SEASONALITY_DEFAULT,
        revenue_streams=[
            RevenueStream("Production contracts", 0.62),
            RevenueStream("Small series and custom jobs", 0.24),
            RevenueStream("Maintenance, tooling and services", 0.14),
        ],
        cost_lines=_industrial_cost_lines(annual_revenue, preset_key, seed),
        benchmark_notes=_default_source_notes() + industrial_benchmark_notes(preset_key),
    )


def _generic_profile(business_type: str, annual_revenue: float, rng: random.Random) -> BusinessProfile:
    text = normalize_text(business_type)
    revenue_streams = [
        RevenueStream("Core sales", 0.72),
        RevenueStream("Recurring contracts", 0.18),
        RevenueStream("Ancillary revenue", 0.10),
    ]

    cost_lines: list[CostLine] = []

    def add_cost_from_revenue_share(
        category: str,
        name: str,
        annual_share: float,
        unit: str,
        unit_price: float,
        source: str,
        underlying: str | None = None,
        market_code: str | None = None,
        volatility: float = 0.03,
        seasonality_linked: bool = True,
    ) -> None:
        monthly_budget = annual_revenue * annual_share / 12
        quantity = max(1.0, monthly_budget / max(unit_price, 0.01))
        cost_lines.append(
            CostLine(
                category,
                name,
                round(quantity, 2),
                unit,
                unit_price,
                source,
                underlying,
                market_code,
                volatility,
                seasonality_linked,
            )
        )

    add_cost_from_revenue_share("Raw materials", "General purchased goods", 0.18, "unit basket", 100, "Generic SMB cost ratio")
    add_cost_from_revenue_share("Energy", "Electricity", 0.035, "kWh", 0.17, "Electricity tariff proxy", "Electricity", None, 0.05)
    add_cost_from_revenue_share("Personnel", "Payroll and charges", 0.24, "monthly package", annual_revenue * 0.24 / 12, "Generic payroll ratio", None, None, 0.00, False)
    add_cost_from_revenue_share("Fixed costs", "Rent and facilities", 0.09, "monthly package", annual_revenue * 0.09 / 12, "Generic rent ratio", None, None, 0.00, False)
    add_cost_from_revenue_share("Fixed costs", "Admin, insurance, accounting", 0.055, "monthly package", annual_revenue * 0.055 / 12, "Generic overhead ratio", None, None, 0.00, False)

    if any(word in text for word in ["delivery", "fleet", "mobile", "chantier", "field"]):
        add_cost_from_revenue_share("Fuel and mobility", "Fuel and logistics", 0.08, "L", 1.62, "Oil-linked fuel proxy", "Oil", "WTI", 0.08)
    if any(word in text for word in ["food", "aliment", "bak", "cafe", "restaurant"]):
        add_cost_from_revenue_share("Raw materials", "Flour or cereal inputs", 0.05, "kg", 0.56, "Wheat proxy", "Wheat", "WHEAT", 0.06)
        add_cost_from_revenue_share("Raw materials", "Butter, cream or fats", 0.035, "kg/L", 4.50, "Fats proxy", "Fats", None, 0.04)
    if any(word in text for word in ["factory", "atelier", "manufact", "industrial", "machine"]):
        add_cost_from_revenue_share("Energy", "Industrial electricity", 0.06, "kWh", 0.16, "Electricity tariff proxy", "Electricity", None, 0.05)
    if any(word in text for word in ["wood", "menuis", "furniture", "packaging"]):
        add_cost_from_revenue_share("Raw materials", "Wood and timber", 0.09, "m3", 420, "Wood proxy", "Wood", None, 0.05)
    if any(word in text for word in ["cable", "electric", "metal", "hardware"]):
        add_cost_from_revenue_share("Raw materials", "Copper inputs", 0.07, "kg", 8.20, "Copper proxy", "Copper", "COPPER", 0.08)
    if any(word in text for word in ["construction", "building", "cement", "btp"]):
        add_cost_from_revenue_share("Raw materials", "Cement and mineral inputs", 0.08, "t", 115, "Gas-linked cement proxy", "Gas", None, 0.05)

    # Add one slight random perturbation so two vague businesses are not exact
    # clones while remaining deterministic under the provided seed.
    cost_lines = [
        replace(line, monthly_quantity=round(line.monthly_quantity * rng.uniform(0.92, 1.08), 2))
        for line in cost_lines
    ]

    return BusinessProfile(
        business_type=business_type,
        archetype="generic",
        description="Generic SMB profile inferred from the business description.",
        annual_revenue=annual_revenue,
        vat_sales=0.20,
        vat_purchases=0.20,
        opening_cash=round(annual_revenue * 0.055, 2),
        owner_social_quarterly=round(annual_revenue * 0.018, 2),
        loan_monthly=round(annual_revenue * 0.009, 2),
        annual_revenue_growth=0.03,
        purchase_inflation=0.035,
        seasonality=MONTHLY_SEASONALITY_DEFAULT,
        revenue_streams=revenue_streams,
        cost_lines=cost_lines,
        benchmark_notes=_default_source_notes(),
    )


def _default_source_notes() -> list[tuple[str, str, str, str]]:
    return [
        (
            "Commodity monthly history",
            "World Bank Pink Sheet or Alpha Vantage when enabled",
            "https://www.worldbank.org/en/research/commodity-markets",
            "Official World Bank commodity-market page; monthly historical XLSX used as no-key source.",
        ),
        (
            "French statistical series",
            "INSEE BDM API",
            "https://www.insee.fr/fr/information/2862759",
            "Official INSEE SDMX web service for time-series data. Exact series IDs can be configured later.",
        ),
        (
            "Business ratios",
            "Generated benchmark assumptions",
            "local archetype generator",
            "Ratios are v1 synthetic assumptions, designed to be replaced by INSEE/sector benchmark series.",
        ),
    ]

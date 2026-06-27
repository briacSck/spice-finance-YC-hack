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
from cashplan.materials import material as material_lookup


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
    "aluminium": "Aluminium",
    "lead": "Lead",
    "nickel": "Nickel",
    "tin": "Tin",
    "zinc": "Zinc",
    "steel": "Steel",
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
    if any(word in text for word in ["metal", "usinage", "foundry", "fonderie", "electricien", "electrical", "cable", "hardware", "aluminium", "aluminum", "copper", "cuivre", "zinc", "acier", "steel", "inox", "stainless", "galvani", "chaudronnerie"]):
        return _scale_profile(_metalwork_profile(), annual_revenue)
    industrial_preset_key = infer_industrial_preset_key(text)
    if industrial_preset_key:
        return _industrial_generic_profile(
            business_type,
            annual_revenue or 1_500_000,
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
            CostLine("Raw materials", "Tourage butter", 280, "kg", 6.20, "INSEE butter producer-price index", "Fats", "BUTTER", 0.04),
            CostLine("Raw materials", "Incorporation butter", 110, "kg", 5.10, "INSEE butter producer-price index", "Fats", "BUTTER", 0.04),
            CostLine("Raw materials", "Baker's yeast", 65, "kg", 3.60, "INSEE other food products proxy", None, "YEAST", 0.02),
            CostLine("Raw materials", "Salt", 55, "kg", 0.65, "INSEE salt producer-price index", None, "SALT", 0.01),
            CostLine("Raw materials", "Eggs", 2200, "unit", 0.25, "INSEE egg producer-price index", None, "EGGS", 0.03),
            CostLine("Raw materials", "Cream", 160, "L", 3.60, "INSEE cream producer-price index", "Fats", "CREAM", 0.04),
            CostLine("Raw materials", "Packaging", 13000, "unit", 0.06, "INSEE paper/cardboard packaging index", "Packaging", "PACKAGING_PAPER", 0.03),
            CostLine("Energy", "Electricity for ovens and refrigeration", 5800, "kWh", 0.17, "ENTSO-E or INSEE electricity index", "Electricity", "ELECTRICITY", 0.05),
            CostLine("Energy", "Gas for heating", 2600, "kWh", 0.10, "Natural gas market proxy", "Gas", "NATURAL_GAS", 0.08),
            CostLine("Personnel", "Owner net compensation", 1, "monthly package", 4200, "Fixed owner draw assumption", None, None, 0.00, False),
            CostLine("Personnel", "Employee salary and charges", 1, "monthly package", 5600, "INSEE hospitality labor-cost index", None, "LABOR_HOSPITALITY", 0.00, False),
            CostLine("Fixed costs", "Commercial rent", 1, "monthly package", 3200, "INSEE commercial rent index", None, "RENT_COMMERCIAL", 0.00, False),
            CostLine("Fixed costs", "Insurance", 1, "monthly package", 250, "Professional insurance estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Maintenance", 1, "monthly package", 350, "INSEE maintenance proxy", None, "MAINTENANCE", 0.00, False),
            CostLine("Fixed costs", "Accountant", 1, "monthly package", 500, "INSEE accounting services index", None, "ACCOUNTING_SERVICES", 0.00, False),
            CostLine("Fixed costs", "Water", 1, "monthly package", 150, "INSEE water retail-price series", None, "WATER", 0.00, False),
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
            CostLine("Fuel and mobility", "Diesel fuel", 8100, "L", 1.62, "INSEE diesel/gazole price series", "Oil", "DIESEL", 0.08),
            CostLine("Fuel and mobility", "Tires and rubber consumables", 4, "unit", 420, "INSEE synthetic rubber producer-price index", "Rubber", "RUBBER", 0.04),
            CostLine("Maintenance", "Truck maintenance and parts", 1, "monthly package", 2800, "INSEE maintenance proxy", "Maintenance", "MAINTENANCE", 0.03, False),
            CostLine("Personnel", "Drivers payroll and charges", 1, "monthly package", 25500, "INSEE transport labor-cost index", None, "LABOR_TRANSPORT", 0.00, False),
            CostLine("Fixed costs", "Vehicle leases", 1, "monthly package", 6400, "INSEE vehicle leasing services index", None, "EQUIPMENT_RENTAL", 0.00, False),
            CostLine("Fixed costs", "Insurance and permits", 1, "monthly package", 2800, "Fleet insurance estimate", None, None, 0.00, False),
            CostLine("Fixed costs", "Depot rent and utilities", 1, "monthly package", 3200, "INSEE commercial rent index", "Rent", "RENT_COMMERCIAL", 0.02, False),
            CostLine("Fixed costs", "Admin, software, bank fees", 1, "monthly package", 2500, "INSEE admin services index", None, "ADMIN_SERVICES", 0.00, False),
        ],
        benchmark_notes=_default_source_notes(),
    )


def _plastics_profile() -> BusinessProfile:
    annual_revenue = 1_600_000
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
    steel = material_lookup("carbon_steel")
    timber = material_lookup("wood_panels")
    copper = material_lookup("copper")
    diesel = material_lookup("diesel")
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
            CostLine("Raw materials", "Cement and concrete inputs", 44, "t", 115, "INSEE construction materials cost index", "Construction materials", "CONSTRUCTION_COST", 0.05),
            CostLine("Raw materials", "Timber and panels", 18, timber.default_unit, timber.default_unit_price, timber.source, timber.underlying, timber.market_code, timber.volatility),
            CostLine("Raw materials", "Carbon steel rebar, sheet and metalwork", 8300, steel.default_unit, steel.default_unit_price, steel.source, steel.underlying, steel.market_code, steel.volatility),
            CostLine("Fuel and mobility", "Diesel for machinery and vehicles", 1950, diesel.default_unit, diesel.default_unit_price, diesel.source, diesel.underlying, diesel.market_code, diesel.volatility),
            CostLine("Raw materials", "Copper electrical wiring", 220, copper.default_unit, copper.default_unit_price, copper.source, copper.underlying, copper.market_code, copper.volatility),
            CostLine("Personnel", "Site payroll and charges", 1, "monthly package", 27500, "INSEE construction labor-cost index", None, "LABOR_CONSTRUCTION", 0.00, False),
            CostLine("Fixed costs", "Tools, equipment rental, depot", 1, "monthly package", 6300, "INSEE construction equipment rental index", None, "RENT_EQUIPMENT_CONSTRUCTION", 0.00, False),
            CostLine("Fixed costs", "Insurance, admin, accounting", 1, "monthly package", 3550, "INSEE admin services index", None, "ADMIN_SERVICES", 0.00, False),
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
            CostLine("Raw materials", "Food purchases", 1, "monthly package", 10000, "INSEE food products producer-price index", None, "FOOD_PRODUCTS", 0.04),
            CostLine("Raw materials", "Butter, cream and dairy fats", 320, "kg/L", 4.20, "INSEE dairy products for wholesalers/restaurants index", "Fats", "DAIRY_FATS", 0.04),
            CostLine("Raw materials", "Bread and flour-based inputs", 1, "monthly package", 2500, "Bakery supplier estimate", "Wheat", "WHEAT", 0.06),
            CostLine("Energy", "Cooking gas", 5200, "kWh", 0.105, "Natural gas proxy", "Gas", "NATURAL_GAS", 0.08),
            CostLine("Energy", "Electricity for kitchen and refrigeration", 7600, "kWh", 0.17, "ENTSO-E or INSEE electricity index", "Electricity", "ELECTRICITY", 0.05),
            CostLine("Personnel", "Kitchen and service payroll", 1, "monthly package", 16000, "INSEE hospitality labor-cost index", None, "LABOR_HOSPITALITY", 0.00, False),
            CostLine("Fixed costs", "Rent", 1, "monthly package", 5200, "INSEE commercial rent index", None, "RENT_COMMERCIAL", 0.00, False),
            CostLine("Fixed costs", "Insurance, accounting, software", 1, "monthly package", 2400, "INSEE admin services index", None, "ADMIN_SERVICES", 0.00, False),
        ],
        benchmark_notes=_default_source_notes(),
    )


def _metalwork_profile() -> BusinessProfile:
    annual_revenue = 1_000_000
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

    add_cost_from_revenue_share("Raw materials", "General purchased goods", 0.18, "unit basket", 100, "INSEE food/products proxy", None, "FOOD_PRODUCTS")
    add_cost_from_revenue_share("Energy", "Electricity", 0.035, "kWh", 0.17, "ENTSO-E or INSEE electricity index", "Electricity", "ELECTRICITY", 0.05)
    add_cost_from_revenue_share("Personnel", "Payroll and charges", 0.24, "monthly package", annual_revenue * 0.24 / 12, "INSEE generic labor-cost index", None, "LABOR_GENERIC", 0.00, False)
    add_cost_from_revenue_share("Fixed costs", "Rent and facilities", 0.09, "monthly package", annual_revenue * 0.09 / 12, "INSEE commercial rent index", None, "RENT_COMMERCIAL", 0.00, False)
    add_cost_from_revenue_share("Fixed costs", "Admin, insurance, accounting", 0.055, "monthly package", annual_revenue * 0.055 / 12, "INSEE admin services index", None, "ADMIN_SERVICES", 0.00, False)

    if any(word in text for word in ["delivery", "fleet", "mobile", "chantier", "field"]):
        add_cost_from_revenue_share("Fuel and mobility", "Fuel and logistics", 0.08, "L", 1.62, "INSEE diesel/gazole price series", "Oil", "DIESEL", 0.08)
    if any(word in text for word in ["food", "aliment", "bak", "cafe", "restaurant"]):
        add_cost_from_revenue_share("Raw materials", "Flour or cereal inputs", 0.05, "kg", 0.56, "Wheat proxy", "Wheat", "WHEAT", 0.06)
        add_cost_from_revenue_share("Raw materials", "Butter, cream or fats", 0.035, "kg/L", 4.50, "INSEE dairy products index", "Fats", "DAIRY_FATS", 0.04)
    if any(word in text for word in ["factory", "atelier", "manufact", "industrial", "machine"]):
        add_cost_from_revenue_share("Energy", "Industrial electricity", 0.06, "kWh", 0.16, "ENTSO-E or INSEE electricity index", "Electricity", "ELECTRICITY", 0.05)
    if any(word in text for word in ["wood", "menuis", "furniture", "packaging"]):
        add_cost_from_revenue_share("Raw materials", "Wood and timber", 0.09, "m3", 420, "INSEE lumber futures proxy", "Wood", "WOOD", 0.05)
    if any(word in text for word in ["cable", "electric", "metal", "hardware"]):
        copper = material_lookup("copper")
        add_cost_from_revenue_share("Raw materials", "Copper inputs", 0.07, copper.default_unit, copper.default_unit_price, copper.source, copper.underlying, copper.market_code, copper.volatility)
    if any(word in text for word in ["alu", "aluminium", "aluminum"]):
        aluminium = material_lookup("aluminium")
        add_cost_from_revenue_share("Raw materials", "Aluminium inputs", 0.05, aluminium.default_unit, aluminium.default_unit_price, aluminium.source, aluminium.underlying, aluminium.market_code, aluminium.volatility)
    if any(word in text for word in ["zinc", "galvani"]):
        zinc = material_lookup("zinc")
        add_cost_from_revenue_share("Raw materials", "Zinc inputs", 0.03, zinc.default_unit, zinc.default_unit_price, zinc.source, zinc.underlying, zinc.market_code, zinc.volatility)
    if any(word in text for word in ["acier", "steel", "chaudronnerie"]):
        steel = material_lookup("carbon_steel")
        add_cost_from_revenue_share("Raw materials", "Steel inputs", 0.06, steel.default_unit, steel.default_unit_price, steel.source, steel.underlying, steel.market_code, steel.volatility)
    if any(word in text for word in ["construction", "building", "cement", "btp"]):
        add_cost_from_revenue_share("Raw materials", "Cement and mineral inputs", 0.08, "t", 115, "INSEE construction materials cost index", "Construction materials", "CONSTRUCTION_COST", 0.05)

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
            "INSEE BDM, ENTSO-E, World Bank Pink Sheet or Alpha Vantage when enabled",
            "https://bdm.insee.fr/series/sdmx/dataflow",
            "Online mode uses curated INSEE IDBANK series first, then venue/API-specific market data and synthetic fallback only when unavailable.",
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

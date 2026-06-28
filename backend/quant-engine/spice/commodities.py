"""Hedgeable-commodity registry.

Each tradeable commodity maps to an Alpaca options ETF (matches
`alpaca-backend/alpaca/contracts.py`) and carries an annualised volatility used
by the quant engine for VaR. Vols are rough, real-economy ballparks — the quant
lane can refine from price history.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Commodity:
    ticker: str        # Alpaca options ETF underlying
    name: str          # FR label
    annual_vol: float  # annualised price volatility (fraction)


# ticker -> Commodity
COMMODITIES: dict[str, Commodity] = {
    "USO": Commodity("USO", "Pétrole", 0.35),
    "UNG": Commodity("UNG", "Gaz", 0.55),
    "WEAT": Commodity("WEAT", "Blé", 0.30),
    "CORN": Commodity("CORN", "Maïs", 0.28),
    "SOYB": Commodity("SOYB", "Matière grasse", 0.25),
    "CPER": Commodity("CPER", "Cuivre", 0.30),
    "XLU": Commodity("XLU", "Électricité", 0.20),
    "WOOD": Commodity("WOOD", "Bois", 0.25),
    "DBB": Commodity("DBB", "Métaux industriels (alu/zinc)", 0.22),
    "SLX": Commodity("SLX", "Acier", 0.32),
}


# ticker -> INSEE BDM market code (see cashplan/data_sources.py:INSEE_SERIES).
# Used to compute real historical price volatility instead of the static
# annual_vol guess above. Tickers absent here have no usable INSEE series.
INSEE_CODE: dict[str, str] = {
    "USO": "BRENT",
    "UNG": "NATURAL_GAS",
    "WEAT": "WHEAT",
    "SOYB": "DAIRY_FATS",
    "CPER": "COPPER",
    "XLU": "ELECTRICITY",
    "WOOD": "WOOD",
    "DBB": "ALUMINUM",
}


def insee_code(ticker: str) -> str | None:
    return INSEE_CODE.get(ticker.upper())


def vol(ticker: str) -> float:
    c = COMMODITIES.get(ticker.upper())
    return c.annual_vol if c else 0.0


def name(ticker: str) -> str:
    c = COMMODITIES.get(ticker.upper())
    return c.name if c else ticker


# ---------------------------------------------------------------------------
# Underlying-name <-> ticker, EN labels, and keyword inference.
# cashplan tags cost lines with underlying NAMES ("Wheat", "Oil"); the engine
# and Alpaca speak ETF TICKERS ("WEAT", "USO"). This is the single source of
# truth that reconciles the two, plus a keyword fallback for untagged files.
# ---------------------------------------------------------------------------
import re as _re

EN_NAMES: dict[str, str] = {
    "USO": "Oil", "UNG": "Gas", "WEAT": "Wheat", "CORN": "Corn",
    "SOYB": "Fats", "CPER": "Copper", "XLU": "Electricity", "WOOD": "Wood",
    "DBB": "Aluminium/Zinc", "SLX": "Steel",
}

_UNDERLYING_TO_TICKER: dict[str, str] = {
    "oil": "USO", "petrole": "USO",
    "electricity": "XLU", "electricite": "XLU", "power": "XLU",
    "gas": "UNG", "gaz": "UNG",
    "wheat": "WEAT", "ble": "WEAT",
    "fats": "SOYB", "fat": "SOYB",
    "copper": "CPER", "cuivre": "CPER",
    "wood": "WOOD", "bois": "WOOD",
    "packaging": "WOOD", "paper": "WOOD", "cardboard": "WOOD", "carton": "WOOD",
    "corn": "CORN", "mais": "CORN",
    "steel": "SLX", "acier": "SLX",
    "aluminium": "DBB", "aluminum": "DBB", "zinc": "DBB",
    "metaux industriels": "DBB", "base metals": "DBB",
}

_KEYWORDS: dict[str, tuple[str, ...]] = {
    "USO": ("diesel", "gasoil", "fuel", "carburant", "transport", "logistique",
            "logistics", "plastic", "plastique", "pvc", "polymer", "polymère",
            "polystyrène", "polyurethane", "bitumen", "bitume", "rubber",
            "caoutchouc", "petrole", "pétrole", "gnr"),
    "UNG": ("gas", "gaz", "natural gas", "chauffage", "cement", "ciment",
            "glass", "verre", "fertilizer", "engrais", "ammonia", "ammoniac",
            "azote", "kiln", "four"),
    "WEAT": ("wheat", "blé", "ble", "flour", "farine", "bread", "pain",
             "bakery", "boulangerie", "feed", "fourrage", "cereal", "céréale"),
    "CORN": ("corn", "maïs", "mais", "starch", "amidon", "ethanol"),
    "SOYB": ("fat", "fats", "huile", "soybean", "soja", "matière grasse",
             "beurre", "butter", "crème", "cream", "margarine"),
    "CPER": ("copper", "cuivre", "wire", "câble", "cable", "wiring", "plumbing",
             "plomberie", "brass", "laiton"),
    "XLU": ("electricity", "électricité", "electricite", "power", "courant", "kwh"),
    "WOOD": ("wood", "bois", "lumber", "timber", "charpente", "menuiserie",
             "palette", "panneau", "contreplaqué", "osb", "papier", "paper",
             "carton", "cardboard", "packaging", "emballage"),
    "SLX": ("steel", "acier", "rebar", "structural steel"),
    "DBB": ("aluminium", "aluminum", "alu", "zinc", "galvanis"),
}


def en_name(ticker: str) -> str:
    return EN_NAMES.get(ticker.upper(), name(ticker))


def ticker_for_underlying(underlying: str | None) -> str | None:
    """Map an underlying name ('Wheat') or ticker ('WEAT') to a known ticker."""
    if not underlying:
        return None
    key = underlying.strip()
    if key.upper() in COMMODITIES:
        return key.upper()
    return _UNDERLYING_TO_TICKER.get(key.lower())


_KW_PATTERNS = {
    t: _re.compile(r"\b(?:" + "|".join(_re.escape(k) for k in kws) + r")\b", _re.IGNORECASE)
    for t, kws in _KEYWORDS.items()
}


def infer_ticker(text: str) -> str | None:
    """Best-effort keyword match of a free-text cost label to a ticker."""
    for t, pat in _KW_PATTERNS.items():
        if pat.search(text or ""):
            return t
    return None

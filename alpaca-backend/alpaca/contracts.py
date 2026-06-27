"""Commodity-ETF registry + exposure inference + OCC symbol helpers.

Each ETF maps a real-economy commodity exposure to an Alpaca-tradable, OPRA-listed
options underlying. `exposure_keywords` (FR + EN) drive the invoice/AP line-item ->
hedge inference, same idea as ibkr/contracts.py.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ETF:
    ticker: str                       # Alpaca options underlying, e.g. "USO"
    commodity: str                    # FR label
    description: str
    exposure_keywords: tuple[str, ...] = field(default_factory=tuple)


# Commodity key (FR) -> Alpaca options ticker, with exposure keywords.
ETFS: dict[str, ETF] = {
    "USO": ETF(
        "USO", "Pétrole", "United States Oil Fund (WTI crude)",
        (
            "diesel", "gasoil", "fuel", "carburant", "transport", "logistics",
            "logistique", "plastic", "plastique", "pvc", "polymer", "polymère",
            "polystyrène", "polyurethane", "polyuréthane", "bitumen", "bitume",
            "rubber", "caoutchouc", "petrol", "petrole", "pétrole", "gnr",
        ),
    ),
    "UNG": ETF(
        "UNG", "Gaz", "United States Natural Gas Fund (Henry Hub)",
        (
            "gas", "gaz", "natural gas", "heating", "chauffage", "cement",
            "ciment", "glass", "verre", "fertilizer", "engrais", "ammonia",
            "ammoniac", "azote", "azoté", "chimie", "kiln", "four",
        ),
    ),
    "WEAT": ETF(
        "WEAT", "Blé", "Teucrium Wheat Fund",
        (
            "wheat", "blé", "ble", "flour", "farine", "bread", "pain",
            "bakery", "boulangerie", "feed", "aliment animal", "fourrage",
            "cereal", "céréale", "viande", "meat",
        ),
    ),
    "CORN": ETF(
        "CORN", "Maïs", "Teucrium Corn Fund",
        ("corn", "maïs", "mais", "feed", "fourrage", "starch", "amidon", "ethanol"),
    ),
    "SOYB": ETF(
        "SOYB", "Matière grasse", "Teucrium Soybean Fund (oils/fats proxy)",
        (
            "oil", "huile", "soybean", "soja", "fat", "matière grasse",
            "beurre", "butter", "crème", "cream", "frying", "friture",
            "margarine", "shortening",
        ),
    ),
    "CPER": ETF(
        "CPER", "Cuivre", "United States Copper Index Fund",
        (
            "copper", "cuivre", "wire", "câble", "cable", "wiring", "plumbing",
            "plomberie", "electrical", "electricien", "électricien", "brass",
            "laiton", "construction", "btp",
        ),
    ),
    "XLU": ETF(
        "XLU", "Électricité", "Utilities Select Sector (electricity proxy)",
        (
            "electricity", "électricité", "electricite", "power", "courant",
            "kwh", "kw/h", "energie electrique", "énergie électrique",
            "aluminium", "aluminum", "alu", "verre electrique",
        ),
    ),
    "WOOD": ETF(
        "WOOD", "Bois", "iShares Global Timber & Forestry (lumber proxy)",
        (
            "wood", "bois", "lumber", "timber", "charpente", "menuiserie",
            "palette", "emballage bois", "panneau", "contreplaqué", "osb",
            "papier", "carton", "pâte à papier",
        ),
    ),
}


def get_etf(ticker: str) -> ETF:
    t = ticker.upper()
    if t not in ETFS:
        raise KeyError(f"unknown ETF {ticker!r}; known: {sorted(ETFS)}")
    return ETFS[t]


# Word-boundary patterns so short keywords ("ble", "alu") don't substring-match
# unrelated words. \b is Unicode-aware on str, so accents are handled.
_KW_PATTERNS: dict[str, re.Pattern[str]] = {
    t: re.compile(
        r"\b(?:" + "|".join(re.escape(kw) for kw in etf.exposure_keywords) + r")\b",
        re.IGNORECASE,
    )
    for t, etf in ETFS.items()
    if etf.exposure_keywords
}


def infer_exposures(line_items: list[str]) -> dict[str, list[str]]:
    """Map free-text invoice/AP line-items -> ETF tickers they imply."""
    hits: dict[str, list[str]] = {}
    for item in line_items:
        for ticker, pat in _KW_PATTERNS.items():
            if pat.search(item):
                hits.setdefault(ticker, []).append(item)
    return hits


def occ_symbol(underlying: str, expiration: str, right: str, strike: float) -> str:
    """Build an OCC option symbol.

    underlying: e.g. "USO"; expiration: "YYYY-MM-DD"; right: "C"/"P"; strike: float.
    -> e.g. occ_symbol("USO","2025-12-19","P",75) == "USO251219P00075000"
    """
    right = right.upper()
    if right not in {"C", "P"}:
        raise ValueError("right must be 'C' or 'P'")
    y, m, d = expiration.split("-")
    yymmdd = f"{y[2:]}{m}{d}"
    strike_int = int(round(strike * 1000))
    return f"{underlying.upper()}{yymmdd}{right}{strike_int:08d}"

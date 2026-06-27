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


def vol(ticker: str) -> float:
    c = COMMODITIES.get(ticker.upper())
    return c.annual_vol if c else 0.0


def name(ticker: str) -> str:
    c = COMMODITIES.get(ticker.upper())
    return c.name if c else ticker

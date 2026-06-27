"""Alpaca backend — options on commodity ETFs (paper) for the YIELD AI-CFO agent.

Alpaca has no futures; commodity exposure is hedged via options on commodity ETFs.
Mirrors the ibkr/ package shape: client + contracts (ETF registry) + service.
"""

from .client import AlpacaClient, AlpacaError
from .contracts import ETFS, ETF, infer_exposures
from .service import AlpacaHedgeService

__all__ = [
    "AlpacaClient", "AlpacaError", "AlpacaHedgeService", "ETFS", "ETF",
    "infer_exposures",
]

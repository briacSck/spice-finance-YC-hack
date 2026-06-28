"""Morpho vault backend — deposit / withdraw / info on an ERC-4626 vault.

info()     : offchain GraphQL (APY, rewards, position) + onchain truth (shares, assets).
deposit()  : approve USDC -> vault.deposit(assets, receiver).
withdraw() : vault.withdraw(assets, receiver, owner).

Chain-agnostic (Base / Ethereum / their Sepolia testnets) via env.
"""

from .client import MorphoClient
from .service import MorphoService

__all__ = ["MorphoClient", "MorphoService"]

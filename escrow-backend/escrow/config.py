"""Chain registry + env settings for the parametric-insurance escrow service.

Mirrors morpho-backend/morpho/config.py so the two on-chain lanes share the same
chain ids, explorers, and USDC addresses. Defaults to Base Sepolia (84532).
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Chain:
    chain_id: int
    name: str
    rpc: str
    explorer: str
    usdc: str  # Circle USDC on that chain (used if you point at the real token)


CHAINS: dict[int, Chain] = {
    8453: Chain(8453, "base", "https://mainnet.base.org",
                "https://basescan.org", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
    84532: Chain(84532, "base-sepolia", "https://sepolia.base.org",
                 "https://sepolia.basescan.org",
                 "0x036CbD53842c5426634e7929541eC2318f3dCF7e"),
    11155111: Chain(11155111, "sepolia", "https://rpc.sepolia.org",
                    "https://sepolia.etherscan.io",
                    "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"),
}


@dataclass(frozen=True)
class Settings:
    chain_id: int = int(os.getenv("ESCROW_CHAIN_ID", "84532"))  # default Base Sepolia
    rpc_url: str = os.getenv("ESCROW_RPC_URL", "")
    escrow: str = os.getenv("ESCROW_ADDRESS", "")       # deployed ParametricEscrow
    usdc_override: str = os.getenv("ESCROW_USDC", "")   # MockUSDC, or real test USDC
    private_key: str = os.getenv("WALLET_PRIVATE_KEY", "")

    @property
    def chain(self) -> Chain:
        if self.chain_id not in CHAINS:
            raise KeyError(f"unsupported chain {self.chain_id}; known {sorted(CHAINS)}")
        return CHAINS[self.chain_id]

    @property
    def rpc(self) -> str:
        return self.rpc_url or self.chain.rpc

    @property
    def usdc(self) -> str:
        # if unset, the client reads the asset straight off the escrow contract
        return self.usdc_override or self.chain.usdc


settings = Settings()

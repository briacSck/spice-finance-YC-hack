"""Chain registry + env settings."""

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
    usdc: str  # Circle USDC on that chain


CHAINS: dict[int, Chain] = {
    8453: Chain(8453, "base", "https://mainnet.base.org",
                "https://basescan.org", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"),
    1: Chain(1, "ethereum", "https://eth.llamarpc.com",
             "https://etherscan.io", "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"),
    84532: Chain(84532, "base-sepolia", "https://sepolia.base.org",
                 "https://sepolia.basescan.org",
                 "0x036CbD53842c5426634e7929541eC2318f3dCF7e"),
    11155111: Chain(11155111, "sepolia", "https://rpc.sepolia.org",
                    "https://sepolia.etherscan.io",
                    "0x1c7D4B196Cb0C7B01d743Fbc6116a902379C7238"),
}


@dataclass(frozen=True)
class Settings:
    chain_id: int = int(os.getenv("MORPHO_CHAIN_ID", "8453"))
    rpc_url: str = os.getenv("MORPHO_RPC_URL", "")
    vault: str = os.getenv("MORPHO_VAULT", "0xbeeF010f9cb27031ad51e3333f9aF9C6B1228183")
    usdc_override: str = os.getenv("MORPHO_USDC", "")
    graphql: str = os.getenv("MORPHO_GRAPHQL", "https://api.morpho.org/graphql")
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
        return self.usdc_override or self.chain.usdc


settings = Settings()

"""The 3 agent-facing functions: deposit, withdraw, info."""

from __future__ import annotations

from typing import Any

from . import graph
from .client import MorphoClient
from .config import settings


class MorphoService:
    def __init__(self, client: MorphoClient | None = None) -> None:
        self.client = client or MorphoClient()

    # --- 1. INFO (read-only, no key needed) ---------------------------------
    def info(self, owner: str | None = None) -> dict[str, Any]:
        """Our placement: live onchain position + offchain APY/rewards."""
        c = self.client
        addr = owner or (c.account.address if c.account else None)

        out: dict[str, Any] = {
            "chain": settings.chain.name,
            "chain_id": settings.chain_id,
            "vault": c.vault_address,
            "usdc": c.usdc_address,
            "wallet": addr,
            "vault_total_assets_usdc": c.from_units(c.total_assets()),
        }

        if addr:
            shares = c.shares_balance(addr)
            out["position"] = {
                "shares": shares,
                "assets_usdc": c.from_units(c.assets_value(addr)),
                "max_withdraw_usdc": c.from_units(c.max_withdraw(addr)),
            }
            out["wallet_usdc_balance"] = c.from_units(c.usdc_balance(addr))

        # offchain enrichment (APY / rewards / pnl) — best-effort, normalized
        apy = graph.vault_apy(c.vault_address, settings.chain_id)
        if apy:
            out["apy"] = apy
        if addr:
            pos = graph.vault_position(addr, c.vault_address, settings.chain_id)
            if pos:
                out["position_offchain"] = pos
        return out

    # --- 2. DEPOSIT ---------------------------------------------------------
    def deposit(self, amount_usdc: float) -> dict[str, Any]:
        """Deposit USDC into the vault. Approves first if allowance is short."""
        c = self.client
        raw = c.to_units(amount_usdc)
        if raw <= 0:
            raise ValueError("amount must be > 0")

        owner = c.address
        if c.usdc_balance(owner) < raw:
            raise ValueError(
                f"insufficient USDC: have {c.from_units(c.usdc_balance(owner))}, "
                f"need {amount_usdc}"
            )

        steps: dict[str, Any] = {"amount_usdc": amount_usdc, "vault": c.vault_address}
        if c.allowance(owner) < raw:
            steps["approve"] = c.approve(raw)
            if c.wait_allowance(owner, raw) < raw:  # tolerate RPC lag before deposit
                raise RuntimeError("approve did not take effect (allowance still short)")
        steps["deposit"] = c.deposit(raw)
        steps["position_after"] = self.info(owner).get("position")
        return steps

    # --- 3. WITHDRAW --------------------------------------------------------
    def withdraw(self, amount_usdc: float) -> dict[str, Any]:
        """Withdraw USDC from the vault back to the wallet."""
        c = self.client
        raw = c.to_units(amount_usdc)
        if raw <= 0:
            raise ValueError("amount must be > 0")

        owner = c.address
        if c.max_withdraw(owner) < raw:
            raise ValueError(
                f"exceeds max withdraw: max {c.from_units(c.max_withdraw(owner))}, "
                f"asked {amount_usdc}"
            )

        return {
            "amount_usdc": amount_usdc,
            "vault": c.vault_address,
            "withdraw": c.withdraw(raw),
            "position_after": self.info(owner).get("position"),
        }

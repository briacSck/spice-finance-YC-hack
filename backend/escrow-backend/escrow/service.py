"""The 3 agent-facing functions: policy, settle, info — the parametric leg.

Matches the orchestrator's :8003 contract (quant-engine/spice/tools.py):
  POST /policy  {premium_usdc, trigger_index, payout_usdc}
  POST /settle  {index_value}
  GET  /info
"""

from __future__ import annotations

from typing import Any

from .client import EscrowClient
from .config import settings


class EscrowService:
    def __init__(self, client: EscrowClient | None = None) -> None:
        self.client = client or EscrowClient()
        self._last_policy_id: int | None = None

    # --- 1. INFO (read-only) ------------------------------------------------
    def info(self, policy_id: int | None = None) -> dict[str, Any]:
        c = self.client
        pid = policy_id if policy_id is not None else self._last_policy_id
        out: dict[str, Any] = {
            "chain": settings.chain.name,
            "chain_id": settings.chain_id,
            "escrow": c.escrow_address,
            "usdc": c.usdc_address,
            "free_liquidity_usdc": c.from_units(c.free_liquidity()),
            "reserved_usdc": c.from_units(c.reserved()),
            "last_index": c.last_index(),
            "policy_count": c.policy_count(),
        }
        if pid is not None and 0 <= pid < c.policy_count():
            out["policy"] = c.policy_info(pid)
        return out

    # --- 2. POLICY (pre-fund + mint) ----------------------------------------
    def policy(self, premium_usdc: float, trigger_index: int, payout_usdc: float,
               insured: str | None = None) -> dict[str, Any]:
        """Pre-fund the escrow with the payout, then mint the parametric policy.

        The premium is recorded for display only — it is NOT pulled on-chain
        (premium == 0 in takePolicy), so the live demo never needs an approve.
        """
        c = self.client
        payout_raw = c.to_units(payout_usdc)
        if payout_raw <= 0:
            raise ValueError("payout must be > 0")
        who = insured or c.address

        steps: dict[str, Any] = {
            "trigger_index": trigger_index, "premium_usdc": premium_usdc,
            "payout_usdc": payout_usdc, "escrow": c.escrow_address,
        }

        # ensure the contract holds enough free liquidity to back this payout
        shortfall = payout_raw - c.free_liquidity()
        if shortfall > 0:
            if c.usdc_balance(c.address) < shortfall:
                steps["mint"] = c.mint_usdc(shortfall)  # MockUSDC is mintable on testnet
            steps["fund"] = c.fund(shortfall)

        steps["policy"] = c.take_policy(who, 0, trigger_index, payout_raw)
        pid = c.policy_count() - 1
        self._last_policy_id = pid
        steps["policy_id"] = pid
        steps["status"] = "accepted"
        # surface the canonical {tx_hash, explorer, block} at the top level too
        for k in ("tx_hash", "explorer", "block"):
            steps[k] = steps["policy"][k]
        steps["info"] = c.policy_info(pid)
        return steps

    # --- 3. SETTLE (fire the oracle) ----------------------------------------
    def settle(self, index_value: int, policy_id: int | None = None) -> dict[str, Any]:
        """Fire the oracle. Pays out instantly if index_value >= trigger."""
        c = self.client
        pid = policy_id if policy_id is not None else self._last_policy_id
        if pid is None:
            raise ValueError("no policy to settle (call /policy first or pass policy_id)")
        before = c.policy_info(pid)
        tx = c.settle(pid, index_value)
        after = c.policy_info(pid)
        return {
            "policy_id": pid, "index_value": index_value,
            "trigger_index": before["trigger_index"],
            "paid": after["paid"],
            "payout_usdc": after["payout_usdc"] if after["paid"] else 0,
            "status": "settled", **tx,
        }

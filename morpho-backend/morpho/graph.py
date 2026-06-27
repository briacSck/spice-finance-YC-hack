"""Morpho offchain GraphQL API: vault APY/rewards + user position.

Best-effort — wrapped by the service so onchain truth still works if the API
shape differs for a given vault (V1 vs V2).
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import settings

_VAULT_APY_V2_Q = """
query($address: String!, $chainId: Int!) {
  vaultV2ByAddress(address: $address, chainId: $chainId) {
    address
    name
    avgNetApy
    avgNetApyExcludingRewards
    performanceFee
    managementFee
    totalAssets
    totalAssetsUsd
    rewards { asset { address } supplyApr }
  }
}
"""

# V1 (MetaMorpho) fallback — most public Base vaults (Steakhouse, etc.) are V1.
_VAULT_APY_V1_Q = """
query($address: String!, $chainId: Int!) {
  vaultByAddress(address: $address, chainId: $chainId) {
    address
    name
    state {
      netApy
      apy
      netApyExcludingRewards
      totalAssets
      totalAssetsUsd
      fee
      rewards { asset { address } supplyApr }
    }
  }
}
"""

_POSITION_Q = """
query($user: String!, $vault: String!, $chainId: Int!) {
  vaultV2PositionByAddress(userAddress: $user, vaultAddress: $vault, chainId: $chainId) {
    assets
    assetsUsd
    shares
    pnl
    pnlUsd
    roe
  }
}
"""


def _post(query: str, variables: dict[str, Any]) -> dict[str, Any]:
    resp = httpx.post(
        settings.graphql, json={"query": query, "variables": variables}, timeout=15.0
    )
    resp.raise_for_status()
    body = resp.json()
    if body.get("errors"):
        raise RuntimeError(body["errors"])
    return body.get("data") or {}


def vault_apy(address: str | None = None, chain_id: int | None = None) -> dict | None:
    """Normalized vault yield info. Tries V2 then V1 (MetaMorpho). Returns:
    {name, net_apy, net_apy_ex_rewards, gross_apy, performance_fee, rewards,
     total_assets_usd} or None.
    """
    addr = address or settings.vault
    cid = chain_id or settings.chain_id

    try:
        v2 = _post(_VAULT_APY_V2_Q, {"address": addr, "chainId": cid}).get("vaultV2ByAddress")
    except Exception:
        v2 = None
    if v2:
        return {
            "name": v2.get("name"),
            "net_apy": v2.get("avgNetApy"),
            "net_apy_ex_rewards": v2.get("avgNetApyExcludingRewards"),
            "gross_apy": None,
            "performance_fee": v2.get("performanceFee"),
            "rewards": v2.get("rewards"),
            "total_assets_usd": v2.get("totalAssetsUsd"),
        }

    try:
        v1 = _post(_VAULT_APY_V1_Q, {"address": addr, "chainId": cid}).get("vaultByAddress")
    except Exception:
        v1 = None
    if v1:
        st = v1.get("state") or {}
        return {
            "name": v1.get("name"),
            "net_apy": st.get("netApy"),
            "net_apy_ex_rewards": st.get("netApyExcludingRewards"),
            "gross_apy": st.get("apy"),
            "performance_fee": st.get("fee"),
            "rewards": st.get("rewards"),
            "total_assets_usd": st.get("totalAssetsUsd"),
        }
    return None


def vault_position(user: str, address: str | None = None,
                   chain_id: int | None = None) -> dict | None:
    try:
        data = _post(_POSITION_Q, {
            "user": user,
            "vault": address or settings.vault,
            "chainId": chain_id or settings.chain_id,
        })
        return data.get("vaultV2PositionByAddress")
    except Exception:
        return None

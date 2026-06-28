"""Deploy a Morpho Vault V2 on Base Sepolia via the factory, then run a full
deposit -> info -> withdraw against morpho-backend.

Needs env: WALLET_PRIVATE_KEY (throwaway, funded with test-USDC + a little ETH).
Run:  MORPHO_CHAIN_ID=84532 python scripts/deploy_test_vault.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from web3 import Web3

from morpho.client import MorphoClient
from morpho.config import settings

FACTORY = Web3.to_checksum_address("0xE3a2CEbca662d99D0F279aF13a6bb8c9825D2ea0")
FACTORY_ABI = [
    {"name": "createVaultV2", "type": "function", "stateMutability": "nonpayable",
     "inputs": [{"name": "owner", "type": "address"},
                {"name": "asset", "type": "address"},
                {"name": "salt", "type": "bytes32"}],
     "outputs": [{"type": "address"}]},
]


def deploy_vault() -> str:
    if not settings.private_key:
        raise SystemExit("set WALLET_PRIVATE_KEY (throwaway) in env/.env first")
    w3 = Web3(Web3.HTTPProvider(settings.rpc))
    acct = w3.eth.account.from_key(settings.private_key)
    owner = acct.address
    asset = Web3.to_checksum_address(settings.usdc)
    factory = w3.eth.contract(address=FACTORY, abi=FACTORY_ABI)

    nonce = w3.eth.get_transaction_count(owner)
    salt = nonce.to_bytes(32, "big")  # deterministic, varies per run (no rng)

    fn = factory.functions.createVaultV2(owner, asset, salt)
    predicted = fn.call({"from": owner})  # CREATE2 address, no state change
    print(f"owner={owner}\nasset(USDC)={asset}\npredicted vault={predicted}")

    tx = fn.build_transaction({
        "from": owner, "nonce": nonce, "chainId": settings.chain_id,
        "gasPrice": w3.eth.gas_price,
    })
    tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)
    signed = acct.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    h = w3.eth.send_raw_transaction(raw)
    print(f"deploy tx: {settings.chain.explorer}/tx/{h.hex()}")
    rcpt = w3.eth.wait_for_transaction_receipt(h)
    print(f"status={rcpt['status']} block={rcpt['blockNumber']}")
    if rcpt["status"] != 1:
        raise SystemExit("deploy reverted")
    return predicted


def e2e(vault: str, amount: float = 5.0) -> None:
    c = MorphoClient(vault=vault)
    from morpho.service import MorphoService
    svc = MorphoService(c)

    print("\n--- info (before) ---")
    print(svc.info())

    print(f"\n--- deposit {amount} USDC ---")
    print(svc.deposit(amount))

    print("\n--- info (after deposit) ---")
    print(svc.info())

    print(f"\n--- withdraw {amount} USDC ---")
    print(svc.withdraw(amount))

    print("\n--- info (after withdraw) ---")
    print(svc.info())


if __name__ == "__main__":
    vault = os.getenv("MORPHO_VAULT")
    if not vault or os.getenv("DEPLOY") == "1":
        vault = deploy_vault()
        print(f"\n>>> deployed vault: {vault}")
        print(f">>> set MORPHO_VAULT={vault}")
    e2e(vault, float(os.getenv("AMOUNT", "5")))

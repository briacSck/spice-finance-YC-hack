"""Compile + deploy the self-contained MockERC4626 vault to Base Sepolia, then run
deposit -> info -> withdraw via morpho-backend. Proves the onchain path end-to-end.

Needs: WALLET_PRIVATE_KEY (throwaway, test-USDC + ETH), MORPHO_CHAIN_ID=84532.
Run:  python scripts/deploy_mock_vault.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import solcx
from web3 import Web3

from morpho.config import settings

SRC = Path(__file__).resolve().parents[1] / "contracts" / "MockERC4626.sol"


def compile_vault():
    try:
        solcx.set_solc_version("0.8.26")
    except Exception:
        solcx.install_solc("0.8.26")
        solcx.set_solc_version("0.8.26")
    out = solcx.compile_files([str(SRC)], output_values=["abi", "bin"], solc_version="0.8.26")
    key = next(k for k in out if k.endswith(":MockERC4626"))
    return out[key]["abi"], out[key]["bin"]


def main():
    if not settings.private_key:
        raise SystemExit("set WALLET_PRIVATE_KEY in .env")
    w3 = Web3(Web3.HTTPProvider(settings.rpc))
    acct = w3.eth.account.from_key(settings.private_key)
    owner = acct.address
    asset = Web3.to_checksum_address(settings.usdc)

    abi, bytecode = compile_vault()
    print("compiled MockERC4626")

    Vault = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(owner)
    tx = Vault.constructor(asset).build_transaction({
        "from": owner, "nonce": nonce, "chainId": settings.chain_id,
        "gasPrice": w3.eth.gas_price,
    })
    tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)
    signed = acct.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    h = w3.eth.send_raw_transaction(raw)
    print(f"deploy tx: {settings.chain.explorer}/tx/{h.hex()}")
    rcpt = w3.eth.wait_for_transaction_receipt(h)
    vault = rcpt["contractAddress"]
    print(f"status={rcpt['status']} vault={vault}")
    if rcpt["status"] != 1:
        raise SystemExit("deploy reverted")

    time.sleep(3)  # let the public RPC index the new contract
    from morpho.client import MorphoClient
    from morpho.service import MorphoService
    svc = MorphoService(MorphoClient(vault=vault))
    amount = float(os.getenv("AMOUNT", "5"))

    def show(tag):
        i = svc.info()
        p = i.get("position", {})
        print(f"[{tag}] vault_total={i['vault_total_assets_usdc']} "
              f"my_assets={p.get('assets_usdc')} my_shares={p.get('shares')} "
              f"wallet_usdc={i.get('wallet_usdc_balance')}")

    show("before")
    print(f"\n>>> deposit {amount} USDC"); print(svc.deposit(amount)); show("after deposit")
    print(f"\n>>> withdraw {amount} USDC"); print(svc.withdraw(amount)); show("after withdraw")
    print(f"\nDONE. vault={vault}")


if __name__ == "__main__":
    main()

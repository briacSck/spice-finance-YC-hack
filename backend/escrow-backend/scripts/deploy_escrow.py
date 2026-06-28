"""Compile + deploy MockUSDC + ParametricEscrow to Base Sepolia, then run
policy -> settle so the parametric payout lands onchain. Proves the escrow path
end-to-end (the demo's parametric-insurance climax).

Needs: WALLET_PRIVATE_KEY (throwaway, with Base Sepolia ETH for gas).
Run:   python scripts/deploy_escrow.py
Env:   ESCROW_CHAIN_ID=84532  PAYOUT(=84000)  PREMIUM(=1240)  TRIGGER(=35)  INDEX(=41)
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import solcx
from web3 import Web3

from escrow.config import settings

CONTRACTS = Path(__file__).resolve().parents[1] / "contracts"


def compile_all():
    try:
        solcx.set_solc_version("0.8.26")
    except Exception:
        solcx.install_solc("0.8.26")
        solcx.set_solc_version("0.8.26")
    out = solcx.compile_files(
        [str(CONTRACTS / "MockUSDC.sol"), str(CONTRACTS / "ParametricEscrow.sol")],
        output_values=["abi", "bin"], solc_version="0.8.26",
    )
    usdc = next(out[k] for k in out if k.endswith(":MockUSDC"))
    esc = next(out[k] for k in out if k.endswith(":ParametricEscrow"))
    return usdc, esc


def _deploy(w3, acct, abi, bytecode, *args) -> str:
    c = w3.eth.contract(abi=abi, bytecode=bytecode)
    tx = c.constructor(*args).build_transaction({
        "from": acct.address, "nonce": w3.eth.get_transaction_count(acct.address),
        "chainId": settings.chain_id, "gasPrice": w3.eth.gas_price,
    })
    tx["gas"] = int(w3.eth.estimate_gas(tx) * 1.2)
    signed = acct.sign_transaction(tx)
    raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
    h = w3.eth.send_raw_transaction(raw)
    r = w3.eth.wait_for_transaction_receipt(h)
    if r["status"] != 1:
        raise SystemExit(f"deploy reverted: {settings.chain.explorer}/tx/{h.hex()}")
    return r["contractAddress"]


def main():
    if not settings.private_key:
        raise SystemExit("set WALLET_PRIVATE_KEY in .env")
    w3 = Web3(Web3.HTTPProvider(settings.rpc))
    acct = w3.eth.account.from_key(settings.private_key)
    owner = acct.address

    payout = float(os.getenv("PAYOUT", "84000"))
    premium = float(os.getenv("PREMIUM", "1240"))
    trigger = int(os.getenv("TRIGGER", "35"))
    index = int(os.getenv("INDEX", "41"))

    usdc_art, esc_art = compile_all()
    print("compiled MockUSDC + ParametricEscrow")

    usdc_addr = _deploy(w3, acct, usdc_art["abi"], usdc_art["bin"])
    print(f"MockUSDC:         {settings.chain.explorer}/address/{usdc_addr}")
    escrow_addr = _deploy(w3, acct, esc_art["abi"], esc_art["bin"],
                          Web3.to_checksum_address(usdc_addr))
    print(f"ParametricEscrow: {settings.chain.explorer}/address/{escrow_addr}")

    time.sleep(3)  # let the public RPC index the new contracts

    from escrow.client import EscrowClient
    from escrow.service import EscrowService
    c = EscrowClient(escrow=escrow_addr, usdc=usdc_addr)
    svc = EscrowService(c)

    print(f"\n>>> mint {payout} mUSDC to wallet")
    print(c.mint_usdc(c.to_units(payout)))

    print(f"\n>>> policy  premium={premium}  trigger={trigger}  payout={payout}")
    print(svc.policy(premium, trigger, payout))

    bal_before = c.from_units(c.usdc_balance(owner))
    print(f"\n>>> settle  index={index}  (trigger={trigger}, pays if index >= trigger)")
    print(svc.settle(index))
    bal_after = c.from_units(c.usdc_balance(owner))
    print(f"\ninsured USDC: {bal_before} -> {bal_after}  (payout {bal_after - bal_before})")

    print(
        "\nDONE. Put these in escrow-backend/.env, then `uvicorn app:app --port 8003`:\n"
        f"  ESCROW_ADDRESS={escrow_addr}\n  ESCROW_USDC={usdc_addr}\n"
        f"  ESCROW_CHAIN_ID={settings.chain_id}"
    )


if __name__ == "__main__":
    main()

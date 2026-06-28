"""Onchain client for the ParametricEscrow (web3.py): reads + signed writes.

Mirrors morpho-backend/morpho/client.py — same _send() returning
{tx_hash, explorer, status, block} so the frontend renders both on-chain lanes
identically.
"""

from __future__ import annotations

from typing import Any

from web3 import Web3

from .abis import ERC20_ABI, ESCROW_ABI
from .config import settings


class EscrowClient:
    def __init__(
        self,
        rpc: str | None = None,
        escrow: str | None = None,
        usdc: str | None = None,
        private_key: str | None = None,
        chain_id: int | None = None,
        web3: Web3 | None = None,
    ) -> None:
        self.chain_id = chain_id or settings.chain_id
        self.w3 = web3 or Web3(Web3.HTTPProvider(rpc or settings.rpc))

        addr = escrow or settings.escrow
        if not addr:
            raise RuntimeError(
                "no ESCROW_ADDRESS set — deploy first (python scripts/deploy_escrow.py)"
            )
        self.escrow_address = Web3.to_checksum_address(addr)
        self.escrow = self.w3.eth.contract(address=self.escrow_address, abi=ESCROW_ABI)

        # if USDC isn't given, read it straight off the escrow's assetToken()
        usdc_addr = usdc or settings.usdc_override or self.escrow.functions.assetToken().call()
        self.usdc_address = Web3.to_checksum_address(usdc_addr)
        self.usdc = self.w3.eth.contract(address=self.usdc_address, abi=ERC20_ABI)

        pk = private_key if private_key is not None else settings.private_key
        self.account = self.w3.eth.account.from_key(pk) if pk else None

    # --- helpers ------------------------------------------------------------
    @property
    def address(self) -> str:
        if not self.account:
            raise RuntimeError("no WALLET_PRIVATE_KEY set — signing disabled")
        return self.account.address

    @property
    def usdc_decimals(self) -> int:
        return self.usdc.functions.decimals().call()

    def to_units(self, amount: float) -> int:
        return int(round(amount * 10 ** self.usdc_decimals))

    def from_units(self, raw: int) -> float:
        return raw / 10 ** self.usdc_decimals

    def explorer_tx(self, tx_hash: str) -> str:
        return f"{settings.chain.explorer}/tx/{tx_hash}"

    def _send(self, fn) -> dict[str, Any]:
        """Build, sign, send a contract call; wait for the receipt."""
        if not self.account:
            raise RuntimeError("no WALLET_PRIVATE_KEY set — cannot sign")
        addr = self.account.address
        tx = fn.build_transaction({
            "from": addr,
            "nonce": self.w3.eth.get_transaction_count(addr),
            "chainId": self.chain_id,
            "gasPrice": self.w3.eth.gas_price,
        })
        signed = self.account.sign_transaction(tx)
        raw = getattr(signed, "raw_transaction", None) or signed.rawTransaction
        tx_hash = self.w3.eth.send_raw_transaction(raw)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        h = tx_hash.hex()
        if int(receipt["status"]) != 1:
            raise RuntimeError(f"tx reverted: {self.explorer_tx(h)}")
        return {"tx_hash": h, "explorer": self.explorer_tx(h),
                "status": int(receipt["status"]), "block": receipt["blockNumber"]}

    # --- reads --------------------------------------------------------------
    def free_liquidity(self) -> int:
        return self.escrow.functions.freeLiquidity().call()

    def reserved(self) -> int:
        return self.escrow.functions.reserved().call()

    def last_index(self) -> int:
        return self.escrow.functions.lastIndex().call()

    def policy_count(self) -> int:
        return self.escrow.functions.policyCount().call()

    def usdc_balance(self, owner: str) -> int:
        return self.usdc.functions.balanceOf(Web3.to_checksum_address(owner)).call()

    def policy_info(self, pid: int) -> dict[str, Any]:
        insured, premium, trigger, payout, is_open, paid = self.escrow.functions.info(pid).call()
        return {"policy_id": pid, "insured": insured,
                "premium_usdc": self.from_units(premium), "trigger_index": trigger,
                "payout_usdc": self.from_units(payout), "open": is_open, "paid": paid}

    # --- writes -------------------------------------------------------------
    def mint_usdc(self, raw_amount: int, to: str | None = None) -> dict[str, Any]:
        return self._send(self.usdc.functions.mint(
            Web3.to_checksum_address(to or self.address), raw_amount))

    def fund(self, raw_amount: int) -> dict[str, Any]:
        """Move USDC into the escrow so it can back a payout."""
        return self._send(self.usdc.functions.transfer(self.escrow_address, raw_amount))

    def take_policy(self, insured: str, premium_raw: int, trigger: int, payout_raw: int) -> dict[str, Any]:
        return self._send(self.escrow.functions.takePolicy(
            Web3.to_checksum_address(insured), premium_raw, trigger, payout_raw))

    def settle(self, pid: int, index_value: int) -> dict[str, Any]:
        return self._send(self.escrow.functions.settle(pid, index_value))

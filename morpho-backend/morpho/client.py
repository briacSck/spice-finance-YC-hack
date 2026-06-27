"""Onchain ERC-4626 client (web3.py) — reads + signed deposit/withdraw txns."""

from __future__ import annotations

import time
from typing import Any

from web3 import Web3

from .abis import ERC20_ABI, ERC4626_ABI
from .config import settings


class MorphoClient:
    def __init__(
        self,
        rpc: str | None = None,
        vault: str | None = None,
        usdc: str | None = None,
        private_key: str | None = None,
        chain_id: int | None = None,
        web3: Web3 | None = None,
    ) -> None:
        self.chain_id = chain_id or settings.chain_id
        self.w3 = web3 or Web3(Web3.HTTPProvider(rpc or settings.rpc))
        self.vault_address = Web3.to_checksum_address(vault or settings.vault)
        self.usdc_address = Web3.to_checksum_address(usdc or settings.usdc)
        self.vault = self.w3.eth.contract(address=self.vault_address, abi=ERC4626_ABI)
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

    def wait_allowance(self, owner: str, min_raw: int, tries: int = 12,
                       delay: float = 2.0) -> int:
        """Poll until allowance >= min_raw (tolerates load-balanced RPC lag)."""
        for _ in range(tries):
            a = self.allowance(owner)
            if a >= min_raw:
                return a
            time.sleep(delay)
        return self.allowance(owner)

    # --- reads --------------------------------------------------------------
    def shares_balance(self, owner: str) -> int:
        return self.vault.functions.balanceOf(Web3.to_checksum_address(owner)).call()

    def assets_value(self, owner: str) -> int:
        """USDC value of the owner's vault shares (convertToAssets)."""
        return self.vault.functions.convertToAssets(self.shares_balance(owner)).call()

    def max_withdraw(self, owner: str) -> int:
        return self.vault.functions.maxWithdraw(Web3.to_checksum_address(owner)).call()

    def usdc_balance(self, owner: str) -> int:
        return self.usdc.functions.balanceOf(Web3.to_checksum_address(owner)).call()

    def allowance(self, owner: str) -> int:
        return self.usdc.functions.allowance(
            Web3.to_checksum_address(owner), self.vault_address
        ).call()

    def total_assets(self) -> int:
        return self.vault.functions.totalAssets().call()

    # --- writes -------------------------------------------------------------
    def approve(self, raw_amount: int) -> dict[str, Any]:
        return self._send(self.usdc.functions.approve(self.vault_address, raw_amount))

    def deposit(self, raw_amount: int) -> dict[str, Any]:
        return self._send(self.vault.functions.deposit(raw_amount, self.address))

    def withdraw(self, raw_amount: int) -> dict[str, Any]:
        return self._send(
            self.vault.functions.withdraw(raw_amount, self.address, self.address)
        )

    def redeem(self, raw_shares: int) -> dict[str, Any]:
        return self._send(
            self.vault.functions.redeem(raw_shares, self.address, self.address)
        )

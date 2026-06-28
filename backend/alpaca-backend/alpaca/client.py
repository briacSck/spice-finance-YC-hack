"""Async REST client for the Alpaca Trading + Market Data API (paper).

Endpoints per ALPACA_API.md: account, option-contract discovery, option snapshots,
orders (single-leg + multi-leg mleg), positions. Paper vs live = host + keys only.
"""

from __future__ import annotations

from typing import Any

import httpx

from ibkr.config import alpaca_settings


class AlpacaError(RuntimeError):
    """Raised on non-2xx responses."""


class AlpacaClient:
    def __init__(
        self,
        key: str | None = None,
        secret: str | None = None,
        trading_url: str | None = None,
        data_url: str | None = None,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.trading_url = (trading_url or alpaca_settings.trading_url).rstrip("/")
        self.data_url = (data_url or alpaca_settings.data_url).rstrip("/")
        headers = {
            "APCA-API-KEY-ID": key or alpaca_settings.key,
            "APCA-API-SECRET-KEY": secret or alpaca_settings.secret,
            "accept": "application/json",
        }
        self._trade = httpx.AsyncClient(
            base_url=self.trading_url, timeout=timeout, transport=transport, headers=headers
        )
        self._data = httpx.AsyncClient(
            base_url=self.data_url, timeout=timeout, transport=transport, headers=headers
        )

    async def aclose(self) -> None:
        await self._trade.aclose()
        await self._data.aclose()

    async def __aenter__(self) -> "AlpacaClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    # --- low-level ----------------------------------------------------------
    @staticmethod
    async def _do(client: httpx.AsyncClient, method: str, path: str, **kw: Any) -> Any:
        try:
            resp = await client.request(method, path, **kw)
        except httpx.ConnectError as e:
            raise AlpacaError(f"cannot reach Alpaca ({e})") from e
        if resp.status_code == 429:
            raise AlpacaError("rate limited (429)")
        if resp.status_code >= 400:
            raise AlpacaError(f"{method} {path} -> {resp.status_code}: {resp.text}")
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return resp.text

    # --- account / positions / orders ---------------------------------------
    async def account(self) -> dict:
        return await self._do(self._trade, "GET", "/v2/account")

    async def positions(self) -> Any:
        return await self._do(self._trade, "GET", "/v2/positions")

    async def list_orders(self, status: str = "all", limit: int = 50) -> Any:
        return await self._do(
            self._trade, "GET", "/v2/orders", params={"status": status, "limit": limit}
        )

    async def cancel_order(self, order_id: str) -> Any:
        return await self._do(self._trade, "DELETE", f"/v2/orders/{order_id}")

    async def place_order(self, order: dict) -> dict:
        return await self._do(self._trade, "POST", "/v2/orders", json=order)

    # --- option discovery / data --------------------------------------------
    async def option_contracts(
        self,
        underlying_symbols: str,
        type: str | None = None,
        expiration_date_gte: str | None = None,
        expiration_date_lte: str | None = None,
        strike_price_gte: float | None = None,
        strike_price_lte: float | None = None,
        status: str = "active",
        limit: int = 1000,
    ) -> dict:
        params: dict[str, Any] = {
            "underlying_symbols": underlying_symbols,
            "status": status,
            "limit": limit,
        }
        if type:
            params["type"] = type
        if expiration_date_gte:
            params["expiration_date_gte"] = expiration_date_gte
        if expiration_date_lte:
            params["expiration_date_lte"] = expiration_date_lte
        if strike_price_gte is not None:
            params["strike_price_gte"] = strike_price_gte
        if strike_price_lte is not None:
            params["strike_price_lte"] = strike_price_lte
        return await self._do(self._trade, "GET", "/v2/options/contracts", params=params)

    async def option_snapshots(self, underlying: str, **params: Any) -> dict:
        return await self._do(
            self._data, "GET", f"/v1beta1/options/snapshots/{underlying}", params=params
        )

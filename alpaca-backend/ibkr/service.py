"""High-level, agent-facing operations.

The Claude CFO agent should call these (via the FastAPI layer), not the raw
client — they bundle session-priming, conid resolution, and the reply loop into
single intents like "hedge this exposure".
"""

from __future__ import annotations

from typing import Any

from .client import IBKRClient
from .contracts import (
    US_ROOTS,
    Root,
    infer_exposures,
    list_strikes,
    resolve_future,
    resolve_option,
)


def _root_view(r: Root) -> dict[str, Any]:
    return {
        "symbol": r.symbol,
        "name": r.name,
        "exchange": r.exchange,
        "currency": r.currency,
        "multiplier": r.multiplier,
        "unit": r.unit,
        "micro": r.micro,
        "exposure_keywords": list(r.exposure_keywords),
    }


class HedgeService:
    def __init__(self, client: IBKRClient) -> None:
        self.client = client

    # --- read ---------------------------------------------------------------
    def instruments(self) -> list[dict]:
        return [_root_view(r) for r in US_ROOTS.values()]

    def infer(self, line_items: list[str]) -> dict[str, list[str]]:
        """Map SMB invoice/AP line-items -> commodity roots they imply."""
        return infer_exposures(line_items)

    async def session(self) -> dict:
        return await self.client.ensure_session()

    async def positions(self) -> Any:
        return await self.client.positions()

    async def strikes(self, root: str, month: str) -> dict:
        return await list_strikes(self.client, root, month)

    # --- write (hedges) -----------------------------------------------------
    async def hedge_future(
        self,
        root: str,
        month: str,
        side: str,
        quantity: int,
        order_type: str = "MKT",
        price: float | None = None,
        tif: str = "DAY",
        use_micro: bool = False,
    ) -> dict:
        """Place a futures hedge. use_micro routes to the micro root if available."""
        sym = root.upper()
        if use_micro:
            micro = US_ROOTS[sym].micro
            if not micro:
                raise ValueError(f"{sym} has no micro contract")
            sym = micro
        resolved = await resolve_future(self.client, sym, month)
        order = _build_order(resolved["conid"], side, quantity, order_type, price, tif)
        result = await self.client.place_order_confirmed(order)
        return {"resolved": resolved, "result": result}

    async def hedge_option(
        self,
        root: str,
        month: str,
        strike: float,
        right: str,
        side: str,
        quantity: int,
        order_type: str = "LMT",
        price: float | None = None,
        tif: str = "DAY",
    ) -> dict:
        """Place a defined-risk options hedge (futures option). See contracts.py caveat."""
        resolved = await resolve_option(self.client, root, month, strike, right)
        order = _build_order(resolved["conid"], side, quantity, order_type, price, tif)
        result = await self.client.place_order_confirmed(order)
        return {"resolved": resolved, "result": result}


def _build_order(
    conid: int, side: str, quantity: int, order_type: str,
    price: float | None, tif: str,
) -> dict:
    side = side.upper()
    order_type = order_type.upper()
    if side not in {"BUY", "SELL"}:
        raise ValueError("side must be BUY or SELL")
    if order_type in {"LMT", "STP_LIMIT"} and price is None:
        raise ValueError(f"{order_type} requires a price")
    order: dict[str, Any] = {
        "conid": conid,
        "orderType": order_type,
        "side": side,
        "quantity": quantity,
        "tif": tif.upper(),
    }
    if price is not None:
        order["price"] = price
    return order

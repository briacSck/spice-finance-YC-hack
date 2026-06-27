"""High-level, agent-facing hedge intents over Alpaca commodity-ETF options."""

from __future__ import annotations

from datetime import date
from typing import Any

from .client import AlpacaClient
from .contracts import ETF, ETFS, get_etf, infer_exposures


def _etf_view(e: ETF) -> dict[str, Any]:
    return {
        "ticker": e.ticker,
        "commodity": e.commodity,
        "description": e.description,
        "exposure_keywords": list(e.exposure_keywords),
    }


def _pick_contract(
    contracts: list[dict], target_strike: float | None, target_exp: str | None
) -> dict:
    """Choose the best contract: nearest expiry (>= target if given), then nearest strike."""
    tradable = [c for c in contracts if c.get("tradable", True)]
    if not tradable:
        raise LookupError("no tradable contracts returned")

    if target_exp:
        future = [c for c in tradable if c.get("expiration_date", "") >= target_exp]
        pool = future or tradable
    else:
        pool = tradable
    # nearest expiry first
    nearest_exp = min(c["expiration_date"] for c in pool)
    pool = [c for c in pool if c["expiration_date"] == nearest_exp]

    if target_strike is not None:
        pool.sort(key=lambda c: abs(float(c["strike_price"]) - target_strike))
    return pool[0]


class AlpacaHedgeService:
    def __init__(self, client: AlpacaClient) -> None:
        self.client = client

    # --- read ---------------------------------------------------------------
    def instruments(self) -> list[dict]:
        return [_etf_view(e) for e in ETFS.values()]

    def infer(self, line_items: list[str]) -> dict[str, list[str]]:
        return infer_exposures(line_items)

    async def account(self) -> dict:
        return await self.client.account()

    async def positions(self) -> Any:
        return await self.client.positions()

    async def chain(self, ticker: str, right: str | None = None,
                    expiration_date_gte: str | None = None) -> dict:
        get_etf(ticker)  # validate
        return await self.client.option_contracts(
            underlying_symbols=ticker.upper(),
            type={"C": "call", "P": "put"}.get((right or "").upper()),
            expiration_date_gte=expiration_date_gte,
        )

    # --- write (hedge) ------------------------------------------------------
    async def hedge_option(
        self,
        ticker: str,
        right: str,
        quantity: int,
        side: str = "buy",
        strike: float | None = None,
        expiration: str | None = None,
        order_type: str = "limit",
        limit_price: float | None = None,
        tif: str = "day",
    ) -> dict:
        """Resolve a commodity-ETF option contract and place a single-leg order.

        right: 'C'/'P'. expiration/strike are targets; nearest available is chosen.
        """
        get_etf(ticker)
        right = right.upper()
        opt_type = {"C": "call", "P": "put"}.get(right)
        if not opt_type:
            raise ValueError("right must be 'C' or 'P'")
        exp_gte = expiration or date(2000, 1, 1).isoformat()
        resp = await self.client.option_contracts(
            underlying_symbols=ticker.upper(),
            type=opt_type,
            expiration_date_gte=exp_gte,
        )
        contracts = resp.get("option_contracts", []) if isinstance(resp, dict) else []
        chosen = _pick_contract(contracts, strike, expiration)

        order: dict[str, Any] = {
            "symbol": chosen["symbol"],
            "qty": str(quantity),
            "side": side.lower(),
            "type": order_type.lower(),
            "time_in_force": tif.lower(),
        }
        if order_type.lower() == "limit":
            if limit_price is None:
                raise ValueError("limit order requires limit_price")
            order["limit_price"] = str(limit_price)
        result = await self.client.place_order(order)
        return {"resolved": chosen, "order": order, "result": result}

    async def hedge_collar(
        self,
        ticker: str,
        quantity: int,
        put_strike: float,
        call_strike: float,
        expiration: str | None = None,
        limit_price: float | None = None,
        tif: str = "day",
    ) -> dict:
        """Multi-leg (L3): buy a protective put + sell a call (zero/low-cost collar)."""
        get_etf(ticker)
        exp_gte = expiration or date(2000, 1, 1).isoformat()
        puts = (await self.client.option_contracts(
            underlying_symbols=ticker.upper(), type="put", expiration_date_gte=exp_gte
        )).get("option_contracts", [])
        calls = (await self.client.option_contracts(
            underlying_symbols=ticker.upper(), type="call", expiration_date_gte=exp_gte
        )).get("option_contracts", [])
        put = _pick_contract(puts, put_strike, expiration)
        call = _pick_contract(calls, call_strike, expiration)

        order: dict[str, Any] = {
            "order_class": "mleg",
            "qty": str(quantity),
            "type": "limit" if limit_price is not None else "market",
            "time_in_force": tif.lower(),
            "legs": [
                {"symbol": put["symbol"], "side": "buy", "ratio_qty": "1",
                 "position_intent": "buy_to_open"},
                {"symbol": call["symbol"], "side": "sell", "ratio_qty": "1",
                 "position_intent": "sell_to_open"},
            ],
        }
        if limit_price is not None:
            order["limit_price"] = str(limit_price)
        result = await self.client.place_order(order)
        return {"resolved": {"put": put, "call": call}, "order": order, "result": result}

"""High-level hedge intents + order building."""

from __future__ import annotations

import pytest

from ibkr.service import HedgeService, _build_order


def test_build_order_market_no_price():
    o = _build_order(123, "buy", 2, "MKT", None, "day")
    assert o == {"conid": 123, "orderType": "MKT", "side": "BUY",
                 "quantity": 2, "tif": "DAY"}


def test_build_order_limit_includes_price():
    o = _build_order(123, "SELL", 1, "LMT", 3.25, "GTC")
    assert o["price"] == 3.25 and o["orderType"] == "LMT"


def test_build_order_limit_without_price_raises():
    with pytest.raises(ValueError):
        _build_order(123, "BUY", 1, "LMT", None, "DAY")


def test_build_order_bad_side_raises():
    with pytest.raises(ValueError):
        _build_order(123, "HODL", 1, "MKT", None, "DAY")


def test_instruments_lists_six(fake_client):
    svc = HedgeService(fake_client)
    rows = svc.instruments()
    assert len(rows) == 6
    assert {r["symbol"] for r in rows} == {"CL", "NG", "ZW", "ZC", "ZL", "HG"}


async def test_hedge_future_places_resolved_conid(fake_client):
    svc = HedgeService(fake_client)
    out = await svc.hedge_future("ZW", "SEP26", "BUY", 1, order_type="MKT")
    assert out["result"]["status"] == "submitted"
    assert fake_client.placed[0]["conid"] == 1001  # nearest expiry conid


async def test_hedge_future_use_micro_routes_to_micro_root(fake_client):
    svc = HedgeService(fake_client)
    await svc.hedge_future("HG", "SEP26", "BUY", 1, order_type="MKT", use_micro=True)
    # MHG underlying conid is 350 -> nearest contract 3501
    assert fake_client.placed[0]["conid"] == 3501


async def test_hedge_future_use_micro_without_micro_raises(fake_client):
    svc = HedgeService(fake_client)
    with pytest.raises(ValueError):
        await svc.hedge_future("ZW", "SEP26", "BUY", 1, use_micro=True)


async def test_hedge_option_places_order(fake_client):
    svc = HedgeService(fake_client)
    out = await svc.hedge_option("CL", "SEP26", 80, "P", "BUY", 1, price=1.5)
    assert out["result"]["status"] == "submitted"
    assert fake_client.placed[0]["price"] == 1.5


def test_infer_passthrough(fake_client):
    svc = HedgeService(fake_client)
    assert "ZW" in svc.infer(["Farine"])

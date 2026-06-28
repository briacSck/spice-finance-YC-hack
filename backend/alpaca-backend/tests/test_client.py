"""REST client: error mapping, secdef params, and the reply-confirm loop.

Uses httpx.MockTransport — no network, no gateway.
"""

from __future__ import annotations

import json

import httpx
import pytest

from ibkr.client import IBKRClient, IBKRError


def make_client(handler) -> IBKRClient:
    return IBKRClient(
        base_url="https://localhost:5000/v1/api",
        account_id="DU123",
        transport=httpx.MockTransport(handler),
    )


async def test_429_raises_rate_limit():
    def handler(req):
        return httpx.Response(429, text="slow down")
    async with make_client(handler) as c:
        with pytest.raises(IBKRError, match="rate limited"):
            await c.tickle()


async def test_4xx_surfaces_body():
    def handler(req):
        return httpx.Response(400, text="bad conid")
    async with make_client(handler) as c:
        with pytest.raises(IBKRError, match="bad conid"):
            await c.secdef_search("ZW")


async def test_empty_body_returns_none():
    def handler(req):
        return httpx.Response(200)
    async with make_client(handler) as c:
        assert await c.tickle() is None


async def test_secdef_info_passes_all_params():
    seen = {}
    def handler(req):
        seen.update(dict(req.url.params))
        return httpx.Response(200, json=[])
    async with make_client(handler) as c:
        await c.secdef_info(conid=100, sectype="OPT", month="SEP26",
                            strike=650, right="C", exchange="ECBOT")
    assert seen == {"conid": "100", "sectype": "OPT", "month": "SEP26",
                    "strike": "650", "right": "C", "exchange": "ECBOT"}


async def test_place_order_confirmed_submits_directly():
    def handler(req):
        return httpx.Response(200, json=[{"order_id": "1", "order_status": "Submitted"}])
    async with make_client(handler) as c:
        out = await c.place_order_confirmed({"conid": 1, "orderType": "MKT",
                                             "side": "BUY", "quantity": 1, "tif": "DAY"})
    assert out["status"] == "submitted"
    assert out["order"]["order_id"] == "1"


async def test_place_order_confirmed_walks_two_questions():
    """orders -> q1 -> reply q1 -> q2 -> reply q2 -> order_id."""
    def handler(req):
        path = req.url.path
        if path.endswith("/orders"):
            return httpx.Response(200, json=[{"id": "q1", "message": ["sure?"],
                                              "messageIds": ["o1"]}])
        if path.endswith("/reply/q1"):
            return httpx.Response(200, json=[{"id": "q2", "message": ["really?"],
                                              "messageIds": ["o2"]}])
        if path.endswith("/reply/q2"):
            return httpx.Response(200, json=[{"order_id": "9", "order_status": "Submitted"}])
        return httpx.Response(404)
    async with make_client(handler) as c:
        out = await c.place_order_confirmed({"conid": 1, "orderType": "MKT",
                                             "side": "BUY", "quantity": 1, "tif": "DAY"})
    assert out["status"] == "submitted"
    assert out["order"]["order_id"] == "9"
    assert out["questions"] == ["sure?", "really?"]


async def test_place_order_confirmed_unknown_shape_needs_review():
    def handler(req):
        return httpx.Response(200, json=[{"weird": "payload"}])
    async with make_client(handler) as c:
        out = await c.place_order_confirmed({"conid": 1, "orderType": "MKT",
                                             "side": "BUY", "quantity": 1, "tif": "DAY"})
    assert out["status"] == "needs_review"


async def test_place_orders_wraps_in_orders_key():
    seen = {}
    def handler(req):
        seen["body"] = json.loads(req.content)
        seen["path"] = req.url.path
        return httpx.Response(200, json=[{"order_id": "1"}])
    async with make_client(handler) as c:
        await c.place_orders([{"conid": 1}])
    assert seen["body"] == {"orders": [{"conid": 1}]}
    assert seen["path"].endswith("/iserver/account/DU123/orders")

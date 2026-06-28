"""Alpaca backend: registry, infer, OCC symbols, client, and hedge service.

Mocked with httpx.MockTransport — no network.
"""

from __future__ import annotations

import json

import httpx
import pytest

from alpaca.client import AlpacaClient, AlpacaError
from alpaca.contracts import ETFS, get_etf, infer_exposures, occ_symbol
from alpaca.service import AlpacaHedgeService, _pick_contract


# --- registry / infer / occ --------------------------------------------------
def test_registry_has_user_tickers():
    assert set(ETFS) == {"USO", "UNG", "WEAT", "CORN", "SOYB", "CPER", "XLU", "WOOD", "DBB", "SLX"}


def test_get_etf_unknown_raises():
    with pytest.raises(KeyError):
        get_etf("GLD")


def test_infer_maps_commodities_to_etfs():
    hits = infer_exposures(
        ["Farine T65", "Diesel camion", "Gaz four", "Cuivre câble",
         "Facture électricité", "Palette bois", "Profilés aluminium",
         "Plaques de zinc", "Poutre acier"]
    )
    assert hits["WEAT"] == ["Farine T65"]
    assert hits["USO"] == ["Diesel camion"]
    assert hits["UNG"] == ["Gaz four"]
    assert hits["CPER"] == ["Cuivre câble"]
    assert hits["XLU"] == ["Facture électricité"]
    assert hits["WOOD"] == ["Palette bois"]
    assert hits["DBB"] == ["Profilés aluminium", "Plaques de zinc"]
    assert hits["SLX"] == ["Poutre acier"]


def test_infer_no_substring_false_positive():
    # "ble" must not match "comptable"; "alu" must not match unrelated words
    assert infer_exposures(["Honoraires comptable"]) == {}


def test_occ_symbol_format():
    assert occ_symbol("USO", "2025-12-19", "P", 75) == "USO251219P00075000"
    assert occ_symbol("uso", "2026-09-18", "c", 80.5) == "USO260918C00080500"


def test_occ_symbol_bad_right():
    with pytest.raises(ValueError):
        occ_symbol("USO", "2025-12-19", "X", 75)


# --- contract selection ------------------------------------------------------
def test_pick_contract_nearest_expiry_then_strike():
    contracts = [
        {"symbol": "A", "expiration_date": "2026-09-18", "strike_price": "70", "tradable": True},
        {"symbol": "B", "expiration_date": "2026-09-18", "strike_price": "80", "tradable": True},
        {"symbol": "C", "expiration_date": "2026-12-18", "strike_price": "80", "tradable": True},
    ]
    chosen = _pick_contract(contracts, target_strike=79, target_exp="2026-09-01")
    assert chosen["symbol"] == "B"  # nearest expiry 09-18, strike closest to 79


def test_pick_contract_no_tradable_raises():
    with pytest.raises(LookupError):
        _pick_contract([{"symbol": "X", "tradable": False}], None, None)


# --- client (mock transport) -------------------------------------------------
def make_client(handler) -> AlpacaClient:
    return AlpacaClient(
        key="k", secret="s",
        trading_url="https://paper-api.alpaca.markets",
        data_url="https://data.alpaca.markets",
        transport=httpx.MockTransport(handler),
    )


async def test_client_sends_auth_headers():
    seen = {}
    def handler(req):
        seen["key"] = req.headers.get("APCA-API-KEY-ID")
        seen["secret"] = req.headers.get("APCA-API-SECRET-KEY")
        return httpx.Response(200, json={"id": "acct"})
    async with make_client(handler) as c:
        await c.account()
    assert seen == {"key": "k", "secret": "s"}


async def test_client_4xx_raises():
    def handler(req):
        return httpx.Response(403, text="forbidden")
    async with make_client(handler) as c:
        with pytest.raises(AlpacaError, match="forbidden"):
            await c.account()


async def test_option_contracts_passes_params():
    seen = {}
    def handler(req):
        seen.update(dict(req.url.params))
        return httpx.Response(200, json={"option_contracts": []})
    async with make_client(handler) as c:
        await c.option_contracts("USO", type="put", expiration_date_gte="2026-09-01",
                                 strike_price_lte=80)
    assert seen["underlying_symbols"] == "USO"
    assert seen["type"] == "put"
    assert seen["expiration_date_gte"] == "2026-09-01"
    assert seen["strike_price_lte"] == "80"


# --- service end-to-end (mocked) --------------------------------------------
async def test_hedge_option_resolves_and_orders():
    posted = {}
    def handler(req):
        if req.url.path == "/v2/options/contracts":
            return httpx.Response(200, json={"option_contracts": [
                {"symbol": "USO260918P00075000", "expiration_date": "2026-09-18",
                 "strike_price": "75", "tradable": True},
                {"symbol": "USO260918P00080000", "expiration_date": "2026-09-18",
                 "strike_price": "80", "tradable": True},
            ]})
        if req.url.path == "/v2/orders":
            posted["body"] = json.loads(req.content)
            return httpx.Response(200, json={"id": "ord1", "status": "accepted"})
        return httpx.Response(404)
    async with make_client(handler) as c:
        svc = AlpacaHedgeService(c)
        out = await svc.hedge_option("USO", "P", 1, strike=79,
                                     expiration="2026-09-01", limit_price=1.2)
    assert out["result"]["status"] == "accepted"
    assert posted["body"]["symbol"] == "USO260918P00080000"  # strike nearest 79
    assert posted["body"]["limit_price"] == "1.2"
    assert posted["body"]["qty"] == "1"


async def test_hedge_collar_builds_mleg():
    posted = {}
    def handler(req):
        if req.url.path == "/v2/options/contracts":
            typ = dict(req.url.params)["type"]
            sym = f"USO260918{'P' if typ=='put' else 'C'}00080000"
            return httpx.Response(200, json={"option_contracts": [
                {"symbol": sym, "expiration_date": "2026-09-18",
                 "strike_price": "80", "tradable": True}]})
        if req.url.path == "/v2/orders":
            posted["body"] = json.loads(req.content)
            return httpx.Response(200, json={"id": "ord2", "status": "accepted"})
        return httpx.Response(404)
    async with make_client(handler) as c:
        svc = AlpacaHedgeService(c)
        out = await svc.hedge_collar("USO", 1, put_strike=75, call_strike=90,
                                     expiration="2026-09-01", limit_price=0.5)
    body = posted["body"]
    assert body["order_class"] == "mleg"
    assert len(body["legs"]) == 2
    assert body["legs"][0]["side"] == "buy" and body["legs"][1]["side"] == "sell"
    assert out["result"]["status"] == "accepted"

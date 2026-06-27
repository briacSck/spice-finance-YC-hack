"""Shared fixtures + fakes. No live gateway is ever touched."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class FakeClient:
    """Stub matching the IBKRClient methods used by contracts/service.

    Canned secdef data for ZW (wheat) + CL (crude). Records placed orders.
    """

    def __init__(self) -> None:
        self.placed: list[dict] = []

    async def secdef_search(self, symbol, name=False, sec_type=None):
        data = {
            "ZW": {"conid": 100, "symbol": "ZW",
                   "sections": [{"secType": "FUT", "months": "SEP26;DEC26"},
                                {"secType": "OPT"}]},
            "CL": {"conid": 200, "symbol": "CL",
                   "sections": [{"secType": "FUT", "months": "AUG26;SEP26"},
                                {"secType": "OPT"}]},
            "HG": {"conid": 300, "symbol": "HG",
                   "sections": [{"secType": "FUT", "months": "SEP26"}]},
            "MHG": {"conid": 350, "symbol": "MHG",
                    "sections": [{"secType": "FUT", "months": "SEP26"}]},
        }
        return [data[symbol.upper()]] if symbol.upper() in data else []

    async def secdef_info(self, conid, sectype, month=None, strike=None,
                          right=None, exchange=None):
        # two expiries within a month -> resolver must pick the nearest
        base = conid * 10
        return [
            {"conid": base + 2, "maturityDate": "20260918", "strike": strike, "right": right},
            {"conid": base + 1, "maturityDate": "20260911", "strike": strike, "right": right},
        ]

    async def secdef_strikes(self, conid, sectype, month, exchange=None):
        return {"call": ["640", "650", "660"], "put": ["640", "650", "660"]}

    async def place_order_confirmed(self, order, account_id=None, max_replies=10):
        self.placed.append(order)
        return {"status": "submitted", "order": {"order_id": "OID1"}, "questions": []}


@pytest.fixture
def fake_client() -> FakeClient:
    return FakeClient()

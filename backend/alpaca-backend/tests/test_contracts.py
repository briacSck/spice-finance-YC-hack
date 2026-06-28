"""Registry, exposure inference, and conid resolution."""

from __future__ import annotations

import pytest

from ibkr.contracts import (
    US_ROOTS,
    get_root,
    infer_exposures,
    list_strikes,
    resolve_future,
    resolve_option,
)


def test_us_roots_are_the_liquid_six():
    assert set(US_ROOTS) == {"CL", "NG", "ZW", "ZC", "ZL", "HG"}


def test_get_root_case_insensitive():
    assert get_root("zw").symbol == "ZW"


def test_get_root_unknown_raises():
    with pytest.raises(KeyError):
        get_root("XAU")


def test_infer_maps_french_and_english_line_items():
    hits = infer_exposures(
        ["Farine T65 50kg", "Diesel livraison camion", "Cuivre cablage", "Gaz four"]
    )
    assert hits["ZW"] == ["Farine T65 50kg"]
    assert hits["CL"] == ["Diesel livraison camion"]
    assert hits["HG"] == ["Cuivre cablage"]
    assert hits["NG"] == ["Gaz four"]


def test_infer_ignores_unrelated_items():
    assert infer_exposures(["Loyer bureau", "Honoraires comptable"]) == {}


def test_infer_one_item_can_hit_multiple_roots():
    # "huile" -> ZL; if the same line also says diesel -> CL
    hits = infer_exposures(["huile de friture et diesel"])
    assert "ZL" in hits and "CL" in hits


async def test_resolve_future_picks_nearest_expiry(fake_client):
    r = await resolve_future(fake_client, "ZW", "SEP26")
    assert r["underlying_conid"] == 100
    assert r["conid"] == 1001  # 100*10 + 1, the earlier maturityDate
    assert r["maturityDate"] == "20260911"
    assert r["exchange"] == "ECBOT"


async def test_resolve_option_carries_strike_right(fake_client):
    r = await resolve_option(fake_client, "CL", "SEP26", 80, "C")
    assert r["underlying_conid"] == 200
    assert r["conid"] == 2001
    assert r["strike"] == 80
    assert r["right"] == "C"


async def test_resolve_option_rejects_bad_right(fake_client):
    with pytest.raises(ValueError):
        await resolve_option(fake_client, "CL", "SEP26", 80, "X")


async def test_list_strikes_returns_calls_and_puts(fake_client):
    strikes = await list_strikes(fake_client, "ZW", "SEP26")
    assert strikes["call"] and strikes["put"]

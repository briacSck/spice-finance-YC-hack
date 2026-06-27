"""Service logic (deposit/withdraw/info) + GraphQL query plumbing. No chain/network."""

from __future__ import annotations

import pytest

from morpho import graph, service as service_mod
from morpho.service import MorphoService


class _Acct:
    address = "0xWALLET"


class FakeClient:
    """Implements only what MorphoService touches. Amounts in 6-dp USDC units."""

    vault_address = "0xVAULT"
    usdc_address = "0xUSDC"

    def __init__(self, usdc=1_000_000_000, shares=500_000, max_w=400_000_000,
                 allowance=0, total=9_000_000_000, with_account=True):
        self.account = _Acct() if with_account else None
        self._usdc = usdc
        self._shares = shares
        self._max_w = max_w
        self._allow = allowance
        self._total = total
        self.calls: list[str] = []

    # conversions (6 dp)
    def to_units(self, a): return int(round(a * 1_000_000))
    def from_units(self, r): return r / 1_000_000

    @property
    def address(self):
        if not self.account:
            raise RuntimeError("no key")
        return self.account.address

    def shares_balance(self, owner): return self._shares
    def assets_value(self, owner): return self._shares  # 1:1 for test
    def max_withdraw(self, owner): return self._max_w
    def usdc_balance(self, owner): return self._usdc
    def allowance(self, owner): return self._allow
    def total_assets(self): return self._total

    def approve(self, raw): self.calls.append(f"approve:{raw}"); return {"tx_hash": "0xa"}
    def deposit(self, raw): self.calls.append(f"deposit:{raw}"); return {"tx_hash": "0xd"}
    def withdraw(self, raw): self.calls.append(f"withdraw:{raw}"); return {"tx_hash": "0xw"}


@pytest.fixture
def no_network(monkeypatch):
    monkeypatch.setattr(graph, "vault_apy", lambda *a, **k: None)
    monkeypatch.setattr(graph, "vault_position", lambda *a, **k: None)


# --- info -------------------------------------------------------------------
def test_info_includes_position_and_vault_total(no_network):
    svc = MorphoService(FakeClient())
    out = svc.info()
    assert out["vault"] == "0xVAULT"
    assert out["vault_total_assets_usdc"] == 9000.0
    assert out["position"]["assets_usdc"] == 0.5
    assert out["wallet_usdc_balance"] == 1000.0


def test_info_without_key_skips_position(no_network):
    svc = MorphoService(FakeClient(with_account=False))
    out = svc.info()
    assert "position" not in out
    assert out["vault_total_assets_usdc"] == 9000.0


# --- deposit ----------------------------------------------------------------
def test_deposit_approves_when_allowance_short(no_network):
    fc = FakeClient(allowance=0)
    svc = MorphoService(fc)
    out = svc.deposit(100)
    assert "approve" in out and "deposit" in out
    assert fc.calls == ["approve:100000000", "deposit:100000000"]


def test_deposit_skips_approve_when_allowance_enough(no_network):
    fc = FakeClient(allowance=200_000_000)
    svc = MorphoService(fc)
    out = svc.deposit(100)
    assert "approve" not in out
    assert fc.calls == ["deposit:100000000"]


def test_deposit_insufficient_usdc_raises(no_network):
    fc = FakeClient(usdc=50_000_000)  # 50 USDC
    svc = MorphoService(fc)
    with pytest.raises(ValueError, match="insufficient USDC"):
        svc.deposit(100)


def test_deposit_zero_raises(no_network):
    with pytest.raises(ValueError):
        MorphoService(FakeClient()).deposit(0)


# --- withdraw ---------------------------------------------------------------
def test_withdraw_ok(no_network):
    fc = FakeClient(max_w=400_000_000)  # 400 USDC max
    svc = MorphoService(fc)
    out = svc.withdraw(100)
    assert out["withdraw"]["tx_hash"] == "0xw"
    assert fc.calls == ["withdraw:100000000"]


def test_withdraw_exceeds_max_raises(no_network):
    fc = FakeClient(max_w=50_000_000)  # 50 USDC max
    svc = MorphoService(fc)
    with pytest.raises(ValueError, match="exceeds max withdraw"):
        svc.withdraw(100)


# --- graphql plumbing -------------------------------------------------------
def test_graph_post_builds_query(monkeypatch):
    captured = {}

    class _Resp:
        def raise_for_status(self): pass
        def json(self): return {"data": {"vaultV2ByAddress": {"avgNetApy": 0.05}}}

    def fake_post(url, json, timeout):
        captured["url"] = url
        captured["json"] = json
        return _Resp()

    monkeypatch.setattr(graph.httpx, "post", fake_post)
    out = graph.vault_apy("0xVAULT", 8453)
    assert out["net_apy"] == 0.05  # normalized from avgNetApy (V2)
    assert captured["json"]["variables"] == {"address": "0xVAULT", "chainId": 8453}


def test_graph_errors_return_none(monkeypatch):
    class _Resp:
        def raise_for_status(self): pass
        def json(self): return {"errors": [{"message": "bad"}]}
    monkeypatch.setattr(graph.httpx, "post", lambda *a, **k: _Resp())
    assert graph.vault_apy("0xV", 1) is None

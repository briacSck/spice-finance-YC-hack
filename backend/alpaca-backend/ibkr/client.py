"""Async REST client for the IBKR Client Portal Web API.

Wraps the endpoints documented in IBKR_API.md: session/auth, secdef discovery,
order placement with the reply-confirm loop, and order management.

All paths are relative to settings.base_url (default https://localhost:5000/v1/api).
The gateway uses a self-signed cert -> verify is off by default in dev.
"""

from __future__ import annotations

from typing import Any

import httpx

from .config import settings


class IBKRError(RuntimeError):
    """Raised on non-2xx responses or unexpected payloads."""


class IBKRClient:
    def __init__(
        self,
        base_url: str | None = None,
        account_id: str | None = None,
        verify_tls: bool | None = None,
        timeout: float = 15.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.base_url = (base_url or settings.base_url).rstrip("/")
        self.account_id = account_id or settings.account_id
        verify = settings.verify_tls if verify_tls is None else verify_tls
        self._http = httpx.AsyncClient(
            base_url=self.base_url,
            verify=verify,
            timeout=timeout,
            transport=transport,  # inject httpx.MockTransport in tests
            headers={"User-Agent": "yield-ibkr-backend/0.1", "Accept": "application/json"},
        )

    async def aclose(self) -> None:
        await self._http.aclose()

    async def __aenter__(self) -> "IBKRClient":
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    # --- low-level ----------------------------------------------------------
    async def _request(self, method: str, path: str, **kw: Any) -> Any:
        try:
            resp = await self._http.request(method, path, **kw)
        except httpx.ConnectError as e:
            raise IBKRError(
                f"cannot reach gateway at {self.base_url} — is the Client Portal "
                f"Gateway running and logged in? ({e})"
            ) from e
        if resp.status_code == 429:
            raise IBKRError("rate limited (429) — back off; cap is 50 req/s/user")
        if resp.status_code >= 400:
            raise IBKRError(f"{method} {path} -> {resp.status_code}: {resp.text}")
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return resp.text

    async def get(self, path: str, **kw: Any) -> Any:
        return await self._request("GET", path, **kw)

    async def post(self, path: str, **kw: Any) -> Any:
        return await self._request("POST", path, **kw)

    async def delete(self, path: str, **kw: Any) -> Any:
        return await self._request("DELETE", path, **kw)

    # --- session / auth -----------------------------------------------------
    async def auth_status(self) -> dict:
        return await self.post("/iserver/auth/status")

    async def reauthenticate(self) -> dict:
        return await self.post("/iserver/reauthenticate")

    async def tickle(self) -> dict:
        """Keepalive; call < every 60s to avoid session timeout."""
        return await self.get("/tickle")

    async def accounts(self) -> Any:
        """Brokerage-side accounts; also primes the session for trading."""
        return await self.get("/iserver/accounts")

    async def portfolio_accounts(self) -> Any:
        return await self.get("/portfolio/accounts")

    async def ensure_session(self) -> dict:
        """Confirm an authenticated brokerage session, reauth if needed."""
        status = await self.auth_status()
        if not status.get("authenticated"):
            await self.reauthenticate()
            status = await self.auth_status()
        await self.accounts()  # required before trading
        return status

    # --- contract discovery (secdef) ----------------------------------------
    async def secdef_search(self, symbol: str, name: bool = False,
                            sec_type: str | None = None) -> list[dict]:
        body: dict[str, Any] = {"symbol": symbol, "name": name}
        if sec_type:
            body["secType"] = sec_type
        return await self.post("/iserver/secdef/search", json=body)

    async def secdef_strikes(self, conid: int, sectype: str, month: str,
                             exchange: str | None = None) -> dict:
        params: dict[str, Any] = {"conid": conid, "sectype": sectype, "month": month}
        if exchange:
            params["exchange"] = exchange
        return await self.get("/iserver/secdef/strikes", params=params)

    async def secdef_info(self, conid: int, sectype: str, month: str | None = None,
                          strike: float | None = None, right: str | None = None,
                          exchange: str | None = None) -> list[dict]:
        params: dict[str, Any] = {"conid": conid, "sectype": sectype}
        if month is not None:
            params["month"] = month
        if strike is not None:
            params["strike"] = strike
        if right is not None:
            params["right"] = right
        if exchange is not None:
            params["exchange"] = exchange
        return await self.get("/iserver/secdef/info", params=params)

    # --- orders -------------------------------------------------------------
    async def place_orders(self, orders: list[dict],
                           account_id: str | None = None) -> Any:
        acct = account_id or self.account_id
        return await self.post(
            f"/iserver/account/{acct}/orders", json={"orders": orders}
        )

    async def reply(self, reply_id: str, confirmed: bool = True) -> Any:
        return await self.post(f"/iserver/reply/{reply_id}", json={"confirmed": confirmed})

    async def place_order_confirmed(
        self, order: dict, account_id: str | None = None, max_replies: int = 10
    ) -> dict:
        """Place one order and auto-confirm IBKR's question prompts.

        Loops POST /iserver/reply/{id} {confirmed:true} until the response is a
        terminal order acknowledgement (has order_id/order_status) or replies run out.
        Returns {"status": "submitted"|"needs_review", "order": ..., "questions": [...]}.
        """
        resp = await self.place_orders([order], account_id=account_id)
        questions: list[str] = []
        for _ in range(max_replies):
            entry = resp[0] if isinstance(resp, list) and resp else resp
            if isinstance(entry, dict) and ("order_id" in entry or "order_status" in entry):
                return {"status": "submitted", "order": entry, "questions": questions}
            if isinstance(entry, dict) and "id" in entry and "message" in entry:
                questions.extend(entry.get("message", []))
                resp = await self.reply(entry["id"], confirmed=True)
                continue
            # unknown shape -> stop and surface it
            return {"status": "needs_review", "order": entry, "questions": questions}
        return {"status": "needs_review", "order": resp, "questions": questions}

    async def live_orders(self) -> Any:
        return await self.get("/iserver/account/orders")

    async def order_status(self, order_id: str) -> Any:
        return await self.get(f"/iserver/account/order/status/{order_id}")

    async def cancel_order(self, order_id: str, account_id: str | None = None) -> Any:
        acct = account_id or self.account_id
        return await self.delete(f"/iserver/account/{acct}/order/{order_id}")

    async def modify_order(self, order_id: str, changes: dict,
                           account_id: str | None = None) -> Any:
        acct = account_id or self.account_id
        return await self.post(f"/iserver/account/{acct}/order/{order_id}", json=changes)

    # --- portfolio ----------------------------------------------------------
    async def positions(self, page: int = 0, account_id: str | None = None) -> Any:
        acct = account_id or self.account_id
        return await self.get(f"/portfolio/{acct}/positions/{page}")

    async def ledger(self, account_id: str | None = None) -> Any:
        acct = account_id or self.account_id
        return await self.get(f"/portfolio/{acct}/ledger")

    async def suppress_questions(self, message_ids: list[str]) -> Any:
        return await self.post("/iserver/questions/suppress", json={"messageIds": message_ids})

    async def suppress_reset(self) -> Any:
        return await self.post("/iserver/questions/suppress/reset")

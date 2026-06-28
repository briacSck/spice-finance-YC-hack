"""Empirically resolve every US root against the live PAPER gateway.

Kills the guesswork: prints the real underlying conid, the nearest futures
contract conid, and whether option strikes come back for each root. Run this
once after logging the Client Portal Gateway into your paper account.

    python scripts/verify_contracts.py
    python scripts/verify_contracts.py --month SEP26
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ibkr.client import IBKRClient, IBKRError  # noqa: E402
from ibkr.contracts import US_ROOTS, list_strikes, resolve_future  # noqa: E402


async def probe(client: IBKRClient, sym: str, month: str | None) -> None:
    try:
        results = await client.secdef_search(sym)
        und = results[0]["conid"] if results else None
        months = ""
        for r in results or []:
            for s in r.get("sections") or []:
                if (s or {}).get("secType") == "FUT" and s.get("months"):
                    months = s["months"]
                    break
            if months:
                break
        print(f"\n=== {sym} ({US_ROOTS[sym].name}) ===")
        print(f"  underlying conid: {und}   FUT months: {months or '?'}")

        use_month = month or (months.split(";")[0] if months else None)
        if not use_month:
            print("  ! no month available; skipping future/strikes")
            return

        fut = await resolve_future(client, sym, use_month)
        print(f"  future {use_month}: conid={fut['conid']} maturity={fut['maturityDate']}")

        try:
            strikes = await list_strikes(client, sym, use_month)
            ncall = len(strikes.get("call", []))
            nput = len(strikes.get("put", []))
            print(f"  options {use_month}: {ncall} calls / {nput} puts"
                  + ("  -> OPTIONS OK" if ncall or nput else "  -> NO OPTIONS (verify secType)"))
        except IBKRError as e:
            print(f"  options {use_month}: strikes failed -> {e}")
    except Exception as e:  # noqa: BLE001
        print(f"\n=== {sym} ===\n  FAILED: {e}")


async def main(month: str | None) -> None:
    async with IBKRClient() as client:
        try:
            status = await client.ensure_session()
        except IBKRError as e:
            print(f"session error: {e}")
            print("Start the Client Portal Gateway and log in with PAPER creds first.")
            return
        print(f"authenticated={status.get('authenticated')} "
              f"competing={status.get('competing')} account={client.account_id}")
        for sym in US_ROOTS:
            await probe(client, sym, month)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--month", help="force MMMYY month, e.g. SEP26")
    args = ap.parse_args()
    asyncio.run(main(args.month))

"""US commodity contract registry + conid resolution via the Web API secdef flow.

Design choices:
- US-only, liquid roots with deep options. Each root carries `exposure_keywords`
  so the agent can map an SMB's invoice/AP line-items -> the commodity it is
  silently exposed to (the "unfair depth" of the demo).
- A standard ("big") contract plus an optional `micro` for SMB-sized hedging.
- Resolution follows IBKR_API.md: secdef/search -> secdef/strikes -> secdef/info.
  Month format for the Web API is MMMYY, e.g. "SEP26".

FUTURES OPTIONS CAVEAT: options-on-futures resolution over the Web API is not
fully documented. `resolve_option` is best-effort (sectype="OPT" against the
underlying conid). Run scripts/verify_contracts.py against the live paper gateway
to confirm the real conid + that strikes are returned before trusting it.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .client import IBKRClient


@dataclass(frozen=True)
class Root:
    symbol: str            # IBKR root, e.g. "CL"
    name: str              # human name
    exchange: str          # IBKR exchange string
    currency: str          # "USD"
    multiplier: int        # contract multiplier (per 1 point move)
    unit: str              # underlying unit
    micro: str | None      # micro/mini root for SMB sizing, if any
    exposure_keywords: tuple[str, ...] = field(default_factory=tuple)


# --- US liquid set (the demo + v1 build) -------------------------------------
US_ROOTS: dict[str, Root] = {
    "CL": Root(
        "CL", "WTI Crude Oil", "NYMEX", "USD", 1000, "bbl", micro="MCL",
        exposure_keywords=(
            "diesel", "gasoil", "fuel", "carburant", "transport", "logistics",
            "plastic", "plastique", "pvc", "polymer", "polymère", "bitumen",
            "bitume", "rubber", "caoutchouc", "petrol", "petrole", "gnr",
        ),
    ),
    "NG": Root(
        "NG", "Henry Hub Natural Gas", "NYMEX", "USD", 10000, "MMBtu", micro="MNG",
        exposure_keywords=(
            "gas", "gaz", "natural gas", "heating", "chauffage", "cement",
            "ciment", "glass", "verre", "fertilizer", "engrais", "ammonia",
            "ammoniac", "kiln", "four",
        ),
    ),
    "ZW": Root(
        "ZW", "Wheat", "ECBOT", "USD", 50, "bushel", micro=None,
        exposure_keywords=(
            "wheat", "blé", "ble", "flour", "farine", "bread", "pain",
            "bakery", "boulangerie", "feed", "aliment animal", "cereal",
        ),
    ),
    "ZC": Root(
        "ZC", "Corn", "ECBOT", "USD", 50, "bushel", micro=None,
        exposure_keywords=(
            "corn", "maïs", "mais", "feed", "fourrage", "aliment animal",
            "starch", "amidon", "ethanol",
        ),
    ),
    "ZL": Root(
        "ZL", "Soybean Oil", "ECBOT", "USD", 600, "lb", micro=None,
        exposure_keywords=(
            "oil", "huile", "soybean", "soja", "fat", "matière grasse",
            "frying", "friture", "margarine", "shortening",
        ),
    ),
    "HG": Root(
        "HG", "Copper", "COMEX", "USD", 25000, "lb", micro="MHG",
        exposure_keywords=(
            "copper", "cuivre", "wire", "câble", "cable", "wiring", "plumbing",
            "plomberie", "electrical", "électricité", "electricien", "brass",
            "laiton", "construction", "btp",
        ),
    ),
}


# Micro/mini roots inherit the parent's exchange + keywords (multiplier differs,
# but resolution only needs symbol + exchange). Lets resolve_future("MHG", ...) work.
MICRO_ROOTS: dict[str, Root] = {
    r.micro: Root(r.micro, f"Micro {r.name}", r.exchange, r.currency, 0, r.unit,
                  None, r.exposure_keywords)
    for r in US_ROOTS.values()
    if r.micro
}


def get_root(symbol: str) -> Root:
    sym = symbol.upper()
    if sym in US_ROOTS:
        return US_ROOTS[sym]
    if sym in MICRO_ROOTS:
        return MICRO_ROOTS[sym]
    raise KeyError(f"unknown root {symbol!r}; known: {sorted(US_ROOTS)}")


# Word-boundary patterns per root so short keywords ("ble") don't substring-match
# unrelated words ("comptable"). \b is Unicode-aware on str, so accents are safe.
_KW_PATTERNS: dict[str, re.Pattern[str]] = {
    sym: re.compile(
        r"\b(?:" + "|".join(re.escape(kw) for kw in root.exposure_keywords) + r")\b",
        re.IGNORECASE,
    )
    for sym, root in US_ROOTS.items()
    if root.exposure_keywords
}


def infer_exposures(line_items: list[str]) -> dict[str, list[str]]:
    """Map free-text invoice/AP line-items -> root symbols they imply.

    Returns {root_symbol: [matched line-items]}. Deterministic keyword baseline
    (word-boundary matched); the agent can layer LLM judgement on top.
    """
    hits: dict[str, list[str]] = {}
    for item in line_items:
        for sym, pat in _KW_PATTERNS.items():
            if pat.search(item):
                hits.setdefault(sym, []).append(item)
    return hits


# --- conid resolution --------------------------------------------------------
async def _underlying_conid(client: IBKRClient, root: Root) -> int:
    """Resolve the underlying conid for a root via secdef/search.

    Prefers a result that exposes a FUT section and matches the symbol.
    """
    results = await client.secdef_search(root.symbol)
    if not results:
        raise LookupError(f"secdef/search returned nothing for {root.symbol}")

    def has_fut(r: dict) -> bool:
        return any(
            (s or {}).get("secType") == "FUT" for s in (r.get("sections") or [])
        )

    for r in results:
        if (r.get("symbol") or "").upper() == root.symbol and has_fut(r):
            return int(r["conid"])
    for r in results:
        if has_fut(r):
            return int(r["conid"])
    # fall back to first hit; verify script will surface mismatches
    return int(results[0]["conid"])


async def resolve_future(client: IBKRClient, root_symbol: str, month: str) -> dict:
    """Resolve a specific futures contract conid.

    month: MMMYY, e.g. "SEP26".
    Returns the chosen secdef/info entry (contains the future `conid`).
    """
    root = get_root(root_symbol)
    und = await _underlying_conid(client, root)
    info = await client.secdef_info(
        conid=und, sectype="FUT", month=month, exchange=root.exchange
    )
    if not info:
        raise LookupError(
            f"no FUT contract for {root.symbol} {month} on {root.exchange}"
        )
    # secdef/info may return several expiries within a month; take the nearest.
    info_sorted = sorted(info, key=lambda c: str(c.get("maturityDate", "")))
    chosen = info_sorted[0]
    return {
        "root": root.symbol,
        "underlying_conid": und,
        "conid": int(chosen["conid"]),
        "month": month,
        "exchange": root.exchange,
        "maturityDate": chosen.get("maturityDate"),
        "raw": chosen,
    }


async def list_strikes(
    client: IBKRClient, root_symbol: str, month: str
) -> dict[str, list[str]]:
    """Available option strikes ({'call': [...], 'put': [...]}) for a month."""
    root = get_root(root_symbol)
    und = await _underlying_conid(client, root)
    return await client.secdef_strikes(
        conid=und, sectype="OPT", month=month, exchange=root.exchange
    )


async def resolve_option(
    client: IBKRClient,
    root_symbol: str,
    month: str,
    strike: float,
    right: str,
) -> dict:
    """Best-effort resolve a futures-option conid (defined-risk hedge).

    right: "C" or "P". See module docstring caveat — verify on paper.
    """
    right = right.upper()
    if right not in {"C", "P"}:
        raise ValueError("right must be 'C' or 'P'")
    root = get_root(root_symbol)
    und = await _underlying_conid(client, root)
    info = await client.secdef_info(
        conid=und,
        sectype="OPT",
        month=month,
        strike=strike,
        right=right,
        exchange=root.exchange,
    )
    if not info:
        raise LookupError(
            f"no OPT contract for {root.symbol} {month} {strike}{right}"
        )
    info_sorted = sorted(info, key=lambda c: str(c.get("maturityDate", "")))
    chosen = info_sorted[0]
    return {
        "root": root.symbol,
        "underlying_conid": und,
        "conid": int(chosen["conid"]),
        "month": month,
        "strike": strike,
        "right": right,
        "exchange": root.exchange,
        "maturityDate": chosen.get("maturityDate"),
        "raw": chosen,
    }

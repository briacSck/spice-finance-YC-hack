# Alpaca API — Commodity-Exposure Options Trading (Paper)

> Scraped from docs.alpaca.markets (2026-06).
> **Key constraint: Alpaca has NO futures.** Asset classes = US equities/ETFs, crypto,
> and **options on equities/ETFs**. "Commodities" on Alpaca therefore = **options on
> commodity ETFs** (oil/gas/wheat/copper funds), not CL/NG/ZW futures like the IBKR backend.

---

## Commodity exposure via ETF options (the mapping)

| Our root (IBKR fut) | Exposure | Alpaca ETF | Options? | Liquidity |
|---|---|---|---|---|
| CL | Crude oil / fuel / plastics | **USO** (US Oil Fund); `XLE` energy | ✅ | good (USO) |
| NG | Natural gas / cement / glass | **UNG** (US NatGas Fund) | ✅ | ok |
| ZW | Wheat / flour / bread | **WEAT** (Teucrium Wheat) | ✅ | thin |
| ZC | Corn / feed | **CORN** (Teucrium Corn) | ✅ | thin |
| ZL | Soy oil / fats | **SOYB** (Teucrium Soy); `DBA` broad ag | ◐ | thin |
| HG | Copper / wiring / BTP | **CPER** (US Copper); `COPX` miners | ◐ | thin (CPER), better COPX |
| — | Broad basket | `DBC` (commodities), `DBA` (ag), `GLD`/`SLV` metals | ✅ | good |

**Honest note:** single-commodity ETF options (WEAT/CORN/CPER) are illiquid. For a smooth
demo, lean on **USO, UNG, and the broad DBC/XLE/GLD** which have real option volume.

---

## Base URLs + auth
| Env | Trading host | Data host |
|---|---|---|
| **Paper** | `https://paper-api.alpaca.markets` | `https://data.alpaca.markets` |
| Live | `https://api.alpaca.markets` | `https://data.alpaca.markets` |

Auth headers on every request:
```
APCA-API-KEY-ID: <key>
APCA-API-SECRET-KEY: <secret>
```
Paper vs live is selected purely by the **host + the keys** (paper keys from the paper
dashboard). No special flag.

---

## Options approval levels
| Level | Allows |
|---|---|
| 0 | disabled |
| 1 | covered calls, cash-secured puts |
| 2 | L1 + **buy calls/puts** (long options = defined-risk hedges) |
| 3 | L2 + **spreads / multi-leg** |
**L3 multi-leg is now available in paper.** For SMB hedging you mostly need **L2** (buy
puts/calls) or **L3** (collars/spreads).

---

## 1. Discover option contracts
```
GET /v2/options/contracts
```
Query params:
| Param | Notes |
|---|---|
| `underlying_symbols` | e.g. `USO` (comma-sep for many) |
| `expiration_date` / `_gte` / `_lte` | `YYYY-MM-DD` |
| `strike_price_gte` / `_lte` | range |
| `type` | `call` / `put` |
| `status` | `active` (default) |
| `root_symbol` | OCC root |
| `limit` | default 100 |

Default returns only active contracts expiring before the upcoming weekend → always pass
`expiration_date_gte` to look further out.

Single contract: `GET /v2/options/contracts/{symbol_or_id}`

```bash
curl -s "https://paper-api.alpaca.markets/v2/options/contracts?underlying_symbols=USO&type=put&expiration_date_gte=2026-09-01&strike_price_lte=80" \
  -H "APCA-API-KEY-ID: $K" -H "APCA-API-SECRET-KEY: $S"
```
Each contract has a `symbol` = **OCC symbol** (use it to trade).

---

## 2. Option chain + greeks (market data)
```
GET https://data.alpaca.markets/v1beta1/options/snapshots/{underlying_symbol}
```
Params: `feed` (`opra`|`indicative`), `type` (`call`|`put`), `strike_price_gte/lte`,
`expiration_date[_gte/_lte]`, `root_symbol`, `limit` (≤1000), `page_token`.
Returns latest trade, latest quote, and **greeks** per contract — use for sizing the hedge.

---

## 3. Place an options order (same Orders API as equities)
```
POST /v2/orders
```
Validations for options: `qty` whole number, no `notional`, `time_in_force` ∈ {`day`,`gtc`},
`extended_hours=false`.

### Single-leg (buy a put = downside hedge)
`symbol` = the **OCC symbol** from step 1.
```json
{
  "symbol": "USO251219P00075000",
  "qty": "1",
  "side": "buy",
  "type": "limit",
  "limit_price": "1.20",
  "time_in_force": "day"
}
```

### Multi-leg (L3) — e.g. a collar / spread
`order_class: "mleg"`, 2–4 legs.
```json
{
  "order_class": "mleg",
  "qty": "1",
  "type": "limit",
  "limit_price": "0.50",
  "time_in_force": "day",
  "legs": [
    { "symbol": "USO251219P00075000", "side": "buy",  "ratio_qty": "1", "position_intent": "buy_to_open" },
    { "symbol": "USO251219C00090000", "side": "sell", "ratio_qty": "1", "position_intent": "sell_to_open" }
  ]
}
```
Each leg carries its own `symbol` (strike/expiry/right), `side`, `ratio_qty`,
`position_intent` (`buy_to_open`/`sell_to_open`/`buy_to_close`/`sell_to_close`).

---

## 4. OCC symbol format
`{ROOT}{YYMMDD}{C|P}{STRIKE×1000, 8 digits}`
- `USO` + `251219` + `P` + `00075000` → **`USO251219P00075000`** = USO 2025-12-19 $75 put.

---

## 5. Manage
| Method | Path | Purpose |
|---|---|---|
| GET | `/v2/orders` | list orders |
| GET | `/v2/orders/{id}` | order status |
| DELETE | `/v2/orders/{id}` | cancel |
| GET | `/v2/positions` | positions |
| GET | `/v2/account` | account / options_approved_level |

---

## Alpaca vs IBKR for this project
| | **Alpaca** | **IBKR (current backend)** |
|---|---|---|
| Instrument | options on **commodity ETFs** | **futures + futures-options** |
| Hedge precision | proxy (ETF tracks, w/ tracking error + contango) | direct commodity |
| API DX | clean REST, OCC symbols, instant paper keys | gateway + secdef 3-call + reply loop |
| Setup friction | **low** (just API keys) | high (run + login gateway) |
| Demo speed | fast | slower, more "real" |
| Liquidity (single commodity) | thin (WEAT/CORN/CPER) | deep (CL/NG/ZW) |

**Read:** Alpaca = faster to demo, weaker hedge precision (ETF proxy + contango), thin
single-commodity options. IBKR = real commodity exposure, heavier setup. Could run **both**:
Alpaca for a frictionless live demo, IBKR for the "real treasury desk" credibility shot.

**Sources:**
- [Options Trading | Alpaca Docs](https://docs.alpaca.markets/us/docs/options-trading)
- [Get Option Contracts | Alpaca Docs](https://docs.alpaca.markets/reference/get-options-contracts)
- [Option Chain | Alpaca Docs](https://docs.alpaca.markets/reference/optionchain)
- [Multi-leg (Level 3) Options in Paper | Alpaca](https://docs.alpaca.markets/us/docs/options-level-3-trading)
- [How to Trade Options with Alpaca](https://alpaca.markets/learn/how-to-trade-options-with-alpaca)
</content>

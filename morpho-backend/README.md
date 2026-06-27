# morpho-backend

Python backend for parking idle USDC in a **Morpho ERC-4626 vault**. Three functions:

- **`info`** — our placement: live onchain position (shares, USDC value, max-withdraw)
  + offchain APY/rewards from the [Morpho GraphQL API](https://docs.morpho.org/tools/offchain/api/morpho-vaults/). No wallet needed.
- **`deposit`** — approve USDC → `vault.deposit(assets, receiver)`.
- **`withdraw`** — `vault.withdraw(assets, receiver, owner)` back to the wallet.

Chain-agnostic (Base / Ethereum + their Sepolia testnets) via `.env`. ERC-4626 is a
standard, so the same code works mainnet and testnet — just swap chain + vault.

## Setup
```bash
cd morpho-backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Edit `.env`:
- `MORPHO_CHAIN_ID` — `8453` Base (default), `1` Ethereum, `84532` Base Sepolia, `11155111` Sepolia
- `MORPHO_VAULT` — ERC-4626 vault (default = Steakhouse USDC on Base)
- `WALLET_PRIVATE_KEY` — signs deposit/withdraw; **needs USDC + a little native gas**.
  Leave empty to run `info` read-only.

## Run
```bash
uvicorn app:app --reload --port 8002   # docs: http://localhost:8002/docs
```
| Method | Path | Notes |
|---|---|---|
| GET | `/info?owner=0x..` | placement + APY (owner optional if key set) |
| POST | `/deposit` `{ "amount_usdc": 100 }` | approve (if needed) + deposit |
| POST | `/withdraw` `{ "amount_usdc": 50 }` | withdraw to wallet |

Each write returns `{tx_hash, explorer, status, block}`.

## Known mainnet Base USDC vaults (ERC-4626)
| Vault | Address |
|---|---|
| Steakhouse USDC | `0xbeeF010f9cb27031ad51e3333f9aF9C6B1228183` |
| Seamless USDC | `0x616a4E1db48e22028f6bbf20444Cd3b8e3273738` |
| Spark USDC | `0x7BfA7C4f149E7415b73bdeDfe609237e29CBF34A` |

## Testnet
Morpho **Vault V2 Factory** is deployed on testnets:
- Base Sepolia: `0x4501125508079A99ebBebCE205DeC9593C2b5857`
- Sepolia: `0xA1D94F746dEfa1928926b84fB2596c06926C0405`

A ready public USDC test-vault isn't guaranteed — either deploy one via the factory,
or point `MORPHO_VAULT` at any ERC-4626 testnet vault (deposit/withdraw are standard).
Circle test-USDC is auto-selected per chain; get it from Circle's faucet.

## Tests
```bash
pip install pytest && python -m pytest -q   # 10 passing, fully mocked (no chain/network)
```

## Verified live (read-only)
`info()` on Base mainnet Steakhouse vault: net APY ~3.36%, gross ~4.5%, ~$227M TVL.

## Notes
- `info`/APY query tries Morpho V2 then falls back to V1 (MetaMorpho) — most public
  Base vaults are V1.
- Onchain values are the source of truth; GraphQL is best-effort enrichment.
- Gas uses legacy `gasPrice` (works on Base + Ethereum).
</content>

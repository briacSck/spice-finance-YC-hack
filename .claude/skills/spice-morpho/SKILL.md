---
name: spice-morpho
description: Use to place or recall idle company cash into a Morpho ERC-4626 yield vault for the Spice demo — deposit, withdraw, and read the live position/APY. Covers the FastAPI on :8002, chains (Base/Ethereum + their Sepolia testnets), env/wallet, and deploying a test vault on Base Sepolia.
---

# spice-morpho — idle-cash yield via Morpho ERC-4626

`info` is read-only (no wallet). `deposit`/`withdraw` are onchain ERC-4626 txns (need a
funded signer). Path: `backend/morpho-backend`. Same code works mainnet + testnet —
ERC-4626 is standard, just swap chain + vault in `.env`.

## Run
```bash
cd backend/morpho-backend
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env
uvicorn app:app --port 8002    # docs: http://localhost:8002/docs
```

## Env (`.env`, gitignored — never commit the key)
- `MORPHO_CHAIN_ID` — `8453` Base · `1` Ethereum · `84532` Base Sepolia · `11155111` Sepolia
- `MORPHO_VAULT` — ERC-4626 vault (default = Steakhouse USDC on Base mainnet)
- `WALLET_PRIVATE_KEY` — signs deposit/withdraw; needs USDC + native gas. Empty = `info` only.
- `MORPHO_RPC_URL` (optional override), `MORPHO_GRAPHQL=https://api.morpho.org/graphql`

## Endpoints (:8002)
| Method | Path | Use |
|---|---|---|
| GET | `/info?owner=0x..` | position (shares, USDC value, max-withdraw) + APY/rewards |
| POST | `/deposit` `{amount_usdc}` | approve (if needed) + deposit; returns tx hashes + explorer |
| POST | `/withdraw` `{amount_usdc}` | recall to wallet |

```bash
curl -s localhost:8002/info
curl -s localhost:8002/deposit -H 'content-type: application/json' -d '{"amount_usdc":100}'
```

## Testnet (Base Sepolia) — proven path
No public Morpho USDC vault is deposit-open on Base Sepolia (V2 caps default to 0). Deploy a
self-contained ERC-4626 instead:
```bash
MORPHO_CHAIN_ID=84532 python scripts/deploy_mock_vault.py   # deploys MockERC4626, runs deposit→info→withdraw
```
Fund the wallet first: Circle test-USDC (`0x036CbD…`, faucet.circle.com → Base Sepolia) + a little Sepolia ETH.
`scripts/deploy_test_vault.py` deploys a real Morpho **Vault V2** via the factory, but its caps
start at 0 (timelocked to open) — use the mock for a working deposit/withdraw test.

## Sizing how much to place
The deterministic engine sweeps **excess cash** (`spice/hedging.py: compute_and_sweep`,
`monthly_excess_cash = revenue − expenses`). A safer waterfall keeps a buffer + VaR cushion:
`deployable = cash − 1.5×monthly_opex − obligations − hedge_reserve − cushion`, place 90%,
skip below a min ticket or if vault net APY < ~2%. Recall when the projected cash trough < buffer.

## Notes
- Mainnet default = real money — test on Base Sepolia first, tiny amounts on mainnet.
- Orchestrator calls this via the `lend_morpho` agent tool (degrades to a sim ref if down).
- ⚠️ Rotate any private key that has touched a chat/transcript.

---
name: spice-escrow
description: Use to take or settle a parametric insurance policy in the Spice demo — an on-chain escrow that pays a fixed payout the instant an index (e.g. heat index) crosses a trigger. Covers the FastAPI on :8003, the heatwave use-case, deploy/fund flow, and env. The "aléa" leg options can't hedge.
---

# spice-escrow — parametric insurance (on-chain)

Third venue: a pre-funded escrow with a settable oracle. Pays a fixed amount the moment an
index crosses a trigger — no claim, no adjuster. Demo: a **heatwave** policy (trigger heat
index e.g. 35; settle at observed 41). Covers the *aléa* options can't touch (lost footfall,
broken refrigeration). Trinity: options=price · Morpho=idle-cash yield · **escrow=aléa**.
Path: `backend/escrow-backend`. Base Sepolia, same explorer/response shape as morpho.

## Run
```bash
cd backend/escrow-backend
python -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt
cp .env.example .env                    # set WALLET_PRIVATE_KEY (Base Sepolia ETH for gas)
python scripts/deploy_escrow.py         # deploy + fund + take + settle end-to-end; prints ESCROW_ADDRESS / ESCROW_USDC
# paste those two into .env, then:
uvicorn app:app --port 8003
```
Uses `MockUSDC` (mintable 6-dp) so the full payout is real on-chain, faucet-free.

## Endpoints (:8003)
| Method | Path | Body / use |
|---|---|---|
| GET | `/info[?policy_id=]` | escrow position + policy |
| POST | `/policy` | `{premium_usdc, trigger_index, payout_usdc, insured?}` → mints policy (pre-funds shortfall) |
| POST | `/settle` | `{index_value, policy_id?}` → pays out if `index_value >= trigger` |

```bash
curl -s localhost:8003/policy -H 'content-type: application/json' \
  -d '{"premium_usdc":1240,"trigger_index":35,"payout_usdc":84000}'
curl -s localhost:8003/settle -H 'content-type: application/json' -d '{"index_value":41}'
```

## Key behaviours
- **Pre-funding rule**: `takePolicy` reverts unless the contract holds ≥ payout; the service mints+funds the shortfall first. Premium is display-only (no on-chain approve needed).
- **Operator-gated**: `policy`/`settle` sign with `WALLET_PRIVATE_KEY` (= deployer). The demo's operator trigger calls `/settle` to fire the payout live.
- Orchestrator calls this via the `take_escrow_policy` agent tool (degrades to a sim ref if down).
- Displayed €84k comes from orchestrator scenario constants, decoupled from the on-chain token amount.
- ⚠️ Rotate any private key used in a chat/transcript.

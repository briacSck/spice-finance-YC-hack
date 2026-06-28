# escrow-backend — parametric insurance (`:8003`)

The third on-chain venue in Spice: a **parametric insurance escrow**. A policy pays a
fixed payout to the insured the instant a settable index (the "oracle") crosses a
trigger — no claim, no adjuster. Demo use-case: a **heatwave** policy (trigger = heat
index, e.g. 35; settle with the observed index, e.g. 41). This protects against an
*aléa* the options can't touch (lost footfall + broken refrigeration are not a tradeable
price), completing the trinity: options = price, Morpho = idle-cash yield, escrow = aléa.

Same chain / explorer / response shape as `morpho-backend` (Base Sepolia), so the
frontend renders both on-chain lanes identically.

## Layout

```
contracts/ParametricEscrow.sol   the escrow (pre-funded, settable oracle)
contracts/MockUSDC.sol           mintable 6-dp USDC so the payout is faucet-free
escrow/{config,abis,client,service}.py   web3.py client + the 3 agent-facing fns
app.py                           FastAPI :8003 — /policy, /settle, /info, /health
scripts/deploy_escrow.py         deploy + fund + policy + settle, end to end
```

## Run

```bash
cd escrow-backend
python -m venv .venv && source .venv/Scripts/activate   # Windows Git Bash
pip install -r requirements.txt
cp .env.example .env            # set WALLET_PRIVATE_KEY (Base Sepolia ETH for gas)

python scripts/deploy_escrow.py # deploys, proves payout on-chain, prints ESCROW_ADDRESS/ESCROW_USDC
# paste those two into .env, then:
uvicorn app:app --port 8003
```

## Contract (matches `quant-engine/spice/tools.py`)

- `POST /policy {premium_usdc, trigger_index, payout_usdc}` → pre-funds + mints the policy
  → `{policy_id, tx_hash, explorer, status, block, ...}`. Premium is display-only (not
  pulled on-chain), so the live demo never needs an approve.
- `POST /settle {index_value}` → if `index_value >= trigger`, payout transfers instantly
  → `{paid, payout_usdc, tx_hash, explorer, status:"settled"}`.
- `GET /info[?policy_id=]` → escrow position + the policy.

## Notes

- **Pre-funding rule:** `takePolicy` reverts unless the contract already holds the payout
  (free liquidity ≥ payout). The service handles this: it mints + funds the shortfall
  before minting the policy. With `MockUSDC` the full ~84k payout is real on-chain with no
  faucet. To use the real Circle test USDC instead, set `ESCROW_USDC` to its address and
  scale the payout to a faucet-sized amount (the displayed €84k comes from the orchestrator
  scenario constants, decoupled from the on-chain token amount).
- **Operator = deployer wallet.** `takePolicy` / `settle` are operator-gated; the service
  signs with `WALLET_PRIVATE_KEY`. The operator-controlled trigger in the demo calls
  `/settle` to fire the payout live.
- Gas: the deployer wallet needs Base Sepolia ETH (Coinbase / Alchemy faucets).

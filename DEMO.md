# YIELD — Hero Demo & Weekend Build Plan

*Built real end-to-end on a testnet.*

---

## The hero demo — "The bakery that out-treasuries a hedge fund"

One continuous **~90-second** narrative blending three "wow" moments (idle-cash sweep + forecasted-gap defense + a shock the agent reacts to). **Real agent reasoning over realistic data → real stablecoin transactions settling on a testnet block explorer, live.** The contrast — a mundane French SMB getting autonomous Fortune-500 treasury — is the wow.

### The script
1. **Onboard in <60s.** "Meet *Maison Levain*, a €4M food distributor near Lyon." Connect accounting (mock Pennylane-style export) + bank data. The agent ingests cash, AP, AR.
2. **The AI CFO thinks out loud.** A live **Agent Activity Feed** shows reasoning: it builds a **13-week cash forecast** and flags three things. *(Show the model output, not just a pretty chart — this is the Polytechnique depth.)*
3. **Action 1 — Idle cash sweep.** "€62,000 sitting in checking at 0%." Agent sweeps it into an onchain RWA/yield vault → **real testnet tx settles, link to block explorer.** "Now earning 4.2%, recallable instantly."
4. **Action 2 — Defend a forecasted gap.** Agent spots a week-6 crunch (a large receivable slipping + a VAT/URSSAF payment due). It pre-emptively schedules a partial yield recall **and** offers a strategic supplier an early payment in stablecoin for a 2% dynamic discount → **tx live.** It just turned idle cash into a guaranteed 2% return *and* locked in a key supplier.
5. **Action 3 — React to a shock.** A signal hits (a rate move, or a key customer's payment behavior deteriorating). The agent re-forecasts on the spot and adjusts its plan — the *closed loop* under live conditions.
6. **Close on the contrast.** "A bakery just ran a treasury desk that, two years ago, only a company with a Goldman relationship could. No CFO touched it."

**Why this beats every demo in the room:** real AI reasoning + real money moving onchain + the most boring imaginable customer. Most "AI CFO" demos are a chat box over a spreadsheet. **Ours moves money.**

---

## Build plan — real end-to-end on testnet

**Honest scope note:** "real end-to-end on testnet" for a weekend = **real agent + real onchain settlement + a curated seed dataset.** We can't connect a live bakery's real bank in 48h, and we shouldn't fake the agent or the chain. So: the **brain is real**, the **money movement is real on a testnet**, the **data is a realistic seeded SMB**. Live bank-connect (Plaid / Bridge / GoCardless sandbox) is a **stretch goal**, not the critical path.

### Stack
- **Frontend:** Next.js + Tailwind. Two surfaces: a clean treasury dashboard (cash position, 13-wk forecast, yield position) and the **Agent Activity Feed** (the live reasoning log — the star of the demo).
- **Agent brain:** **Claude (Opus 4.8)** as the CFO reasoning engine, in a tool-calling agent loop (latest, most capable Claude model). Tools:
  `get_cash_position`, `build_forecast`, `sweep_to_yield`, `recall_yield`, `pay_supplier_early`, `offer_dynamic_discount`, `pull_credit_line`, `get_macro_signal`.
- **Forecasting engine:** a *real* but bounded model — 13-week direct-method cash forecast + a lightweight model on AR payment-behavior (probability/timing each receivable actually lands). Real math, not a hardcoded chart. Small and correct.
- **Onchain (the real part):** testnet (**Base Sepolia** recommended), test USDC. A minimal **ERC-4626 yield vault** (or a thin mock) for the sweep + a supplier-payment transfer. **viem/wagmi** for tx + block-explorer links shown live in the UI.
- **Agent wallet (high-value detail):** give the agent its **own smart-contract wallet with on-chain spend policies / guardrails** (account abstraction — session-key/policy module). The AI literally has a wallet it acts from, *within limits the business sets.* This — autonomy *with* programmable guardrails — is what makes a serious jury lean in, and it's the honest answer to "would you trust an AI with your money?"
- **Data:** one richly seeded SMB (Maison Levain) as JSON — bank balances, ~40 AR invoices with realistic aging, ~30 AP bills, supplier list, a VAT/URSSAF obligation calendar.

### Who builds what (3–4 people, parallelized)
- **A — Agent + tools (the brain):** Claude agent loop, tool definitions, the reasoning that produces the demo narrative. *Owns the "wow."*
- **B — Onchain (the rail):** testnet vault + USDC transfers + agent smart wallet w/ spend policy + explorer integration. *Owns credibility.*
- **C — Frontend (the show):** dashboard + Agent Activity Feed + demo-flow choreography. *Owns the polish.*
- **D (or shared) — Forecasting + data:** the 13-week model, AR-behavior model, seeded dataset, the macro/shock signal. *Owns the depth.*

### Timeline (48h)
- **H0–6:** freeze the demo script; scaffold Next.js; deploy vault + mint test USDC; define the 8 agent tools as stubs returning realistic data.
- **H6–18:** make each tool real one by one (forecast → sweep → discount → recall); agent loop produces a coherent narrated plan over the seed data.
- **H18–30:** wire real testnet txs into `sweep_to_yield` / `pay_supplier_early`; agent smart wallet + spend policy; explorer links in UI.
- **H30–42:** Agent Activity Feed UX; choreograph the 90-second flow; the shock/re-forecast moment; visual polish.
- **H42–48:** **rehearse to death.** Pre-fund wallets, cache nothing that can break live, record a fallback. Tighten the pitch.

### Risks & mitigations
- **Live testnet flakiness** → pre-fund + pre-warm; retry logic; a recorded backup of the exact tx flow.
- **Agent goes off-script live** → constrain tool outputs + a "demo mode" seed deterministic enough to be safe while still *running for real*.
- **Scope creep** → bank-connect, multi-SMB, and the credit-line tool are all **stretch**. Critical path: forecast → sweep (real tx) → discount (real tx) → narrate. Protect it.

---

## The 3-minute pitch (if we present)

1. **Cold open (demo, 60s):** the bakery sweeps €62k onchain and defends a cash gap, live. Lead with the money moving.
2. **The insight (30s):** every cash tool stops at the glass because bank rails can't execute. We close the loop because money is now programmable.
3. **The market (30s):** 24M EU SMBs, none with a real CFO, all leaking working capital. Turnkey, 5-min setup, short sales cycle.
4. **The moat (20s):** data flywheel + system-of-record + becoming the best SMB underwriter in Europe.
5. **Why now / why us (20s):** YC's own stablecoin RFS + MiCA + agent capability crossed the line; a Berkeley/Polytechnique team that builds the quant *and* the chain.
6. **Land it:** *"Agicap is a dashboard. YIELD is a CFO."*

---

## Verification — before we walk on stage

1. **Onchain:** sweep + supplier-payment txs visible on the Base Sepolia explorer with the agent's smart-wallet as sender, executed *within* its spend policy. Show a tx that would be *rejected* if over-limit — proves the guardrail is real.
2. **Forecast:** the 13-week number changes correctly when we inject the shock (re-run → a different, defensible plan).
3. **Agent:** the activity feed shows genuine tool calls + reasoning, not a script — verifiable by changing a seed value and watching the plan adapt.
4. **End-to-end:** full 90s run completes ≥5 times consecutively without manual intervention, plus a recorded fallback.

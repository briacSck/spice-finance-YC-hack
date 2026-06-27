import type { Company, FeedItem } from "./types";

// Maison Levain — the hero synthetic client (DEMO.md + API_CONTRACT.md).
// Numbers chosen so the demo math is coherent: 74% of cost is commodities,
// 11% margin today -> 3.3% under the shock, VaR 13.1% -> 2.0% hedged.
export const MAISON_LEVAIN: Company = {
  name: "Maison Levain",
  revenue: 1_400_000,
  cash: 180_000,
  net_margin: 0.11,
  exposures: [
    { commodity: "WEAT", name: "Wheat", amount: 300_000, share_of_revenue: 0.214, vol: 0.3 },
    { commodity: "ENERGY", name: "Energy", amount: 161_000, share_of_revenue: 0.115, vol: 0.45 },
    { commodity: "FATS", name: "Fats", amount: 80_000, share_of_revenue: 0.057, vol: 0.25 },
  ],
};

// Cost-share view (share of TOTAL COST, what the bars/donut show).
export const COST_SHARES = [
  { name: "Wheat", sub: "WEAT · flour", pct: 41, amount: "€300k", color: "var(--green)", bar: "55%" },
  { name: "Energy", sub: "gas + power", pct: 22, amount: "€161k", color: "#5C7A6E", bar: "30%" },
  { name: "Fats", sub: "butter, cream", pct: 11, amount: "€80k", color: "#94A89E", bar: "15%" },
];

export const DONUT = {
  commodityPct: 74,
  segments: [
    { name: "Wheat", sub: "WEAT", pct: 41, color: "var(--green)" },
    { name: "Energy", sub: "gas+power", pct: 22, color: "#5C7A6E" },
    { name: "Fats", sub: "butter", pct: 11, color: "#94A89E" },
    { name: "Labour, rent, other", sub: "", pct: 26, color: "var(--hair2)" },
  ],
};

export const ANALYSIS = {
  scenario: "+38% wheat · +25% gas · next quarter",
  marginToday: 0.11,
  marginShock: 0.033,
  varBefore: 0.131,
  marginAtRisk: "€108k",
  buffer: "~6 wks",
};

export const RECOMMENDATIONS = [
  {
    venue: "Alpaca · options",
    venueColor: "var(--green)",
    title: "Cap the wheat & gas spike",
    body: "Calls on WEAT + UNG ETFs. If inputs spike, the options pay the difference.",
    impact: "↳ neutralises ~80% of the input shock",
  },
  {
    venue: "Escrow · insurance",
    venueColor: "#C97B5E",
    title: "Parametric energy policy",
    body: "Pays out automatically if the energy index crosses a trigger. 24/7, on-chain.",
    impact: "↳ covers the tail the options miss",
  },
  {
    venue: "Aave · yield",
    venueColor: "#5C7A6E",
    title: "Fund it from idle cash",
    body: "Sweep €180k idle into yield to pay the premiums. Recallable on trigger.",
    impact: "↳ premiums self-fund · cash stays liquid",
  },
];

export const RESULT = {
  varAfter: 0.02,
  marginHeld: 0.11,
  peerMargin: 0.033,
  hedgePnl: 107_500,
};

// Venue execution rows (Execution screen agent lanes).
export const HEDGING_VENUES = [
  { n: "Alpaca · options", s: "WEAT / UNG calls", status: "queued" as const, label: "order queued", ref: "id 6f2a…b1", amount: "€3,900", pos: false },
  { n: "Escrow · insurance", s: "energy parametric", status: "settled" as const, label: "payout settled", ref: "0x9c…4e", explorer: true, amount: "+€84,000", pos: true },
];
export const PLACEMENT_VENUES = [
  { n: "Aave · yield", s: "recallable supply", status: "settled" as const, label: "supplied · recalled", ref: "0x21…af", explorer: true, amount: "€180,000", pos: false },
];

// Scripted activity feed — the mock=true deterministic stream (DR4).
// Mirrors the SSE event order; the real run replaces this with /api/run/{id}/events.
export const SCRIPTED_FEED: Omit<FeedItem, "id">[] = [
  { kind: "message", who: "Orchestrator", text: "Margin holds only if I cap wheat & gas and cover the energy tail. Routing to both specialists.", time: "12:04:01" },
  { kind: "tool", who: "Hedging agent", text: "hedge_options(WEAT, calls, Δ≈0.4)", time: "12:04:03" },
  { kind: "exec", who: "Alpaca", text: "Resolved OCC contract · paper order queued, fills Monday.", time: "12:04:05" },
  { kind: "exec", who: "Escrow · testnet", text: "Policy minted. Premium €1,240 paid. Watching the energy oracle.", time: "12:04:11" },
  { kind: "exec", who: "Aave · testnet", text: "€180k idle cash supplied, earning yield to self-fund premiums.", time: "12:04:16" },
  { kind: "trigger", who: "Scenario · trigger", text: "Energy index +27% — crossed. Firing payout + cash recall.", time: "12:05:00" },
  { kind: "exec", who: "Escrow → paid", text: "Parametric payout settled to the bakery wallet. Aave position recalled.", time: "12:05:02" },
];

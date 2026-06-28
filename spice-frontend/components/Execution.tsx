"use client";

import { useEffect, useRef, useState } from "react";

// ---------------------------------------------------------------------------
// Story events — 8-month simulation
//
// Number coherence:
//   Monthly premium  : €1,300  (wheat + gas options, matches ~€1.3k/month in Analyse)
//   7 months × €1,300 = €9,100 total premiums
//   Options payout   : +€33,000 (month 6 price spike settlement)
//   Insurance payout : +€84,000 (month 8 heatwave trigger)
//   Hedging net      : −9,100 + 33,000 + 84,000 = +€107,900 ≈ €108k at risk (Analyse)
//
//   Morpho yield     : €630/month = €180k × 4.2% ÷ 12
//   6 months × €630  = +€3,780 → recall shows €180k + €3,780 = €183,780
// ---------------------------------------------------------------------------

interface StoryEvent {
  month: number;
  kind: "setup" | "roll" | "yield" | "spike" | "optpayout" | "trigger" | "payout" | "recall";
  lane: "hedging" | "placement" | "event";
  title: string;
  detail: string;
  /** signed P&L — positive = gain, negative = cost */
  amount: number;
  /** override the displayed label (e.g. principal return) */
  amountLabel?: string;
}

const MONTHLY_PREMIUM = 1_300;
const MONTHLY_YIELD   = 630;
const OPTIONS_PAYOUT  = 33_000;
const INSURANCE_PAYOUT = 84_000;

const STORY: StoryEvent[] = [
  // ── Month 1: initial setup ───────────────────────────────────────────────
  {
    month: 1, kind: "setup", lane: "hedging",
    title: "Wheat & gas price protection bought",
    detail: "If flour or energy gets more expensive this year, these contracts automatically pay the difference.",
    amount: -MONTHLY_PREMIUM,
  },
  {
    month: 1, kind: "setup", lane: "placement",
    title: "€180,000 idle cash put to work",
    detail: "Your spare cash earns 4.2% a year in a savings vault — fully withdrawable at any time.",
    amount: 0,
  },

  // ── Months 2–5: steady state ──────────────────────────────────────────────
  { month: 2, kind: "roll",  lane: "hedging",   title: "Protection renewed automatically",   detail: "Coverage always stays 12 months ahead — renewed without you lifting a finger.", amount: -MONTHLY_PREMIUM },
  { month: 2, kind: "yield", lane: "placement", title: "Savings interest collected",          detail: "Monthly interest on your €180,000 at 4.2%/year.", amount: MONTHLY_YIELD },

  { month: 3, kind: "roll",  lane: "hedging",   title: "Protection renewed automatically",   detail: "Coverage extended — always 12 months ahead.", amount: -MONTHLY_PREMIUM },
  { month: 3, kind: "yield", lane: "placement", title: "Savings interest collected",          detail: "Monthly interest on your €180,000 at 4.2%/year.", amount: MONTHLY_YIELD },

  { month: 4, kind: "roll",  lane: "hedging",   title: "Protection renewed automatically",   detail: "Coverage extended — always 12 months ahead.", amount: -MONTHLY_PREMIUM },
  { month: 4, kind: "yield", lane: "placement", title: "Savings interest collected",          detail: "Monthly interest on your €180,000 at 4.2%/year.", amount: MONTHLY_YIELD },

  { month: 5, kind: "roll",  lane: "hedging",   title: "Protection renewed automatically",   detail: "Coverage extended — always 12 months ahead.", amount: -MONTHLY_PREMIUM },
  { month: 5, kind: "yield", lane: "placement", title: "Savings interest collected",          detail: "Monthly interest on your €180,000 at 4.2%/year.", amount: MONTHLY_YIELD },

  // ── Month 6: commodity price spike ──────────────────────────────────────
  {
    month: 6, kind: "spike", lane: "event",
    title: "Commodity prices spiked — wheat +38%, gas +25%",
    detail: "Global supply disruption. Bakeries without protection face a sudden margin squeeze.",
    amount: 0,
  },
  {
    month: 6, kind: "optpayout", lane: "hedging",
    title: "Options settled — price difference covered",
    detail: "Your wheat & gas contracts paid the full cost increase automatically. No action needed.",
    amount: OPTIONS_PAYOUT,
  },
  {
    month: 6, kind: "roll", lane: "hedging",
    title: "New coverage bought for the next 12 months",
    detail: "Protection automatically refreshed at the new price level.",
    amount: -MONTHLY_PREMIUM,
  },
  { month: 6, kind: "yield", lane: "placement", title: "Savings interest collected", detail: "Monthly interest on your €180,000 at 4.2%/year.", amount: MONTHLY_YIELD },

  // ── Month 7: back to steady state ────────────────────────────────────────
  { month: 7, kind: "roll",  lane: "hedging",   title: "Protection renewed automatically",   detail: "Coverage extended — always 12 months ahead.", amount: -MONTHLY_PREMIUM },
  { month: 7, kind: "yield", lane: "placement", title: "Savings interest collected",          detail: "Monthly interest on your €180,000 at 4.2%/year.", amount: MONTHLY_YIELD },

  // ── Month 8: heatwave trigger ────────────────────────────────────────────
  {
    month: 8, kind: "trigger", lane: "event",
    title: "Heatwave alert — temperature reached 41°C",
    detail: "The weather sensor crossed the 35°C threshold. Your insurance policy activates automatically.",
    amount: 0,
  },
  {
    month: 8, kind: "payout", lane: "hedging",
    title: "Insurance paid out instantly",
    detail: "€84,000 sent to your account. No paperwork. No adjuster. No waiting.",
    amount: INSURANCE_PAYOUT,
  },
  {
    month: 8, kind: "recall", lane: "placement",
    title: "Savings recalled from the vault",
    detail: "€180,000 + all accumulated interest returned instantly to your account.",
    amount: 0,
    amountLabel: `€${(180_000 + 6 * MONTHLY_YIELD).toLocaleString("en-US")} returned`,
  },
];

// ---------------------------------------------------------------------------
// helpers
// ---------------------------------------------------------------------------

function fmt(n: number) {
  return Math.round(Math.abs(n)).toLocaleString("en-US");
}

function dotColor(lane: StoryEvent["lane"]) {
  if (lane === "hedging")   return "bg-green";
  if (lane === "placement") return "bg-[#5C7A6E]";
  return "bg-terra";
}

function rowBg(kind: StoryEvent["kind"]) {
  if (kind === "trigger")   return "bg-[#FFF0EE]";
  if (kind === "spike")     return "bg-[#FFF6EE]";
  if (kind === "payout")    return "bg-[#EDF7F3]";
  if (kind === "optpayout") return "bg-[#EDF7F3]";
  return "bg-[#F5F5F5]";
}

function titleColor(kind: StoryEvent["kind"]) {
  if (kind === "trigger")   return "text-terra";
  if (kind === "spike")     return "text-[#C25A00]";
  if (kind === "payout")    return "text-green";
  if (kind === "optpayout") return "text-green";
  return "text-ink";
}

// ---------------------------------------------------------------------------
// component
// ---------------------------------------------------------------------------

export function Execution({ run }: { run: boolean }) {
  const [count, setCount]       = useState(0);
  const [triggered, setTriggered] = useState(false);
  const feedRef = useRef<HTMLDivElement>(null);

  // When run=true: animate the story event-by-event.
  // page.tsx passes key={execRun} so the component remounts fresh each visit.
  useEffect(() => {
    if (!run) return;
    setCount(0);
    setTriggered(false);
    let i = 0;
    const id = setInterval(() => {
      i++;
      const ev = STORY[i - 1];
      setCount(i);
      if (ev?.kind === "trigger") setTriggered(true);
      if (i >= STORY.length) clearInterval(id);
    }, 500);
    return () => clearInterval(id);
  }, [run]);

  // Keep the feed scrolled to the latest event
  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: "smooth" });
  }, [count]);

  const shown = STORY.slice(0, count);

  // Compute per-agent P&L from visible events
  let hedgingTotal   = 0;
  let placementTotal = 0;
  for (const e of shown) {
    if (e.lane === "hedging")   hedgingTotal   += e.amount;
    if (e.lane === "placement") placementTotal += e.amount;
  }
  const grandTotal = hedgingTotal + placementTotal;

  return (
    <>
      {/* ── Top banner ──────────────────────────────────────────────────── */}
      <div
        className={`mx-11 mt-2 rounded-[18px] bg-inkdeep px-[34px] py-5 text-[#E8EDE9] transition-opacity duration-700 ${
          triggered ? "opacity-100" : "opacity-55"
        }`}
      >
        <div className="flex items-center gap-10">
          <div className="max-w-[420px]">
            <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">
              {triggered
                ? "Weather insurance settled · on-chain"
                : "Protection active — watching live market & weather data"}
            </div>
            <div className="mt-2 text-[19px] font-semibold leading-[1.35]">
              {triggered
                ? "The heatwave hit. €84,000 paid out automatically — your margin held."
                : "Hedges are live. If commodity prices spike or the weather turns, Spice acts first."}
            </div>
          </div>

          <div className="ml-auto flex gap-12">
            <div>
              <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">
                Your net margin
              </div>
              <div className="mt-2 font-mono text-[28px] font-semibold tracking-tight tnum">
                11.0%
                <span className="ml-2 text-[12px] font-normal text-[#9DBDB1]">
                  vs 3.3% unprotected
                </span>
              </div>
            </div>
            <div>
              <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">
                Total earned
              </div>
              <div
                className={`mt-2 font-mono text-[28px] font-semibold tracking-tight tnum ${
                  grandTotal > 0 ? "text-[#6FCF97]" : "text-[#E8EDE9]"
                }`}
              >
                {grandTotal > 0 ? `+€${fmt(grandTotal)}` : "—"}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── Scrollable content ──────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-11 pb-10 pt-5">

        {/* Agent summary cards */}
        <div className="mb-5 grid grid-cols-2 gap-5">

          {/* Hedging agent */}
          <div className="card px-7 py-5">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-[9px] bg-green text-[14px] font-semibold text-paper">
                H
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-[15px] font-semibold">Price protection agent</div>
                <div className="mt-0.5 text-[12px] text-faint">
                  Options on wheat &amp; gas · weather insurance policy
                </div>
              </div>
              <div
                className={`flex-shrink-0 font-mono text-[20px] font-semibold tnum ${
                  hedgingTotal >= 0 ? "text-green" : "text-terra"
                }`}
              >
                {hedgingTotal >= 0 ? "+" : "−"}€{fmt(hedgingTotal)}
              </div>
            </div>
            <div className="mt-3 text-[12.5px] leading-relaxed text-dim">
              Buys price contracts every month on wheat &amp; gas. If prices spike, the contracts pay the difference. When the wheat &amp; gas prices spiked in month 6, the options settled +€33,000. The heatwave policy added +€84,000 more.
            </div>
          </div>

          {/* Placement agent */}
          <div className="card px-7 py-5">
            <div className="flex items-start gap-3">
              <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-[9px] bg-[#5C7A6E] text-[14px] font-semibold text-paper">
                P
              </div>
              <div className="min-w-0 flex-1">
                <div className="text-[15px] font-semibold">Cash placement agent</div>
                <div className="mt-0.5 text-[12px] text-faint">
                  Savings vault · 4.2% / year · €630/month · withdrawable instantly
                </div>
              </div>
              <div
                className={`flex-shrink-0 font-mono text-[20px] font-semibold tnum ${
                  placementTotal > 0 ? "text-green" : "text-dim"
                }`}
              >
                {placementTotal > 0 ? `+€${fmt(placementTotal)}` : "—"}
              </div>
            </div>
            <div className="mt-3 text-[12.5px] leading-relaxed text-dim">
              Puts your idle €180,000 to work at 4.2%/year. The €630/month interest covers about half the monthly cost of the price protection. Cash is always withdrawable — recalled instantly when needed.
            </div>
          </div>
        </div>

        {/* 8-month activity timeline */}
        <div className="card px-8 py-6">
          <div className="mb-1 flex items-baseline justify-between">
            <div className="label">8-month activity log</div>
            <div className="font-mono text-[11px] text-faint">
              everything done automatically — no human in the loop
            </div>
          </div>
          <div className="mb-5 text-[12.5px] text-faint">
            Every action Spice took on behalf of Maison Levain, month by month
          </div>

          <div ref={feedRef} className="overflow-y-auto" style={{ maxHeight: 296 }}>
            {count === 0 && (
              <div className="py-8 text-center text-[12.5px] text-faint">
                Starting 8-month simulation…
              </div>
            )}

            {shown.map((e, idx) => {
              const prevMonth  = idx > 0 ? shown[idx - 1].month : null;
              const isNewMonth = e.month !== prevMonth;

              return (
                <div key={idx}>
                  {isNewMonth && (
                    <div className={`flex items-center gap-3 ${idx > 0 ? "mt-4" : ""} mb-2`}>
                      <span className="flex-shrink-0 text-[11px] font-semibold uppercase tracking-label text-faint">
                        Month {e.month}
                      </span>
                      {e.kind === "trigger" && (
                        <span className="flex-shrink-0 rounded-full bg-terra px-2 py-0.5 text-[9px] font-semibold uppercase tracking-label text-paper">
                          Alert
                        </span>
                      )}
                      {e.kind === "spike" && (
                        <span className="flex-shrink-0 rounded-full bg-[#C25A00] px-2 py-0.5 text-[9px] font-semibold uppercase tracking-label text-paper">
                          Price spike
                        </span>
                      )}
                      <div className="flex-1 border-t border-hair2" />
                    </div>
                  )}

                  <div
                    className={`mb-1.5 flex items-center gap-4 rounded-[10px] px-4 py-2.5 ${rowBg(e.kind)}`}
                  >
                    <span className={`h-2 w-2 flex-shrink-0 rounded-full ${dotColor(e.lane)}`} />
                    <div className="min-w-0 flex-1">
                      <div className={`text-[13px] font-semibold ${titleColor(e.kind)}`}>
                        {e.title}
                      </div>
                      <div className="mt-0.5 text-[11.5px] text-dim">{e.detail}</div>
                    </div>
                    {(e.amount !== 0 || e.amountLabel) && (
                      <div
                        className={`flex-shrink-0 font-mono text-[13px] font-semibold tnum ${
                          e.amountLabel
                            ? "text-green"
                            : e.amount > 0
                              ? "text-green"
                              : "text-terra"
                        }`}
                      >
                        {e.amountLabel
                          ? e.amountLabel
                          : `${e.amount > 0 ? "+" : "−"}€${fmt(e.amount)}`}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Result card — appears once insurance triggers */}
        {triggered && (
          <div className="mt-5 card px-8 py-5">
            <div className="label mb-2">The bottom line</div>
            <div className="text-[16px] font-medium leading-relaxed text-ink">
              When wheat &amp; gas prices spiked in month 6, the options paid{" "}
              <span className="font-semibold text-green">+€33,000</span> automatically. When the
              heatwave hit in month 8, the insurance added{" "}
              <span className="font-semibold text-green">+€84,000</span> — covering the exact{" "}
              <span className="font-semibold">€108k of margin</span> that was at risk. Maison
              Levain kept its{" "}
              <span className="font-semibold text-green">11%</span> margin while an unprotected
              bakery fell to{" "}
              <span className="font-semibold text-terra">3.3%</span>.
            </div>
          </div>
        )}
      </div>
    </>
  );
}

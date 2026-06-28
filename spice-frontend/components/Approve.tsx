"use client";

import { useEffect, useRef, useState } from "react";
import { approveProposal, createProgram, getProposals } from "@/lib/api";
import { ANALYSIS } from "@/lib/mockData";
import { useCountUp } from "@/lib/useCountUp";
import type { HedgeProposal } from "@/lib/types";

/**
 * Merged analysis + approvals screen. Left = the margin-collapse analysis (the
 * commodity book lives on the dashboard, not here). Right = the real hedge
 * proposals as a checklist (all checked by default) with one big green button
 * that approves the checked proposals and routes straight to execution.
 */
export function Approve({ run, onExecute }: { run: boolean; onExecute: () => void }) {
  const [proposals, setProposals] = useState<HedgeProposal[]>([]);
  const [checked, setChecked] = useState<Record<string, boolean>>({});
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const programRef = useRef<string | null>(null);
  const creatingRef = useRef(false);

  const today = ANALYSIS.marginToday * 100;
  const shocked = useCountUp(ANALYSIS.marginShock * 100, run, 1100, today);

  // Create the program + load the real proposals once on mount.
  useEffect(() => {
    if (creatingRef.current) return;
    creatingRef.current = true;
    createProgram()
      .then(async (id) => {
        programRef.current = id;
        const props = await getProposals(id);
        setProposals(props);
        setChecked(Object.fromEntries(props.map((p) => [p.ticker, true])));
      })
      .catch((e) => setError(String(e)));
  }, []);

  const selected = proposals.filter((p) => checked[p.ticker]);

  async function handleApproveAll() {
    const id = programRef.current;
    if (!id || busy || selected.length === 0) return;
    setBusy(true);
    setError(null);
    try {
      // Approve concurrently — fast now that the ladder build is non-blocking.
      await Promise.all(selected.map((p) => approveProposal(id, p.ticker)));
      onExecute();
    } catch (e) {
      setError(String(e));
      setBusy(false);
    }
  }

  return (
    <>
      {/* kicker */}
      <div className="flex items-end justify-between px-11 pb-5 pt-2">
        <h1 className="max-w-[820px] text-[27px] font-semibold leading-[1.2] tracking-tight">
          If prices spike like in 2022, your margin{" "}
          <b className="font-semibold text-terra">nearly disappears.</b>{" "}
          <span className="text-green">One click protects you.</span>
        </h1>
        <div className="font-mono text-[12.5px] text-faint">{ANALYSIS.scenario}</div>
      </div>

      {error && <div className="mx-11 mb-3 text-[12.5px] text-terra">{error}</div>}

      <div className="grid min-h-0 flex-1 grid-cols-[1fr_440px] gap-[30px] px-11 pb-9">
        {/* LEFT: scenario context + margin collapse */}
        <div className="card relative flex flex-col px-8 py-[30px]">
          {/* Scenario callout */}
          <div className="mb-5 rounded-[10px] bg-[#FFF6EE] px-4 py-3">
            <div className="text-[10.5px] font-semibold uppercase tracking-label text-terra">
              Price spike scenario — what Spice is stress-testing
            </div>
            <div className="mt-1.5 flex items-center gap-6">
              <div>
                <span className="font-mono text-[18px] font-semibold text-terra">+38%</span>
                <span className="ml-2 text-[12.5px] text-dim">wheat prices</span>
              </div>
              <div className="h-5 w-px bg-hair2" />
              <div>
                <span className="font-mono text-[18px] font-semibold text-terra">+25%</span>
                <span className="ml-2 text-[12.5px] text-dim">gas prices</span>
              </div>
              <div className="h-5 w-px bg-hair2" />
              <div className="text-[12px] text-dim">
                This happened in 2022. <br />It can happen again next quarter.
              </div>
            </div>
          </div>
          <div className="label">What it does to your margin</div>
          <div className="flex flex-1 items-center justify-center gap-2">
            <div className="flex-1 text-center">
              <div className="text-[11px] uppercase tracking-label text-faint">Today</div>
              <div className="mt-3 font-mono text-[64px] font-semibold leading-none tracking-tight text-green tnum">
                {today.toFixed(1)}%
              </div>
              <div className="mt-[14px] text-[12.5px] text-dim">healthy bakery</div>
            </div>
            <div className="flex w-[92px] flex-col items-center gap-2.5 text-terra">
              <div className="text-[30px] font-light text-faint">→</div>
              <div className="text-[13px] font-semibold">−7.7 pts</div>
            </div>
            <div className="flex-1 text-center">
              <div className="text-[11px] uppercase tracking-label text-faint">Q+1 · unhedged</div>
              <div className="mt-3 font-mono text-[64px] font-semibold leading-none tracking-tight text-terra tnum">
                {shocked.toFixed(1)}%
              </div>
              <div className="mt-[14px] text-[12.5px] text-dim">two thin quarters from red</div>
            </div>
          </div>
          <div className="mt-auto flex border-t border-hair2 pt-[22px]">
            {[
              { k: "Value at Risk · 95%", v: "13.1%", bad: true },
              { k: "Margin € at risk", v: ANALYSIS.marginAtRisk, bad: true },
              { k: "Cash buffer", v: ANALYSIS.buffer, bad: false },
            ].map((s, i) => (
              <div key={s.k} className={`flex-1 text-center ${i < 2 ? "border-r border-hair2" : ""}`}>
                <div className="text-[10.5px] uppercase tracking-label text-faint">{s.k}</div>
                <div className={`mt-2 font-mono text-[21px] font-semibold tnum ${s.bad ? "text-terra" : ""}`}>{s.v}</div>
              </div>
            ))}
          </div>
        </div>

        {/* RIGHT: proposal checklist + big green button */}
        <div className="card flex min-h-0 flex-col px-7 py-[26px]">
          <div className="label mb-[6px]">Protect against those risks</div>
          <div className="mb-[14px] text-[12.5px] leading-relaxed text-dim">
            Lock in prices on wheat &amp; gas. Add a weather policy for extreme events.
            Put your €180k idle cash to work — it earns enough to cover the cost.
          </div>
          <div className="flex-1 overflow-y-auto pr-1">
            {proposals.length === 0 && (
              <div className="text-[12.5px] text-faint">{error ? "Could not load proposals." : "Loading proposals…"}</div>
            )}
            {proposals.map((p) => {
              const on = !!checked[p.ticker];
              return (
                <button
                  key={p.proposal_id}
                  onClick={() => setChecked((c) => ({ ...c, [p.ticker]: !c[p.ticker] }))}
                  className={`mb-3 flex w-full items-start gap-3 rounded-[10px] border px-4 py-3 text-left transition-colors ${
                    on ? "border-green bg-panel" : "border-hair2 hover:border-dim"
                  }`}
                >
                  <span
                    className={`mt-0.5 flex h-[18px] w-[18px] flex-shrink-0 items-center justify-center rounded-[5px] border text-[11px] font-bold ${
                      on ? "border-green bg-green text-paper" : "border-hair2 text-transparent"
                    }`}
                  >
                    ✓
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="flex items-baseline gap-2">
                      <span className="text-[10px] font-semibold uppercase tracking-label text-faint">{p.ticker}</span>
                      <span className="text-[14px] font-semibold">{p.underlying}</span>
                    </span>
                    <span className="mt-1 block text-[12px] leading-snug text-dim">{p.explanation}</span>
                    <span className="mt-1.5 block font-mono text-[11.5px] text-faint">
                      {p.kind === "escrow"
                        ? `premium ~€${Math.round(p.monthly_notional).toLocaleString()} · one-time`
                        : `~€${Math.round(p.monthly_notional / 100) / 10}k/month`}
                    </span>
                  </span>
                </button>
              );
            })}

            {/* Morpho placement — always included, funds the cost of protection */}
            <div className="mb-3 flex items-start gap-3 rounded-[10px] border border-[#5C7A6E] bg-panel px-4 py-3">
              <span className="mt-0.5 flex h-[18px] w-[18px] flex-shrink-0 items-center justify-center rounded-[5px] border border-[#5C7A6E] bg-[#5C7A6E] text-[11px] font-bold text-paper">
                ✓
              </span>
              <span className="min-w-0 flex-1">
                <span className="flex items-baseline gap-2">
                  <span className="text-[10px] font-semibold uppercase tracking-label text-faint">MORPHO</span>
                  <span className="text-[14px] font-semibold">Invest idle cash to fund the costs</span>
                  <span className="ml-auto flex-shrink-0 rounded-full bg-hair2 px-2 py-0.5 text-[9px] font-semibold uppercase tracking-label text-faint">
                    auto
                  </span>
                </span>
                <span className="mt-1 block text-[12px] leading-snug text-dim">
                  €180,000 earns 4.2%/year in a savings vault — the interest covers the monthly cost of price protection. Recalled instantly if any trigger fires.
                </span>
                <span className="mt-1.5 block font-mono text-[11.5px] text-faint">
                  +€630/month income · self-funded · fully liquid
                </span>
              </span>
            </div>
          </div>
          <button
            className="btn-primary mt-4 py-3 text-[15px]"
            disabled={busy || selected.length === 0}
            onClick={handleApproveAll}
          >
            {busy
              ? "Setting up protection…"
              : `Protect my prices & invest spare cash`}{" "}
            <span className="font-normal opacity-75">→</span>
          </button>
        </div>
      </div>
    </>
  );
}

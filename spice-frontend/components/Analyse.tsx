"use client";

import { ANALYSIS, DONUT, RECOMMENDATIONS } from "@/lib/mockData";
import { useCountUp } from "@/lib/useCountUp";

// Build the conic-gradient string for the exposure donut from segments.
function donutGradient() {
  let acc = 0;
  const stops = DONUT.segments.map((s) => {
    const start = acc;
    acc += s.pct;
    return `${s.color} ${start}% ${acc}%`;
  });
  return `conic-gradient(${stops.join(", ")})`;
}

export function Analyse({ onExecute, run }: { onExecute: () => void; run: boolean }) {
  // DR4: today holds at 11.0%, then drops to 3.3% under the shock.
  const today = ANALYSIS.marginToday * 100;
  const shocked = useCountUp(ANALYSIS.marginShock * 100, run, 1100, today);

  return (
    <>
      {/* kicker */}
      <div className="flex items-end justify-between px-11 pb-5 pt-2">
        <h1 className="max-w-[760px] text-[27px] font-semibold leading-[1.2] tracking-tight">
          Forecast a wheat &amp; gas spike, and Maison Levain&apos;s margin{" "}
          <b className="font-semibold text-terra">nearly disappears.</b>
        </h1>
        <div className="font-mono text-[12.5px] text-faint">{ANALYSIS.scenario}</div>
      </div>

      <div className="grid flex-1 grid-cols-[300px_1fr_400px] gap-[30px] px-11 pb-9">
        {/* exposure donut */}
        <div className="card flex flex-col items-center px-8 py-[30px]">
          <div className="label self-start">Commodity book</div>
          <div className="relative m-auto h-[188px] w-[188px] rounded-full" style={{ background: donutGradient() }}>
            <div className="absolute inset-[22px] rounded-full bg-panel" />
            <div className="absolute inset-0 z-[2] flex flex-col items-center justify-center">
              <div className="font-mono text-[32px] font-semibold tracking-tight tnum">{DONUT.commodityPct}%</div>
              <div className="mt-[3px] text-center text-[10.5px] uppercase tracking-label text-faint">
                commodity
                <br />
                cost
              </div>
            </div>
          </div>
          <div className="mt-7 flex w-full flex-col gap-[14px]">
            {DONUT.segments.map((s) => (
              <div key={s.name} className="flex items-center gap-[11px] text-[13.5px]">
                <span className="h-[9px] w-[9px] rounded-[3px]" style={{ background: s.color }} />
                <span className="flex-1">
                  {s.name}
                  {s.sub && <small className="ml-1.5 text-[11.5px] text-faint">{s.sub}</small>}
                </span>
                <span className="font-mono font-medium text-dim tnum">{s.pct}%</span>
              </div>
            ))}
          </div>
        </div>

        {/* margin collapse hero */}
        <div className="card relative flex flex-col px-8 py-[30px]">
          <div className="label">Net margin under the shock</div>
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

        {/* recommendations */}
        <div className="card flex flex-col px-8 py-[30px]">
          <div className="label mb-[18px]">Recommendations · Spice</div>
          <div className="mb-1.5 text-[17px] font-semibold tracking-tight">A 3-venue hedge that holds the margin</div>
          <div className="mb-6 text-[12.5px] leading-relaxed text-dim">
            Sized for a €1.4M bakery, not a treasury desk. Funded from idle cash, fully recallable.
          </div>
          {RECOMMENDATIONS.map((r, i) => (
            <div key={r.title} className={`mb-5 pb-5 ${i < RECOMMENDATIONS.length - 1 ? "border-b border-hair2" : ""}`}>
              <div className="mb-2 flex items-baseline gap-2.5">
                <span className="text-[10px] font-semibold uppercase tracking-label" style={{ color: r.venueColor }}>
                  {r.venue}
                </span>
                <span className="text-[14.5px] font-semibold">{r.title}</span>
              </div>
              <div className="text-[12.5px] leading-relaxed text-dim">{r.body}</div>
              <div className="mt-2 text-[12.5px] font-medium text-green">{r.impact}</div>
            </div>
          ))}
          <button className="btn-primary mt-1.5" onClick={onExecute}>
            Execute across 3 venues <span className="font-normal opacity-75">→ Execution</span>
          </button>
        </div>
      </div>
    </>
  );
}

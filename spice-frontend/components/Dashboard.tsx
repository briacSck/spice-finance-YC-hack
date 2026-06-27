"use client";

import { COST_SHARES } from "@/lib/mockData";

const STATUS_ROWS = [
  { dot: "bg-green", t: "Books ingested", s: "cost ledger · cash position", time: "done" },
  { dot: "bg-green", t: "Exposure mapped", s: "invoices → commodities", time: "done" },
  { dot: "bg-terra", t: "Forecast + VaR", s: "ready to run", time: "queued" },
  { dot: "bg-faint", t: "Hedge execution", s: "3 venues standing by", time: "idle" },
];

export function Dashboard({ onRun }: { onRun: () => void }) {
  return (
    <div className="flex flex-1 flex-col gap-[30px] px-11 pt-[14px]">
      {/* client header */}
      <div className="mt-[18px] flex items-end justify-between">
        <div>
          <div className="label">Client · synthetic</div>
          <h1 className="mt-[10px] text-[36px] font-semibold tracking-tight">Maison Levain</h1>
          <div className="mt-[11px] flex items-center gap-4 text-[13.5px] text-dim">
            <span>Bakery · Lyon</span>
            <span className="text-faint">·</span>
            <span>€1.4M revenue</span>
            <span className="text-faint">·</span>
            <span className="font-mono text-faint">books synced 30s ago</span>
          </div>
        </div>
        <div className="flex items-center gap-[11px] text-[13.5px] font-medium text-terra">
          <span className="h-[7px] w-[7px] rounded-full bg-terra" />
          Unhedged commodity book detected
        </div>
      </div>

      {/* KPI band — one card, hairline columns (NOT a 2x2 grid) */}
      <div className="card grid grid-cols-4 py-[6px]">
        {[
          { k: "Revenue", v: "€1.40M", d: "FY trailing", t: false },
          { k: "Cash on hand", v: "€180k", d: "idle · deployable", t: false },
          { k: "Net margin", v: "11.0%", d: "exposed to input shock", t: true },
          { k: "Hidden exposure", v: "74%", d: "of costs are commodities", t: true },
        ].map((kpi, i) => (
          <div key={kpi.k} className={`px-[30px] py-[26px] ${i < 3 ? "border-r border-hair2" : ""}`}>
            <div className="label">{kpi.k}</div>
            <div className="mt-[14px] font-mono text-[34px] font-semibold leading-none tracking-tight tnum">
              {kpi.v}
            </div>
            <div className={`mt-[11px] text-[12.5px] ${kpi.t ? "text-terra" : "text-dim"}`}>{kpi.d}</div>
          </div>
        ))}
      </div>

      {/* lower */}
      <div className="grid flex-1 grid-cols-[1.6fr_1fr] gap-[30px] pb-[34px]">
        {/* commodity book */}
        <div className="card flex flex-col px-8 py-7">
          <h2 className="text-[15px] font-semibold tracking-tight">The commodity book inside the bakery</h2>
          <div className="mb-6 mt-1 text-[12.5px] text-faint">
            Cost structure, re-expressed as what it actually trades
          </div>
          {COST_SHARES.map((c) => (
            <div key={c.name} className="mb-[22px] flex items-center gap-5 last:mb-0">
              <div className="w-[108px]">
                <div className="text-[14px] font-medium">{c.name}</div>
                <div className="mt-0.5 text-[11.5px] text-faint">{c.sub}</div>
              </div>
              <div className="h-2 flex-1 overflow-hidden rounded-full bg-hair2">
                <div className="h-full rounded-full" style={{ width: c.bar, background: c.color }} />
              </div>
              <div className="w-[96px] text-right font-mono text-[13.5px] text-dim tnum">
                <b className="mr-2 font-semibold text-ink">{c.pct}%</b>
                {c.amount}
              </div>
            </div>
          ))}
          <div className="mt-auto flex items-center justify-between pt-6 text-[12.5px] text-dim">
            <span>3 tradeable commodities found inside ordinary invoices</span>
            <span className="font-medium text-terra">0% hedged</span>
          </div>
        </div>

        {/* agent status */}
        <div className="card flex flex-col px-8 py-7">
          <h2 className="text-[15px] font-semibold tracking-tight">Agent status</h2>
          <div className="mb-4 mt-1 text-[12.5px] text-faint">Autonomous, end to end</div>
          <div className="flex flex-col">
            {STATUS_ROWS.map((r) => (
              <div key={r.t} className="flex items-center gap-[14px] border-b border-hair2 py-4 last:border-0">
                <span className={`h-[7px] w-[7px] flex-shrink-0 rounded-full ${r.dot}`} />
                <div className="flex-1 text-[14px] font-medium">
                  {r.t}
                  <small className="mt-0.5 block text-[11.5px] font-normal text-faint">{r.s}</small>
                </div>
                <div className="text-[11px] uppercase tracking-wide text-faint">{r.time}</div>
              </div>
            ))}
          </div>
          <div className="mt-auto pt-6">
            <button className="btn-primary" onClick={onRun}>
              Run risk analysis →
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

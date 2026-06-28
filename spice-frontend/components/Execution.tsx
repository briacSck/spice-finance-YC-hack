"use client";

import { useEffect, useRef, useState } from "react";
import { HEDGING_VENUES, PLACEMENT_VENUES, RESULT, SCRIPTED_FEED } from "@/lib/mockData";
import { USE_MOCK } from "@/lib/api";
import { useRun } from "@/lib/useRun";
import type { ExecutionEvent, FeedItem } from "@/lib/types";

interface VenueRowData {
  n: string;
  s: string;
  status: "queued" | "accepted" | "settled";
  label: string;
  ref: string;
  amount: string;
  pos: boolean;
  explorer?: boolean;
}

function VenueRow({ v }: { v: VenueRowData }) {
  const settled = v.status === "settled";
  return (
    <div className="flex items-center gap-[18px] border-t border-hair2 py-[10px]">
      <div className="w-[150px]">
        <div className="text-[14px] font-medium">{v.n}</div>
        <div className="mt-0.5 text-[11.5px] text-faint">{v.s}</div>
      </div>
      <div className="flex flex-1 items-center gap-3">
        <span className={`flex items-center gap-[7px] text-[12px] font-medium ${settled ? "text-green" : "text-dim"}`}>
          <span className={`h-1.5 w-1.5 rounded-full ${settled ? "bg-green" : "bg-faint"}`} />
          {v.label}
        </span>
        <span className="font-mono text-[11.5px] text-faint">
          {v.ref}
          {v.explorer && (
            <>
              {" · "}
              <a className="text-green no-underline" href="#">
                explorer ↗
              </a>
            </>
          )}
        </span>
      </div>
      <div className={`w-[90px] text-right font-mono text-[14px] tnum ${v.pos ? "text-green" : ""}`}>{v.amount}</div>
    </div>
  );
}

// Map a live execution event onto the UI's venue-row shape + its lane.
const VENUE_META: Record<string, { name: string; lane: "hedging" | "placement" }> = {
  alpaca: { name: "Alpaca · options", lane: "hedging" },
  escrow: { name: "Insurance · parametric", lane: "hedging" },
  morpho: { name: "Morpho · yield", lane: "placement" },
};

function execToRow(e: ExecutionEvent): VenueRowData & { lane: "hedging" | "placement" } {
  const meta = VENUE_META[e.venue] ?? { name: e.venue, lane: "hedging" as const };
  const val = e.pnl ?? e.amount ?? 0;
  const sign = e.pnl && e.pnl > 0 ? "+" : "";
  return {
    n: meta.name,
    lane: meta.lane,
    s: e.action,
    status: e.status,
    label: e.status === "settled" ? "settled" : "accepted",
    ref: e.ref,
    amount: val ? `${sign}€${Math.round(val).toLocaleString("en-US")}` : "—",
    pos: !!e.pnl && e.pnl > 0,
    explorer: !!e.explorer_url,
  };
}

export function Execution({ run }: { run: boolean }) {
  // Live SSE run (no-op when USE_MOCK — the scripted path below drives the demo).
  const live = useRun(run, false);

  // DR4 (mock): type the scripted feed in event-by-event.
  const [shown, setShown] = useState(run ? 0 : SCRIPTED_FEED.length);
  const feedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!run || !USE_MOCK) return;
    setShown(0);
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setShown(i);
      if (i >= SCRIPTED_FEED.length) clearInterval(id);
    }, 650);
    return () => clearInterval(id);
  }, [run]);

  // Feed items: scripted (mock) or live SSE.
  const feedItems: Array<Omit<FeedItem, "id">> = USE_MOCK ? SCRIPTED_FEED.slice(0, shown) : live.feed;

  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: "smooth" });
  }, [feedItems.length]);

  // Venue lanes + banner: mock constants, or derived from live executions / done.
  const liveRows = live.executions.map(execToRow);
  const hedgingVenues: VenueRowData[] = USE_MOCK ? HEDGING_VENUES : liveRows.filter((r) => r.lane === "hedging");
  const placementVenues: VenueRowData[] = USE_MOCK ? PLACEMENT_VENUES : liveRows.filter((r) => r.lane === "placement");

  const varAfter = USE_MOCK ? RESULT.varAfter : live.analysis?.var_after ?? RESULT.varAfter;
  const marginHeld = USE_MOCK ? RESULT.marginHeld : live.done?.margin_with_hedge ?? RESULT.marginHeld;
  const hedgePnl = USE_MOCK ? RESULT.hedgePnl : live.done?.hedge_pnl ?? RESULT.hedgePnl;

  const nodeColor = (kind: string) =>
    kind === "exec"
      ? "border-green bg-green"
      : kind === "trigger"
        ? "border-terra bg-terra"
        : "border-hair bg-panel";
  const whoColor = (kind: string) =>
    kind === "tool" ? "text-dim font-medium" : kind === "trigger" ? "text-terra" : kind === "exec" ? "text-green" : "";

  return (
    <>
      {/* CLIMAX banner — deep ink, restrained */}
      <div className="relative mx-11 mt-2 flex items-center gap-10 rounded-[18px] bg-inkdeep px-[34px] py-[18px] text-[#E8EDE9]">
        <div className="absolute right-7 top-5 flex items-center gap-2 text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">
          <span className="live-dot h-[7px] w-[7px] rounded-full bg-[#46C795]" />
          Live · testnet settled
        </div>
        <div className="max-w-[330px]">
          <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">The hedge paid out</div>
          <div className="mt-2.5 text-[20px] font-semibold leading-[1.3]">
            Energy crossed the trigger. The policy settled on-chain — no one had to approve it.
          </div>
        </div>
        <div className="ml-auto flex gap-12">
          <div>
            <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">Value at Risk · 95%</div>
            <div className="mt-2 font-mono text-[30px] font-semibold tracking-tight tnum">
              <span className="mr-2.5 text-[19px] font-normal text-[#6E8C80] line-through">13.1%</span>
              {(varAfter * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">Net margin · held</div>
            <div className="mt-2 font-mono text-[30px] font-semibold tracking-tight tnum">
              {(marginHeld * 100).toFixed(1)}%
              <span className="ml-[7px] text-[12.5px] font-normal text-[#9DBDB1]">peer 3.3%</span>
            </div>
          </div>
          <div>
            <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">Hedge P&amp;L</div>
            <div className="mt-2 font-mono text-[30px] font-semibold tracking-tight text-greenon tnum">
              +€{(hedgePnl / 1000).toFixed(1)}k
            </div>
          </div>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-[420px_1fr] gap-[30px] px-11 pb-24 pt-[18px]">
        {/* activity feed */}
        <div className="card flex min-h-0 flex-col">
          <div className="flex items-baseline justify-between px-7 pb-[18px] pt-[22px]">
            <span className="label">Agent activity</span>
            <span className="font-mono text-[11px] text-faint">real tool calls</span>
          </div>
          <div ref={feedRef} className="relative flex-1 overflow-hidden px-7 pb-[18px]">
            <div className="absolute bottom-[18px] left-[34px] top-0 w-px bg-hair" />
            {feedItems.map((e, i) => (
              <div key={i} className="ev-in relative flex gap-4 pb-[15px]">
                <span className={`z-[2] mt-0.5 h-[13px] w-[13px] flex-shrink-0 rounded-full border-[1.5px] ${nodeColor(e.kind)}`} />
                <div className="flex-1">
                  <div className={`text-[12.5px] font-semibold ${whoColor(e.kind)}`}>{e.who}</div>
                  {e.kind === "tool" ? (
                    <div className="mt-[3px] font-mono text-[12px] text-dim">{e.text}</div>
                  ) : (
                    <div className="mt-[3px] text-[13px] leading-snug text-ink">{e.text}</div>
                  )}
                  <div className="mt-[3px] font-mono text-[10px] text-faint">{e.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* agent lanes + result */}
        <div className="flex min-h-0 flex-col gap-3">
          <div className="card px-[30px] py-4">
            <div className="mb-3 flex items-center gap-[14px]">
              <div className="flex h-8 w-8 items-center justify-center rounded-[9px] bg-green text-[13px] font-semibold text-paper">H</div>
              <div className="text-[15.5px] font-semibold">
                Hedging agent
                <small className="mt-0.5 block text-[12px] font-normal text-faint">caps the spike · covers the tail</small>
              </div>
              <div className="ml-auto flex items-center gap-2 text-[12px] text-dim">
                <span className="h-1.5 w-1.5 rounded-full bg-green" />
                {hedgingVenues.length} venues
              </div>
            </div>
            {hedgingVenues.map((v) => (
              <VenueRow key={v.n} v={v} />
            ))}
          </div>

          <div className="card px-[30px] py-4">
            <div className="mb-3 flex items-center gap-[14px]">
              <div className="flex h-8 w-8 items-center justify-center rounded-[9px] bg-[#5C7A6E] text-[13px] font-semibold text-paper">P</div>
              <div className="text-[15.5px] font-semibold">
                Placement agent
                <small className="mt-0.5 block text-[12px] font-normal text-faint">funds the hedge from idle cash</small>
              </div>
              <div className="ml-auto flex items-center gap-2 text-[12px] text-dim">
                <span className="h-1.5 w-1.5 rounded-full bg-green" />
                {placementVenues.length} venue
              </div>
            </div>
            {placementVenues.map((v) => (
              <VenueRow key={v.n} v={v} />
            ))}
          </div>

          <div className="card flex flex-1 flex-col justify-center px-[30px] py-4">
            <div className="label">The result</div>
            <div className="mt-2.5 max-w-[600px] text-[16px] font-medium leading-snug text-ink">
              The hedge was in place weeks before the spike. When energy crossed the trigger it{" "}
              <b className="font-semibold">paid out €84k on its own</b> — Maison Levain kept its{" "}
              <span className="text-green">11%</span> margin while an unhedged bakery fell to{" "}
              <span className="text-terra">3.3%</span>.
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

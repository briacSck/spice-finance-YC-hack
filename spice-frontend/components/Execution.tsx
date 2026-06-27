"use client";

import { useEffect, useRef, useState } from "react";
import { HEDGING_VENUES, PLACEMENT_VENUES, RESULT, SCRIPTED_FEED } from "@/lib/mockData";

type Venue = (typeof HEDGING_VENUES)[number];

function VenueRow({ v }: { v: Venue }) {
  const settled = v.status === "settled";
  return (
    <div className="flex items-center gap-[18px] border-t border-hair2 py-[14px]">
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
          {"explorer" in v && v.explorer && (
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

export function Execution({ run }: { run: boolean }) {
  // DR4: type the feed in event-by-event. Mock timing; swap for SSE via lib/api subscribeToRun.
  const [shown, setShown] = useState(run ? 0 : SCRIPTED_FEED.length);
  const feedRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!run) return;
    setShown(0);
    let i = 0;
    const id = setInterval(() => {
      i += 1;
      setShown(i);
      if (i >= SCRIPTED_FEED.length) clearInterval(id);
    }, 650);
    return () => clearInterval(id);
  }, [run]);

  useEffect(() => {
    feedRef.current?.scrollTo({ top: feedRef.current.scrollHeight, behavior: "smooth" });
  }, [shown]);

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
      <div className="relative mx-11 mt-2 flex items-center gap-10 rounded-[18px] bg-inkdeep px-[34px] py-[26px] text-[#E8EDE9]">
        <div className="absolute right-7 top-5 flex items-center gap-2 text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">
          <span className="live-dot h-[7px] w-[7px] rounded-full bg-[#46C795]" />
          Live · testnet settled
        </div>
        <div className="max-w-[330px]">
          <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">The hedge just paid</div>
          <div className="mt-2.5 text-[20px] font-semibold leading-[1.3]">
            Energy index crossed. Spice&apos;s protection paid out on-chain.
          </div>
        </div>
        <div className="ml-auto flex gap-12">
          <div>
            <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">Value at Risk · 95%</div>
            <div className="mt-2 font-mono text-[30px] font-semibold tracking-tight tnum">
              <span className="mr-2.5 text-[19px] font-normal text-[#6E8C80] line-through">13.1%</span>
              {(RESULT.varAfter * 100).toFixed(1)}%
            </div>
          </div>
          <div>
            <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">Net margin · held</div>
            <div className="mt-2 font-mono text-[30px] font-semibold tracking-tight tnum">
              {(RESULT.marginHeld * 100).toFixed(1)}%
              <span className="ml-[7px] text-[12.5px] font-normal text-[#9DBDB1]">peer 3.3%</span>
            </div>
          </div>
          <div>
            <div className="text-[10.5px] font-medium uppercase tracking-label text-[#7FB7A2]">Hedge P&amp;L</div>
            <div className="mt-2 font-mono text-[30px] font-semibold tracking-tight text-greenon tnum">
              +€107.5k
            </div>
          </div>
        </div>
      </div>

      <div className="grid min-h-0 flex-1 grid-cols-[420px_1fr] gap-[30px] px-11 pb-9 pt-[26px]">
        {/* activity feed */}
        <div className="card flex min-h-0 flex-col">
          <div className="flex items-baseline justify-between px-7 pb-[18px] pt-[22px]">
            <span className="label">Agent activity</span>
            <span className="font-mono text-[11px] text-faint">real tool calls</span>
          </div>
          <div ref={feedRef} className="relative flex-1 overflow-hidden px-7 pb-[18px]">
            <div className="absolute bottom-[18px] left-[34px] top-0 w-px bg-hair" />
            {SCRIPTED_FEED.slice(0, shown).map((e, i) => (
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
        <div className="flex min-h-0 flex-col gap-6">
          <div className="card px-[30px] py-6">
            <div className="mb-[18px] flex items-center gap-[14px]">
              <div className="flex h-8 w-8 items-center justify-center rounded-[9px] bg-green text-[13px] font-semibold text-paper">H</div>
              <div className="text-[15.5px] font-semibold">
                Hedging agent
                <small className="mt-0.5 block text-[12px] font-normal text-faint">caps the spike · covers the tail</small>
              </div>
              <div className="ml-auto flex items-center gap-2 text-[12px] text-dim">
                <span className="h-1.5 w-1.5 rounded-full bg-green" />2 venues
              </div>
            </div>
            {HEDGING_VENUES.map((v) => (
              <VenueRow key={v.n} v={v} />
            ))}
          </div>

          <div className="card px-[30px] py-6">
            <div className="mb-[18px] flex items-center gap-[14px]">
              <div className="flex h-8 w-8 items-center justify-center rounded-[9px] bg-[#5C7A6E] text-[13px] font-semibold text-paper">P</div>
              <div className="text-[15.5px] font-semibold">
                Placement agent
                <small className="mt-0.5 block text-[12px] font-normal text-faint">funds the hedge from idle cash</small>
              </div>
              <div className="ml-auto flex items-center gap-2 text-[12px] text-dim">
                <span className="h-1.5 w-1.5 rounded-full bg-green" />1 venue
              </div>
            </div>
            {PLACEMENT_VENUES.map((v) => (
              <VenueRow key={v.n} v={v} />
            ))}
          </div>

          <div className="card flex flex-1 flex-col justify-center px-[30px] py-6">
            <div className="label">The result</div>
            <div className="mt-3 max-w-[600px] text-[18px] font-medium leading-[1.5] text-ink">
              The AI didn&apos;t predict the spike — it{" "}
              <b className="font-semibold">pre-bought protection that just paid out.</b> Maison Levain&apos;s margin holds at{" "}
              <span className="text-green">11%</span> while an unhedged peer drops to{" "}
              <span className="text-terra">3.3%</span>.
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

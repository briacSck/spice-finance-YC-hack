"use client";

import { useEffect, useState } from "react";
import { TopBar, type Tab } from "@/components/TopBar";
import { Landing } from "@/components/Landing";
import { Dashboard } from "@/components/Dashboard";
import { Approve } from "@/components/Approve";
import { Execution } from "@/components/Execution";

// "landing" is the screen-0 entry; it renders standalone (no top nav). Every other
// view is a Tab in TopBar.
type View = "landing" | Tab;

const STATUS: Record<Tab, string> = {
  dashboard: "Agent online · Opus 4.8 · ready",
  approve: "Analysing · awaiting approval",
  execution: "Executing · 2 agents · 3 venues",
};

// The design is a pixel-perfect 1280x832 stage (DESIGN.md). To stay responsive
// on any screen — small laptop, big projector, phone — we scale the whole stage
// to fit the viewport (preserving aspect ratio), centered with letterboxing.
const STAGE_W = 1280;
// 800 of content area + 100 navbar. Bumped from 832 when the navbar grew from
// 68→100px, so the content area keeps its original height and nothing clips.
const STAGE_H = 864;

function useFitScale() {
  const [scale, setScale] = useState(1);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    const fit = () =>
      setScale(Math.min(window.innerWidth / STAGE_W, window.innerHeight / STAGE_H));
    fit();
    setReady(true);
    window.addEventListener("resize", fit);
    window.addEventListener("orientationchange", fit);
    return () => {
      window.removeEventListener("resize", fit);
      window.removeEventListener("orientationchange", fit);
    };
  }, []);
  return { scale, ready };
}

export default function Page() {
  const [view, setView] = useState<View>("landing");
  // bump on each entry so on-screen motion (count-up, feed type-in) replays
  const [approveRun, setApproveRun] = useState(0);
  const [execRun, setExecRun] = useState(0);
  const { scale, ready } = useFitScale();

  function go(next: View) {
    if (next === "approve") setApproveRun((n) => n + 1);
    if (next === "execution") setExecRun((n) => n + 1);
    setView(next);
  }

  return (
    // Full-viewport canvas; the fixed stage is scaled to fit and centered.
    // overflow-auto + m-auto: fits the screen with no scroll when it can, but if
    // the scaled stage is taller than the viewport on a given machine, the page
    // scrolls instead of clipping — the bottom is always reachable.
    <main className="flex min-h-screen overflow-auto bg-paper">
      <div
        className="m-auto transition-opacity duration-200"
        style={{ width: STAGE_W * scale, height: STAGE_H * scale, opacity: ready ? 1 : 0 }}
      >
        <div
          className="flex flex-col"
          style={{ width: STAGE_W, height: STAGE_H, transform: `scale(${scale})`, transformOrigin: "top left" }}
        >
          {view === "landing" ? (
            <Landing onEnter={() => go("dashboard")} />
          ) : (
            <>
              <TopBar active={view} onTab={go} status={STATUS[view]} />
              {view === "dashboard" && <Dashboard onRun={() => go("approve")} />}
              {view === "approve" && (
                <Approve key={approveRun} run={approveRun > 0} onExecute={() => go("execution")} />
              )}
              {view === "execution" && <Execution key={execRun} run={execRun > 0} />}
            </>
          )}
        </div>
      </div>
    </main>
  );
}

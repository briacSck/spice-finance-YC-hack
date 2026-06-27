"use client";

import { useState } from "react";
import { TopBar, type Tab } from "@/components/TopBar";
import { Dashboard } from "@/components/Dashboard";
import { Analyse } from "@/components/Analyse";
import { Execution } from "@/components/Execution";

const STATUS: Record<Tab, string> = {
  dashboard: "Agent online · Opus 4.8 · ready",
  analyse: "Analysing · propagate_shock",
  execution: "Executing · 2 agents · 3 venues",
};

export default function Page() {
  const [tab, setTab] = useState<Tab>("dashboard");
  // bump on each entry so on-screen motion (count-up, feed type-in) replays
  const [analyseRun, setAnalyseRun] = useState(0);
  const [execRun, setExecRun] = useState(0);

  function go(next: Tab) {
    if (next === "analyse") setAnalyseRun((n) => n + 1);
    if (next === "execution") setExecRun((n) => n + 1);
    setTab(next);
  }

  return (
    // Fixed 1280x832 stage (demo canvas, DESIGN.md). Centered on larger screens.
    <main className="flex min-h-screen items-center justify-center bg-paper">
      <div className="flex h-[832px] w-stage flex-col overflow-hidden">
        <TopBar active={tab} onTab={go} status={STATUS[tab]} />
        {tab === "dashboard" && <Dashboard onRun={() => go("analyse")} />}
        {tab === "analyse" && (
          <Analyse key={analyseRun} run={analyseRun > 0} onExecute={() => go("execution")} />
        )}
        {tab === "execution" && <Execution key={execRun} run={execRun > 0} />}
      </div>
    </main>
  );
}

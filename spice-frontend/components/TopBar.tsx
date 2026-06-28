"use client";

import { LogoMark } from "@/components/Logo";

export type Tab = "dashboard" | "approve" | "execution";

const TABS: { id: Tab; label: string }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "approve", label: "Analyse & approve" },
  { id: "execution", label: "Execution" },
];

export function TopBar({
  active,
  onTab,
  status,
}: {
  active: Tab;
  onTab: (t: Tab) => void;
  status: string; // e.g. "Agent online · Opus 4.8 · ready"
}) {
  return (
    <header className="flex h-[100px] shrink-0 items-center justify-between border-b border-hair2 px-11">
      <div className="flex items-center gap-[34px]">
        <div className="flex items-center gap-3">
          <LogoMark size={34} variant="seed" />
          <div className="hidden text-[18px] font-semibold tracking-tight sm:flex sm:items-baseline">
            Spice
            <span className="ml-3 text-[11px] font-normal uppercase tracking-label text-faint">
              The Exotic Asset Company
            </span>
          </div>
        </div>
        <nav className="flex gap-[26px]">
          {TABS.map((t) => (
            <button
              key={t.id}
              onClick={() => onTab(t.id)}
              className={`text-[13.5px] font-medium transition-colors ${
                active === t.id ? "text-ink" : "text-faint hover:text-dim"
              }`}
            >
              {t.label}
            </button>
          ))}
        </nav>
      </div>
      <div className="flex items-center gap-[9px] text-[12.5px] text-dim">
        <span className="live-dot h-[7px] w-[7px] rounded-full bg-green" />
        <span>
          <b className="font-semibold text-ink">{status.split(" · ")[0]}</b>
          {status.includes(" · ") && (
            <span className="font-mono"> · {status.split(" · ").slice(1).join(" · ")}</span>
          )}
        </span>
      </div>
    </header>
  );
}

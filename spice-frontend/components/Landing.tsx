"use client";

import { useRef } from "react";
import { LogoMark } from "@/components/Logo";

/**
 * Screen 0 — landing. Big product name + value proposition, then two entry boxes:
 * left = the Maison Levain demo (the wired path), right = "upload your data" (bring
 * your own bank statement / relevé de compte). The upload box accepts a file but the
 * relevé→exposure analysis isn't wired yet, so for now it enters the same demo.
 */
export function Landing({ onEnter }: { onEnter: (source: "demo" | "upload") => void }) {
  const fileRef = useRef<HTMLInputElement>(null);

  return (
    <div className="flex h-full flex-col items-center justify-center px-11">
      {/* brand + value proposition */}
      <div className="flex flex-col items-center text-center">
        <div className="flex items-center gap-3">
          <LogoMark size={44} variant="seed" />
          <div className="flex items-baseline text-[40px] font-semibold tracking-tight">
            Spice
            <span className="ml-3 text-[12px] font-normal uppercase tracking-label text-faint">
              The Exotic Asset Company
            </span>
          </div>
        </div>
        <h1 className="mt-7 max-w-[820px] text-[34px] font-semibold leading-[1.2] tracking-tight">
          Every ordinary business is an unhedged commodity trader.{" "}
          <span className="text-green">Spice runs the desk for them.</span>
        </h1>
        <p className="mt-4 max-w-[640px] text-[15px] leading-relaxed text-dim">
          Read the bank statement, find the hidden commodity exposure, and hedge it across
          options, parametric cover and on-chain yield — autonomously, with a human approving
          once.
        </p>
      </div>

      {/* two entry boxes */}
      <div className="mt-12 grid w-full max-w-[860px] grid-cols-2 gap-[30px]">
        {/* left — the demo */}
        <button
          onClick={() => onEnter("demo")}
          className="card group flex flex-col px-8 py-7 text-left transition-colors hover:border-green"
        >
          <div className="label text-green">Try the live demo</div>
          <h2 className="mt-3 text-[22px] font-semibold tracking-tight">Maison Levain</h2>
          <div className="mt-1 text-[13px] text-dim">Bakery · Lyon · €1.4M revenue</div>
          <p className="mt-4 flex-1 text-[13px] leading-relaxed text-dim">
            A real, relatable business that is secretly long wheat, gas and power. Watch Spice
            decompose its costs and hedge a 2026 heatwave end-to-end.
          </p>
          <span className="btn-primary mt-6 inline-flex w-fit items-center">
            Enter demo <span className="ml-1.5 font-normal opacity-75">→</span>
          </span>
        </button>

        {/* right — upload your data */}
        <button
          onClick={() => fileRef.current?.click()}
          className="card group flex flex-col px-8 py-7 text-left transition-colors hover:border-green"
        >
          <div className="label">Upload your data</div>
          <h2 className="mt-3 text-[22px] font-semibold tracking-tight">Your business</h2>
          <div className="mt-1 text-[13px] text-dim">Bring your own relevé de compte</div>
          <div className="mt-4 flex flex-1 flex-col items-center justify-center rounded-[10px] border border-dashed border-hair2 py-6 text-center">
            <div className="text-[13px] font-medium text-dim">Drop a bank statement</div>
            <div className="mt-0.5 text-[11.5px] text-faint">CSV · PDF · or click to browse</div>
          </div>
          <span className="mt-6 inline-flex w-fit items-center text-[13.5px] font-medium text-dim group-hover:text-ink">
            Upload bank statement <span className="ml-1.5 font-normal opacity-75">→</span>
          </span>
          <input
            ref={fileRef}
            type="file"
            accept=".csv,.pdf,.xlsx"
            className="hidden"
            onClick={(e) => e.stopPropagation()}
            onChange={() => onEnter("upload")}
          />
        </button>
      </div>
    </div>
  );
}

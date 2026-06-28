"use client";

import { useEffect, useRef, useState } from "react";
import {
  advanceMonth,
  approveProposal,
  createProgram,
  getProgramState,
  getProposals,
  rejectProposal,
} from "@/lib/api";
import type { HedgeProposal, ProgramState } from "@/lib/types";

const STATUS_STYLE: Record<HedgeProposal["status"], string> = {
  pending: "text-dim",
  approved: "text-green",
  rejected: "text-faint",
};

export function Approvals({
  programId,
  onProgramId,
}: {
  programId: string | null;
  onProgramId: (id: string) => void;
}) {
  const [proposals, setProposals] = useState<HedgeProposal[]>([]);
  const [state, setState] = useState<ProgramState | null>(null);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  // Guards against React 18 dev-mode double-effect: without this, two
  // createProgram() calls can race and silently strand the UI on whichever
  // program_id resolves second.
  const creatingRef = useRef(false);

  async function refresh(id: string) {
    const [props, programState] = await Promise.all([getProposals(id), getProgramState(id)]);
    setProposals(props);
    setState(programState);
  }

  useEffect(() => {
    if (programId) {
      refresh(programId).catch((e) => setError(String(e)));
      return;
    }
    if (creatingRef.current) return;
    creatingRef.current = true;
    createProgram()
      .then((id) => {
        onProgramId(id);
        return refresh(id);
      })
      .catch((e) => setError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [programId]);

  async function handleApprove(ticker: string) {
    if (!programId) return;
    setBusy(ticker);
    try {
      await approveProposal(programId, ticker);
      await refresh(programId);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  async function handleReject(ticker: string) {
    if (!programId) return;
    setBusy(ticker);
    try {
      await rejectProposal(programId, ticker);
      await refresh(programId);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  async function handleAdvanceMonth() {
    if (!programId) return;
    setBusy("advance-month");
    try {
      await advanceMonth(programId);
      await refresh(programId);
    } catch (e) {
      setError(String(e));
    } finally {
      setBusy(null);
    }
  }

  return (
    <>
      <div className="flex items-end justify-between px-11 pb-5 pt-2">
        <h1 className="max-w-[760px] text-[27px] font-semibold leading-[1.2] tracking-tight">
          Approve each hedge once. <span className="text-green">Spice rolls the ladder every month after.</span>
        </h1>
        <div className="font-mono text-[12.5px] text-faint">
          {state ? `${state.company_name} · month ${state.current_month_index}` : "loading…"}
        </div>
      </div>

      {error && <div className="mx-11 mb-3 text-[12.5px] text-terra">{error}</div>}

      <div className="grid min-h-0 flex-1 grid-cols-[1fr_380px] gap-[30px] px-11 pb-9">
        {/* proposals */}
        <div className="card flex min-h-0 flex-col px-8 py-[30px]">
          <div className="label mb-[18px]">Hedge proposals · real exposure analysis</div>
          <div className="flex-1 overflow-y-auto pr-1">
            {proposals.length === 0 && <div className="text-[12.5px] text-faint">No proposals yet.</div>}
            {proposals.map((p, i) => (
              <div
                key={p.proposal_id}
                className={`mb-5 pb-5 ${i < proposals.length - 1 ? "border-b border-hair2" : ""}`}
              >
                <div className="mb-2 flex items-baseline gap-2.5">
                  <span className="text-[10px] font-semibold uppercase tracking-label text-faint">{p.ticker}</span>
                  <span className="text-[14.5px] font-semibold">{p.underlying}</span>
                  <span className={`ml-auto text-[11px] font-medium uppercase tracking-label ${STATUS_STYLE[p.status]}`}>
                    {p.status}
                  </span>
                </div>
                <div className="text-[12.5px] leading-relaxed text-dim">{p.explanation}</div>
                <div className="mt-2 flex items-center gap-4">
                  <span className="font-mono text-[12.5px] font-medium text-ink tnum">
                    ~€{Math.round(p.monthly_notional / 100) / 10}k/month
                  </span>
                  <span className="font-mono text-[11.5px] text-faint">score {p.score}</span>
                  {p.status === "pending" && (
                    <div className="ml-auto flex gap-2">
                      <button
                        className="btn-primary px-4 py-1.5 text-[12.5px]"
                        disabled={busy === p.ticker}
                        onClick={() => handleApprove(p.ticker)}
                      >
                        Approve
                      </button>
                      <button
                        className="rounded-[8px] border border-hair2 px-4 py-1.5 text-[12.5px] font-medium text-dim hover:text-ink"
                        disabled={busy === p.ticker}
                        onClick={() => handleReject(p.ticker)}
                      >
                        Reject
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* program state: ladders + sweep */}
        <div className="card flex min-h-0 flex-col px-7 py-[26px]">
          <div className="label mb-[14px]">Program state</div>

          <div className="mb-5">
            <div className="text-[10.5px] uppercase tracking-label text-faint">Lending sweep · monthly excess cash</div>
            <div className="mt-1 font-mono text-[20px] font-semibold tnum">
              €{state ? Math.round(state.monthly_excess_cash).toLocaleString() : "—"}
            </div>
            <div className="mt-0.5 text-[11.5px] text-faint">active automatically once the program exists</div>
          </div>

          <button
            className="btn-primary mb-5"
            disabled={!programId || busy === "advance-month"}
            onClick={handleAdvanceMonth}
          >
            Advance month → {state ? state.current_month_index + 1 : 1}
          </button>

          <div className="flex-1 overflow-y-auto pr-1">
            {state &&
              Object.entries(state.ladders).map(([ticker, ladder]) => (
                <div key={ticker} className="mb-4">
                  <div className="mb-1.5 text-[12.5px] font-semibold">{ladder.underlying}</div>
                  <div className="flex flex-wrap gap-1">
                    {ladder.rungs.slice(-12).map((r) => (
                      <span
                        key={r.month_index}
                        title={`${r.target_month} · qty ${r.quantity} · ${r.status}`}
                        className={`rounded-[4px] px-1.5 py-0.5 font-mono text-[10px] ${
                          r.status === "bought" ? "bg-green text-paper" : "bg-panel text-faint"
                        }`}
                      >
                        {r.target_month.slice(2)}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            {state && state.sweep_log.length > 0 && (
              <div className="mt-5 border-t border-hair2 pt-3">
                <div className="mb-1.5 text-[11px] uppercase tracking-label text-faint">Sweep log</div>
                {state.sweep_log.slice(-5).map((s) => (
                  <div key={s.month_index} className="flex justify-between text-[11.5px] text-dim">
                    <span>month {s.month_index}</span>
                    <span className="font-mono">{s.status}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

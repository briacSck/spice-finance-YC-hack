import type { Company, EscrowPolicy, HedgeLadder, HedgeProposal, ProgramState, RunEvent } from "./types";
import { MAISON_LEVAIN } from "./mockData";

// The frontend talks ONLY to the orchestrator (eng-review D2).
// Base URL is configurable; defaults to the orchestrator's localhost port.
export const ORCHESTRATOR_BASE =
  process.env.NEXT_PUBLIC_ORCHESTRATOR_URL ?? "http://localhost:8000";

// Flip to false once the orchestrator is live to use real REST + SSE.
export const USE_MOCK = true;

/** GET /api/company */
export async function getCompany(): Promise<Company> {
  if (USE_MOCK) return MAISON_LEVAIN;
  const res = await fetch(`${ORCHESTRATOR_BASE}/api/company`);
  if (!res.ok) throw new Error(`getCompany ${res.status}`);
  return res.json();
}

/** POST /api/run -> { run_id }.  ?mock=true for the deterministic scripted run. */
export async function startRun(mock = false): Promise<string> {
  if (USE_MOCK) return "r_mock";
  const res = await fetch(`${ORCHESTRATOR_BASE}/api/run${mock ? "?mock=true" : ""}`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`startRun ${res.status}`);
  const data = await res.json();
  return data.run_id as string;
}

/**
 * Subscribe to GET /api/run/{run_id}/events (Server-Sent Events).
 * Returns an unsubscribe fn. When USE_MOCK, the caller drives the scripted
 * feed itself (see useDemoRun); this real path is here for the teammate to flip on.
 */
export function subscribeToRun(
  runId: string,
  onEvent: (e: RunEvent) => void,
  onError?: (err: unknown) => void
): () => void {
  const src = new EventSource(`${ORCHESTRATOR_BASE}/api/run/${runId}/events`);
  src.onmessage = (msg) => {
    try {
      onEvent(JSON.parse(msg.data) as RunEvent);
    } catch (err) {
      onError?.(err);
    }
  };
  src.onerror = (err) => onError?.(err);
  return () => src.close();
}

// --- hedge program: real recommendations -> approval -> rolling ladder ---
// This flow always talks to the real orchestrator (never mocked, per spec).

/** POST /api/program -> { program_id } */
export async function createProgram(): Promise<string> {
  const res = await fetch(`${ORCHESTRATOR_BASE}/api/program`, { method: "POST" });
  if (!res.ok) throw new Error(`createProgram ${res.status}`);
  const data = await res.json();
  return data.program_id as string;
}

/** GET /api/program/{id}/proposals */
export async function getProposals(programId: string): Promise<HedgeProposal[]> {
  const res = await fetch(`${ORCHESTRATOR_BASE}/api/program/${programId}/proposals`);
  if (!res.ok) throw new Error(`getProposals ${res.status}`);
  const data = await res.json();
  return data.proposals as HedgeProposal[];
}

/**
 * POST /api/program/{id}/proposals/{ticker}/approve
 * -> the built 12-rung ladder (option proposals) or the minted policy (escrow proposal).
 */
export async function approveProposal(
  programId: string,
  ticker: string
): Promise<HedgeLadder | EscrowPolicy> {
  const res = await fetch(`${ORCHESTRATOR_BASE}/api/program/${programId}/proposals/${ticker}/approve`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`approveProposal ${res.status}`);
  return res.json();
}

/** POST /api/program/{id}/proposals/{ticker}/reject */
export async function rejectProposal(programId: string, ticker: string): Promise<void> {
  const res = await fetch(`${ORCHESTRATOR_BASE}/api/program/${programId}/proposals/${ticker}/reject`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`rejectProposal ${res.status}`);
}

/** POST /api/program/{id}/advance-month — the operator-fired monthly clock tick */
export async function advanceMonth(
  programId: string
): Promise<{ month_index: number; rungs_bought: unknown[]; sweep: unknown }> {
  const res = await fetch(`${ORCHESTRATOR_BASE}/api/program/${programId}/advance-month`, {
    method: "POST",
  });
  if (!res.ok) throw new Error(`advanceMonth ${res.status}`);
  return res.json();
}

/** GET /api/program/{id}/state */
export async function getProgramState(programId: string): Promise<ProgramState> {
  const res = await fetch(`${ORCHESTRATOR_BASE}/api/program/${programId}/state`);
  if (!res.ok) throw new Error(`getProgramState ${res.status}`);
  return res.json();
}

import type { Company, RunEvent } from "./types";
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

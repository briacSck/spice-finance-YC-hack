"use client";

import { useEffect, useState } from "react";
import { startRun, subscribeToRun, USE_MOCK } from "./api";
import type { AnalysisEvent, DoneEvent, ExecutionEvent, FeedItem, RunEvent } from "./types";

// Live run state, fed from the orchestrator's SSE stream (GET /api/run/{id}/events).
// One hook the screens read instead of mockData when USE_MOCK is false.
export interface RunState {
  feed: FeedItem[]; // activity feed (Execution)
  analysis: AnalysisEvent | null; // latest margin/VaR snapshot (Analyse)
  executions: ExecutionEvent[]; // venue rows (Execution)
  done: DoneEvent | null; // climax banner payload
}

const EMPTY: RunState = { feed: [], analysis: null, executions: [], done: null };

function clock(): string {
  const d = new Date();
  return d.toTimeString().slice(0, 8); // HH:MM:SS
}

function toFeedItem(e: RunEvent, id: number): FeedItem | null {
  switch (e.type) {
    case "agent_message": {
      const who = e.who ?? "Orchestrator";
      const isTrigger = /trigger/i.test(who);
      return { id, kind: isTrigger ? "trigger" : "message", who, text: e.text, time: clock() };
    }
    case "tool_call": {
      const args = Object.values(e.input ?? {}).join(", ");
      return { id, kind: "tool", who: e.who ?? "Agent", text: `${e.tool}(${args})`, time: clock() };
    }
    case "execution":
      return { id, kind: "exec", who: e.venue, text: e.action, time: clock() };
    default:
      return null; // analysis / tool_result / done don't render as feed rows
  }
}

/**
 * Drives one run against the orchestrator and accumulates its SSE events.
 * `active` flips true when the run should start (e.g. entering the Execution tab).
 * No-op when USE_MOCK — the screens keep their scripted mock in that mode.
 */
export function useRun(active: boolean, mock = false): RunState {
  const [state, setState] = useState<RunState>(EMPTY);

  useEffect(() => {
    if (!active || USE_MOCK) return;
    setState(EMPTY);
    let cancelled = false;
    let unsub = () => {};

    (async () => {
      try {
        const runId = await startRun(mock);
        if (cancelled) return;
        unsub = subscribeToRun(
          runId,
          (e) => {
            setState((prev) => {
              const next: RunState = { ...prev };
              if (e.type === "analysis") next.analysis = e;
              else if (e.type === "execution") next.executions = [...prev.executions, e];
              else if (e.type === "done") next.done = e;
              const item = toFeedItem(e, prev.feed.length);
              if (item) next.feed = [...prev.feed, item];
              return next;
            });
          },
          (err) => console.error("[useRun] SSE error", err)
        );
      } catch (err) {
        console.error("[useRun] startRun failed", err);
      }
    })();

    return () => {
      cancelled = true;
      unsub();
    };
  }, [active, mock]);

  return state;
}

// Shapes mirror spice-backend/API_CONTRACT.md exactly.

export interface Exposure {
  commodity: string; // e.g. "WEAT"
  name: string; // e.g. "Wheat"
  amount: number; // € cost
  share_of_revenue: number; // 0..1
  vol: number; // annualised vol, 0..1
}

export interface Company {
  name: string;
  revenue: number;
  cash: number;
  net_margin: number; // 0..1
  exposures: Exposure[];
}

// --- SSE event stream (GET /api/run/{id}/events) ---

export interface AgentMessageEvent {
  type: "agent_message";
  who?: string; // UI-only convenience; defaults to "Orchestrator"
  text: string;
}
export interface ToolCallEvent {
  type: "tool_call";
  who?: string;
  tool: string;
  input: Record<string, unknown>;
}
export interface ToolResultEvent {
  type: "tool_result";
  tool: string;
  output: Record<string, unknown>;
}
export interface AnalysisEvent {
  type: "analysis";
  decomposition: Exposure[];
  margin_before: number;
  margin_after: number; // shocked, unhedged
  var_before: number;
  var_after: number; // after hedge
}
export interface ExecutionEvent {
  type: "execution";
  venue: "alpaca" | "morpho" | "escrow";
  action: string;
  status: "accepted" | "settled";
  ref: string; // order id / tx hash
  explorer_url?: string;
  amount?: number; // UI-only convenience
  pnl?: number; // UI-only convenience
}
export interface DoneEvent {
  type: "done";
  summary: string;
  hedge_pnl: number;
  margin_with_hedge: number;
}

export type RunEvent =
  | AgentMessageEvent
  | ToolCallEvent
  | ToolResultEvent
  | AnalysisEvent
  | ExecutionEvent
  | DoneEvent;

// UI-side normalized feed item (what Execution renders)
export interface FeedItem {
  id: number;
  kind: "message" | "tool" | "exec" | "trigger";
  who: string;
  text: string;
  time: string;
}

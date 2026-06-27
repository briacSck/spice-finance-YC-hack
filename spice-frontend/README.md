# spice-frontend

The 3-screen demo UI for Spice. **Next.js (App Router) + Tailwind + TypeScript.**
Built from the `/plan-design-review` mockups; design system locked in `../DESIGN.md`.

This is the **show** (in production the agent runs headless). It drives a continuous
~2-minute live story for the jury: a healthy bakery → its hidden risk → the autonomous
hedge paying out live.

## Run it

```bash
npm install
npm run dev      # http://localhost:3000
```

Runs standalone on **mock data** out of the box (no backend needed). The flow:
**Dashboard → "Run risk analysis" → Analyse → "Execute across 3 venues" → Execution.**
You can also click the top tabs directly; entering Analyse/Execution replays the motion.

## What's done

- All 3 screens, pixel-close to the approved mockups, fixed **1280×832** stage.
- Design tokens wired into Tailwind (`tailwind.config.ts`) — `bg-paper`, `text-ink`,
  `text-dim`, `bg-green`, `text-terra`, `font-mono`, `.card`, `.label`, `.btn-primary`.
- DR4 motion: count-up on the margin collapse, event-by-event type-in on the activity
  feed (auto-scrolls to newest).
- Data layer typed against `../spice-backend/API_CONTRACT.md` (`lib/types.ts`).
- Mock data for Maison Levain in `lib/mockData.ts`.
- REST + SSE client in `lib/api.ts` — ready to flip from mock to the live orchestrator.

## Wire it to the orchestrator

`lib/api.ts` talks ONLY to the orchestrator (eng-review D2), default
`http://localhost:8000`. To go live:

1. Set `USE_MOCK = false` in `lib/api.ts` (or `NEXT_PUBLIC_ORCHESTRATOR_URL`).
2. Dashboard/Analyse read `GET /api/company` (`getCompany`).
3. On "Run", call `startRun()` → `POST /api/run` → `{ run_id }`, then
   `subscribeToRun(runId, onEvent)` for the SSE stream. Map events to UI:
   - `analysis` → Analyse numbers (margin_before/after, var_before/after)
   - `execution` → Execution venue rows (venue/status/ref/explorer_url)
   - `agent_message` / `tool_call` → the activity feed
   - `done` → climax banner (hedge_pnl, margin_with_hedge)
4. Use `POST /api/run?mock=true` as the **deterministic on-stage fallback** if a venue hangs.

The current scripted feed (`SCRIPTED_FEED` in `lib/mockData.ts`) mirrors the SSE event
order, so swapping in the real stream is mostly a render-loop change in `Execution.tsx`.

## What to fine-tune (see ../TODOS.md)

- Real SSE streaming wired in (replace the mock interval in `Execution.tsx`).
- Projector rehearsal pass — contrast/type if the warm-paper bg glares (DESIGN.md DR2).
- Empty / pre-run states (feed "Waiting for run…", venues hidden, donut grey).
- Tighten the Analyse middle panel's vertical whitespace; optional forecast sparkline.

## Layout

```
app/layout.tsx      fonts (Satoshi + Spline Sans Mono) + globals
app/page.tsx        the stage shell: tab nav + demo flow + motion replay
app/globals.css     tokens as CSS vars + .card/.label/.btn-primary + keyframes
components/TopBar   logo, tabs, live agent status
components/Dashboard / Analyse / Execution
lib/types.ts        API_CONTRACT shapes
lib/mockData.ts     Maison Levain data + scripted feed
lib/api.ts          REST + SSE client (USE_MOCK toggle)
lib/useCountUp.ts   count-up hook (DR4)
```

> Design source of truth: `../DESIGN.md`. Don't introduce a second accent color or a
> generic KPI card grid — see the anti-slop guardrails there.

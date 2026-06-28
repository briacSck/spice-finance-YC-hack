# TODOS

## Design (from plan-design-review, 2026-06-27)

- [ ] **Choreographed streaming UI (DR4).** Implement count-up on numbers, type-in on the
  activity feed (event-by-event over SSE), the margin-collapse transition, and the climax
  banner slide-in. Drive timing from the scenario clock so it's deterministic and repeatable.
  *Why:* the demo IS the live stream — this is where the "wow" lives. *Blocked by:* orchestrator
  SSE events (`API_CONTRACT.md`). Owner: frontend lane.
- [ ] **Projector rehearsal check (DR2).** Test all 3 screens on the actual venue projector
  at H42–48. Bump contrast / type size if the warm-paper bg glares in a dark room.
  *Why:* light UI in a dark jury room is the one live legibility risk we accepted.
- [ ] **`mock=true` recorded fallback wired to the UI.** The deterministic scripted run
  (`POST /api/run?mock=true`) must drive the same screens/feed with canned timing, as the
  guaranteed-safe demo path. Plus a screen-recording of one clean run as ultimate backup.
  *Why:* venues can hang on stage; the show must survive it.
- [ ] **Tighten Analyse middle panel.** The margin-collapse card has vertical dead space
  around the centered numbers. Reduce panel height or add a sparkline of the forecast path.
  *Why:* polish; it reads slightly empty on the projector. Low priority.
- [ ] **Empty / pre-run states.** Activity feed "Waiting for run…", venue rows hidden until
  acted, donut grey before analysis. Spec'd in `DESIGN.md`; build them so a re-run from cold
  looks intentional, not broken.

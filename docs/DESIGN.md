# SPICE — Design System

> Source of truth for the 3-screen demo UI. Locked via `/plan-design-review` (2026-06-27).
> Aesthetic: **premium fintech, épuré.** Calm, trusted, money-grade — Mercury/Ramp register,
> not a generic SaaS dashboard. The quant is the proof; the design is the believability.

The UI is **demo-only** (in production the agent runs headless). It drives a continuous
~2-minute live story for a YC jury on a projector. Every decision below serves: *legible
from the back row, premium at a glance, and dramatic at the two hero moments.*

---

## Locked decisions (plan-design-review)

| # | Decision | Choice |
|---|----------|--------|
| DR1 | Aesthetic direction | **Premium fintech, refined (épuré).** Light, calm, one accent. |
| DR2 | Projection | **Keep light**, tune contrast + min type for the room; verify on the real projector at rehearsal (H42–48). |
| DR3 | UI language | **Fully English chrome.** Keep the proper noun *Maison Levain*; everything else English ("Recommendations", "Bakery", "Run risk analysis"). |
| DR4 | Live motion | **Choreographed but safe.** Count-up numbers, feed types in, banner slides; driven by the scenario clock (deterministic, eng-review D1); recorded fallback. |

---

## Color

CSS variables. One accent (deep green). Terracotta is the *only* risk/negative color —
used sparingly. Everything else is neutral warm-paper.

```css
:root{
  /* surfaces */
  --bg:      #F4F3EF;  /* warm paper — app background (NOT pure white: less projector glare) */
  --panel:   #FFFFFF;  /* cards */
  --hair:    #ECEAE3;  /* hairline borders */
  --hair-2:  #F2F0EA;  /* internal dividers */
  --ink-deep:#13231D;  /* climax banner — deep forest-ink */

  /* text */
  --ink:     #1A1916;  /* primary */
  --dim:     #797469;  /* secondary */
  --faint:   #ABA59A;  /* labels, captions */

  /* accent + semantic (use sparingly) */
  --green:   #1B5E4C;  /* THE accent: positive, actions, brand */
  --terra:   #A85436;  /* risk / negative ONLY */
  --green-on-ink:#5DD3A3; /* positive numbers on the deep-ink banner */

  /* commodity series (exposure donut / bars) — green → desaturated, never rainbow */
  --c-wheat: #1B5E4C;
  --c-energy:#5C7A6E;
  --c-fats:  #94A89E;
  --c-other: #F2F0EA;
}
```

Rules:
- **One accent.** Green carries brand + positive + primary actions. Do not introduce a
  second bright color. Saffron/orange fills were explored and cut — too busy.
- **Terracotta means risk.** Margin collapse, VaR, "0% hedged", trigger events. Nowhere else.
- **No gradients** except the (optional) micro-fade inside the deep-ink climax banner.

---

## Typography

Two families. No default stacks (no Inter/Roboto/system as display).

| Role | Font | Usage |
|------|------|-------|
| Display + body | **Satoshi** (Fontshare) | headings, labels, body. Weights 300–700. |
| Numerals + tickers | **Spline Sans Mono** (Fontshare) | all money, %, refs, tx hashes, timestamps. `font-variant-numeric: tabular-nums`. |

Scale (demo, 1280px):
- Screen headline (Analyse kicker): 27px / 600 / −0.025em
- Client name (Dashboard H1): 36px / 600 / −0.03em
- Hero numbers (margin collapse): 64px / 600 / −0.04em mono
- KPI value: 34px / 600 mono
- Panel title: 15–17px / 600
- Body: 13px / 400
- **Label (uppercase):** 10.5px / 500 / letter-spacing .14em / `--faint`
- Min body size on screen: **≥12.5px** (projection floor)

---

## Layout & components

- **Canvas:** fixed **1280 × 832** (demo, not responsive — production is headless).
- **Grid:** 44px horizontal page padding; 30px gaps between cards.
- **Cards are borderless.** White on warm paper, separated by soft shadow + whitespace,
  not nested boxes. `box-shadow: 0 1px 2px rgba(40,36,28,.04), 0 12px 32px -12px rgba(40,36,28,.10)`.
  Radius 18px, padding 28–32px.
- **Status = quiet dot + label**, never filled pills. `done/settled` = green dot,
  `queued/idle` = faint dot, `risk/trigger` = terracotta dot.
- **Hairline dividers** inside panels only where a list needs separation (`--hair-2`).
- **Primary button:** green fill, `#F4F3EF` text, radius 13px, 16px padding.
- **Top bar:** logo (green rounded square "S") + wordmark "Spice / The Exotic Asset Company";
  right side = tabs (Dashboard / Analyse / Execution) + a live agent-status pill
  (pulsing green dot + "Agent online · Opus 4.8").

### The exposure donut (Analyse)
Thin ring (inset 22px), center stat (`74% / commodity cost`), legend tied to **real
commodities** (Wheat/WEAT, Energy, Fats). This is the core "bakery = commodity book"
idea made visual — it earns its place; do not add decorative charts elsewhere.

### The climax banner (Execution)
Deep-ink (`--ink-deep`) flat panel, full width at top. Left: "The hedge just paid" +
one sentence. Right: three numbers — VaR `13.1% → 2.0%` (old struck through), margin
held `11.0%` (vs peer 3.3%), Hedge P&L `+€107.5k` in `--green-on-ink`. Live dot top-right.

---

## Interaction states (the demo IS the live stream — eng-review D1/D3, API SSE)

| Surface | Loading / streaming | Empty / pre-run | Settled / done | Error / fallback |
|---|---|---|---|---|
| KPI band | skeleton shimmer, then **count-up** to value | — (always loaded from `/api/company`) | static | last-known value, no error chrome |
| Agent status list | rows light up green as steps complete | all faint dots | green dots, "done" | step turns terracotta + retry note |
| Exposure donut | ring draws in (0→full) | grey ring | full | static (analysis is in-process, can't fail mid-demo) |
| Margin collapse | 11.0% holds, then animates → 3.3% on shock | shows today's 11.0% only | both numbers | scenario clock is deterministic — no live fail |
| Activity feed | events **type in** one by one over SSE; auto-scroll to newest | "Waiting for run…" | full timeline | on venue hang → switch to `mock=true` scripted stream (recorded fallback) |
| Venue rows | "submitting…" faint dot | hidden until acted | green dot + ref + explorer link | "order prepared" if Alpaca rejects weekend order (D3) |
| Climax banner | slides in when trigger fires + payout settles | hidden until the live beat | full | recorded backup of the exact tx flow |

**Motion budget (DR4):** count-up on numbers, type-in on the feed, a quick margin-collapse
transition, banner slide-in. Timing comes from the scenario clock so it's repeatable across
≥5 clean runs. Nothing waits on a live network call to animate.

---

## Anti-slop guardrails (do NOT)

- No 2×2 / 3-up generic KPI card grid (we use a hairline stat-band).
- No purple/indigo, no icon-in-colored-circle rows, no centered-everything.
- No second bright accent. No decorative blobs/dividers. No emoji as UI.
- No placeholder-as-label in any form. No body text < 12.5px on the projector.
- Cards must earn their existence — if a panel is just a box around text, drop the box.

---

## Approved mockups

| Screen | File | Role |
|--------|------|------|
| Dashboard | `~/.gstack/projects/briacSck-spice-finance-YC-hack/designs/dashboard-variants-20260627/variant-B2.png` | the ordinary business + the AI watching it |
| Analyse | `~/.gstack/projects/.../designs/analyse-20260627/analyse-v2.png` | margin collapse + recommendations |
| Execution | `~/.gstack/projects/.../designs/execution-20260627/execution-v2.png` | live agents + on-chain payout climax |

HTML sources sit next to each PNG (real Satoshi + Spline Sans Mono, convertible straight
to Next.js + Tailwind). 3-screen board: `designs/spice-3screen-board.html`.

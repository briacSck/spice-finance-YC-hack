# SPICE — Competitive Whitespace Map

*Validated against fresh 2026 research, EU incumbents included.*

**Thesis:** everyone can hedge a commodity *once you tell them what you're exposed to*. Nobody tells an ordinary SMB what they're exposed to. The exposure-**discovery** step — reading raw accounting data and surfacing the hidden commodity risk inside it — is the empty center. The center is: **automatic, explainable commodity-exposure discovery from ordinary books, for non-finance SMBs.**

---

## Who's out there, and where they stop

| Player | What they do | What they **don't / can't** do |
|---|---|---|
| **Pillar** (FR) | Hedging optimization platform | **Assumes the customer already knows their exposures** and is fluent with instruments; large-corporate focus; no discovery from raw books |
| **Agicap** (FR, 7,000+ clients — the one the jury knows) | Cash-flow mgmt, forecasting, collection | Shows cost *categories*, never **maps them to commodity underlyings**; no shock/stress test; no hedge priority; read-only advisory |
| **Pennylane / commodity-aware ERPs** (FR) | AI-assisted accounting / ledger | Records the flour invoice; never tells you flour = **wheat exposure**; no risk lens at all |
| **Commodity risk advisories** (Vialto, INTL FCStone, bank trade desks) | Bespoke exposure audits + hedging programs | Manual, consultant-priced, **enterprise-only**; weeks of work; not turnkey; not for a €2M-revenue bakery |
| **Procurement/spend-analytics tools** (Spendesk, Coupa) | Categorize and visualize spend | Map spend by *vendor/category*, not by **underlying commodity**; no price-sensitivity model; no margin stress |
| **Bloomberg / Refinitiv / commodity terminals** | Commodity prices, vol, curves | Give you the *price of wheat* — but never connect it to **your** flour line; you must already be a trader |
| **YC W26/S26 AI-accounting agents** | Invoice capture, reconciliation, "CFO insights" | Bookkeeping automation; **no commodity mapping, no exposure model, no stress test** |

---

## Capability matrix

| Capability | Pillar | Agicap | Risk advisories | Spend analytics | **Spice** |
|---|:--:|:--:|:--:|:--:|:--:|
| Works from a raw Excel/accounting export (no setup) | ✗ | ◐ | ✗ | ◐ | ✅ |
| **Discovers** which commodities you're exposed to | ✗ | ✗ | ◐ | ✗ | ✅ |
| Maps expense lines → underlyings, line-by-line | ✗ | ✗ | ◐ | ✗ | ✅ |
| Material-level granularity (steel ≠ aluminium ≠ copper) | ◐ | ✗ | ◐ | ✗ | ✅ |
| Margin stress test under +10/20/30% shocks | ◐ | ✗ | ✅ | ✗ | ✅ |
| Explainable + cited to the source row | ✗ | ◐ | ◐ | ◐ | ✅ |
| Turnkey for a non-finance SMB | ✗ | ◐ | ✗ | ◐ | ✅ |
| EU / France-first (Insee-grounded shocks) | ✗ | ✅ | ◐ | ◐ | ✅ |

Legend: ✅ yes · ◐ partial · ✗ no

---

## The frontier the hedging world opened but didn't finish

| Player | Cracked | Did NOT crack |
|---|---|---|
| **Pillar / corporate hedge desks** | Optimizing a hedge *once exposures are known* | **Finding the exposures** in an ordinary business's books |
| **Bloomberg / Refinitiv** | The commodity price layer itself | Connecting that price to *your* flour, *your* diesel, *your* steel |
| **Agicap / accounting AIs** | Reading the books cleanly | Reading **risk** out of the books — the commodity hiding behind every cost line |

The instrument layer is solved. **The layer that reads an ordinary bakery's books and says "you have €420k of wheat exposure threatening 3.6 margin points" does not exist.** That is the frontier: exposure discovery as the missing first step before anyone can hedge.

## The killer line for the jury

> *"Pillar optimizes a hedge once you know your exposure. Bloomberg gives you the price of wheat. Nobody tells the bakery that its flour line *is* wheat. Spice reads ordinary books and turns invisible commodity risk into a ranked, cited hedge list — the step that has to happen before any hedge can exist."*

---

## Why no one has done it (the structural answer)

- **The hedging crowd (Pillar, bank desks)** starts the conversation *after* exposures are known — they're built for customers who already speak the language, so they *skip* discovery entirely.
- **The accounting crowd (Agicap, Pennylane, YC AIs)** reads the books for bookkeeping, not for risk — a flour invoice is a cost category to them, never a wheat position.
- **The data crowd (Bloomberg, Refinitiv)** sells the price of the underlying but never the bridge from that underlying to *your* specific cost line.

Spice is the only player that does the unglamorous bridge: **raw books → commodity underlyings → margin sensitivity → ranked hedge priority**, explainable and cited. That bridge is the empty center of the map — and it's the mandatory on-ramp to everything Spice does next.

---

## Defensibility — the mapping moat

Per-business, the agent is an exposure report. At scale it becomes irreplaceable:

- **Mapping corpus** — every accounting label resolved to an underlying (and every correction the business owner makes) trains a mapping layer no competitor can match: the dictionary from messy real-world cost lines to commodity exposures.
- **Sensitivity priors** — across millions of SMBs, Spice learns how each business input's price actually tracks its underlying — real elasticities, not textbook assumptions.
- **The endgame** — exposure discovery is the wedge that makes Spice the default first step. Once Spice has mapped a business's risk, it owns the natural next action: hedging it. Discovery feeds execution; execution feeds [the data moat](COMPETITION.md).

---

*Sources behind the 2026 figures: YC Spring 2026 RFS; Insee commodity & producer-price series (used for historical shock calibration); Agicap 7,000+ clients across 12+ countries; Pillar positioning (corporate hedging optimization, exposures-assumed). See [COMPETITION.md](COMPETITION.md) for the broader YIELD/Spice competitive map.*

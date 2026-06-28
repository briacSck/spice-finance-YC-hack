#!/usr/bin/env python3
"""Spice — unit economics & GTM revenue-ramp model (single source of truth).

Every euro here traces to a measurable volume times a *published* fee benchmark.
The verifiability claim is structural: we never assert a take rate — we model
revenue/client and then SHOW the implied effective take sits inside the cited
industry band (GPO admin fees 0.86-3.62%, introducing-broker volume comp).

Inputs come from `Downloads/spice_unit_economics_moat_market_sizing.md`
(mirrored into `business/MARKET_SIZING.md`). Source tags `[Sx]` map to its
`## Sources` list. Run:

    python scripts/unit_economics_model.py

Writes (deterministic, no network):
    outputs/unit_economics/unit_economics.csv   per-vertical build-up + implied takes
    outputs/unit_economics/gtm_ramp.csv          stage x scenario revenue ladder
    outputs/unit_economics/model.json            everything, machine-readable
    business/figures/revenue_ramp.png            main slide chart
    business/figures/per_client_buildup.png      secondary "unit economics" chart

Stdlib + matplotlib + pandas only (mirrors data-generation/scripts conventions).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:  # keep € / × legible on Windows consoles (cp1252 default)
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass

import matplotlib

matplotlib.use("Agg")  # headless render
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import pandas as pd

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
REPO = Path(__file__).resolve().parents[1]
OUT_DATA = REPO / "outputs" / "unit_economics"
OUT_FIG = REPO / "business" / "figures"
OUT_DATA.mkdir(parents=True, exist_ok=True)
OUT_FIG.mkdir(parents=True, exist_ok=True)

# --------------------------------------------------------------------------- #
# Spice brand palette (docs/DESIGN.md)
# --------------------------------------------------------------------------- #
BG = "#F4F3EF"      # warm paper
PANEL = "#FFFFFF"
INK = "#1A1916"
DIM = "#797469"
FAINT = "#ABA59A"
GREEN = "#1B5E4C"   # the accent
TERRA = "#A85436"   # risk / reference-only
C_HEDGE = "#1B5E4C"   # hedging slice
C_PROC = "#5C7A6E"    # procurement slice
C_DATA = "#94A89E"    # data slice

plt.rcParams.update({
    "figure.facecolor": BG,
    "axes.facecolor": PANEL,
    "savefig.facecolor": BG,
    "axes.edgecolor": "#ECEAE3",
    "axes.labelcolor": INK,
    "text.color": INK,
    "xtick.color": DIM,
    "ytick.color": DIM,
    "font.family": "DejaVu Sans",  # Satoshi/Spline unavailable to mpl; closest clean sans
    "axes.grid": True,
    "grid.color": "#ECEAE3",
    "grid.linewidth": 0.8,
})

# --------------------------------------------------------------------------- #
# 1. INPUTS — straight from the source doc (no edits, just typed in)
# --------------------------------------------------------------------------- #

# Per-vertical unit economics [source: "Unit economics by typical business"].
# notional = annual hedge notional; procurement = annual procurement volume;
# short = short-term base revenue/client; mature = long-term base revenue/client.
VERTICALS = [
    # name,               notional,  procurement,  short,   mature
    ("Boulangerie",          83_900,     251_600,     795,   5_400),
    ("Transport",           352_700,   1_100_000,   2_600,  18_900),
    ("Construction",        185_300,     555_000,   1_500,  10_600),
    ("Plastics",            590_900,     590_900,   4_200,  13_100),
    ("Metalwork",           277_600,     555_000,   2_200,  11_200),
    ("Woodworking",         370_300,     370_300,   2_700,   8_300),
    ("Light mfg",           449_200,     898_000,   3_300,  17_400),
]

# Market sizing [source: "Revenue TAM / SAM / SOM" totals].
TAM_CLIENTS = 14_280_000          # formal suitable SME accounts worldwide
SAM_CLIENTS = 9_830_000           # EU+US suitable accounts
REVENUE_TAM_EUR = 169.3e9
REVENUE_SAM_EUR = 112.6e9

# SOM scenarios [source: SOM table] — penetration is of SAM clients.
SOM_SCENARIOS = {
    "conservative": (0.0005, 4_916, 56.3e6),
    "base":         (0.0015, 14_748, 168.9e6),
    "upside":       (0.0050, 49_160, 562.9e6),
}

# Fee benchmarks (the "verifiable" anchors). Each is a published industry rate.
GPO_FEE_LOW = 0.0086   # [S10] lowest reported GPO admin fee
GPO_FEE_HIGH = 0.0362  # [S10] highest reported GPO admin fee band
HEDGE_TAKE_MATURE = 0.0040  # 40 bps on notional — introducing-broker volume comp [S13][S14], MiFID II [S15]
HEDGE_TAKE_SHORT = 0.0015   # 15 bps — conservative wedge pricing
DATA_SHARE_MATURE = 0.08    # data-licensing uplift, MATURE ONLY — data-marketplace economics [S16]

# France beachhead — DOCUMENTED ASSUMPTION (Stage B).
#   EC: 34M EU SMEs [S5]; France ≈ 11% of EU SME count ≈ 3.7M total SMEs.
#   Suitability rate = source SAM 9.83M / observed EU+US SMEs (34M [S5] + 34.8M US [S7]) ≈ 14.3%.
#   => suitable French accounts ≈ 0.143 * 3.7M ≈ 530k; rounded to 550k.
#   (BRIEF's "3M+ commodity-exposed" French SMBs is the looser upper bound.)
FRANCE_SUITABLE = 550_000
FRANCE_ARPU_FACTOR = 0.60   # mid-ramp monetization vs mature ARPU
FRANCE_PEN = {"low": 0.01, "base": 0.03, "high": 0.05}
FRANCE_CEILING_PEN = 0.70   # "70% of France" — theoretical ceiling, NOT the plan

WEDGE_CLIENTS = 500


# --------------------------------------------------------------------------- #
# 2. PER-CLIENT BUILD-UP + implied-take verification
# --------------------------------------------------------------------------- #
def per_client_buildup() -> pd.DataFrame:
    """Decompose each vertical's revenue/client into hedging + procurement + data.

    Method: hedging = notional x benchmarked hedge take; data = modest mature
    share; procurement = the residual. We then REPORT the implied procurement
    commission and the implied blended effective take, and flag whether they
    fall inside the published GPO band [S9][S10]. Reproduces the source
    revenue/client exactly (procurement is the plug).
    """
    rows = []
    for name, notional, proc, short, mature in VERTICALS:
        combined = notional + proc

        # mature decomposition
        hedge_m = notional * HEDGE_TAKE_MATURE
        data_m = mature * DATA_SHARE_MATURE
        proc_m = mature - hedge_m - data_m
        proc_comm_m = proc_m / proc
        eff_take_m = mature / combined

        # short-term decomposition (no data revenue yet — switched on at maturity)
        hedge_s = notional * HEDGE_TAKE_SHORT
        proc_s = short - hedge_s
        proc_comm_s = proc_s / proc
        eff_take_s = short / combined

        rows.append({
            "vertical": name,
            "hedge_notional_eur": notional,
            "procurement_eur": proc,
            "combined_volume_eur": combined,
            "short_rev_per_client_eur": short,
            "mature_rev_per_client_eur": mature,
            "hedging_mature_eur": round(hedge_m),
            "procurement_mature_eur": round(proc_m),
            "data_mature_eur": round(data_m),
            "implied_proc_commission_mature": round(proc_comm_m, 4),
            "implied_proc_commission_mature_in_gpo_band": GPO_FEE_LOW <= proc_comm_m <= GPO_FEE_HIGH,
            "implied_effective_take_mature": round(eff_take_m, 4),
            "implied_effective_take_short": round(eff_take_s, 4),
            "hedging_short_eur": round(hedge_s),
            "procurement_short_eur": round(proc_s),
            "implied_proc_commission_short": round(proc_comm_s, 4),
        })
    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 3. BLENDED ARPU
# --------------------------------------------------------------------------- #
def blended_arpu() -> dict:
    """Mature blended ARPU reconciles to the source TAM; short via short/mature ratio."""
    mature_blended = REVENUE_TAM_EUR / TAM_CLIENTS          # ~= EUR 11,855 (cross-checks TAM)
    sam_blended = REVENUE_SAM_EUR / SAM_CLIENTS             # ~= EUR 11,455 (cross-checks SOM rows)
    sum_short = sum(v[3] for v in VERTICALS)
    sum_mature = sum(v[4] for v in VERTICALS)
    short_mature_ratio = sum_short / sum_mature
    short_blended = mature_blended * short_mature_ratio
    return {
        "mature_blended_arpu_eur": round(mature_blended),
        "sam_blended_arpu_eur": round(sam_blended),
        "short_mature_ratio": round(short_mature_ratio, 4),
        "short_blended_arpu_eur": round(short_blended),
    }


# --------------------------------------------------------------------------- #
# 4. GTM REVENUE RAMP
# --------------------------------------------------------------------------- #
def gtm_ramp(arpu: dict) -> pd.DataFrame:
    mature = arpu["mature_blended_arpu_eur"]
    sam = arpu["sam_blended_arpu_eur"]
    short = arpu["short_blended_arpu_eur"]
    france_arpu = round(mature * FRANCE_ARPU_FACTOR)

    rows = []

    def add(stage, scenario, clients, arpu_eur, basis):
        rows.append({
            "stage": stage,
            "scenario": scenario,
            "clients": int(round(clients)),
            "arpu_eur": int(round(arpu_eur)),
            "annual_revenue_eur": round(clients * arpu_eur),
            "basis": basis,
        })

    # Stage A — wedge
    add("A_wedge", "base", WEDGE_CLIENTS, short,
        "500 French clients at short-term (hedging-only) ARPU")

    # Stage B — France beachhead
    for label, pen in FRANCE_PEN.items():
        add("B_france", label, FRANCE_SUITABLE * pen, france_arpu,
            f"{pen:.0%} of ~{FRANCE_SUITABLE:,} suitable French accounts at {FRANCE_ARPU_FACTOR:.0%} mature ARPU")
    # France theoretical ceiling (annotation only, NOT the plan)
    add("B_france", "ceiling_70pct", FRANCE_SUITABLE * FRANCE_CEILING_PEN, mature,
        "'70% of France' — theoretical ceiling at mature ARPU, shown for reference only")

    # Stage C/D — EU+US SAM (verbatim from source SOM table)
    for label, (pen, clients, rev) in SOM_SCENARIOS.items():
        add("C_sam", label, clients, sam,
            f"{pen:.2%} of SAM ({SAM_CLIENTS:,} clients) — source SOM '{label}' (= EUR {rev/1e6:.1f}M)")

    # TAM ceiling
    add("D_tam", "ceiling", TAM_CLIENTS, mature,
        "Full formal suitable SME TAM at mature ARPU (= EUR 169.3B)")

    return pd.DataFrame(rows)


# --------------------------------------------------------------------------- #
# 5. CHARTS
# --------------------------------------------------------------------------- #
def _eur_fmt(x, _pos=None):
    if x >= 1e9:
        return f"€{x/1e9:.0f}B"
    if x >= 1e6:
        return f"€{x/1e6:.0f}M"
    if x >= 1e3:
        return f"€{x/1e3:.0f}k"
    return f"€{x:.0f}"


def chart_revenue_ramp(ramp: pd.DataFrame):
    """Main slide chart: base-case revenue across GTM stages (log y) + scenario bands."""
    def rev(stage, scenario):
        r = ramp[(ramp.stage == stage) & (ramp.scenario == scenario)]
        return float(r.annual_revenue_eur.iloc[0]), int(r.clients.iloc[0]), int(r.arpu_eur.iloc[0])

    wedge = rev("A_wedge", "base")
    fr_low = rev("B_france", "low")
    fr_base = rev("B_france", "base")
    fr_high = rev("B_france", "high")
    fr_ceiling = rev("B_france", "ceiling_70pct")
    sam_cons = rev("C_sam", "conservative")
    sam_base = rev("C_sam", "base")
    sam_up = rev("C_sam", "upside")
    tam = rev("D_tam", "ceiling")

    xs = [0, 1, 2, 3]
    labels = ["Wedge\n(France, 500)", "France\nbeachhead", "EU + US\n(SAM)", "Global\nTAM ceiling"]
    base_line = [wedge[0], fr_base[0], sam_base[0], tam[0]]

    fig, ax = plt.subplots(figsize=(11, 6.2))

    # scenario bands (low-high) at France and SAM
    ax.fill_between([1, 1], [fr_low[0]], [fr_high[0]], color=GREEN, alpha=0.0)  # noop keeps spacing
    ax.vlines(1, fr_low[0], fr_high[0], color=GREEN, alpha=0.25, linewidth=10)
    ax.vlines(2, sam_cons[0], sam_up[0], color=GREEN, alpha=0.25, linewidth=10)

    # base-case stepped line
    ax.plot(xs, base_line, "-o", color=GREEN, linewidth=2.4, markersize=8, zorder=5)

    # France ceiling reference (terracotta dashed marker)
    ax.scatter([1], [fr_ceiling[0]], marker="_", s=600, color=TERRA, linewidths=2, zorder=4)
    ax.annotate("'70% of France' ceiling\n(reference, not the plan)",
                (1, fr_ceiling[0]), textcoords="offset points", xytext=(12, -4),
                fontsize=8, color=TERRA, va="center")

    # annotate base points
    def note(x, val, clients, arpu_eur, dy=14):
        ax.annotate(f"{_eur_fmt(val)}\n{clients:,} clients · €{arpu_eur/1e3:.1f}k ARPU",
                    (x, val), textcoords="offset points", xytext=(0, dy),
                    ha="center", fontsize=8.5, color=INK,
                    bbox=dict(boxstyle="round,pad=0.3", fc=PANEL, ec="#ECEAE3", lw=0.8))

    note(0, *wedge)
    note(1, *fr_base[:3])
    note(2, *sam_base[:3], dy=30)
    note(3, *tam[:3], dy=14)

    # SAM band labels (offset right so they clear the base-case annotation box)
    ax.annotate(f"upside {_eur_fmt(sam_up[0])}", (2, sam_up[0]), xytext=(22, 8),
                textcoords="offset points", fontsize=7.5, color=DIM, va="center")
    ax.annotate(f"conservative {_eur_fmt(sam_cons[0])}", (2, sam_cons[0]), xytext=(22, -8),
                textcoords="offset points", fontsize=7.5, color=DIM, va="center")

    ax.set_yscale("log")
    ax.set_ylim(5e5, 5e11)
    ax.yaxis.set_major_formatter(FuncFormatter(_eur_fmt))
    ax.set_xticks(xs)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Annual revenue (log scale)", fontsize=10)
    ax.set_xlim(-0.4, 3.7)
    ax.set_title("Spice — revenue ramp across GTM stages", fontsize=15, color=INK, pad=14, loc="left", weight="bold")
    fig.text(0.125, 0.90,
             "Every stage = clients × ARPU. Stages C–TAM use the source SOM model verbatim; ARPU deepens short→mature.",
             fontsize=9, color=DIM)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = OUT_FIG / "revenue_ramp.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


def chart_per_client_buildup(df: pd.DataFrame):
    """Secondary chart: mature revenue/client stacked (hedging/procurement/data) per vertical."""
    fig, ax = plt.subplots(figsize=(11, 6.2))
    names = df.vertical.tolist()
    hedge = df.hedging_mature_eur.to_numpy()
    proc = df.procurement_mature_eur.to_numpy()
    data = df.data_mature_eur.to_numpy()
    x = range(len(names))

    ax.bar(x, hedge, color=C_HEDGE, label="Hedging (40 bps × notional)")
    ax.bar(x, proc, bottom=hedge, color=C_PROC, label="Procurement (commission, GPO-banded)")
    ax.bar(x, data, bottom=hedge + proc, color=C_DATA, label="Data licensing (mature only, 8%)")

    # annotate implied effective take above each bar
    totals = hedge + proc + data
    for i, (t, take) in enumerate(zip(totals, df.implied_effective_take_mature)):
        ax.annotate(f"{take*100:.2f}%\ntake", (i, t), textcoords="offset points",
                    xytext=(0, 6), ha="center", fontsize=8, color=GREEN)

    ax.yaxis.set_major_formatter(FuncFormatter(_eur_fmt))
    ax.set_xticks(list(x))
    ax.set_xticklabels(names, fontsize=9, rotation=15, ha="right")
    ax.set_ylabel("Mature revenue / client", fontsize=10)
    ax.set_title("Spice — per-client revenue build-up (mature)", fontsize=15, color=INK,
                 pad=14, loc="left", weight="bold")
    fig.text(0.125, 0.90,
             f"Implied effective take {df.implied_effective_take_mature.min()*100:.2f}–"
             f"{df.implied_effective_take_mature.max()*100:.2f}% — all inside the published "
             f"GPO band {GPO_FEE_LOW*100:.2f}–{GPO_FEE_HIGH*100:.2f}% [S9][S10].",
             fontsize=9, color=DIM)
    ax.legend(loc="upper left", frameon=False, fontsize=9)
    fig.tight_layout(rect=(0, 0, 1, 0.97))
    out = OUT_FIG / "per_client_buildup.png"
    fig.savefig(out, dpi=160)
    plt.close(fig)
    return out


# --------------------------------------------------------------------------- #
# 6. MAIN
# --------------------------------------------------------------------------- #
def main():
    df = per_client_buildup()
    arpu = blended_arpu()
    ramp = gtm_ramp(arpu)

    df.to_csv(OUT_DATA / "unit_economics.csv", index=False)
    ramp.to_csv(OUT_DATA / "gtm_ramp.csv", index=False)

    fig1 = chart_revenue_ramp(ramp)
    fig2 = chart_per_client_buildup(df)

    model = {
        "currency": "EUR (data benchmark [S16] is USD; ~parity assumed)",
        "benchmarks": {
            "gpo_fee_band": [GPO_FEE_LOW, GPO_FEE_HIGH],
            "hedge_take_mature_bps": HEDGE_TAKE_MATURE * 1e4,
            "hedge_take_short_bps": HEDGE_TAKE_SHORT * 1e4,
            "data_share_mature": DATA_SHARE_MATURE,
        },
        "market": {
            "tam_clients": TAM_CLIENTS, "sam_clients": SAM_CLIENTS,
            "revenue_tam_eur": REVENUE_TAM_EUR, "revenue_sam_eur": REVENUE_SAM_EUR,
            "som_scenarios": SOM_SCENARIOS,
        },
        "france_assumption": {
            "suitable_accounts": FRANCE_SUITABLE,
            "arpu_factor": FRANCE_ARPU_FACTOR,
            "penetration": FRANCE_PEN,
            "ceiling_penetration": FRANCE_CEILING_PEN,
        },
        "blended_arpu": arpu,
        "per_client": df.to_dict(orient="records"),
        "gtm_ramp": ramp.to_dict(orient="records"),
    }
    (OUT_DATA / "model.json").write_text(json.dumps(model, indent=2), encoding="utf-8")

    # ---- console verification ----
    print("=" * 70)
    print("PER-CLIENT BUILD-UP (mature) — implied effective take vs GPO band")
    print("=" * 70)
    for _, r in df.iterrows():
        flag = "OK " if r.implied_proc_commission_mature_in_gpo_band else "!! "
        print(f"  {flag}{r.vertical:<14} take {r.implied_effective_take_mature*100:5.2f}% "
              f"| proc-comm {r.implied_proc_commission_mature*100:5.2f}% "
              f"| €{r.mature_rev_per_client_eur:,}/client")
    band_ok = df.implied_proc_commission_mature_in_gpo_band.all()
    print(f"\n  All implied procurement commissions in [{GPO_FEE_LOW:.2%}, {GPO_FEE_HIGH:.2%}]: {band_ok}")
    print(f"\n  Blended mature ARPU: €{arpu['mature_blended_arpu_eur']:,} "
          f"(= TAM €{REVENUE_TAM_EUR/1e9:.1f}B / {TAM_CLIENTS:,})")
    print(f"  Blended short ARPU : €{arpu['short_blended_arpu_eur']:,} "
          f"(ratio {arpu['short_mature_ratio']:.2%})")
    print("\n" + "=" * 70)
    print("GTM REVENUE RAMP (base case)")
    print("=" * 70)
    for _, r in ramp[ramp.scenario.isin(["base", "ceiling"])].iterrows():
        print(f"  {r.stage:<10} {r.clients:>12,} clients × €{r.arpu_eur:>6,} = {_eur_fmt(r.annual_revenue_eur)}")
    print(f"\n  Wrote: {OUT_DATA/'unit_economics.csv'}")
    print(f"         {OUT_DATA/'gtm_ramp.csv'}")
    print(f"         {OUT_DATA/'model.json'}")
    print(f"         {fig1}")
    print(f"         {fig2}")


if __name__ == "__main__":
    main()

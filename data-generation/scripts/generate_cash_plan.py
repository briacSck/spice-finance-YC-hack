from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path
import sys


DATA_GEN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = DATA_GEN_ROOT.parent
if str(DATA_GEN_ROOT) not in sys.path:
    sys.path.insert(0, str(DATA_GEN_ROOT))

from cashplan.business_profiles import infer_business_profile, slugify
from cashplan.data_sources import CommodityDataProvider, fetch_insee_sdmx_url
from cashplan.workbook import build_cash_plan_workbook


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate a Spice-style monthly cash-plan workbook for a business type.",
    )
    parser.add_argument(
        "business_type",
        help='Business description, e.g. "boulangerie artisanale", "transport routier", "plasturgie".',
    )
    parser.add_argument(
        "--annual-revenue",
        type=float,
        default=None,
        help="Target year-1 annual revenue in EUR. If omitted, the selected archetype default is used.",
    )
    parser.add_argument("--start-year", type=int, default=datetime.now().year, help="First model year.")
    parser.add_argument("--years", type=int, default=3, choices=[1, 2, 3, 4, 5], help="Number of forecast years.")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed for synthetic variations.")
    parser.add_argument(
        "--online",
        action="store_true",
        help="Try live commodity APIs. Falls back to cached/synthetic data if unavailable.",
    )
    parser.add_argument(
        "--alpha-vantage-key",
        default=None,
        help="Optional Alpha Vantage API key for commodity endpoints.",
    )
    parser.add_argument(
        "--entsoe-token",
        default=None,
        help="Optional ENTSO-E security token for France day-ahead electricity prices.",
    )
    parser.add_argument(
        "--insee-sdmx-url",
        default=None,
        help="Optional full INSEE BDM/SDMX URL to fetch and cache for benchmark work.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output .xlsx path. Defaults to outputs/cashplans/<business>.xlsx.",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=REPO_ROOT / ".cache" / "cashplan",
        help="Cache directory for downloaded market/INSEE data.",
    )
    parser.add_argument(
        "--template",
        type=Path,
        default=None,
        help="Optional path to the reference workbook. Recorded for traceability only; not modified.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    profile = infer_business_profile(args.business_type, args.annual_revenue, args.seed)
    alpha_vantage_key = args.alpha_vantage_key or _load_secret("ALPHA_VANTAGE_API_KEY")
    entsoe_token = args.entsoe_token or _load_secret("ENTSOE_SECURITY_TOKEN")

    output_path = args.output
    if output_path is None:
        output_path = REPO_ROOT / "outputs" / "cashplans" / f"{slugify(args.business_type)}_cash_plan.xlsx"

    provider = CommodityDataProvider(
        cache_dir=args.cache_dir,
        online=args.online,
        alpha_vantage_key=alpha_vantage_key,
        entsoe_token=entsoe_token,
        seed=args.seed,
    )

    if args.insee_sdmx_url:
        payload = fetch_insee_sdmx_url(args.insee_sdmx_url, args.cache_dir)
        status = "cached" if payload else "unavailable"
        print(f"INSEE SDMX fetch: {status}")

    if args.template:
        if not args.template.exists():
            print(f"Warning: template not found: {args.template}")
        else:
            print(f"Reference template: {args.template}")

    output = build_cash_plan_workbook(
        profile=profile,
        output_path=output_path,
        data_provider=provider,
        start_year=args.start_year,
        years=args.years,
    )
    print(f"Generated: {output}")
    print(f"Archetype: {profile.archetype}")
    print(f"Revenue A1: {profile.annual_revenue:,.0f} EUR")
    print(f"API mode: {'online' if args.online else 'offline'}")
    print(f"Alpha Vantage: {'configured' if alpha_vantage_key else 'not configured'}")
    print(f"ENTSO-E: {'configured' if entsoe_token else 'not configured'}")
    return 0


def _load_secret(name: str) -> str | None:
    value = os.environ.get(name)
    if value:
        return value.strip()

    env_path = REPO_ROOT / ".env"
    if not env_path.exists():
        return None

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, raw_value = line.split("=", 1)
        if key.strip() == name:
            return raw_value.strip().strip('"').strip("'") or None
    return None


if __name__ == "__main__":
    raise SystemExit(main())

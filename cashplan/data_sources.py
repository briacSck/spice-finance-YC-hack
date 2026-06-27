from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import io
import json
import math
from pathlib import Path
import random
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import urlopen

import openpyxl


WORLD_BANK_PINK_SHEET_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "5d903e848db1d1b83e0ec8f744e55570-0350012021/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"

DEFAULT_BASE_PRICES = {
    "WTI": 78.0,
    "BRENT": 82.0,
    "NATURAL_GAS": 3.2,
    "COPPER": 8_200.0,
    "ALUMINUM": 2_500.0,
    "WHEAT": 275.0,
    "SUGAR": 0.47,
    "COCOA": 7_000.0,
    "WOOD": 420.0,
    "ELECTRICITY": 0.17,
}

DEFAULT_VOLATILITY = {
    "WTI": 0.08,
    "BRENT": 0.08,
    "NATURAL_GAS": 0.12,
    "COPPER": 0.08,
    "ALUMINUM": 0.06,
    "WHEAT": 0.08,
    "SUGAR": 0.07,
    "COCOA": 0.14,
    "WOOD": 0.05,
    "ELECTRICITY": 0.05,
}

WORLD_BANK_LABEL_HINTS = {
    "WTI": ["crude oil, wti"],
    "BRENT": ["crude oil, brent"],
    "NATURAL_GAS": ["natural gas, us", "natural gas, europe"],
    "COPPER": ["copper"],
    "ALUMINUM": ["aluminum", "aluminium"],
    "WHEAT": ["wheat, us hrw", "wheat"],
    "SUGAR": ["sugar, world", "sugar"],
    "COCOA": ["cocoa"],
    "WOOD": ["logs", "sawnwood", "timber"],
}


@dataclass(frozen=True)
class PricePoint:
    month: str
    value: float
    source: str


@dataclass(frozen=True)
class PriceSeries:
    code: str
    points: list[PricePoint]
    source: str

    def values_for_months(self, months: list[str], default: float) -> list[float]:
        by_month = {point.month: point.value for point in self.points}
        values: list[float] = []
        last = default
        for month in months:
            if month in by_month:
                last = by_month[month]
            values.append(float(last))
        return values


class CommodityDataProvider:
    def __init__(
        self,
        cache_dir: Path,
        online: bool = False,
        alpha_vantage_key: str | None = None,
        seed: int = 42,
    ) -> None:
        self.cache_dir = cache_dir
        self.online = online
        self.alpha_vantage_key = alpha_vantage_key
        self.seed = seed
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_series(self, code: str, months: list[str], unit_price_hint: float | None = None) -> PriceSeries:
        normalized_code = code.upper()
        if self.online and self.alpha_vantage_key:
            series = self._fetch_alpha_vantage(normalized_code)
            if series and series.points:
                return _trim_or_extend(series, months, unit_price_hint or DEFAULT_BASE_PRICES.get(normalized_code, 1.0))

        if self.online:
            series = self._fetch_world_bank(normalized_code)
            if series and series.points:
                return _trim_or_extend(series, months, unit_price_hint or DEFAULT_BASE_PRICES.get(normalized_code, 1.0))

        return self.synthetic_series(normalized_code, months, unit_price_hint)

    def synthetic_series(
        self,
        code: str,
        months: list[str],
        unit_price_hint: float | None = None,
        volatility: float | None = None,
    ) -> PriceSeries:
        base = unit_price_hint or DEFAULT_BASE_PRICES.get(code.upper(), 1.0)
        vol = volatility or DEFAULT_VOLATILITY.get(code.upper(), 0.05)
        rng = random.Random(f"{self.seed}:{code}")
        values: list[PricePoint] = []
        level = base
        drift = rng.uniform(-0.002, 0.006)
        for index, month in enumerate(months):
            seasonal = 1 + 0.03 * math.sin((index / 12) * 2 * math.pi + rng.random())
            shock = rng.gauss(drift, vol / 3.5)
            level = max(base * 0.25, level * (1 + shock))
            values.append(
                PricePoint(
                    month=month,
                    value=round(level * seasonal, 4),
                    source=f"synthetic fallback for {code}",
                )
            )
        return PriceSeries(code=code, points=values, source=f"synthetic fallback for {code}")

    def _fetch_alpha_vantage(self, code: str) -> PriceSeries | None:
        params = urlencode(
            {
                "function": code,
                "interval": "monthly",
                "apikey": self.alpha_vantage_key or "",
            }
        )
        url = f"{ALPHA_VANTAGE_URL}?{params}"
        cache_path = self.cache_dir / f"alpha_vantage_{code}.json"
        try:
            with urlopen(url, timeout=20) as response:
                payload = response.read().decode("utf-8")
            cache_path.write_text(payload, encoding="utf-8")
        except Exception:
            if cache_path.exists():
                payload = cache_path.read_text(encoding="utf-8")
            else:
                return None

        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            return None

        rows = data.get("data")
        if not isinstance(rows, list):
            return None

        points: list[PricePoint] = []
        for row in rows:
            try:
                month = str(row["date"])[:7]
                value = float(row["value"])
            except (KeyError, TypeError, ValueError):
                continue
            points.append(PricePoint(month=month, value=value, source="Alpha Vantage commodities API"))
        points.sort(key=lambda item: item.month)
        return PriceSeries(code=code, points=points, source="Alpha Vantage commodities API")

    def _fetch_world_bank(self, code: str) -> PriceSeries | None:
        xlsx_path = self.cache_dir / "world_bank_pink_sheet_monthly.xlsx"
        try:
            with urlopen(WORLD_BANK_PINK_SHEET_URL, timeout=30) as response:
                xlsx_path.write_bytes(response.read())
        except Exception:
            if not xlsx_path.exists():
                return None

        try:
            workbook = openpyxl.load_workbook(xlsx_path, data_only=True, read_only=True)
        except Exception:
            return None

        hints = WORLD_BANK_LABEL_HINTS.get(code, [code.lower()])
        for sheet in workbook.worksheets:
            parsed = _parse_world_bank_sheet(sheet, hints, code)
            if parsed:
                return parsed
        return None


def fetch_insee_sdmx_url(url: str, cache_dir: Path) -> str | None:
    """Fetch a user-provided INSEE SDMX URL and cache the raw response.

    INSEE BDM exposes many series via SDMX. The exact series IDs are domain
    choices, so this helper intentionally accepts a full URL instead of hiding a
    brittle guessed endpoint behind the generator.
    """

    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path = cache_dir / "insee_sdmx_response.xml"
    try:
        with urlopen(url, timeout=30) as response:
            payload = response.read().decode("utf-8", errors="replace")
        cache_path.write_text(payload, encoding="utf-8")
        return payload
    except Exception:
        if cache_path.exists():
            return cache_path.read_text(encoding="utf-8")
    return None


def _parse_world_bank_sheet(sheet: openpyxl.worksheet.worksheet.Worksheet, hints: Iterable[str], code: str) -> PriceSeries | None:
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return None

    date_columns: list[tuple[int, str]] = []
    for row_index in range(min(12, len(rows))):
        for col_index, value in enumerate(rows[row_index]):
            month = _coerce_month(value)
            if month:
                date_columns.append((col_index, month))
        if len(date_columns) >= 12:
            break

    if not date_columns:
        return None

    normalized_hints = [hint.lower() for hint in hints]
    for row in rows:
        label = " ".join(str(cell).lower() for cell in row[:4] if cell is not None)
        if not label:
            continue
        if not any(hint in label for hint in normalized_hints):
            continue

        points: list[PricePoint] = []
        for col_index, month in date_columns:
            if col_index >= len(row):
                continue
            try:
                value = float(row[col_index])
            except (TypeError, ValueError):
                continue
            points.append(PricePoint(month=month, value=value, source="World Bank Pink Sheet"))
        if points:
            points.sort(key=lambda item: item.month)
            return PriceSeries(code=code, points=points, source="World Bank Pink Sheet")
    return None


def _coerce_month(value: object) -> str | None:
    if isinstance(value, date):
        return f"{value.year:04d}-{value.month:02d}"
    if isinstance(value, str):
        text = value.strip()
        for fmt in ("%YM%m", "%Y-%m", "%b %Y", "%Y %b"):
            parsed = _try_parse_month(text, fmt)
            if parsed:
                return parsed
        if len(text) >= 7 and text[:4].isdigit() and text[4] in "-/":
            return f"{text[:4]}-{int(text[5:7]):02d}"
    return None


def _try_parse_month(value: str, fmt: str) -> str | None:
    from datetime import datetime

    try:
        parsed = datetime.strptime(value, fmt)
    except ValueError:
        return None
    return f"{parsed.year:04d}-{parsed.month:02d}"


def _trim_or_extend(series: PriceSeries, months: list[str], default: float) -> PriceSeries:
    values = series.values_for_months(months, default)
    first_non_zero = next((value for value in values if value), None)
    if first_non_zero:
        scale = default / first_non_zero
        values = [value * scale for value in values]
    points = [
        PricePoint(month=month, value=round(value, 4), source=series.source)
        for month, value in zip(months, values, strict=True)
    ]
    return PriceSeries(code=series.code, points=points, source=series.source)

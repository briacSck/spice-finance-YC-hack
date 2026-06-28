from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
import json
import math
from pathlib import Path
import random
from typing import Iterable
from urllib.parse import urlencode
from urllib.request import urlopen
import xml.etree.ElementTree as ET

import openpyxl


WORLD_BANK_PINK_SHEET_URL = (
    "https://thedocs.worldbank.org/en/doc/"
    "5d903e848db1d1b83e0ec8f744e55570-0350012021/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)

ALPHA_VANTAGE_URL = "https://www.alphavantage.co/query"
ENTSOE_URL = "https://web-api.tp.entsoe.eu/api"
ENTSOE_FRANCE_DOMAIN = "10YFR-RTE------C"
INSEE_SERIES_URL = "https://bdm.insee.fr/series/sdmx/data/SERIES_BDM"
ALPHA_VANTAGE_SUPPORTED = {
    "WTI",
    "BRENT",
    "NATURAL_GAS",
    "COPPER",
    "ALUMINUM",
    "WHEAT",
    "SUGAR",
}

INSEE_SERIES = {
    "ALUMINUM": "010002041",
    "ACCOUNTING_SERVICES": "010766437",
    "ADMIN_SERVICES": "010766756",
    "BRENT": "010002078",
    "BUTTER": "010763694",
    "CONSTRUCTION_COST": "011800507",
    "COCOA": "010002048",
    "COPPER": "010767327",
    "CREAM": "010763691",
    "DAIRY_FATS": "010763706",
    "DIESEL": "010002076",
    "EGGS": "010776696",
    "ELECTRICITY": "010777317",
    "EQUIPMENT_RENTAL": "010766451",
    "FOOD_PRODUCTS": "010763739",
    "IRON_ORE": "010002059",
    "LABOR_CONSTRUCTION": "010762002",
    "LABOR_GENERIC": "010761999",
    "LABOR_HOSPITALITY": "010762009",
    "LABOR_INDUSTRY": "010762004",
    "LABOR_TRANSPORT": "010762008",
    "LEAD": "010002064",
    "MAINTENANCE": "010777481",
    "NATURAL_GAS": "010767333",
    "NICKEL": "010767326",
    "PACKAGING_PAPER": "010763805",
    "RENT_COMMERCIAL": "001532540",
    "RENT_EQUIPMENT_CONSTRUCTION": "010766449",
    "RUBBER": "010763822",
    "SALT": "010766282",
    "SOFTWARE_SERVICES": "010766417",
    "SUGAR": "010002069",
    "TIN": "010002035",
    "WATER": "001634676",
    "WHEAT": "010002046",
    "WOOD": "010762320",
    "YEAST": "010763751",
    "ZINC": "010002072",
}

INSEE_DIRECT_PRICE_CONVERSIONS = {
    "COPPER": ("EUR/tonne -> EUR/kg", lambda value: value / 1000),
    "NATURAL_GAS": ("EUR/MWh -> EUR/kWh", lambda value: value / 1000),
    "NICKEL": ("EUR/tonne -> EUR/kg", lambda value: value / 1000),
}

DEFAULT_BASE_PRICES = {
    "WTI": 78.0,
    "BRENT": 82.0,
    "NATURAL_GAS": 3.2,
    "COPPER": 8_200.0,
    "ALUMINUM": 2_500.0,
    "IRON_ORE": 115.0,
    "STEEL_REBAR": 650.0,
    "LEAD": 2_100.0,
    "NICKEL": 18_000.0,
    "TIN": 28_000.0,
    "ZINC": 2_800.0,
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
    "IRON_ORE": 0.10,
    "STEEL_REBAR": 0.07,
    "LEAD": 0.07,
    "NICKEL": 0.11,
    "TIN": 0.10,
    "ZINC": 0.08,
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
    "IRON_ORE": ["iron ore"],
    "STEEL_REBAR": ["steel rebar", "steel"],
    "LEAD": ["lead"],
    "NICKEL": ["nickel"],
    "TIN": ["tin"],
    "ZINC": ["zinc"],
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
    price_basis: str = "normalized to model unit price"

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
        entsoe_token: str | None = None,
        seed: int = 42,
    ) -> None:
        self.cache_dir = cache_dir
        self.online = online
        self.alpha_vantage_key = alpha_vantage_key
        self.entsoe_token = entsoe_token
        self.seed = seed
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_series(self, code: str, months: list[str], unit_price_hint: float | None = None) -> PriceSeries:
        normalized_code = code.upper()
        if self.online and self.entsoe_token and normalized_code == "ELECTRICITY":
            series = self._fetch_entsoe_france_electricity(months)
            if series and series.points:
                return _trim_or_extend(series, months, unit_price_hint or DEFAULT_BASE_PRICES.get(normalized_code, 1.0))

        if self.online and normalized_code in INSEE_SERIES:
            series = self._fetch_insee_series(normalized_code)
            if series and series.points:
                if normalized_code in INSEE_DIRECT_PRICE_CONVERSIONS:
                    return _convert_direct_price_series(series, normalized_code, months)
                return _trim_or_extend(series, months, unit_price_hint or DEFAULT_BASE_PRICES.get(normalized_code, 1.0))

        if self.online and self.alpha_vantage_key and normalized_code in ALPHA_VANTAGE_SUPPORTED:
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

    def _fetch_insee_series(self, code: str) -> PriceSeries | None:
        idbank = INSEE_SERIES.get(code)
        if not idbank:
            return None

        cache_path = self.cache_dir / f"insee_series_{code}_{idbank}.xml"
        try:
            with urlopen(f"{INSEE_SERIES_URL}/{idbank}", timeout=30) as response:
                payload = response.read().decode("utf-8", errors="replace")
            cache_path.write_text(payload, encoding="utf-8")
        except Exception:
            if cache_path.exists():
                payload = cache_path.read_text(encoding="utf-8")
            else:
                return None

        return _parse_insee_series(payload, code, idbank)

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

    def _fetch_entsoe_france_electricity(self, months: list[str]) -> PriceSeries | None:
        if not months:
            return None

        start = datetime.strptime(months[0], "%Y-%m")
        end_year, end_month = map(int, months[-1].split("-"))
        end = _add_month(datetime(end_year, end_month, 1))
        params = urlencode(
            {
                "securityToken": self.entsoe_token or "",
                "documentType": "A44",
                "in_Domain": ENTSOE_FRANCE_DOMAIN,
                "out_Domain": ENTSOE_FRANCE_DOMAIN,
                "periodStart": start.strftime("%Y%m%d%H%M"),
                "periodEnd": end.strftime("%Y%m%d%H%M"),
            }
        )
        cache_path = self.cache_dir / "entsoe_france_electricity_day_ahead.xml"
        try:
            with urlopen(f"{ENTSOE_URL}?{params}", timeout=30) as response:
                payload = response.read().decode("utf-8", errors="replace")
            cache_path.write_text(payload, encoding="utf-8")
        except Exception:
            if cache_path.exists():
                payload = cache_path.read_text(encoding="utf-8")
            else:
                return None

        return _parse_entsoe_day_ahead(payload)


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


def _parse_entsoe_day_ahead(payload: str) -> PriceSeries | None:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return None

    values_by_month: dict[str, list[float]] = {}
    for period in _iter_local(root, "Period"):
        start_node = _find_local(period, "start")
        resolution_node = _find_local(period, "resolution")
        if start_node is None or not start_node.text:
            continue
        try:
            period_start = _parse_entsoe_time(start_node.text)
        except ValueError:
            continue
        step = _resolution_to_timedelta(resolution_node.text if resolution_node is not None else None)

        for point in _iter_local(period, "Point"):
            position_node = _find_local(point, "position")
            price_node = _find_local(point, "price.amount")
            if position_node is None or price_node is None:
                continue
            try:
                timestamp = period_start + step * (int(position_node.text or "1") - 1)
                value = float(price_node.text or "")
            except ValueError:
                continue
            values_by_month.setdefault(f"{timestamp.year:04d}-{timestamp.month:02d}", []).append(value)

    points = [
        PricePoint(month=month, value=round(sum(values) / len(values), 4), source="ENTSO-E day-ahead France electricity")
        for month, values in sorted(values_by_month.items())
        if values
    ]
    if not points:
        return None
    return PriceSeries(code="ELECTRICITY", points=points, source="ENTSO-E day-ahead France electricity")


def _parse_insee_series(payload: str, code: str, idbank: str) -> PriceSeries | None:
    try:
        root = ET.fromstring(payload)
    except ET.ParseError:
        return None

    points: list[PricePoint] = []
    title = ""
    for series in _iter_local(root, "Series"):
        if series.attrib.get("IDBANK") != idbank:
            continue
        title = series.attrib.get("TITLE_FR", "")
        for obs in _iter_local(series, "Obs"):
            month = obs.attrib.get("TIME_PERIOD")
            value = obs.attrib.get("OBS_VALUE")
            if not month or not value:
                continue
            try:
                parsed = float(value)
            except ValueError:
                continue
            points.append(
                PricePoint(
                    month=month[:7],
                    value=parsed,
                    source=f"INSEE BDM {idbank}",
                )
            )

    if not points:
        return None
    points.sort(key=lambda item: item.month)
    source = f"INSEE BDM {idbank}"
    if title:
        source = f"{source}: {title}"
    return PriceSeries(code=code, points=points, source=source)


def _iter_local(node: ET.Element, local_name: str) -> Iterable[ET.Element]:
    return (child for child in node.iter() if _local_name(child.tag) == local_name)


def _find_local(node: ET.Element, local_name: str) -> ET.Element | None:
    for child in node.iter():
        if _local_name(child.tag) == local_name:
            return child
    return None


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _parse_entsoe_time(value: str) -> datetime:
    normalized = value.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(normalized).replace(tzinfo=None)


def _resolution_to_timedelta(value: str | None) -> timedelta:
    if value == "PT15M":
        return timedelta(minutes=15)
    if value == "PT30M":
        return timedelta(minutes=30)
    return timedelta(hours=1)


def _add_month(value: datetime) -> datetime:
    if value.month == 12:
        return datetime(value.year + 1, 1, 1)
    return datetime(value.year, value.month + 1, 1)


def _convert_direct_price_series(series: PriceSeries, code: str, months: list[str]) -> PriceSeries:
    label, converter = INSEE_DIRECT_PRICE_CONVERSIONS[code]
    values = series.values_for_months(months, DEFAULT_BASE_PRICES.get(code, 1.0))
    points = [
        PricePoint(
            month=month,
            value=round(converter(value), 4),
            source=series.source,
        )
        for month, value in zip(months, values, strict=True)
    ]
    return PriceSeries(
        code=series.code,
        points=points,
        source=series.source,
        price_basis=f"direct INSEE price converted ({label})",
    )


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

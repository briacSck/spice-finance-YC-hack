"""Runtime settings loaded from environment (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _bool(v: str | None, default: bool) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    base_url: str = os.getenv("IBKR_BASE_URL", "https://localhost:5000/v1/api").rstrip("/")
    account_id: str = os.getenv("IBKR_ACCOUNT_ID", "DU0000000")
    verify_tls: bool = _bool(os.getenv("IBKR_VERIFY_TLS"), False)
    default_tif: str = os.getenv("IBKR_DEFAULT_TIF", "DAY")


@dataclass(frozen=True)
class AlpacaSettings:
    key: str = os.getenv("ALPACA_KEY", "")
    secret: str = os.getenv("ALPACA_SECRET", "")
    trading_url: str = os.getenv("ALPACA_TRADING_URL", "https://paper-api.alpaca.markets").rstrip("/")
    data_url: str = os.getenv("ALPACA_DATA_URL", "https://data.alpaca.markets").rstrip("/")


settings = Settings()
alpaca_settings = AlpacaSettings()

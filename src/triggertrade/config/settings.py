"""Safe bootstrap configuration for TriggerTrade."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import os
from typing import Mapping


class ConfigError(ValueError):
    """Raised when configuration would allow an unsafe runtime state."""


class TradingMode(StrEnum):
    PAPER = "paper"
    LIVE = "live"


class RuntimeMode(StrEnum):
    DEVELOPMENT = "development"
    TEST = "test"
    PRODUCTION = "production"


@dataclass(frozen=True)
class WatchlistItem:
    symbol: str
    enabled: bool = False


@dataclass(frozen=True)
class ExchangeConfig:
    name: str = "paper"
    api_key_env: str = "TRIGGERTRADE_EXCHANGE_API_KEY"
    api_secret_env: str = "TRIGGERTRADE_EXCHANGE_API_SECRET"


@dataclass(frozen=True)
class TriggerConfig:
    enabled: bool = False
    parameters: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class StrategyConfig:
    enabled: bool = False
    parameters: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RiskConfig:
    enabled: bool = False
    parameters: Mapping[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class AppConfig:
    runtime_mode: RuntimeMode = RuntimeMode.DEVELOPMENT
    trading_mode: TradingMode = TradingMode.PAPER
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    watchlist: tuple[WatchlistItem, ...] = ()
    triggers: Mapping[str, TriggerConfig] = field(default_factory=dict)
    strategies: Mapping[str, StrategyConfig] = field(default_factory=dict)
    risk: RiskConfig = field(default_factory=RiskConfig)


def load_config(env: Mapping[str, str] | None = None) -> AppConfig:
    """Load minimal config from environment without requiring secrets by default."""

    source = os.environ if env is None else env
    runtime_mode = _enum_value(
        RuntimeMode,
        source.get("TRIGGERTRADE_RUNTIME_MODE", RuntimeMode.DEVELOPMENT.value),
        "TRIGGERTRADE_RUNTIME_MODE",
    )
    trading_mode = _enum_value(
        TradingMode,
        source.get("TRIGGERTRADE_TRADING_MODE", TradingMode.PAPER.value),
        "TRIGGERTRADE_TRADING_MODE",
    )
    exchange = ExchangeConfig(name=source.get("TRIGGERTRADE_EXCHANGE", "paper"))

    if trading_mode is TradingMode.LIVE:
        _require_live_secret(source, exchange.api_key_env)
        _require_live_secret(source, exchange.api_secret_env)

    return AppConfig(
        runtime_mode=runtime_mode,
        trading_mode=trading_mode,
        exchange=exchange,
    )


def _enum_value(enum_type: type[TradingMode] | type[RuntimeMode], raw: str, env_name: str):
    try:
        return enum_type(raw.strip().lower())
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_type)
        raise ConfigError(f"{env_name} must be one of: {allowed}") from exc


def _require_live_secret(source: Mapping[str, str], env_name: str) -> None:
    value = source.get(env_name, "").strip()
    if not value or value.startswith("replace-with-"):
        raise ConfigError(f"{env_name} must be set before live trading mode can start")

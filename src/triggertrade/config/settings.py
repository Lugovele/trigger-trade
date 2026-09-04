"""Safe bootstrap configuration for TriggerTrade."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
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


class Market(StrEnum):
    SPOT = "spot"


class BybitEnvironment(StrEnum):
    DEMO = "demo"


class ExecutionVenue(StrEnum):
    LOCAL_PAPER = "local_paper"
    BYBIT_DEMO = "bybit_demo"


@dataclass(frozen=True)
class WatchlistItem:
    symbol: str
    enabled: bool = True


@dataclass(frozen=True)
class ExchangeConfig:
    name: str = "paper"
    api_key_env: str = "BYBIT_API_KEY"
    api_secret_env: str = "BYBIT_API_SECRET"


@dataclass(frozen=True)
class BybitConfig:
    environment: BybitEnvironment = BybitEnvironment.DEMO
    base_url: str = "https://api-demo.bybit.com"
    recv_window_ms: int = 5000
    account_types: tuple[str, ...] = ("UNIFIED", "SPOT")


@dataclass(frozen=True, repr=False)
class ApiCredentials:
    api_key: str
    api_secret: str


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
class TriggerRuleConfig:
    rule_id: str = "TRG-001"
    version: str = "0.1.0"
    status: str = "DRAFT_DEMO_ONLY"
    lookback_window: str = "1m"
    threshold_pct: Decimal = Decimal("-1.0")
    stale_after_seconds: int = 60


@dataclass(frozen=True)
class StrategyRuleConfig:
    rule_id: str = "STR-001"
    version: str = "0.1.0"
    status: str = "DRAFT_DEMO_ONLY"
    enabled: bool = True


@dataclass(frozen=True)
class RiskRulesConfig:
    max_demo_order_notional: Decimal = Decimal("6")
    stale_after_seconds: int = 60


@dataclass(frozen=True)
class AppConfig:
    runtime_mode: RuntimeMode = RuntimeMode.DEVELOPMENT
    trading_mode: TradingMode = TradingMode.PAPER
    live_trading_enabled: bool = False
    execution_venue: ExecutionVenue = ExecutionVenue.LOCAL_PAPER
    market: Market = Market.SPOT
    exchange: ExchangeConfig = field(default_factory=ExchangeConfig)
    bybit: BybitConfig = field(default_factory=BybitConfig)
    watchlist: tuple[WatchlistItem, ...] = ()
    triggers: Mapping[str, TriggerConfig] = field(default_factory=dict)
    strategies: Mapping[str, StrategyConfig] = field(default_factory=dict)
    risk: RiskConfig = field(default_factory=RiskConfig)
    trigger_rule: TriggerRuleConfig = field(default_factory=TriggerRuleConfig)
    strategy_rule: StrategyRuleConfig = field(default_factory=StrategyRuleConfig)
    risk_rules: RiskRulesConfig = field(default_factory=RiskRulesConfig)


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
    live_trading_enabled = _bool_value(
        source.get("TRIGGERTRADE_LIVE_TRADING_ENABLED", "false"),
        "TRIGGERTRADE_LIVE_TRADING_ENABLED",
    )
    execution_venue = _enum_value(
        ExecutionVenue,
        source.get("TRIGGERTRADE_EXECUTION_VENUE", ExecutionVenue.LOCAL_PAPER.value),
        "TRIGGERTRADE_EXECUTION_VENUE",
    )
    market = _enum_value(
        Market,
        source.get("TRIGGERTRADE_MARKET", Market.SPOT.value),
        "TRIGGERTRADE_MARKET",
    )
    exchange = ExchangeConfig(name=source.get("TRIGGERTRADE_EXCHANGE", "paper"))
    bybit = BybitConfig(
        environment=_enum_value(
            BybitEnvironment,
            source.get("TRIGGERTRADE_BYBIT_ENV", BybitEnvironment.DEMO.value),
            "TRIGGERTRADE_BYBIT_ENV",
        ),
        base_url=source.get("BYBIT_BASE_URL", BybitConfig.base_url).rstrip("/"),
    )
    watchlist = _watchlist(source.get("TRIGGERTRADE_WATCHLIST", ""))
    trigger_rule = TriggerRuleConfig(
        lookback_window=source.get("TRIGGERTRADE_TRG_001_LOOKBACK_WINDOW", "1m"),
        threshold_pct=_decimal_value(
            source.get("TRIGGERTRADE_TRG_001_THRESHOLD_PCT", "-1.0"),
            "TRIGGERTRADE_TRG_001_THRESHOLD_PCT",
        ),
        stale_after_seconds=_int_value(
            source.get("TRIGGERTRADE_STALE_AFTER_SECONDS", "60"),
            "TRIGGERTRADE_STALE_AFTER_SECONDS",
        ),
    )
    strategy_rule = StrategyRuleConfig(
        enabled=_bool_value(source.get("TRIGGERTRADE_STR_001_ENABLED", "true"), "TRIGGERTRADE_STR_001_ENABLED")
    )
    risk_rules = RiskRulesConfig(
        max_demo_order_notional=_decimal_value(
            source.get("TRIGGERTRADE_MAX_DEMO_ORDER_NOTIONAL", "6"),
            "TRIGGERTRADE_MAX_DEMO_ORDER_NOTIONAL",
        ),
        stale_after_seconds=trigger_rule.stale_after_seconds,
    )

    if trading_mode is TradingMode.LIVE or live_trading_enabled:
        _require_live_secret(source, exchange.api_key_env)
        _require_live_secret(source, exchange.api_secret_env)
    if trading_mode is not TradingMode.PAPER or live_trading_enabled:
        raise ConfigError("this integration slice requires paper mode with live trading disabled")

    return AppConfig(
        runtime_mode=runtime_mode,
        trading_mode=trading_mode,
        live_trading_enabled=live_trading_enabled,
        execution_venue=execution_venue,
        market=market,
        exchange=exchange,
        bybit=bybit,
        watchlist=watchlist,
        trigger_rule=trigger_rule,
        strategy_rule=strategy_rule,
        risk_rules=risk_rules,
    )


def load_bybit_credentials(env: Mapping[str, str] | None = None) -> ApiCredentials:
    """Load Bybit credentials for explicit private connectivity checks."""

    source = os.environ if env is None else env
    key = source.get("BYBIT_API_KEY", "").strip()
    secret = source.get("BYBIT_API_SECRET", "").strip()
    if not key or key.startswith("PASTE_"):
        raise ConfigError("BYBIT_API_KEY is required for private Bybit Demo connectivity")
    if not secret or secret.startswith("PASTE_"):
        raise ConfigError("BYBIT_API_SECRET is required for private Bybit Demo connectivity")
    return ApiCredentials(api_key=key, api_secret=secret)


def _enum_value(
    enum_type: (
        type[TradingMode]
        | type[RuntimeMode]
        | type[Market]
        | type[BybitEnvironment]
        | type[ExecutionVenue]
    ),
    raw: str,
    env_name: str,
):
    try:
        return enum_type(raw.strip().lower())
    except ValueError as exc:
        allowed = ", ".join(member.value for member in enum_type)
        raise ConfigError(f"{env_name} must be one of: {allowed}") from exc


def _require_live_secret(source: Mapping[str, str], env_name: str) -> None:
    value = source.get(env_name, "").strip()
    if not value or value.startswith("replace-with-") or value.startswith("PASTE_"):
        raise ConfigError(f"{env_name} must be set before live trading mode can start")


def _bool_value(raw: str, env_name: str) -> bool:
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{env_name} must be true or false")


def _watchlist(raw: str) -> tuple[WatchlistItem, ...]:
    symbols = [symbol.strip().upper() for symbol in raw.split(",") if symbol.strip()]
    return tuple(WatchlistItem(symbol=symbol) for symbol in symbols)


def _decimal_value(raw: str, env_name: str) -> Decimal:
    try:
        return Decimal(raw.strip())
    except Exception as exc:
        raise ConfigError(f"{env_name} must be a decimal value") from exc


def _int_value(raw: str, env_name: str) -> int:
    try:
        value = int(raw.strip())
    except ValueError as exc:
        raise ConfigError(f"{env_name} must be an integer") from exc
    if value <= 0:
        raise ConfigError(f"{env_name} must be positive")
    return value

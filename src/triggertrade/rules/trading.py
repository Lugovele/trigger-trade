"""Immutable trading rules versions used by futures runtime decisions."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from hashlib import sha256
import json
from typing import Callable, Mapping

from triggertrade.config import AppConfig


TRADING_RULES_SCHEMA_VERSION = "trading-rules-v1"
TRADING_RULES_SCOPE_LIVE = "LIVE"


class TradingRulesError(ValueError):
    pass


class TakeProfitMode(StrEnum):
    FIXED = "FIXED"
    DYNAMIC = "DYNAMIC"


class DirectionMode(StrEnum):
    LONG_SHORT = "LONG_SHORT"
    LONG_ONLY = "LONG_ONLY"
    SHORT_ONLY = "SHORT_ONLY"


@dataclass(frozen=True)
class CoinRule:
    symbol: str
    enabled: bool = True
    max_allocation_pct: Decimal | None = None


@dataclass(frozen=True)
class TradingRulesVersionDraft:
    position_size_pct: Decimal
    take_profit_mode: TakeProfitMode
    fixed_take_profit_pct: Decimal | None
    minimum_take_profit_pct: Decimal | None
    stop_loss_pct: Decimal
    minimum_risk_reward: Decimal
    minimum_net_edge_enabled: bool
    minimum_net_edge_pct: Decimal | None
    leverage: Decimal
    max_capital_in_positions_pct: Decimal
    max_open_positions_enabled: bool
    max_open_positions: int | None
    max_positions_per_coin_enabled: bool
    max_positions_per_coin: int | None
    direction_mode: DirectionMode
    daily_loss_limit_enabled: bool
    daily_loss_limit_pct: Decimal | None
    maker_fee_rate: Decimal
    taker_fee_rate: Decimal
    spread_cost: Decimal
    slippage_cost: Decimal
    funding_cost: Decimal
    coins: tuple[CoinRule, ...]
    metadata: Mapping[str, str] | None = None


@dataclass(frozen=True)
class TradingRulesVersion:
    rules_version_id: str
    version: str
    created_at: str
    created_from_version_id: str | None
    created_source: str
    change_summary: str
    config_hash: str
    schema_version: str
    draft: TradingRulesVersionDraft
    is_current: bool = False


@dataclass(frozen=True)
class TradingRulesUsage:
    rules_version_id: str
    usage_type: str
    entity_id: str
    entity_version: str | None
    context: str | None
    created_at: str


@dataclass(frozen=True)
class TradingRulesChange:
    changed: bool
    rules: TradingRulesVersion
    change_summary: str


class TradingRulesService:
    """Service boundary for immutable TradingRulesVersion lifecycle."""

    def __init__(self, store, *, symbol_validator: Callable[[str], object] | None = None) -> None:
        self._store = store
        self._symbol_validator = symbol_validator

    def ensure_initial_version(self, config: AppConfig, *, created_at: str = "2026-09-07T00:00:00+00:00") -> TradingRulesVersion:
        draft = build_initial_trading_rules(config)
        return self._store.bootstrap_initial(draft, created_at=created_at, created_source="config_bootstrap")

    def get_current_rules_version(self) -> TradingRulesVersion:
        current = self._store.get_current()
        if current is None:
            raise TradingRulesError("current trading rules version is not initialized")
        return current

    def create_rules_version_from_current(self, *, changes: Mapping[str, object], created_source: str = "service", created_at: str | None = None) -> TradingRulesChange:
        current = self.get_current_rules_version()
        draft = apply_changes(current.draft, changes)
        validate_rules_draft(draft, symbol_validator=self._symbol_validator)
        if semantic_hash(draft) == current.config_hash:
            return TradingRulesChange(False, current, "No semantic changes")
        version = self._store.create_next_version(
            draft,
            created_from_version_id=current.rules_version_id,
            created_source=created_source,
            change_summary=change_summary(current.draft, draft),
            created_at=created_at or datetime.now(UTC).isoformat(),
        )
        return TradingRulesChange(True, version, version.change_summary)

    def list_rules_versions(self) -> tuple[TradingRulesVersion, ...]:
        return self._store.list_versions()

    def get_rules_version(self, rules_version_id_or_version: str) -> TradingRulesVersion | None:
        return self._store.get_version(rules_version_id_or_version)

    def record_usage(self, usage: TradingRulesUsage) -> bool:
        return self._store.record_usage(usage)

    def get_rules_version_usage(self, rules_version_id: str) -> tuple[TradingRulesUsage, ...]:
        return self._store.list_usage(rules_version_id)


def build_initial_trading_rules(config: AppConfig) -> TradingRulesVersionDraft:
    runtime = config.futures_runtime
    symbol = runtime.symbol.strip().upper()
    max_capital = runtime.max_total_position_notional / Decimal("100")
    if max_capital > Decimal("1"):
        max_capital = Decimal("1")
    return TradingRulesVersionDraft(
        position_size_pct=runtime.position_size_pct_of_available_capital,
        take_profit_mode=TakeProfitMode.FIXED,
        fixed_take_profit_pct=runtime.take_profit_pct,
        minimum_take_profit_pct=runtime.take_profit_pct,
        stop_loss_pct=runtime.stop_loss_pct,
        minimum_risk_reward=runtime.minimum_risk_reward,
        minimum_net_edge_enabled=True,
        minimum_net_edge_pct=runtime.minimum_net_edge,
        leverage=runtime.leverage,
        max_capital_in_positions_pct=max_capital,
        max_open_positions_enabled=True,
        max_open_positions=runtime.max_open_positions,
        max_positions_per_coin_enabled=True,
        max_positions_per_coin=1,
        direction_mode=DirectionMode.LONG_SHORT,
        daily_loss_limit_enabled=False,
        daily_loss_limit_pct=None,
        maker_fee_rate=runtime.maker_fee_rate,
        taker_fee_rate=runtime.taker_fee_rate,
        spread_cost=runtime.spread_cost,
        slippage_cost=runtime.slippage_cost,
        funding_cost=runtime.funding_cost,
        coins=(CoinRule(symbol=symbol, enabled=symbol == "BTCUSDT", max_allocation_pct=None),),
        metadata={"source": "current_futures_runtime_config"},
    )


def apply_changes(draft: TradingRulesVersionDraft, changes: Mapping[str, object]) -> TradingRulesVersionDraft:
    allowed = set(draft.__dataclass_fields__)
    unknown = set(changes) - allowed
    if unknown:
        raise TradingRulesError(f"unknown trading rules fields: {', '.join(sorted(unknown))}")
    converted = {key: _convert_change(key, value) for key, value in changes.items()}
    return replace(draft, **converted)


def validate_rules_draft(draft: TradingRulesVersionDraft, *, symbol_validator: Callable[[str], object] | None = None) -> None:
    if not (Decimal("0") < draft.position_size_pct <= Decimal("1")):
        raise TradingRulesError("position_size_pct must be > 0 and <= 1")
    if draft.take_profit_mode is TakeProfitMode.FIXED:
        if draft.fixed_take_profit_pct is None or draft.fixed_take_profit_pct <= 0:
            raise TradingRulesError("fixed take-profit mode requires positive fixed_take_profit_pct")
        if draft.minimum_take_profit_pct is not None and draft.fixed_take_profit_pct < draft.minimum_take_profit_pct:
            raise TradingRulesError("fixed_take_profit_pct must meet the minimum take-profit floor")
    elif draft.take_profit_mode is TakeProfitMode.DYNAMIC:
        if draft.minimum_take_profit_pct is None or draft.minimum_take_profit_pct <= 0:
            raise TradingRulesError("dynamic take-profit mode requires a positive minimum_take_profit_pct")
    else:
        raise TradingRulesError("unsupported take-profit mode")
    if draft.stop_loss_pct <= 0:
        raise TradingRulesError("stop_loss_pct must be positive")
    if draft.minimum_risk_reward <= 0:
        raise TradingRulesError("minimum_risk_reward must be positive")
    if draft.minimum_net_edge_enabled and (draft.minimum_net_edge_pct is None or draft.minimum_net_edge_pct < 0):
        raise TradingRulesError("enabled minimum net edge requires a non-negative threshold")
    if draft.leverage <= 0:
        raise TradingRulesError("leverage must be positive")
    if not (Decimal("0") < draft.max_capital_in_positions_pct <= Decimal("1")):
        raise TradingRulesError("max_capital_in_positions_pct must be > 0 and <= 1")
    if draft.max_open_positions_enabled and (draft.max_open_positions is None or draft.max_open_positions <= 0):
        raise TradingRulesError("enabled max open positions requires a positive threshold")
    if draft.max_positions_per_coin_enabled:
        if draft.max_positions_per_coin is None or draft.max_positions_per_coin <= 0:
            raise TradingRulesError("enabled max positions per coin requires a positive threshold")
        if draft.max_positions_per_coin != 1:
            raise TradingRulesError("max_positions_per_coin must be 1 until pyramiding is approved")
    if draft.daily_loss_limit_enabled and (draft.daily_loss_limit_pct is None or draft.daily_loss_limit_pct <= 0):
        raise TradingRulesError("enabled daily loss limit requires a positive threshold")
    if not draft.coins:
        raise TradingRulesError("trading rules require at least one coin rule")
    seen: set[str] = set()
    for coin in draft.coins:
        symbol = normalize_symbol(coin.symbol)
        if coin.enabled and symbol_validator is not None:
            try:
                symbol_validator(symbol)
            except Exception as exc:
                raise TradingRulesError(f"coin {symbol} is not valid in the futures instrument catalog") from exc
        if symbol in seen:
            raise TradingRulesError("duplicate coin rule symbol")
        seen.add(symbol)
        if coin.max_allocation_pct is not None and not (Decimal("0") < coin.max_allocation_pct <= Decimal("1")):
            raise TradingRulesError("coin max_allocation_pct must be > 0 and <= 1")
    if not any(coin.enabled for coin in draft.coins):
        raise TradingRulesError("at least one coin must be enabled")


def coin_rule_for(draft: TradingRulesVersionDraft, symbol: str) -> CoinRule | None:
    normalized = normalize_symbol(symbol)
    for coin in draft.coins:
        if normalize_symbol(coin.symbol) == normalized:
            return coin
    return None


def semantic_hash(draft: TradingRulesVersionDraft) -> str:
    raw = json.dumps(_draft_payload(draft), sort_keys=True, separators=(",", ":"))
    return sha256(raw.encode("utf-8")).hexdigest()


def rules_version_id(version: str, config_hash: str) -> str:
    return f"trules-{version}-{config_hash[:16]}"


def change_summary(previous: TradingRulesVersionDraft, new: TradingRulesVersionDraft) -> str:
    changes: list[str] = []
    prev = _draft_payload(previous)
    nxt = _draft_payload(new)
    labels = {
        "minimum_net_edge_pct": "Minimum Net Edge",
        "stop_loss_pct": "Stop Loss",
        "fixed_take_profit_pct": "Fixed Take Profit",
        "minimum_take_profit_pct": "Minimum Take Profit",
        "take_profit_mode": "TP mode",
        "position_size_pct": "Position size",
        "leverage": "Leverage",
        "direction_mode": "Direction",
    }
    for key, label in labels.items():
        if prev.get(key) != nxt.get(key):
            changes.append(f"{label} {prev.get(key)} -> {nxt.get(key)}")
    prev_coins = {item["symbol"]: item for item in prev["coins"]}
    next_coins = {item["symbol"]: item for item in nxt["coins"]}
    for symbol in sorted(next_coins.keys() - prev_coins.keys()):
        changes.append(f"Added {symbol}")
    for symbol in sorted(prev_coins.keys() - next_coins.keys()):
        changes.append(f"Removed {symbol}")
    for symbol in sorted(prev_coins.keys() & next_coins.keys()):
        if prev_coins[symbol] != next_coins[symbol]:
            changes.append(f"{symbol} allocation {prev_coins[symbol].get('max_allocation_pct')} -> {next_coins[symbol].get('max_allocation_pct')}")
    return "; ".join(changes) if changes else "No semantic changes"


def normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if not normalized.endswith("USDT") or not normalized.removesuffix("USDT").isalnum():
        raise TradingRulesError("only USDT linear perpetual symbols are supported before catalog integration")
    return normalized


def draft_to_json(draft: TradingRulesVersionDraft) -> str:
    return json.dumps(_draft_payload(draft), sort_keys=True, separators=(",", ":"))


def draft_from_json(raw: str) -> TradingRulesVersionDraft:
    payload = json.loads(raw)
    return TradingRulesVersionDraft(
        position_size_pct=Decimal(payload["position_size_pct"]),
        take_profit_mode=TakeProfitMode(payload["take_profit_mode"]),
        fixed_take_profit_pct=None if payload["fixed_take_profit_pct"] is None else Decimal(payload["fixed_take_profit_pct"]),
        minimum_take_profit_pct=None if payload["minimum_take_profit_pct"] is None else Decimal(payload["minimum_take_profit_pct"]),
        stop_loss_pct=Decimal(payload["stop_loss_pct"]),
        minimum_risk_reward=Decimal(payload["minimum_risk_reward"]),
        minimum_net_edge_enabled=bool(payload["minimum_net_edge_enabled"]),
        minimum_net_edge_pct=None if payload["minimum_net_edge_pct"] is None else Decimal(payload["minimum_net_edge_pct"]),
        leverage=Decimal(payload["leverage"]),
        max_capital_in_positions_pct=Decimal(payload["max_capital_in_positions_pct"]),
        max_open_positions_enabled=bool(payload["max_open_positions_enabled"]),
        max_open_positions=payload["max_open_positions"],
        max_positions_per_coin_enabled=bool(payload["max_positions_per_coin_enabled"]),
        max_positions_per_coin=payload["max_positions_per_coin"],
        direction_mode=DirectionMode(payload["direction_mode"]),
        daily_loss_limit_enabled=bool(payload["daily_loss_limit_enabled"]),
        daily_loss_limit_pct=None if payload["daily_loss_limit_pct"] is None else Decimal(payload["daily_loss_limit_pct"]),
        maker_fee_rate=Decimal(payload["maker_fee_rate"]),
        taker_fee_rate=Decimal(payload["taker_fee_rate"]),
        spread_cost=Decimal(payload["spread_cost"]),
        slippage_cost=Decimal(payload["slippage_cost"]),
        funding_cost=Decimal(payload["funding_cost"]),
        coins=tuple(
            CoinRule(item["symbol"], bool(item["enabled"]), None if item["max_allocation_pct"] is None else Decimal(item["max_allocation_pct"]))
            for item in payload["coins"]
        ),
        metadata=payload.get("metadata") or {},
    )


def _convert_change(key: str, value: object) -> object:
    if key == "take_profit_mode":
        return value if isinstance(value, TakeProfitMode) else TakeProfitMode(str(value).upper())
    if key == "direction_mode":
        return value if isinstance(value, DirectionMode) else DirectionMode(str(value).upper())
    if key == "coins":
        return tuple(value)  # type: ignore[arg-type]
    if key.endswith("_enabled"):
        return _bool_value(value)
    if key in {"max_open_positions", "max_positions_per_coin"}:
        return None if value is None else int(value)  # type: ignore[arg-type]
    if key == "metadata":
        return value
    if key.endswith("_pct") or key in {"leverage", "maker_fee_rate", "taker_fee_rate", "spread_cost", "slippage_cost", "funding_cost"}:
        return None if value is None else Decimal(str(value))
    return value


def _bool_value(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "on"}:
            return True
        if normalized in {"false", "0", "no", "off"}:
            return False
    raise TradingRulesError("enabled flags require an explicit boolean value")


def _draft_payload(draft: TradingRulesVersionDraft) -> dict[str, object]:
    return {
        "position_size_pct": str(draft.position_size_pct),
        "take_profit_mode": draft.take_profit_mode.value,
        "fixed_take_profit_pct": None if draft.fixed_take_profit_pct is None else str(draft.fixed_take_profit_pct),
        "minimum_take_profit_pct": None if draft.minimum_take_profit_pct is None else str(draft.minimum_take_profit_pct),
        "stop_loss_pct": str(draft.stop_loss_pct),
        "minimum_risk_reward": str(draft.minimum_risk_reward),
        "minimum_net_edge_enabled": draft.minimum_net_edge_enabled,
        "minimum_net_edge_pct": None if draft.minimum_net_edge_pct is None else str(draft.minimum_net_edge_pct),
        "leverage": str(draft.leverage),
        "max_capital_in_positions_pct": str(draft.max_capital_in_positions_pct),
        "max_open_positions_enabled": draft.max_open_positions_enabled,
        "max_open_positions": draft.max_open_positions,
        "max_positions_per_coin_enabled": draft.max_positions_per_coin_enabled,
        "max_positions_per_coin": draft.max_positions_per_coin,
        "direction_mode": draft.direction_mode.value,
        "daily_loss_limit_enabled": draft.daily_loss_limit_enabled,
        "daily_loss_limit_pct": None if draft.daily_loss_limit_pct is None else str(draft.daily_loss_limit_pct),
        "maker_fee_rate": str(draft.maker_fee_rate),
        "taker_fee_rate": str(draft.taker_fee_rate),
        "spread_cost": str(draft.spread_cost),
        "slippage_cost": str(draft.slippage_cost),
        "funding_cost": str(draft.funding_cost),
        "coins": [
            {
                "symbol": normalize_symbol(coin.symbol),
                "enabled": coin.enabled,
                "max_allocation_pct": None if coin.max_allocation_pct is None else str(coin.max_allocation_pct),
            }
            for coin in draft.coins
        ],
        "metadata": dict(draft.metadata or {}),
    }

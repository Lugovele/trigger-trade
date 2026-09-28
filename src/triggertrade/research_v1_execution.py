"""Research V1 multi-coin execution definitions and shared portfolio policy."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.persistence.postgres_research_set_registry import ResearchSetVersion, research_set_from_package_record
from triggertrade.research_pins import research_pin_payload
from triggertrade.rules import TradingRulesVersion
from triggertrade.rules.trading import CoinRule, coin_rule_for
from triggertrade.trigger_sets import TriggerSetStatus, TriggerSetVersion


RESEARCH_V1_PROGRAM_ID = "RESEARCH_V1_R3"
RESEARCH_V1_SCHEMA_VERSION = "research_v1_build_spec.v1"
RESEARCH_V1_METHODOLOGY_BASELINE = "v1.2.15"
RESEARCH_V1_ASSETS: tuple[str, ...] = ("BTC", "ETH", "SOL", "XRP", "DOGE", "SUI", "PEPE", "AVAX", "LINK", "BNB")
RESEARCH_V1_SYMBOLS: tuple[str, ...] = tuple(f"{asset}USDT" for asset in RESEARCH_V1_ASSETS)
RESEARCH_V1_ALLOCATION_PCT = Decimal("0.10")
RESEARCH_V1_ALLOCATION_BY_SYMBOL: dict[str, Decimal] = {symbol: RESEARCH_V1_ALLOCATION_PCT for symbol in RESEARCH_V1_SYMBOLS}
RESEARCH_V1_SEGMENTS: dict[str, tuple[str, ...]] = {
    "MAJORS": ("BTC", "ETH"),
    "HIGH_VOLATILITY_HIGH_BETA": ("SOL", "XRP", "DOGE", "SUI", "PEPE", "AVAX"),
    "DIVERSIFIERS": ("LINK", "BNB"),
}
RESEARCH_V1_RUN_PROFILES: tuple[str, ...] = ("BACKTEST_90D", "BACKTEST_30D", "BACKTEST_7D", "DEMO_7D")
RESEARCH_V1_RESULT_SCOPES: tuple[str, ...] = ("OVERALL", "BY_SEGMENT", "BY_COIN", "BY_DIRECTION")
RESEARCH_V1_COMPARE_ORDER: tuple[str, ...] = ("ACTIVE", "DEMO_7D", "BACKTEST_7D", "BACKTEST_30D", "BACKTEST_90D")


class ResearchV1ExecutionError(ValueError):
    """Raised when an approved Research V1 execution definition cannot fail safely."""


@dataclass(frozen=True)
class ResearchV1SetBinding:
    set_version_id: str | None
    set_id: str | None
    set_version: str | None
    btc_applicability: str | None = None


@dataclass(frozen=True)
class ResearchV1ArmBinding:
    arm: str
    rules_version_id: str
    btc: ResearchV1SetBinding
    non_btc: ResearchV1SetBinding


@dataclass(frozen=True)
class ResearchV1SymbolBinding:
    asset: str
    symbol: str
    instrument_symbol: str
    segment: str
    allocation_pct: Decimal
    applicable: bool
    applicability: str
    reason: str | None
    arm: str
    set_version_id: str | None
    set_id: str | None
    set_version: str | None
    rules_version_id: str


@dataclass(frozen=True)
class ResearchV1ExecutionDefinition:
    research_id: str
    hypothesis_id: str
    title: str
    status: str
    program_id: str
    methodology_baseline: str
    selected_arm: str
    primary_set_version_id: str
    primary_rules_version_id: str
    baseline: ResearchV1ArmBinding
    variant: ResearchV1ArmBinding
    universe_id: str
    ordered_assets: tuple[str, ...]
    ordered_symbols: tuple[str, ...]
    allocation_profile_id: str
    allocation_by_symbol: Mapping[str, Decimal]
    applicable_coins: tuple[str, ...]
    excluded_coins: tuple[str, ...]
    segment_scope: Any
    direction_scope: Any
    run_profiles: tuple[str, ...]
    result_scopes: tuple[str, ...]
    compare_order: tuple[str, ...]
    special_applicability: Mapping[str, Any]
    provenance: Mapping[str, Any]
    source_refs: tuple[Any, ...]

    @property
    def selected_binding(self) -> ResearchV1ArmBinding:
        if self.selected_arm == "BASELINE":
            return self.baseline
        if self.selected_arm == "VARIANT":
            return self.variant
        raise ResearchV1ExecutionError(f"unsupported Research V1 arm: {self.selected_arm}")


@dataclass(frozen=True)
class ResearchV1ExecutionResult:
    research_id: str
    hypothesis_id: str
    run_kind: str
    run_profile: str
    symbol_results: tuple[Mapping[str, Any], ...]
    not_applicable: tuple[ResearchV1SymbolBinding, ...]
    portfolio_snapshot: Mapping[str, str | Mapping[str, str]]


@dataclass(frozen=True)
class ResearchV1SharedPortfolioState:
    """Research-scoped portfolio capacity shared across all symbols in one run."""

    total_capital: Decimal
    max_capital_in_positions_pct: Decimal
    allocation_by_symbol: Mapping[str, Decimal]
    max_open_positions: int
    max_positions_per_coin: int
    committed_by_symbol: Mapping[str, Decimal] | None = None
    open_positions_by_symbol: Mapping[str, int] | None = None

    def __post_init__(self) -> None:
        if self.total_capital <= 0:
            raise ResearchV1ExecutionError("Research portfolio total capital must be positive")
        if not (Decimal("0") < self.max_capital_in_positions_pct <= Decimal("1")):
            raise ResearchV1ExecutionError("Research portfolio aggregate cap must be > 0 and <= 1")
        if self.max_open_positions < 1 or self.max_positions_per_coin < 1:
            raise ResearchV1ExecutionError("Research portfolio slot limits must be positive")
        if sum(self.allocation_by_symbol.values(), Decimal("0")) != Decimal("1.00"):
            raise ResearchV1ExecutionError("Research V1 allocation must total exactly 100%")

    @property
    def committed_by_symbol_map(self) -> dict[str, Decimal]:
        return dict(self.committed_by_symbol or {})

    @property
    def open_positions_by_symbol_map(self) -> dict[str, int]:
        return dict(self.open_positions_by_symbol or {})

    @property
    def committed_capital(self) -> Decimal:
        return sum(self.committed_by_symbol_map.values(), Decimal("0"))

    @property
    def aggregate_capital_cap(self) -> Decimal:
        return self.total_capital * self.max_capital_in_positions_pct

    @property
    def available_capital(self) -> Decimal:
        return self.aggregate_capital_cap - self.committed_capital

    def reserve(self, symbol: str, amount: Decimal) -> "ResearchV1SharedPortfolioState":
        normalized = symbol.upper()
        if amount <= 0:
            raise ResearchV1ExecutionError("Research capital reservation must be positive")
        allocations = dict(self.allocation_by_symbol)
        if normalized not in allocations:
            raise ResearchV1ExecutionError(f"Research symbol is outside the allocation profile: {normalized}")
        committed = self.committed_by_symbol_map
        open_positions = self.open_positions_by_symbol_map
        current_symbol_commitment = committed.get(normalized, Decimal("0"))
        if current_symbol_commitment + amount > self.total_capital * allocations[normalized]:
            raise ResearchV1ExecutionError("Research per-coin allocation cap exceeded")
        if self.committed_capital + amount > self.aggregate_capital_cap:
            raise ResearchV1ExecutionError("Research aggregate portfolio cap exceeded")
        if sum(open_positions.values()) + 1 > self.max_open_positions:
            raise ResearchV1ExecutionError("Research global open-position cap exceeded")
        if open_positions.get(normalized, 0) + 1 > self.max_positions_per_coin:
            raise ResearchV1ExecutionError("Research per-coin open-position cap exceeded")
        committed[normalized] = current_symbol_commitment + amount
        open_positions[normalized] = open_positions.get(normalized, 0) + 1
        return replace(self, committed_by_symbol=committed, open_positions_by_symbol=open_positions)

    def release(self, symbol: str, amount: Decimal) -> "ResearchV1SharedPortfolioState":
        normalized = symbol.upper()
        if amount <= 0:
            raise ResearchV1ExecutionError("Research capital release must be positive")
        committed = self.committed_by_symbol_map
        open_positions = self.open_positions_by_symbol_map
        current = committed.get(normalized, Decimal("0"))
        if amount > current:
            raise ResearchV1ExecutionError("Research capital release exceeds committed capital")
        next_amount = current - amount
        if next_amount:
            committed[normalized] = next_amount
        else:
            committed.pop(normalized, None)
        if open_positions.get(normalized, 0) > 0:
            if open_positions[normalized] == 1:
                open_positions.pop(normalized, None)
            else:
                open_positions[normalized] -= 1
        return replace(self, committed_by_symbol=committed, open_positions_by_symbol=open_positions)

    def snapshot(self) -> dict[str, str | Mapping[str, str]]:
        return {
            "total_capital": str(self.total_capital),
            "aggregate_capital_cap": str(self.aggregate_capital_cap),
            "committed_capital": str(self.committed_capital),
            "available_capital": str(self.available_capital),
            "committed_by_symbol": {symbol: str(value) for symbol, value in sorted(self.committed_by_symbol_map.items())},
        }


def apply_research_v1_portfolio_events(
    portfolio: ResearchV1SharedPortfolioState,
    events: Sequence[Mapping[str, Any]],
) -> ResearchV1SharedPortfolioState:
    """Apply canonical per-symbol commitment/release evidence to a Research V1 portfolio projection."""

    updated = portfolio
    for event in events:
        action = str(event.get("action") or event.get("event_type") or "").upper()
        symbol = str(event.get("symbol") or "").upper()
        amount = _event_amount(event)
        source = str(event.get("canonical_source") or event.get("source") or "")
        if not symbol:
            raise ResearchV1ExecutionError("Research V1 portfolio event requires symbol")
        if action in {"RESERVE", "COMMIT", "OPEN"}:
            if source not in {
                "lifecycle_start_gate.held_committed_capital",
                "submit_authorization.held_committed_capital",
                "order_spec.economics.actual_committed_capital",
                "futures_position.position_value_over_leverage",
                "backtest_canonical_commitment.actual_committed_capital",
            }:
                raise ResearchV1ExecutionError("Research V1 portfolio reserve requires canonical commitment source")
            updated = updated.reserve(symbol, amount)
            continue
        if action in {"RELEASE", "CLOSE", "CLOSED"}:
            state = str(event.get("lifecycle_state") or event.get("position_status") or event.get("terminal_state") or "").upper()
            if state != "CLOSED":
                raise ResearchV1ExecutionError("Research V1 portfolio release requires CLOSED finality")
            updated = updated.release(symbol, amount)
            continue
        raise ResearchV1ExecutionError(f"unsupported Research V1 portfolio event action: {action}")
    return updated


def default_build_spec_path() -> Path:
    return Path(__file__).resolve().parents[2] / "docs" / "research-import" / "build" / "RESEARCH_V1_BUILD_SPEC.json"


def load_research_v1_build_spec(path: Path | None = None) -> Mapping[str, Any]:
    spec_path = path or default_build_spec_path()
    try:
        payload = json.loads(spec_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise ResearchV1ExecutionError("Research V1 build spec is unavailable") from exc
    except json.JSONDecodeError as exc:
        raise ResearchV1ExecutionError("Research V1 build spec is malformed") from exc
    validate_research_v1_build_spec(payload)
    return payload


def validate_research_v1_build_spec(spec: Mapping[str, Any]) -> None:
    if spec.get("schema_version") != RESEARCH_V1_SCHEMA_VERSION:
        raise ResearchV1ExecutionError("unsupported Research V1 build spec schema")
    program = _mapping(spec.get("research_program"), "research_program")
    if program.get("program_id") != RESEARCH_V1_PROGRAM_ID:
        raise ResearchV1ExecutionError("unexpected Research V1 program")
    if program.get("methodology_baseline") != RESEARCH_V1_METHODOLOGY_BASELINE:
        raise ResearchV1ExecutionError("unexpected Research V1 methodology baseline")
    definitions = spec.get("research_definitions")
    if not isinstance(definitions, list) or len(definitions) != 30:
        raise ResearchV1ExecutionError("Research V1 build spec must define exactly 30 ResearchDefinitions")
    if tuple(_asset["asset"] for _asset in _universe_profile(spec)["ordered_assets"]) != RESEARCH_V1_ASSETS:
        raise ResearchV1ExecutionError("Research V1 universe assets do not match the approved order")
    allocation = _allocation_profile(spec)
    asset_allocations = _mapping(allocation.get("per_asset_allocation_pct"), "per_asset_allocation_pct")
    if set(asset_allocations) != set(RESEARCH_V1_ASSETS):
        raise ResearchV1ExecutionError("Research V1 allocation must contain exactly 10 approved assets")
    total = Decimal("0")
    for asset in RESEARCH_V1_ASSETS:
        pct = _percent_decimal(asset_allocations[asset])
        if pct != RESEARCH_V1_ALLOCATION_PCT:
            raise ResearchV1ExecutionError("Research V1 allocation must be fixed 10% per approved symbol")
        total += pct
    if total != Decimal("1.00"):
        raise ResearchV1ExecutionError("Research V1 allocation must total exactly 100%")


def build_research_v1_execution_definition(
    research_id: str,
    *,
    spec: Mapping[str, Any] | None = None,
    selected_arm: str | None = None,
) -> ResearchV1ExecutionDefinition:
    payload = spec or load_research_v1_build_spec()
    definitions = _definitions_by_id(payload)
    try:
        record = definitions[research_id]
    except KeyError as exc:
        raise ResearchV1ExecutionError(f"unknown Research V1 definition: {research_id}") from exc
    selected = str(selected_arm or _mapping(record.get("set_version_bindings"), "set_version_bindings").get("primary_arm") or "VARIANT").upper()
    baseline = _arm_binding(record, "BASELINE")
    variant = _arm_binding(record, "VARIANT")
    universe = _universe_profile(payload)
    allocation = _allocation_profile(payload)
    return ResearchV1ExecutionDefinition(
        research_id=str(record["research_id"]),
        hypothesis_id=str(record["hypothesis_id"]),
        title=str(record.get("title") or ""),
        status=str(record.get("status") or ""),
        program_id=str(_mapping(payload.get("research_program"), "research_program")["program_id"]),
        methodology_baseline=str(_mapping(payload.get("research_program"), "research_program")["methodology_baseline"]),
        selected_arm=selected,
        primary_set_version_id=str(record["set_version_id"]),
        primary_rules_version_id=str(record["rules_version_id"]),
        baseline=baseline,
        variant=variant,
        universe_id=str(record["universe_id"]),
        ordered_assets=tuple(str(item["asset"]) for item in universe["ordered_assets"]),
        ordered_symbols=tuple(f"{item['asset']}USDT" for item in universe["ordered_assets"]),
        allocation_profile_id=str(record["allocation_profile_id"]),
        allocation_by_symbol=_allocation_by_symbol(allocation),
        applicable_coins=tuple(str(item) for item in record.get("applicable_coins") or ()),
        excluded_coins=tuple(str(item) for item in record.get("excluded_coins") or ()),
        segment_scope=record.get("segment_scope"),
        direction_scope=record.get("direction_scope"),
        run_profiles=tuple(str(item) for item in record.get("run_profiles") or ()),
        result_scopes=tuple(str(item) for item in record.get("result_scopes") or ()),
        compare_order=tuple(str(item) for item in record.get("compare_order") or ()),
        special_applicability=dict(record.get("special_applicability") or {}),
        provenance=dict(record.get("provenance") or {}),
        source_refs=tuple(record.get("source_refs") or ()),
    )


def resolve_research_v1_symbol_bindings(
    definition: ResearchV1ExecutionDefinition,
    *,
    available_sets: Mapping[str, ResearchSetVersion] | Sequence[ResearchSetVersion],
    instrument_resolver: Callable[[str], object] | None = None,
) -> tuple[ResearchV1SymbolBinding, ...]:
    set_map = _set_map(available_sets)
    selected = definition.selected_binding
    bindings: list[ResearchV1SymbolBinding] = []
    for asset in definition.ordered_assets:
        symbol = f"{asset}USDT"
        instrument_symbol = symbol
        if instrument_resolver is not None:
            try:
                instrument = instrument_resolver(symbol)
            except Exception as exc:
                raise ResearchV1ExecutionError(f"Research V1 instrument is unavailable: {symbol}") from exc
            instrument_symbol = str(getattr(instrument, "symbol", symbol)).upper()
            if instrument_symbol != symbol:
                raise ResearchV1ExecutionError(f"Research V1 instrument resolver returned mismatched symbol: {instrument_symbol}")
        allocation = definition.allocation_by_symbol.get(symbol)
        if allocation != RESEARCH_V1_ALLOCATION_PCT:
            raise ResearchV1ExecutionError(f"Research V1 allocation is not fixed at 10% for {symbol}")
        if asset == "BTC" and _btc_not_applicable(definition):
            bindings.append(_symbol_binding(definition, asset, symbol, instrument_symbol, selected, None, applicable=False))
            continue
        source = selected.btc if asset == "BTC" else selected.non_btc
        if source.set_version_id is None:
            raise ResearchV1ExecutionError(f"Research V1 Set binding is missing for {definition.research_id} {asset}")
        if source.set_version_id not in set_map:
            raise ResearchV1ExecutionError(f"Research V1 Set binding does not resolve: {source.set_version_id}")
        bindings.append(_symbol_binding(definition, asset, symbol, instrument_symbol, selected, set_map[source.set_version_id], applicable=True))
    return tuple(bindings)


def research_v1_config_pin_payload(
    definition: ResearchV1ExecutionDefinition,
    *,
    created_source: str,
    instrument_resolver: Callable[[str], object] | None = None,
) -> dict[str, Any]:
    symbol_bindings = resolve_research_v1_symbol_bindings(
        definition,
        available_sets={binding.set_version_id: _stub_set(binding) for binding in _arm_set_bindings(definition) if binding.set_version_id},
        instrument_resolver=instrument_resolver,
    )
    return research_pin_payload(
        config_pins={
            "research_v1_execution": {
                "schema_version": RESEARCH_V1_SCHEMA_VERSION,
                "program_id": definition.program_id,
                "methodology_baseline": definition.methodology_baseline,
                "research_id": definition.research_id,
                "hypothesis_id": definition.hypothesis_id,
                "title": definition.title,
                "selected_arm": definition.selected_arm,
                "primary_set_version_id": definition.primary_set_version_id,
                "primary_rules_version_id": definition.primary_rules_version_id,
                "baseline": _arm_payload(definition.baseline),
                "variant": _arm_payload(definition.variant),
                "symbol_bindings": tuple(_binding_payload(binding) for binding in symbol_bindings),
                "universe_id": definition.universe_id,
                "ordered_assets": definition.ordered_assets,
                "ordered_universe": definition.ordered_assets,
                "ordered_symbols": definition.ordered_symbols,
                "instrument_bindings": tuple(
                    {"asset": binding.asset, "requested_symbol": binding.symbol, "instrument_symbol": binding.instrument_symbol}
                    for binding in symbol_bindings
                ),
                "allocation_profile_id": definition.allocation_profile_id,
                "allocation_by_symbol": {symbol: str(definition.allocation_by_symbol[symbol]) for symbol in definition.ordered_symbols},
                "applicable_coins": definition.applicable_coins,
                "excluded_coins": definition.excluded_coins,
                "segment_scope": definition.segment_scope,
                "direction_scope": definition.direction_scope,
                "special_applicability": dict(definition.special_applicability),
                "run_profiles": definition.run_profiles,
                "result_scopes": definition.result_scopes,
                "compare_order": definition.compare_order,
                "provenance": dict(definition.provenance),
                "source_refs": definition.source_refs,
            }
        },
        source_pins={
            "research_v1_build_spec": "docs/research-import/build/RESEARCH_V1_BUILD_SPEC.json",
            "set_registry": "exact_immutable_set_version_ids_from_build_spec",
            "rules_registry": "exact_immutable_trading_rules_version_ids_from_build_spec",
        },
        adapter_profile_pins={"live_side_effects": "forbidden", "ordinary_live_runtime": "unchanged_single_symbol"},
        simulation_assumptions={"allocation": "fixed_10x10_no_redistribution"},
        created_source=created_source,
    )


def is_research_v1_pin_payload(pin_payload: Mapping[str, Any]) -> bool:
    config = pin_payload.get("config_pins")
    if not isinstance(config, Mapping):
        return False
    execution = config.get("research_v1_execution")
    return isinstance(execution, Mapping) and execution.get("schema_version") == RESEARCH_V1_SCHEMA_VERSION


def research_v1_definition_from_pin_payload(pin_payload: Mapping[str, Any]) -> ResearchV1ExecutionDefinition:
    config = _research_v1_pin_config(pin_payload)
    baseline = _arm_from_pin(_mapping(config.get("baseline"), "baseline"))
    variant = _arm_from_pin(_mapping(config.get("variant"), "variant"))
    allocation = {
        str(symbol): Decimal(str(value))
        for symbol, value in _mapping(config.get("allocation_by_symbol"), "allocation_by_symbol").items()
    }
    return ResearchV1ExecutionDefinition(
        research_id=str(config["research_id"]),
        hypothesis_id=str(config["hypothesis_id"]),
        title=str(config.get("title") or ""),
        status=str(config.get("status") or ""),
        program_id=str(config["program_id"]),
        methodology_baseline=str(config["methodology_baseline"]),
        selected_arm=str(config["selected_arm"]),
        primary_set_version_id=str(config["primary_set_version_id"]),
        primary_rules_version_id=str(config["primary_rules_version_id"]),
        baseline=baseline,
        variant=variant,
        universe_id=str(config["universe_id"]),
        ordered_assets=tuple(str(item) for item in config.get("ordered_assets") or config.get("ordered_universe") or ()),
        ordered_symbols=tuple(str(item) for item in config.get("ordered_symbols") or ()),
        allocation_profile_id=str(config["allocation_profile_id"]),
        allocation_by_symbol=allocation,
        applicable_coins=tuple(str(item) for item in config.get("applicable_coins") or ()),
        excluded_coins=tuple(str(item) for item in config.get("excluded_coins") or ()),
        segment_scope=config.get("segment_scope"),
        direction_scope=config.get("direction_scope"),
        run_profiles=tuple(str(item) for item in config.get("run_profiles") or ()),
        result_scopes=tuple(str(item) for item in config.get("result_scopes") or ()),
        compare_order=tuple(str(item) for item in config.get("compare_order") or ()),
        special_applicability=dict(config.get("special_applicability") or {}),
        provenance=dict(config.get("provenance") or {}),
        source_refs=tuple(config.get("source_refs") or ()),
    )


def research_v1_rules_allocation_supported(rules: TradingRulesVersion) -> bool:
    draft = rules.draft
    enabled = tuple(coin for coin in draft.coins if coin.enabled)
    if len(enabled) != 10:
        return False
    if {coin.symbol.upper() for coin in enabled} != set(RESEARCH_V1_SYMBOLS):
        return False
    if any(coin.max_allocation_pct != RESEARCH_V1_ALLOCATION_PCT for coin in enabled):
        return False
    return sum((coin.max_allocation_pct or Decimal("0")) for coin in enabled) == Decimal("1.00")


def research_v1_backtest_allocation_supported(rules: TradingRulesVersion, symbol: str) -> bool:
    if not research_v1_rules_allocation_supported(rules):
        return False
    coin = coin_rule_for(rules.draft, symbol)
    return coin is not None and coin.enabled and coin.max_allocation_pct == RESEARCH_V1_ALLOCATION_PCT


def run_research_v1_backtest_orchestration(
    definition: ResearchV1ExecutionDefinition,
    *,
    available_sets: Mapping[str, ResearchSetVersion] | Sequence[ResearchSetVersion],
    run_profile: str,
    portfolio: ResearchV1SharedPortfolioState,
    symbol_runner: Callable[[ResearchV1SymbolBinding, ResearchV1SharedPortfolioState], Mapping[str, Any] | tuple[Mapping[str, Any], ResearchV1SharedPortfolioState]],
) -> ResearchV1ExecutionResult:
    if run_profile not in RESEARCH_V1_RUN_PROFILES or not run_profile.startswith("BACKTEST_"):
        raise ResearchV1ExecutionError("unsupported Research V1 backtest run profile")
    return _run_research_v1_orchestration(definition, available_sets=available_sets, run_kind="BACKTEST", run_profile=run_profile, portfolio=portfolio, runner=symbol_runner)


def run_research_v1_demo_orchestration(
    definition: ResearchV1ExecutionDefinition,
    *,
    available_sets: Mapping[str, ResearchSetVersion] | Sequence[ResearchSetVersion],
    portfolio: ResearchV1SharedPortfolioState,
    symbol_runner: Callable[[ResearchV1SymbolBinding, ResearchV1SharedPortfolioState], Mapping[str, Any] | tuple[Mapping[str, Any], ResearchV1SharedPortfolioState]],
) -> ResearchV1ExecutionResult:
    return _run_research_v1_orchestration(definition, available_sets=available_sets, run_kind="DEMO", run_profile="DEMO_7D", portfolio=portfolio, runner=symbol_runner)


def _run_research_v1_orchestration(
    definition: ResearchV1ExecutionDefinition,
    *,
    available_sets: Mapping[str, ResearchSetVersion] | Sequence[ResearchSetVersion],
    run_kind: str,
    run_profile: str,
    portfolio: ResearchV1SharedPortfolioState,
    runner: Callable[[ResearchV1SymbolBinding, ResearchV1SharedPortfolioState], Mapping[str, Any] | tuple[Mapping[str, Any], ResearchV1SharedPortfolioState]],
) -> ResearchV1ExecutionResult:
    results: list[Mapping[str, Any]] = []
    not_applicable: list[ResearchV1SymbolBinding] = []
    current_portfolio = portfolio
    for binding in resolve_research_v1_symbol_bindings(definition, available_sets=available_sets):
        if not binding.applicable:
            not_applicable.append(binding)
            continue
        runner_result = runner(binding, current_portfolio)
        if isinstance(runner_result, tuple):
            raw_result, next_portfolio = runner_result
        else:
            raw_result, next_portfolio = runner_result, current_portfolio
        result = dict(raw_result)
        current_portfolio = next_portfolio
        result.setdefault("research_id", definition.research_id)
        result.setdefault("hypothesis_id", definition.hypothesis_id)
        result.setdefault("run_kind", run_kind)
        result.setdefault("symbol", binding.symbol)
        result.setdefault("set_version_id", binding.set_version_id)
        result.setdefault("rules_version_id", binding.rules_version_id)
        result.setdefault("arm", binding.arm)
        results.append(result)
    return ResearchV1ExecutionResult(
        research_id=definition.research_id,
        hypothesis_id=definition.hypothesis_id,
        run_kind=run_kind,
        run_profile=run_profile,
        symbol_results=tuple(results),
        not_applicable=tuple(not_applicable),
        portfolio_snapshot=current_portfolio.snapshot(),
    )


def research_set_to_trigger_set(research_set: ResearchSetVersion, *, symbol: str) -> TriggerSetVersion:
    return TriggerSetVersion(
        set_id=research_set.set_id,
        version=research_set.set_version,
        purpose=research_set.display_name,
        status=TriggerSetStatus.ACTIVE,
        symbol=symbol.upper(),
        timeframe=research_set.timeframe,
        rule_versions=tuple((member.trigger_id, member.trigger_version) for member in research_set.trigger_members),
        strategy_version="RESEARCH_V1_SET_COMPOSITION",
        risk_profile_version="RESEARCH_V1_RULES",
        config_snapshot={
            "research_set_version_id": research_set.set_version,
            "trigger_composition_logic": research_set.trigger_composition_logic,
            "direction_semantics": research_set.direction_semantics,
        },
        created_at=research_set.created_at,
        provenance="postgres_research_set_registry",
    )


def _definitions_by_id(spec: Mapping[str, Any]) -> dict[str, Mapping[str, Any]]:
    return {str(item["research_id"]): _mapping(item, "research_definition") for item in spec["research_definitions"]}


def _arm_binding(record: Mapping[str, Any], arm: str) -> ResearchV1ArmBinding:
    set_bindings = _mapping(record.get("set_version_bindings"), "set_version_bindings")
    rules_bindings = _mapping(record.get("rules_version_bindings"), "rules_version_bindings")
    arm_sets = _mapping(set_bindings.get(arm.lower()), f"{arm} set binding")
    arm_rules = _mapping(rules_bindings.get(arm.lower()), f"{arm} rules binding")
    return ResearchV1ArmBinding(
        arm=arm,
        rules_version_id=str(arm_rules["rules_version_id"]),
        btc=_set_binding(arm_sets, "btc"),
        non_btc=_set_binding(arm_sets, "non_btc"),
    )


def _set_binding(payload: Mapping[str, Any], key: str) -> ResearchV1SetBinding:
    raw = payload.get(f"{key}_set_version_id")
    set_version_id = None if raw in {None, "NOT_APPLICABLE"} else str(raw)
    return ResearchV1SetBinding(
        set_version_id=set_version_id,
        set_id=None if set_version_id is None else "-".join(set_version_id.split("-")[:-1]),
        set_version=None if set_version_id is None else set_version_id,
        btc_applicability=None if payload.get("btc_applicability") is None else str(payload.get("btc_applicability")),
    )


def _allocation_profile(spec: Mapping[str, Any]) -> Mapping[str, Any]:
    profiles = spec.get("allocation_profiles")
    if isinstance(profiles, Sequence) and not isinstance(profiles, (str, bytes)):
        if not profiles:
            raise ResearchV1ExecutionError("allocation_profiles must not be empty")
        return _mapping(profiles[0], "allocation_profile")
    profiles_map = _mapping(profiles, "allocation_profiles")
    return _mapping(next(iter(profiles_map.values())), "allocation_profile")


def _universe_profile(spec: Mapping[str, Any]) -> Mapping[str, Any]:
    profiles = spec.get("universe_profiles")
    if isinstance(profiles, Sequence) and not isinstance(profiles, (str, bytes)):
        if not profiles:
            raise ResearchV1ExecutionError("universe_profiles must not be empty")
        return _mapping(profiles[0], "universe_profile")
    profiles_map = _mapping(profiles, "universe_profiles")
    return _mapping(next(iter(profiles_map.values())), "universe_profile")


def _allocation_by_symbol(allocation: Mapping[str, Any]) -> dict[str, Decimal]:
    result: dict[str, Decimal] = {}
    for asset, pct in _mapping(allocation.get("per_asset_allocation_pct"), "per_asset_allocation_pct").items():
        result[f"{str(asset).upper()}USDT"] = _percent_decimal(pct)
    return result


def _percent_decimal(value: Any) -> Decimal:
    return Decimal(str(value)) / Decimal("100")


def _btc_not_applicable(definition: ResearchV1ExecutionDefinition) -> bool:
    return definition.special_applicability.get("btc_result_scope_applicability") == "NOT_APPLICABLE"


def _symbol_binding(
    definition: ResearchV1ExecutionDefinition,
    asset: str,
    symbol: str,
    instrument_symbol: str,
    selected: ResearchV1ArmBinding,
    research_set: ResearchSetVersion | None,
    *,
    applicable: bool,
) -> ResearchV1SymbolBinding:
    reason = None
    applicability = "APPLICABLE"
    if not applicable:
        applicability = "NOT_APPLICABLE"
        reason = str(definition.special_applicability.get("btc_not_applicable_reason") or "NOT_APPLICABLE")
    return ResearchV1SymbolBinding(
        asset=asset,
        symbol=symbol,
        instrument_symbol=instrument_symbol,
        segment=_segment_for_asset(asset),
        allocation_pct=definition.allocation_by_symbol[symbol],
        applicable=applicable,
        applicability=applicability,
        reason=reason,
        arm=selected.arm,
        set_version_id=None if research_set is None else research_set.set_version,
        set_id=None if research_set is None else research_set.set_id,
        set_version=None if research_set is None else research_set.set_version,
        rules_version_id=selected.rules_version_id,
    )


def _segment_for_asset(asset: str) -> str:
    for segment, assets in RESEARCH_V1_SEGMENTS.items():
        if asset in assets:
            return segment
    raise ResearchV1ExecutionError(f"Research V1 asset has no segment: {asset}")


def _set_map(available_sets: Mapping[str, ResearchSetVersion] | Sequence[ResearchSetVersion]) -> dict[str, ResearchSetVersion]:
    if isinstance(available_sets, Mapping):
        return dict(available_sets)
    return {item.set_version: item for item in available_sets}


def _stub_set(binding: ResearchV1SetBinding) -> ResearchSetVersion:
    return research_set_from_package_record(
        {
            "set_id": binding.set_id,
            "set_version": binding.set_version_id,
            "backend_set_id": binding.set_id,
            "backend_version": "v" + str(binding.set_version_id).rsplit("-V", 1)[1],
            "display_name": binding.set_version_id,
            "status": "PIN_ONLY",
            "source_hypothesis_ids": [],
            "source_candidate_ids": [],
            "source_position_ids": [],
            "source_portfolio_ids": [],
            "coin_applicability": [],
            "excluded_coins": [],
            "segment_applicability": "PIN_ONLY",
            "timeframe": "1m",
            "profile_applicability": [],
            "trigger_members": [
                {
                    "position": 1,
                    "trigger_id": "TR-R-PIN-ONLY",
                    "trigger_version": "0.0.0",
                    "role": "PIN_ONLY",
                    "direction_applicability": None,
                    "condition": "PIN_ONLY",
                    "operator": None,
                    "threshold": None,
                    "threshold_unit": None,
                    "metric_references": [],
                    "formula_references": [],
                    "output_states": [],
                    "required": True,
                }
            ],
            "trigger_composition_logic": "AND(PIN_ONLY)",
            "direction_semantics": "PIN_ONLY",
            "edge_behavior": {},
            "provenance": {},
            "source_yaml_excerpt": "",
            "backend_mapping": {},
            "created_at": "PIN_ONLY",
        }
    )


def _arm_set_bindings(definition: ResearchV1ExecutionDefinition) -> tuple[ResearchV1SetBinding, ...]:
    return (definition.baseline.btc, definition.baseline.non_btc, definition.variant.btc, definition.variant.non_btc)


def _arm_payload(binding: ResearchV1ArmBinding) -> dict[str, Any]:
    return {
        "arm": binding.arm,
        "rules_version_id": binding.rules_version_id,
        "btc": _set_binding_payload(binding.btc),
        "non_btc": _set_binding_payload(binding.non_btc),
    }


def _set_binding_payload(binding: ResearchV1SetBinding) -> dict[str, Any]:
    return {
        "set_version_id": binding.set_version_id,
        "set_id": binding.set_id,
        "set_version": binding.set_version,
        "btc_applicability": binding.btc_applicability,
    }


def _binding_payload(binding: ResearchV1SymbolBinding) -> dict[str, Any]:
    return {
        "asset": binding.asset,
        "symbol": binding.symbol,
        "instrument_symbol": binding.instrument_symbol,
        "segment": binding.segment,
        "allocation_pct": str(binding.allocation_pct),
        "applicable": binding.applicable,
        "applicability": binding.applicability,
        "reason": binding.reason,
        "arm": binding.arm,
        "set_version_id": binding.set_version_id,
        "set_id": binding.set_id,
        "set_version": binding.set_version,
        "rules_version_id": binding.rules_version_id,
    }


def _research_v1_pin_config(pin_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    config = _mapping(pin_payload.get("config_pins"), "config_pins")
    execution = _mapping(config.get("research_v1_execution"), "research_v1_execution")
    if execution.get("schema_version") != RESEARCH_V1_SCHEMA_VERSION:
        raise ResearchV1ExecutionError("Research pin is not a Research V1 execution pin")
    return execution


def _arm_from_pin(payload: Mapping[str, Any]) -> ResearchV1ArmBinding:
    return ResearchV1ArmBinding(
        arm=str(payload["arm"]),
        rules_version_id=str(payload["rules_version_id"]),
        btc=_set_binding_from_pin(_mapping(payload.get("btc"), "btc")),
        non_btc=_set_binding_from_pin(_mapping(payload.get("non_btc"), "non_btc")),
    )


def _set_binding_from_pin(payload: Mapping[str, Any]) -> ResearchV1SetBinding:
    return ResearchV1SetBinding(
        set_version_id=None if payload.get("set_version_id") is None else str(payload.get("set_version_id")),
        set_id=None if payload.get("set_id") is None else str(payload.get("set_id")),
        set_version=None if payload.get("set_version") is None else str(payload.get("set_version")),
        btc_applicability=None if payload.get("btc_applicability") is None else str(payload.get("btc_applicability")),
    )


def _mapping(value: Any, field: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ResearchV1ExecutionError(f"{field} must be an object")
    return value


def _event_amount(event: Mapping[str, Any]) -> Decimal:
    raw = event.get("actual_committed_capital")
    if raw is None:
        raw = event.get("held_committed_capital")
    if raw is None:
        raw = event.get("amount")
    try:
        amount = Decimal(str(raw))
    except Exception as exc:
        raise ResearchV1ExecutionError("Research V1 portfolio event requires exact committed capital") from exc
    if amount <= 0:
        raise ResearchV1ExecutionError("Research V1 portfolio event amount must be positive")
    return amount

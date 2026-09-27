from __future__ import annotations

import json
import os
from decimal import Decimal
from pathlib import Path
import uuid

import pytest

from triggertrade.persistence import (
    PostgresConnectionFactory,
    PostgresResearchConfigurationRegistry,
    PostgresSettings,
    PostgresUnitOfWork,
    apply_postgres_migrations,
)
from triggertrade.rules import CoinRule, DirectionMode, StopLossMode, TakeProfitMode, TradingRulesVersion, TradingRulesVersionDraft
from triggertrade.rules.trading import draft_from_json, draft_to_json, semantic_hash, validate_rules_draft


RULES_PACKAGE = Path("docs/research-import/rules/RESEARCH_V1_RULES.json")
RULES_WEB_IMPORT = Path("docs/research-import/rules/RESEARCH_V1_RULES_WEB_IMPORT.json")


def test_research_v1_combined_rules_validate_through_backend_model():
    rules = _research_v1_rules()

    assert len(rules) == 16
    for rule in rules:
        validate_rules_draft(rule.draft)
        assert draft_from_json(draft_to_json(rule.draft)) == rule.draft
        assert rule.config_hash == semantic_hash(rule.draft)


def test_research_v1_rules_web_import_validates_through_backend_model():
    data = json.loads(RULES_WEB_IMPORT.read_text(encoding="utf-8"))
    rules = tuple(_rules_from_web_import_record(record) for record in data["trading_rules_versions"])

    assert data["schema_version"] == "research-v1-trading-rules-web-import@1"
    assert len(rules) == 16
    for rule in rules:
        validate_rules_draft(rule.draft)
        assert rule.config_hash == semantic_hash(rule.draft)


def test_research_v1_rules_round_trip_real_postgres_owner_state():
    psycopg = pytest.importorskip("psycopg")
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    settings = PostgresSettings(dsn=dsn, schema=f"tt_rules_gap_{uuid.uuid4().hex[:16]}")
    rules = _research_v1_rules()
    try:
        applied = apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        assert applied[-1].version == "0024"
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        with PostgresUnitOfWork(factory) as uow:
            registry = PostgresResearchConfigurationRegistry(uow.connection)
            first = [registry.put_trading_rules_version(rule) for rule in rules]
            assert sum(1 for _rule, created in first if created) == 16
        with PostgresUnitOfWork(factory) as uow:
            registry = PostgresResearchConfigurationRegistry(uow.connection)
            second = [registry.put_trading_rules_version(rule) for rule in rules]
            assert sum(1 for _rule, created in second if created) == 0
            persisted = registry.list_trading_rules_versions()
            assert len(persisted) == 16
            assert {rule.rules_version_id: rule.draft for rule in persisted} == {rule.rules_version_id: rule.draft for rule in rules}
    finally:
        with psycopg.connect(settings.dsn, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _research_v1_rules() -> tuple[TradingRulesVersion, ...]:
    package = json.loads(RULES_PACKAGE.read_text(encoding="utf-8"))
    return tuple(_rules_from_package_record(package, record) for record in package["combined_trading_rules_versions"])


def _rules_from_package_record(package: dict[str, object], record: dict[str, object]) -> TradingRulesVersion:
    draft = _draft_from_components(
        package,
        position_component_id=str(record["position_component_id"]),
        portfolio_component_id=str(record["portfolio_component_id"]),
        metadata={
            "source": "research-v1",
            "position_component_id": str(record["position_component_id"]),
            "portfolio_component_id": str(record["portfolio_component_id"]),
        },
    )
    validate_rules_draft(draft)
    config_hash = semantic_hash(draft)
    return TradingRulesVersion(
        rules_version_id=str(record["rules_version_id"]),
        version=str(record["display_version"]),
        created_at="2026-09-27T00:00:00+00:00",
        created_from_version_id=None,
        created_source="research_v1_rules_package",
        change_summary="Research V1 combined TradingRulesVersion",
        config_hash=config_hash,
        schema_version="trading-rules-v1",
        draft=draft,
        is_current=False,
    )


def _rules_from_web_import_record(record: dict[str, object]) -> TradingRulesVersion:
    draft = draft_from_json(json.dumps(record["draft"], sort_keys=True, separators=(",", ":")))
    return TradingRulesVersion(
        rules_version_id=str(record["rules_version_id"]),
        version=str(record["version"]),
        created_at=str(record["created_at"]),
        created_from_version_id=None if record.get("created_from_version_id") is None else str(record.get("created_from_version_id")),
        created_source=str(record["created_source"]),
        change_summary=str(record["change_summary"]),
        config_hash=str(record["config_hash"]),
        schema_version=str(record["schema_version"]),
        draft=draft,
        is_current=False,
    )


def _draft_from_components(
    package: dict[str, object],
    *,
    position_component_id: str,
    portfolio_component_id: str,
    metadata: dict[str, str],
) -> TradingRulesVersionDraft:
    position_components = package["position_components"]
    portfolio_components = package["portfolio_components"]
    assert isinstance(position_components, dict)
    assert isinstance(portfolio_components, dict)
    position = _resolve_component(position_components, position_component_id)
    portfolio = portfolio_components[portfolio_component_id]
    allocation = package["allocation_policy"]
    assert isinstance(portfolio, dict)
    assert isinstance(allocation, dict)
    stop_loss = position["stop_loss"]
    take_profit = position["take_profit"]
    min_rr = position["minimum_risk_reward"]
    min_edge = position["minimum_net_edge"]
    daily_loss = portfolio["daily_loss_limit"]
    assert isinstance(stop_loss, dict)
    assert isinstance(take_profit, dict)
    assert isinstance(min_rr, dict)
    assert isinstance(min_edge, dict)
    assert isinstance(daily_loss, dict)
    return TradingRulesVersionDraft(
        position_size_pct=Decimal("0.10"),
        take_profit_mode=TakeProfitMode(str(take_profit["mode"])),
        fixed_take_profit_pct=None if take_profit.get("fixed_pct") is None else _pct(take_profit["fixed_pct"]),
        minimum_take_profit_pct=None,
        stop_loss_mode=StopLossMode(str(stop_loss["mode"])),
        stop_loss_pct=None if stop_loss.get("fixed_pct") is None else _pct(stop_loss["fixed_pct"]),
        minimum_risk_reward_enabled=bool(min_rr["enabled"]),
        minimum_risk_reward=Decimal(str(min_rr["value"])),
        minimum_net_edge_enabled=bool(min_edge["enabled"]),
        minimum_net_edge_pct=None if not min_edge["enabled"] else _pct(min_edge["pct"]),
        leverage=Decimal(str(position["leverage"])),
        max_capital_in_positions_pct=_pct(portfolio["max_capital_in_positions_pct"]),
        max_open_positions_enabled=True,
        max_open_positions=int(portfolio["max_open_positions"]),
        max_positions_per_coin_enabled=True,
        max_positions_per_coin=int(portfolio["max_positions_per_coin"]),
        direction_mode=DirectionMode.LONG_SHORT,
        daily_loss_limit_enabled=bool(daily_loss["enabled"]),
        daily_loss_limit_pct=None if not daily_loss["enabled"] else _pct(daily_loss["pct"]),
        minimum_tranche_capital=Decimal(str(portfolio["minimum_tranche_capital"])),
        cooldown_minutes=int(portfolio["cooldown_minutes"]),
        maker_fee_rate=Decimal("0.0002"),
        taker_fee_rate=Decimal("0.00055"),
        spread_cost=Decimal("0"),
        slippage_cost=Decimal("0"),
        funding_cost=Decimal("0"),
        coins=tuple(
            CoinRule(symbol=str(item["backend_symbol"]), enabled=True, max_allocation_pct=_pct(item["allocation_pct"]))
            for item in allocation["coins"]
        ),
        metadata=metadata,
    )


def _resolve_component(components: dict[str, object], component_id: str) -> dict[str, object]:
    component = dict(components[component_id])
    parent_id = component.pop("extends", None)
    if parent_id is None:
        return component
    parent = _resolve_component(components, str(parent_id))
    parent.update(component)
    return parent


def _pct(value: object) -> Decimal:
    return Decimal(str(value)) / Decimal("100")

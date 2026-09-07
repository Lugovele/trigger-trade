from __future__ import annotations

from decimal import Decimal

import pytest

from triggertrade.config import ExecutionVenue, load_config
from triggertrade.execution import OrderType
from triggertrade.execution.futures import FundingEstimate, FuturesRiskManager, FuturesTradeIntent, PositionAction, PositionState, estimate_costs
from triggertrade.execution.position_lifecycle import build_fixed_protective_exit_plan
from triggertrade.market_data import ContractCategory, FuturesAccountState, FuturesInstrumentMetadata
from triggertrade.persistence import FuturesExecutionStore, TradingRulesStore
from triggertrade.rules import CoinRule, DirectionMode, TakeProfitMode, TradingRulesError, TradingRulesService, build_initial_trading_rules


def test_bootstrap_empty_db_creates_single_current_v1_and_is_idempotent(tmp_path):
    path = tmp_path / "rules.sqlite3"
    service = TradingRulesService(TradingRulesStore(path))
    config = _config(path)

    first = service.ensure_initial_version(config, created_at="2026-09-07T00:00:00+00:00")
    second = service.ensure_initial_version(config, created_at="2026-09-07T00:01:00+00:00")
    third = service.ensure_initial_version(config, created_at="2026-09-07T00:02:00+00:00")

    assert first.rules_version_id == second.rules_version_id == third.rules_version_id
    assert first.version == "v1"
    assert first.is_current is True
    assert [version.version for version in service.list_rules_versions()] == ["v1"]
    assert first.draft.coins == (CoinRule("BTCUSDT", True, None),)


def test_bootstrap_after_current_v2_keeps_pointer_and_does_not_mutate_versions(tmp_path):
    path = tmp_path / "rules.sqlite3"
    service = TradingRulesService(TradingRulesStore(path))
    config = _config(path)
    v1 = service.ensure_initial_version(config)
    change = service.create_rules_version_from_current(
        changes={"fixed_take_profit_pct": Decimal("0.02"), "minimum_take_profit_pct": Decimal("0.01")},
        created_source="unit",
        created_at="2026-09-07T01:00:00+00:00",
    )

    after_bootstrap = service.ensure_initial_version(config, created_at="2026-09-07T02:00:00+00:00")

    assert change.changed is True
    assert after_bootstrap.rules_version_id == change.rules.rules_version_id
    assert after_bootstrap.version == "v2"
    assert service.get_rules_version(v1.rules_version_id).draft.fixed_take_profit_pct == Decimal("0.01")
    assert service.get_rules_version(change.rules.rules_version_id).draft.fixed_take_profit_pct == Decimal("0.02")


def test_same_semantic_change_noops_and_immutable_v1_conflict_fails_closed(tmp_path):
    path = tmp_path / "rules.sqlite3"
    store = TradingRulesStore(path)
    service = TradingRulesService(store)
    config = _config(path)
    current = service.ensure_initial_version(config)

    no_change = service.create_rules_version_from_current(changes={}, created_source="unit")
    assert no_change.changed is False
    assert no_change.rules.rules_version_id == current.rules_version_id

    conflict = build_initial_trading_rules(config)
    conflict = conflict.__class__(**{**conflict.__dict__, "stop_loss_pct": Decimal("0.009")})
    orphan_path = tmp_path / "orphan.sqlite3"
    orphan_store = TradingRulesStore(orphan_path)
    with orphan_store._connect() as conn:  # intentional white-box legacy-conflict setup
        orphan_store._insert_version(
            conn,
            build_initial_trading_rules(config),
            version="v1",
            created_at="2026-09-07T00:00:00+00:00",
            created_from_version_id=None,
            created_source="legacy",
            change_summary="legacy v1",
        )
    with pytest.raises(TradingRulesError, match="v1"):
        orphan_store.bootstrap_initial(conflict, created_at="2026-09-07T00:00:00+00:00", created_source="config_bootstrap")



def test_per_coin_position_count_must_match_one_net_position_invariant(tmp_path):
    service = TradingRulesService(TradingRulesStore(tmp_path / "rules.sqlite3"))
    service.ensure_initial_version(_config(tmp_path / "rules.sqlite3"))

    with pytest.raises(TradingRulesError, match="must be 1"):
        service.create_rules_version_from_current(
            changes={"max_positions_per_coin_enabled": True, "max_positions_per_coin": 2},
            created_source="unit",
        )


def test_bootstrap_checks_immutable_v1_conflict_even_when_current_pointer_exists(tmp_path):
    path = tmp_path / "rules.sqlite3"
    service = TradingRulesService(TradingRulesStore(path))
    config = _config(path)
    service.ensure_initial_version(config)
    service.create_rules_version_from_current(
        changes={"fixed_take_profit_pct": Decimal("0.02"), "minimum_take_profit_pct": Decimal("0.01")},
        created_source="unit",
    )

    conflicting_config = _config(path)
    conflicting_config = conflicting_config.__class__(
        **{**conflicting_config.__dict__, "futures_runtime": conflicting_config.futures_runtime.__class__(**{**conflicting_config.futures_runtime.__dict__, "stop_loss_pct": Decimal("0.009")})}
    )

    with pytest.raises(TradingRulesError, match="v1"):
        service.ensure_initial_version(conflicting_config)


def test_reversion_to_prior_semantics_creates_new_immutable_version(tmp_path):
    path = tmp_path / "rules.sqlite3"
    service = TradingRulesService(TradingRulesStore(path))
    config = _config(path)
    v1 = service.ensure_initial_version(config)
    service.create_rules_version_from_current(
        changes={"fixed_take_profit_pct": Decimal("0.02"), "minimum_take_profit_pct": Decimal("0.01")},
        created_source="unit",
    )
    reverted = service.create_rules_version_from_current(
        changes={"fixed_take_profit_pct": v1.draft.fixed_take_profit_pct, "minimum_take_profit_pct": v1.draft.minimum_take_profit_pct},
        created_source="unit",
    )

    assert reverted.changed is True
    assert reverted.rules.version == "v3"
    assert reverted.rules.config_hash == v1.config_hash
    assert reverted.rules.rules_version_id != v1.rules_version_id
    assert service.get_current_rules_version().rules_version_id == reverted.rules.rules_version_id

def test_usage_records_are_idempotent(tmp_path):
    path = tmp_path / "rules.sqlite3"
    service = TradingRulesService(TradingRulesStore(path))
    current = service.ensure_initial_version(_config(path))

    from triggertrade.rules import TradingRulesUsage

    usage = TradingRulesUsage(current.rules_version_id, "LIVE_POSITION", "pos-1", "v1", "ACTIVE", "2026-09-07T00:00:00+00:00")
    assert service.record_usage(usage) is True
    assert service.record_usage(usage) is False
    assert service.get_rules_version_usage(current.rules_version_id) == (usage,)


def test_risk_manager_excludes_minimum_net_edge_when_rule_disabled(tmp_path):
    intent = _intent(expected_move=None)
    tp, sl = build_fixed_protective_exit_plan(
        action=PositionAction.OPEN_LONG,
        entry_price=intent.price,
        take_profit_pct=Decimal("0.01"),
        stop_loss_pct=Decimal("0.005"),
        price_tick=Decimal("0.1"),
    )
    intent = intent.__class__(**{**intent.__dict__, "take_profit": tp, "stop_loss": sl, "minimum_risk_reward": Decimal("1.5")})
    risk = FuturesRiskManager(
        config=__import__("triggertrade.execution.futures", fromlist=["FuturesExecutionConfig"]).FuturesExecutionConfig(),
        store=FuturesExecutionStore(tmp_path / "risk.sqlite3"),
        minimum_net_edge=None,
        max_position_notional=Decimal("10"),
        max_simultaneous_exposure=Decimal("10"),
    ).evaluate(intent=intent, instrument=_instrument(), account=_account(), cost=_cost(), funding=_funding())

    assert risk.approved is True
    assert "FRSK-010" not in risk.blocking_rule_ids
    assert risk.net_edge is not None
    assert risk.net_edge.reason == "minimum net edge disabled by current trading rules"


def _config(db_path):
    return load_config(
        {
            "TRIGGERTRADE_MARKET": "linear",
            "TRIGGERTRADE_CATEGORY": "linear",
            "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO_FUTURES.value,
            "TRIGGERTRADE_ACTIVE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO_FUTURES.value,
            "TRIGGERTRADE_TEST_EXECUTION_VENUE": ExecutionVenue.LOCAL_TEST_SIMULATION.value,
            "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT",
            "TRIGGERTRADE_WATCHLIST": "BTCUSDT",
            "TRIGGERTRADE_RUNTIME_DB_PATH": str(db_path),
            "TRIGGERTRADE_MAX_FUTURES_POSITION_NOTIONAL": "20",
            "TRIGGERTRADE_MAX_TOTAL_FUTURES_POSITION_NOTIONAL": "30",
            "TRIGGERTRADE_FUTURES_POSITION_SIZE_PCT": "0.10",
            "TRIGGERTRADE_TAKE_PROFIT_PCT": "0.01",
            "TRIGGERTRADE_STOP_LOSS_PCT": "0.005",
            "TRIGGERTRADE_MINIMUM_RISK_REWARD": "1.5",
            "TRIGGERTRADE_MINIMUM_NET_EDGE": "0.01",
        }
    )


def _intent(*, expected_move=Decimal("1")):
    return FuturesTradeIntent(
        intent_id="rules-risk-intent",
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        action=PositionAction.OPEN_LONG,
        order_type=OrderType.LIMIT,
        quantity=Decimal("0.1"),
        price=Decimal("95"),
        current_position_state=PositionState.FLAT,
        configured_leverage=Decimal("1"),
        expected_gross_price_move=expected_move,
    )


def _instrument():
    return FuturesInstrumentMetadata(
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        contract_type="LinearPerpetual",
        settlement_asset="USDT",
        quantity_step=Decimal("0.001"),
        price_tick=Decimal("0.1"),
        minimum_order_quantity=Decimal("0.001"),
        minimum_notional=Decimal("5"),
        max_leverage=Decimal("100"),
    )


def _account():
    return FuturesAccountState(
        symbol="BTCUSDT",
        category=ContractCategory.LINEAR,
        settlement_asset="USDT",
        available_margin=Decimal("100"),
        equity=Decimal("100"),
        wallet_balance=Decimal("100"),
        configured_leverage=Decimal("1"),
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        position_size=Decimal("0"),
    )


def _cost():
    return estimate_costs(notional=Decimal("9.5"), maker_fee_rate=Decimal("0"), taker_fee_rate=Decimal("0"))


def _funding():
    return FundingEstimate(None, None, Decimal("0"), Decimal("0"))

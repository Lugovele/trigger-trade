from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
import inspect
import os
from uuid import uuid4

import pytest

from triggertrade.accounting import FuturesFillEvent
from triggertrade.execution.contracts import OrderStatus, OrderType
from triggertrade.execution.futures import PositionAction, PositionState
from triggertrade.persistence.postgres import PostgresConnectionFactory, PostgresSettings, apply_postgres_migrations
from triggertrade.persistence.futures_execution_store import FuturesExecutionRecord
from triggertrade.persistence.futures_position_store import FuturesPositionRecord
from triggertrade.persistence.postgres_futures_stores import (
    PostgresFuturesAccountingStore,
    PostgresFuturesExecutionStore,
    PostgresFuturesPositionStore,
    PostgresOperatorStateStore,
)
from triggertrade.services import runtime as runtime_module
from triggertrade.persistence.operator_state_store import TradingState
from triggertrade.services.futures_runtime import FuturesOperatorExecutionRuntime


def test_canonical_runtime_constructs_worker_owned_postgres_executor():
    source = inspect.getsource(runtime_module.build_canonical_runtime_from_env)

    assert "FuturesOperatorExecutionRuntime" in source
    assert "PostgresFuturesExecutionStore" in source
    assert "PostgresFuturesAccountingStore" in source
    assert "PostgresFuturesPositionStore" in source
    assert "PostgresOperatorStateStore" in source
    assert "operator_executor=operator_executor" in source
    assert "CanonicalResearchDemoTradingCycleProvider" in source
    assert "research_demo_executor=research_demo_executor" in source
    assert " futures_execution_store=FuturesExecutionStore(" not in source
    assert " accounting_store=FuturesAccountingStore(" not in source
    assert " position_store=FuturesPositionStore(" not in source


def test_postgres_futures_store_module_has_no_sqlite_dependency():
    import triggertrade.persistence.postgres_futures_stores as stores

    source = inspect.getsource(stores)

    assert "sqlite3" not in source
    assert "runtime/triggertrade_paper.sqlite3" not in source
    assert "OwnerStateStore" in source


def test_canonical_instrument_resolver_avoids_sqlite_catalog_cache():
    source = inspect.getsource(runtime_module._BybitRuntimeInstrumentCatalog)

    assert "InstrumentCatalogStore" not in source
    assert "linear_instrument_metadata" in source


def test_postgres_operator_state_missing_record_fails_closed(monkeypatch):
    class EmptyOwnerStore:
        def __init__(self, connection):
            pass

        def get(self, **kwargs):
            return None

    class FakeUnitOfWork:
        connection = object()

        def __init__(self, factory):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

    import triggertrade.persistence.postgres_futures_stores as stores

    monkeypatch.setattr(stores, "OwnerStateStore", EmptyOwnerStore)
    monkeypatch.setattr(stores, "PostgresUnitOfWork", FakeUnitOfWork)

    state = PostgresOperatorStateStore(object()).get_trading_state()

    assert state.state is TradingState.TRADING_PAUSED
    assert state.source == "system_default_fail_closed"


def test_close_all_uses_stable_operation_id_and_keeps_nonterminal_aggregate_in_progress(monkeypatch):
    runtime = object.__new__(FuturesOperatorExecutionRuntime)
    position = _position_record("close-all-nonterminal", _execution_record("close-all-nonterminal"))
    store = _FakePositionStore((position,))
    runtime._position_store = store

    class FakeLifecycle:
        def close_position(self, *, position_id, close_reason):
            return type(
                "CloseResult",
                (),
                {
                    "position": type("Position", (), {"position_id": position_id, "status": "CLOSING"})(),
                    "execution": None,
                    "closed_trade": None,
                    "reason": "close_submitted",
                },
            )()

    monkeypatch.setattr(FuturesOperatorExecutionRuntime, "_lifecycle", lambda self, instrument: FakeLifecycle())
    monkeypatch.setattr(FuturesOperatorExecutionRuntime, "_resolve_instrument", lambda self, symbol: object())

    result = runtime.close_all_positions(scope="ACTIVE", operation_id="operator-command-1")

    assert result["close_all_id"] == "operator-command-1"
    assert result["terminal"] is False
    assert store.started == ["operator-command-1"]
    assert store.completed == [("operator-command-1", "in_progress")]


@pytest.mark.skipif(
    not os.environ.get("TRIGGERTRADE_POSTGRES_DSN"),
    reason="isolated PostgreSQL DSN is required for canonical futures persistence smoke",
)
def test_postgres_futures_stores_persist_execution_position_and_accounting_round_trip():
    psycopg = pytest.importorskip("psycopg")
    base = PostgresSettings.from_env(os.environ)
    settings = PostgresSettings(dsn=base.dsn, schema=f"tt_futures_store_{uuid4().hex[:16]}")
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        suffix = uuid4().hex

        execution_store = PostgresFuturesExecutionStore(factory)
        position_store = PostgresFuturesPositionStore(factory)
        accounting_store = PostgresFuturesAccountingStore(factory)

        execution = _execution_record(suffix)
        reserved, created = execution_store.reserve(execution)
        assert created is True
        assert reserved.intent_id == execution.intent_id

        submitted = execution_store.update(
            replace(
                reserved,
                status=OrderStatus.SUBMITTED,
                exchange_order_id=f"exchange-{suffix}",
                reconciliation_state="submitted",
                updated_at=_now(),
            )
        )
        assert PostgresFuturesExecutionStore(factory).get_by_client_order_id(execution.client_order_id) == submitted
        assert submitted in PostgresFuturesExecutionStore(factory).unresolved()

        position = _position_record(suffix, execution)
        position_store.save_open_position(position)
        marked = PostgresFuturesPositionStore(factory).mark_closing(
            position.position_id,
            f"close-intent-{suffix}",
            f"risk-close-{suffix}",
            "MANUAL",
        )
        assert marked.status == "CLOSING"
        assert marked.close_intent_id == f"close-intent-{suffix}"

        fill = FuturesFillEvent(
            event_id=f"fill-{suffix}",
            trade_id=position.trade_id,
            execution_id=execution.client_order_id,
            symbol=position.symbol,
            direction=PositionState.LONG,
            action=PositionAction.OPEN_LONG.value,
            quantity=Decimal("0.001"),
            price=Decimal("50000"),
            fee=Decimal("0.01"),
            fee_asset="USDT",
            occurred_at=_now(),
            settlement_asset="USDT",
        )
        assert accounting_store.record_fill(fill) is True
        assert PostgresFuturesAccountingStore(factory).list_fills(position.trade_id) == (fill,)
    finally:
        with psycopg.connect(base.dsn, autocommit=True) as conn:
            with conn.cursor() as cursor:
                cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _execution_record(suffix: str) -> FuturesExecutionRecord:
    now = _now()
    return FuturesExecutionRecord(
        intent_id=f"intent-{suffix}",
        risk_decision_id=f"risk-{suffix}",
        client_order_id=f"client-{suffix}",
        exchange_order_id=None,
        symbol="BTCUSDT",
        category="linear",
        position_action=PositionAction.OPEN_LONG.value,
        exchange_side="Buy",
        order_type=OrderType.LIMIT.value,
        requested_qty="0.001",
        requested_price="50000",
        leverage="1",
        status=OrderStatus.CREATED,
        created_at=now,
        updated_at=now,
        margin_mode="ISOLATED",
        position_mode="ONE_WAY",
        lane="ACTIVE",
    )


def _position_record(suffix: str, execution: FuturesExecutionRecord) -> FuturesPositionRecord:
    now = _now()
    return FuturesPositionRecord(
        position_id=f"fpos-{suffix}",
        trade_id=f"trade-{suffix}",
        symbol="BTCUSDT",
        side=PositionState.LONG.value,
        status="OPEN",
        opened_at=now,
        closed_at=None,
        entry_price="50000",
        current_qty="0.001",
        initial_qty="0.001",
        leverage="1",
        position_value="50",
        tp_price="50500",
        tp_pct="0.01",
        sl_price="49875",
        sl_pct="0.0025",
        trigger_set_id="set",
        trigger_set_version="v1",
        strategy_rule_id="manual",
        strategy_rule_version="1",
        risk_rule_version="risk-v1",
        protective_exit_version="protective-exit-v1",
        evidence_source="ACTIVE",
        open_intent_id=execution.intent_id,
        open_risk_decision_id=execution.risk_decision_id,
        open_execution_id=execution.client_order_id,
        close_intent_id=None,
        close_risk_decision_id=None,
        close_execution_id=None,
        close_reason=None,
        rule_snapshot={"rules_version_id": "rules-v1"},
        updated_at=now,
        rules_version_id="rules-v1",
        instrument_snapshot={
            "symbol": "BTCUSDT",
            "category": "linear",
            "contract_type": "LinearPerpetual",
            "settle_coin": "USDT",
            "tick_size": "0.1",
            "qty_step": "0.001",
            "min_order_qty": "0.001",
            "min_notional_value": "5",
            "max_leverage": "1",
        },
    )


def _now() -> str:
    return datetime.now(UTC).isoformat()


class _FakePositionStore:
    def __init__(self, positions):
        self._positions = tuple(positions)
        self.started = []
        self.completed = []

    def begin_close_all(self, close_all_id: str) -> None:
        self.started.append(close_all_id)

    def list_open_positions(self, *, include_unknown: bool = False):
        return self._positions

    def complete_close_all(self, close_all_id: str, status: str) -> None:
        self.completed.append((close_all_id, status))

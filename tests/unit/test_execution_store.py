from dataclasses import replace

import pytest

from triggertrade.execution import OrderStatus
from triggertrade.persistence import ExecutionRecord, ExecutionStore


def test_order_lifecycle_persists_and_reloads(tmp_path):
    path = tmp_path / "orders.sqlite3"
    store = ExecutionStore(path)
    record, created = store.reserve(_record())

    assert created is True
    updated = store.update(replace(record, status=OrderStatus.UNKNOWN))
    reloaded = ExecutionStore(path).get_by_intent(updated.intent_id)

    assert reloaded is not None
    assert reloaded.status is OrderStatus.UNKNOWN


def test_unique_client_order_id_is_enforced(tmp_path):
    store = ExecutionStore(tmp_path / "orders.sqlite3")
    store.reserve(_record())

    record, created = store.reserve(replace(_record(), intent_id="intent-2", risk_decision_id="risk-2"))

    assert created is False
    assert record.intent_id == "intent-1"


def _record():
    return ExecutionRecord(
        intent_id="intent-1",
        risk_decision_id="risk-1",
        client_order_id="tt-client",
        exchange_order_id=None,
        symbol="BTCUSDT",
        side="Buy",
        order_type="Limit",
        requested_qty="0.001",
        requested_price="10000.00",
        status=OrderStatus.CREATED,
        created_at="2026-09-04T00:00:00+00:00",
        updated_at="2026-09-04T00:00:00+00:00",
    )

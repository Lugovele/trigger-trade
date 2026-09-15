from __future__ import annotations

import os
import uuid

import pytest

from triggertrade.market_data import MarketRegimeContext, MarketRegimeLabel, RegimeCapability
from triggertrade.persistence import (
    LaneCandleLifecycle,
    LaneRuntimeCheckpoint,
    PostgresConnectionFactory,
    PostgresRuntimeStore,
    PostgresSettings,
    RuntimeHeartbeat,
    apply_postgres_migrations,
)


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_sys009_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def test_postgres_runtime_store_recovers_lane_state_and_heartbeats_after_restart():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        store = PostgresRuntimeStore(factory)

        checkpoint = LaneRuntimeCheckpoint(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
            last_processed_candle_id="BTCUSDT:1m:2026-09-15T00:00:00Z",
            last_processed_candle_open_time="2026-09-15T00:00:00Z",
            last_processed_at="2026-09-15T00:01:00Z",
            runtime_version="futures-dual-lane-v1",
        )
        lifecycle = LaneCandleLifecycle(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id=checkpoint.last_processed_candle_id,
            candle_open_time=checkpoint.last_processed_candle_open_time,
            trigger_set_id=checkpoint.trigger_set_id,
            trigger_set_version=checkpoint.trigger_set_version,
            status="completed",
            signal_id="signal-1",
            intent_id="intent-1",
            risk_decision_id="risk-1",
            execution_intent_id="intent-1",
            processed_at=checkpoint.last_processed_at,
            rules_evaluation={"rules_version_id": "rules-v1"},
        )
        store.lane_checkpoint(checkpoint)
        store.save_lane_lifecycle(lifecycle)
        store.record_heartbeat(
            RuntimeHeartbeat(
                component="futures_runtime",
                status="RUNNING",
                observed_at="2026-09-15T00:01:00Z",
                detail="cycle completed",
                metadata={"symbol": "BTCUSDT"},
            )
        )

        restarted = PostgresRuntimeStore(factory)

        assert restarted.get_lane_checkpoint(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
        ) == checkpoint
        assert restarted.get_lane_lifecycle(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id=checkpoint.last_processed_candle_id,
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
        ) == lifecycle
        assert restarted.lane_processed_count(
            lane="ACTIVE",
            symbol="BTCUSDT",
            timeframe="1m",
            candle_id=checkpoint.last_processed_candle_id,
            trigger_set_id="triggertrade-futures-core",
            trigger_set_version="v1",
        ) == 1
        assert restarted.list_heartbeats()[0].status == "RUNNING"
    finally:
        _drop_schema(settings)


def test_postgres_runtime_store_recovers_latest_market_regime():
    settings = _settings()
    try:
        apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
        factory = PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)
        store = PostgresRuntimeStore(factory)
        older = _regime("regime-old", "2026-09-15T00:00:00Z", MarketRegimeLabel.UPTREND)
        newer = _regime("regime-new", "2026-09-15T00:01:00Z", MarketRegimeLabel.SIDEWAYS)

        store.save_market_regime(older)
        store.save_market_regime(newer)

        restarted = PostgresRuntimeStore(factory)

        assert restarted.get_market_regime("regime-old") == older
        assert restarted.latest_market_regime("BTCUSDT", "1m") == newer
    finally:
        _drop_schema(settings)


def _regime(context_id: str, observed_at: str, label: MarketRegimeLabel) -> MarketRegimeContext:
    return MarketRegimeContext(
        context_id=context_id,
        symbol="BTCUSDT",
        timeframe="1m",
        observed_at=observed_at,
        capability=RegimeCapability.AVAILABLE,
        rule_id="market-regime-v1",
        version="1",
        label=label,
        input_snapshot={"close": "100"},
        normalized_features={"atr": "1"},
        thresholds={"range": "0.01"},
        reason=None,
    )

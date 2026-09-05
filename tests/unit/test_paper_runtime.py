from datetime import UTC, datetime, timedelta
from decimal import Decimal
import sqlite3

import pytest

from triggertrade.config import ConfigError, ExecutionVenue, load_config
from triggertrade.execution import PaperExecutionAdapter
from triggertrade.exchanges import BybitApiError
from triggertrade.persistence import CandleLifecycle, ExecutionStore, RuntimeStore, RuntimeStoreError, TraceStore
from triggertrade.services.runtime import PaperTradingRuntime, RuntimeStatus


def test_no_signal_path_is_successful_and_persisted(tmp_path):
    runtime = _runtime(tmp_path, closes=("100", "99.50"))

    result = runtime.process_once()

    assert result.signal_type == "NO_SIGNAL"
    assert result.intent_id is None
    lifecycle = RuntimeStore(tmp_path / "runtime.sqlite3").get_lifecycle(result.candle_id)
    assert lifecycle is not None
    assert lifecycle.status == "no_signal"


def test_buy_candidate_path_runs_through_risk_and_paper_execution(tmp_path):
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    runtime = _runtime(tmp_path, closes=("100", "98"), adapter=adapter)

    result = runtime.process_once()

    assert result.signal_type == "BUY_CANDIDATE"
    assert result.risk_approved is True
    assert result.execution_status == "filled"
    assert adapter.create_calls == 1
    assert len(ExecutionStore(tmp_path / "runtime.sqlite3").fills_for_intent(result.intent_id)) == 1
    trace = TraceStore(tmp_path / "runtime.sqlite3").trace_for_intent(result.intent_id)
    assert trace["strategy"] is not None
    assert trace["risk"] is not None
    assert len(trace["signals"]) == 1


def test_same_completed_candle_processed_once(tmp_path):
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    runtime = _runtime(tmp_path, closes=("100", "98"), adapter=adapter)

    first = runtime.process_once()
    second = runtime.process_once()

    assert first.execution_status == "filled"
    assert second.skipped_reason == "already_processed"
    assert adapter.create_calls == 1
    assert RuntimeStore(tmp_path / "runtime.sqlite3").processed_count(first.candle_id) == 1


def test_next_candle_processes_after_checkpoint(tmp_path):
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    path = tmp_path / "runtime.sqlite3"
    client = FakeMarketClient(closes=("100", "98"))
    runtime = _runtime(tmp_path, client=client, adapter=adapter, path=path)
    first = runtime.process_once()

    client.closes = ("98", "96")
    client.start = client.start + timedelta(minutes=1)
    second = _runtime(
        tmp_path,
        client=client,
        adapter=adapter,
        path=path,
        now=datetime(2026, 9, 5, 12, 3, 30, tzinfo=UTC),
    ).process_once()

    assert first.candle_id != second.candle_id
    assert second.execution_status == "filled"
    assert adapter.create_calls == 2


def test_restart_does_not_reprocess_same_candle(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    first = _runtime(tmp_path, closes=("100", "98"), path=path).process_once()

    restarted = _runtime(tmp_path, closes=("100", "98"), path=path).process_once()

    assert first.execution_status == "filled"
    assert restarted.skipped_reason == "already_processed"


def test_crash_after_execution_before_checkpoint_does_not_duplicate(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    client = FakeMarketClient(closes=("100", "98"))
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    runtime = _runtime(tmp_path, client=client, adapter=adapter, path=path)
    result = runtime.process_once()
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM runtime_candle_state")

    restarted = _runtime(tmp_path, client=client, adapter=adapter, path=path).process_once()

    assert restarted.skipped_reason == "already_durable"
    assert adapter.create_calls == 1


def test_fresh_adapter_restart_after_submit_reconstructs_paper_fill(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    first_adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    first = _runtime(tmp_path, closes=("100", "98"), adapter=first_adapter, path=path).process_once()
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM runtime_candle_state")
        conn.execute("DELETE FROM runtime_candle_lifecycles")
        conn.execute("DELETE FROM execution_fills")
        conn.execute(
            """
            UPDATE execution_orders
            SET status = 'submitted', exchange_status = 'create_accepted',
                reconciliation_state = 'submitted'
            WHERE intent_id = ?
            """,
            (first.intent_id,),
        )

    fresh_adapter = PaperExecutionAdapter(clock_ms=lambda: 456)
    restarted = _runtime(tmp_path, closes=("100", "98"), adapter=fresh_adapter, path=path).process_once()

    assert restarted.execution_status == "filled"
    assert fresh_adapter.create_calls == 0
    assert len(ExecutionStore(path).fills_for_intent(first.intent_id)) == 1


def test_crash_before_execution_reprocesses_without_skipping_lifecycle(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    client = FakeMarketClient(closes=("100", "98"))
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    RuntimeStore(path).save_lifecycle(
        CandleLifecycle(
            candle_id="BTCUSDT:1m:2026-09-05T12:01:00+00:00",
            symbol="BTCUSDT",
            timeframe="1",
            candle_open_time="2026-09-05T12:01:00+00:00",
            status="risk_recorded",
            signal_id="sig-before-crash",
            intent_id="intent-before-crash",
            risk_decision_id="risk-before-crash",
        )
    )

    result = _runtime(tmp_path, client=client, adapter=adapter, path=path).process_once()

    assert result.execution_status == "filled"
    assert adapter.create_calls == 1


def test_ambiguous_runtime_state_fails_closed_without_paper_execution(tmp_path):
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    store = RuntimeStore(tmp_path / "runtime.sqlite3")
    store.get_checkpoint = lambda symbol, timeframe: (_ for _ in ()).throw(RuntimeStoreError("ambiguous"))
    runtime = _runtime(tmp_path, closes=("100", "98"), adapter=adapter, runtime_store=store)

    with pytest.raises(RuntimeStoreError):
        runtime.process_once()
    assert adapter.create_calls == 0


def test_rejected_risk_does_not_reach_paper_execution(tmp_path):
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    runtime = _runtime(
        tmp_path,
        closes=("100", "98"),
        adapter=adapter,
        extra_env={"TRIGGERTRADE_PAPER_QUOTE_BALANCE": "1"},
    )

    result = runtime.process_once()

    assert result.risk_approved is False
    assert result.execution_status is None
    assert adapter.create_calls == 0


def test_network_failure_creates_no_trade_and_runtime_can_recover(tmp_path):
    client = FakeMarketClient(closes=("100", "98"), fail_once=True)
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    runtime = _runtime(tmp_path, client=client, adapter=adapter)

    failed = runtime.process_once()
    recovered = runtime.process_once()

    assert failed.skipped_reason == "market_data_unavailable"
    assert recovered.execution_status == "filled"
    assert adapter.create_calls == 1


def test_checkpoint_gap_fails_closed_without_paper_execution(tmp_path):
    path = tmp_path / "runtime.sqlite3"
    adapter = PaperExecutionAdapter(clock_ms=lambda: 123)
    first = _runtime(tmp_path, closes=("100", "99.5"), path=path, adapter=adapter).process_once()
    client = FakeMarketClient(closes=("98", "96"))
    client.start = datetime(2026, 9, 5, 12, 5, tzinfo=UTC)

    gap = _runtime(
        tmp_path,
        client=client,
        adapter=adapter,
        path=path,
        now=datetime(2026, 9, 5, 12, 7, 30, tzinfo=UTC),
    ).process_once()

    assert first.signal_type == "NO_SIGNAL"
    assert gap.skipped_reason == "checkpoint_gap"
    assert adapter.create_calls == 0


def test_unsafe_runtime_config_refuses_to_start(tmp_path):
    runtime = _runtime(
        tmp_path,
        extra_env={"TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.BYBIT_DEMO.value},
    )

    with pytest.raises(ConfigError):
        runtime.process_once()


def test_local_paper_runtime_rejects_live_bybit_public_url(tmp_path):
    runtime = _runtime(
        tmp_path,
        extra_env={"BYBIT_BASE_URL": "https://api.bybit.com"},
    )

    with pytest.raises(ConfigError, match="Demo base URL"):
        runtime.process_once()


def test_graceful_stop_prevents_additional_cycles(tmp_path):
    sleeps = []
    runtime = _runtime(tmp_path, closes=("100", "99.5"), sleeper=lambda seconds: sleeps.append(seconds))
    runtime.stop()
    runtime.run_forever(max_cycles=5)

    assert runtime.status is RuntimeStatus.STOPPED
    assert sleeps == []


def _runtime(
    tmp_path,
    *,
    closes=("100", "98"),
    client=None,
    adapter=None,
    path=None,
    extra_env=None,
    sleeper=None,
    now=datetime(2026, 9, 5, 12, 2, 30, tzinfo=UTC),
    runtime_store=None,
):
    env = {
        "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.LOCAL_PAPER.value,
        "TRIGGERTRADE_WATCHLIST": "BTCUSDT",
        "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT",
        "TRIGGERTRADE_CANDLE_INTERVAL": "1",
        "TRIGGERTRADE_POLL_INTERVAL_SECONDS": "1",
        "TRIGGERTRADE_STALE_AFTER_SECONDS": "120",
    }
    if extra_env:
        env.update(extra_env)
    config = load_config(env)
    db_path = path or (tmp_path / "runtime.sqlite3")
    return PaperTradingRuntime(
        config=config,
        market_client=client or FakeMarketClient(closes=closes),
        execution_store=ExecutionStore(db_path),
        trace_store=TraceStore(db_path),
        runtime_store=runtime_store or RuntimeStore(db_path),
        paper_adapter=adapter or PaperExecutionAdapter(clock_ms=lambda: 123),
        clock=lambda: now,
        sleeper=sleeper or (lambda seconds: None),
        logger=lambda message: None,
    )


class FakeResponse:
    def __init__(self, result):
        self.result = result


class FakeMarketClient:
    def __init__(self, *, closes=("100", "98"), fail_once=False):
        self.closes = closes
        self.fail_once = fail_once
        self.start = datetime(2026, 9, 5, 12, 0, tzinfo=UTC)
        self.private_order_calls = 0

    def instrument_metadata(self, symbol):
        if self.fail_once:
            self.fail_once = False
            raise BybitApiError("Bybit API request failed: TimeoutError")
        return FakeResponse(
            {
                "list": [
                    {
                        "symbol": symbol,
                        "baseCoin": "BTC",
                        "quoteCoin": "USDT",
                        "priceFilter": {"tickSize": "0.01"},
                        "lotSizeFilter": {
                            "basePrecision": "0.000001",
                            "minOrderQty": "0.00001",
                            "minOrderAmt": "5",
                        },
                    }
                ]
            }
        )

    def recent_candles(self, symbol, interval, limit):
        older = _candle(self.start, self.closes[0])
        latest = _candle(self.start + timedelta(minutes=1), self.closes[1])
        current_open = _candle(self.start + timedelta(minutes=2), self.closes[1])
        return FakeResponse({"list": [current_open, latest, older]})

    def linear_recent_candles(self, symbol, interval, limit):
        return self.recent_candles(symbol, interval, limit)


def _candle(open_time: datetime, close: str) -> list[str]:
    return [
        str(int(open_time.timestamp() * 1000)),
        close,
        close,
        close,
        close,
        "1",
        close,
    ]

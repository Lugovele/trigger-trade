import os

import pytest

from triggertrade.config import ExecutionVenue, load_config
from triggertrade.execution import PaperExecutionAdapter
from triggertrade.exchanges import BybitDemoClient
from triggertrade.persistence import ExecutionStore, RuntimeStore, TraceStore, TriggerSetStore
from triggertrade.services.dual_lane_runtime import DualLaneRuntime


@pytest.mark.skipif(
    os.environ.get("RUN_TRIGGERTRADE_PUBLIC_DUAL_LANE_SMOKE") != "1",
    reason="real public-market dual-lane smoke is opt-in",
)
def test_public_market_dual_lane_smoke_no_private_order_calls(tmp_path):
    env = dict(os.environ)
    env.update(
        {
            "TRIGGERTRADE_EXECUTION_VENUE": ExecutionVenue.LOCAL_PAPER.value,
            "TRIGGERTRADE_TRADING_MODE": "paper",
            "TRIGGERTRADE_LIVE_TRADING_ENABLED": "false",
            "TRIGGERTRADE_MARKET": "spot",
            "TRIGGERTRADE_RUNTIME_SYMBOL": "BTCUSDT",
            "TRIGGERTRADE_CANDLE_INTERVAL": "1",
            "TRIGGERTRADE_STALE_AFTER_SECONDS": "300",
        }
    )
    config = load_config(env)
    db = tmp_path / "dual-smoke.sqlite3"
    active_adapter = PaperExecutionAdapter()
    test_adapters: list[PaperExecutionAdapter] = []

    runtime = DualLaneRuntime(
        config=config,
        market_client=BybitDemoClient(config=config.bybit),
        execution_store=ExecutionStore(db),
        trace_store=TraceStore(db),
        runtime_store=RuntimeStore(db),
        trigger_set_store=TriggerSetStore(db),
        active_adapter=active_adapter,
        test_adapter_factory=lambda: _test_adapter(test_adapters),
        logger=lambda message: None,
    )

    first = runtime.process_once()
    second = runtime.process_once()

    assert first.candle_id is not None
    assert len(first.active) == 1
    assert len(first.test) >= 1
    assert first.active[0].candle_id == first.test[0].candle_id
    assert second.active[0].skipped_reason == "already_processed"
    assert second.test[0].skipped_reason == "already_processed"
    assert not active_adapter.uses_private_exchange_orders
    assert all(not adapter.uses_private_exchange_orders for adapter in test_adapters)
    assert TriggerSetStore(db).get_active_set("BTCUSDT", "1m").version == "v1"


def _test_adapter(adapters: list[PaperExecutionAdapter]) -> PaperExecutionAdapter:
    adapter = PaperExecutionAdapter()
    adapters.append(adapter)
    return adapter

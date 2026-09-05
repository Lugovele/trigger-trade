from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from triggertrade.market_data import BybitCandle, MarketRegimeLabel, RegimeCapability, RegimeEvaluationWindow, evaluate_market_regime
from triggertrade.market_data.regime import _classify
from triggertrade.persistence import RuntimeStore, RuntimeStoreError


def test_strong_rise_mild_rise_flat_decline_and_strong_decline_sequences():
    assert _evaluate(_trend("100", Decimal("0.10"))).label is MarketRegimeLabel.STRONG_UPTREND
    assert _evaluate(_sparse_steps("100", Decimal("0.02"), up_steps=11)).label is MarketRegimeLabel.UPTREND
    assert _evaluate(_flat_noisy()).label is MarketRegimeLabel.SIDEWAYS
    assert _evaluate(_sparse_steps("100", Decimal("-0.02"), down_steps=11)).label is MarketRegimeLabel.DOWNTREND
    assert _evaluate(_trend("100", Decimal("-0.10"))).label is MarketRegimeLabel.STRONG_DOWNTREND


def test_insufficient_history_incomplete_candle_and_malformed_window_fail_explicitly():
    insufficient = _evaluate(_trend("100", Decimal("0.10"))[:29])
    incomplete = evaluate_market_regime(
        RegimeEvaluationWindow(
            symbol="BTCUSDT",
            timeframe="1m",
            observed_at=_close_time(_trend("100", Decimal("0.10"))[-1]),
            candles=_trend("100", Decimal("0.10")),
            current_candle_completed=False,
        )
    )
    non_contiguous = list(_trend("100", Decimal("0.10")))
    non_contiguous[10] = _candle(_open_time(12), "101")

    assert insufficient.label is MarketRegimeLabel.INSUFFICIENT_DATA
    assert insufficient.reason == "need_30_completed_candles"
    assert incomplete.label is MarketRegimeLabel.UNKNOWN
    assert incomplete.reason == "current_candle_not_completed"
    assert _evaluate(tuple(non_contiguous)).label is MarketRegimeLabel.UNKNOWN


def test_lagging_window_does_not_attach_stale_regime_to_newer_candle():
    candles = _trend("100", Decimal("0.10"))
    evaluation = evaluate_market_regime(
        RegimeEvaluationWindow(
            symbol="BTCUSDT",
            timeframe="1m",
            observed_at=_close_time(candles[-1]) + timedelta(minutes=1),
            candles=candles,
            category="linear",
            current_candle_completed=True,
        )
    )

    assert evaluation.label is MarketRegimeLabel.UNKNOWN
    assert evaluation.reason == "incomplete_or_non_contiguous_window"


def test_unsupported_symbol_or_category_fail_closed():
    candles = _trend("100", Decimal("0.10"))
    unsupported_symbol = evaluate_market_regime(
        RegimeEvaluationWindow(
            symbol="ETHUSDT",
            timeframe="1m",
            observed_at=_close_time(candles[-1]),
            candles=candles,
            category="linear",
            current_candle_completed=True,
        )
    )
    unsupported_category = evaluate_market_regime(
        RegimeEvaluationWindow(
            symbol="BTCUSDT",
            timeframe="1m",
            observed_at=_close_time(candles[-1]),
            candles=candles,
            category="spot",
            current_candle_completed=True,
        )
    )

    assert unsupported_symbol.label is MarketRegimeLabel.UNKNOWN
    assert unsupported_symbol.reason == "unsupported_symbol"
    assert unsupported_category.label is MarketRegimeLabel.UNKNOWN
    assert unsupported_category.reason == "unsupported_category"


def test_exact_boundaries_are_inclusive():
    assert _classify(Decimal("0.50"), Decimal("5"), Decimal("0.65")) is MarketRegimeLabel.STRONG_UPTREND
    assert _classify(Decimal("0.15"), Decimal("2"), Decimal("0.35")) is MarketRegimeLabel.UPTREND
    assert _classify(Decimal("-0.50"), Decimal("-5"), Decimal("-0.65")) is MarketRegimeLabel.STRONG_DOWNTREND
    assert _classify(Decimal("-0.15"), Decimal("-2"), Decimal("-0.35")) is MarketRegimeLabel.DOWNTREND


def test_volatility_shock_without_persistence_is_sideways():
    closes = [Decimal("100")] * 29 + [Decimal("101")]

    evaluation = _evaluate(_candles(closes))

    assert evaluation.label is MarketRegimeLabel.SIDEWAYS
    assert evaluation.normalized_features is not None
    assert evaluation.normalized_features["directional_persistence"] == "0.03448275862068965517241379310"


def test_same_input_same_regime_and_context_id():
    candles = _trend("100", Decimal("0.10"))

    first = _evaluate(candles)
    second = _evaluate(candles)

    assert first == second
    assert first.context_id.startswith("regime-")
    assert first.rule_id == "CTX-REGIME"
    assert first.version == "0.1.0"
    assert first.input_snapshot is not None
    assert first.input_snapshot["category"] == "linear"
    assert "candle_ids" in first.input_snapshot


def test_runtime_store_persists_regime_idempotently_and_rejects_mutation(tmp_path):
    store = RuntimeStore(tmp_path / "regime.sqlite3")
    context = _evaluate(_trend("100", Decimal("0.10")))

    store.save_market_regime(context)
    store.save_market_regime(context)
    saved = store.get_market_regime(context.context_id)

    assert saved == context
    assert store.latest_market_regime("BTCUSDT", "1m") == context
    with pytest.raises(RuntimeStoreError, match="immutable"):
        store.save_market_regime(
            type(context)(
                **{
                    **context.__dict__,
                    "label": MarketRegimeLabel.SIDEWAYS,
                }
            )
        )
    with pytest.raises(RuntimeStoreError, match="immutable"):
        store.save_market_regime(type(context)(**{**context.__dict__, "context_id": "regime-mutated"}))
    with pytest.raises(RuntimeStoreError, match="immutable"):
        store.save_market_regime(type(context)(**{**context.__dict__, "capability": RegimeCapability.UNSUPPORTED}))


def _evaluate(candles: tuple[BybitCandle, ...]):
    observed_at = _close_time(candles[-1]) if candles else datetime(2026, 9, 5, tzinfo=UTC)
    return evaluate_market_regime(
        RegimeEvaluationWindow(
            symbol="BTCUSDT",
            timeframe="1m",
            observed_at=observed_at,
            candles=candles,
            current_candle_completed=True,
        )
    )


def _trend(start: str, step_pct: Decimal) -> tuple[BybitCandle, ...]:
    close = Decimal(start)
    closes = []
    for _ in range(30):
        closes.append(close)
        close = close * (Decimal("1") + step_pct / Decimal("100"))
    return _candles(closes)


def _sparse_steps(start: str, step_pct: Decimal, *, up_steps: int = 0, down_steps: int = 0) -> tuple[BybitCandle, ...]:
    close = Decimal(start)
    closes = [close]
    for index in range(29):
        if index < up_steps:
            close = close * (Decimal("1") + step_pct / Decimal("100"))
        elif index < up_steps + down_steps:
            close = close * (Decimal("1") + step_pct / Decimal("100"))
        closes.append(close)
    return _candles(closes)


def _flat_noisy() -> tuple[BybitCandle, ...]:
    closes = []
    close = Decimal("100")
    for index in range(30):
        closes.append(close)
        close = close + (Decimal("0.01") if index % 2 == 0 else Decimal("-0.01"))
    return _candles(closes)


def _candles(closes: list[Decimal] | tuple[Decimal, ...]) -> tuple[BybitCandle, ...]:
    return tuple(_candle(_open_time(index), str(close)) for index, close in enumerate(closes))


def _candle(open_time: datetime, close: str) -> BybitCandle:
    value = Decimal(close)
    return BybitCandle(
        start_time_ms=int(open_time.timestamp() * 1000),
        open=value,
        high=value,
        low=value,
        close=value,
        volume=Decimal("1"),
        turnover=value,
    )


def _open_time(index: int) -> datetime:
    return datetime(2026, 9, 5, tzinfo=UTC) + timedelta(minutes=index)


def _close_time(candle: BybitCandle) -> datetime:
    return datetime.fromtimestamp(candle.start_time_ms / 1000, UTC) + timedelta(minutes=1)

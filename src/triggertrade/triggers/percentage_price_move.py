"""TRG-001 percentage price move trigger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256

from triggertrade.config import TriggerRuleConfig
from triggertrade.market_data import MarketObservation

from .contracts import Signal, SignalType


@dataclass(frozen=True)
class PercentagePriceMoveTrigger:
    config: TriggerRuleConfig
    symbol: str = "BTCUSDT"

    def evaluate(self, observation: MarketObservation, now: datetime | None = None) -> Signal:
        snapshot = _snapshot(observation, self.config.threshold_pct)
        reason: str | None = None
        condition_result = False
        signal_type = SignalType.NO_SIGNAL

        if observation.symbol != self.symbol:
            reason = "wrong_symbol"
        elif observation.window != self.config.lookback_window:
            reason = "wrong_window"
        elif observation.current_price is None or observation.previous_price is None:
            reason = "missing_price"
        elif observation.previous_price <= 0:
            reason = "invalid_previous_price"
        elif observation.is_stale(now):
            reason = "stale_observation"
        else:
            price_change_pct = _price_change_pct(observation.current_price, observation.previous_price)
            snapshot = {**snapshot, "price_change_pct": str(price_change_pct)}
            condition_result = price_change_pct <= self.config.threshold_pct
            signal_type = SignalType.BUY_CANDIDATE if condition_result else SignalType.NO_SIGNAL
            reason = "threshold_reached" if condition_result else "threshold_not_reached"

        return Signal(
            signal_id=_signal_id(self.config.rule_id, self.config.version, observation, snapshot),
            trigger_rule_id=self.config.rule_id,
            trigger_rule_version=self.config.version,
            symbol=observation.symbol,
            observed_at=_iso(observation.observed_at),
            window=observation.window,
            input_snapshot=snapshot,
            condition_result=condition_result,
            signal_type=signal_type,
            reason=reason,
        )


def _price_change_pct(current: Decimal, previous: Decimal) -> Decimal:
    return ((current - previous) / previous) * Decimal("100")


def _snapshot(observation: MarketObservation, threshold_pct: Decimal) -> dict[str, str]:
    return {
        "current_price": "" if observation.current_price is None else str(observation.current_price),
        "previous_price": "" if observation.previous_price is None else str(observation.previous_price),
        "threshold_pct": str(threshold_pct),
        "source": observation.source,
    }


def _signal_id(
    rule_id: str,
    version: str,
    observation: MarketObservation,
    snapshot: dict[str, str],
) -> str:
    raw = "|".join(
        [
            rule_id,
            version,
            observation.symbol,
            _iso(observation.observed_at),
            observation.window,
            repr(sorted(snapshot.items())),
        ]
    )
    return f"sig-{sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.isoformat()

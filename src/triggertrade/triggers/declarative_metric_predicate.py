"""Generic declarative metric predicate trigger."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from typing import Mapping

from triggertrade.trigger_sets import RuleDefinition

from .contracts import Signal, SignalType


DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY = "triggertrade.research.DeclarativeMetricPredicateTrigger"
DECLARATIVE_METRIC_PREDICATE_SCHEMA = "research-v1-declarative-metric-predicate@1"

_SUPPORTED_OPERATORS = {"EQ", "GTE", "LTE", "GT", "LT"}
_UNAVAILABLE_VALUES = {"", "UNAVAILABLE", "NONE_AVAILABLE", "NULL", "N/A"}
_ALLOWED_OUTPUT_STATES = {"TRUE", "FALSE", "ZERO", "UNAVAILABLE", "LONG", "SHORT", "NONE"}


class DeclarativeTriggerConfigError(ValueError):
    pass


@dataclass(frozen=True)
class DeclarativeTriggerContext:
    symbol: str
    observed_at: datetime
    window: str
    metric_values: Mapping[str, object]
    source: str = "declarative_metric_context"
    lane: str | None = None
    trigger_set_id: str | None = None
    trigger_set_version: str | None = None


@dataclass(frozen=True)
class DeclarativeMetricPredicateConfig:
    metric_ref: str
    operator: str
    threshold: str
    output_states: tuple[str, ...]
    direction_applicability: str | None
    freshness_semantics: str | None

    @classmethod
    def from_rule(cls, rule: RuleDefinition) -> "DeclarativeMetricPredicateConfig":
        definition = dict(rule.definition)
        schema = str(definition.get("schema") or "")
        if schema and schema != DECLARATIVE_METRIC_PREDICATE_SCHEMA:
            raise DeclarativeTriggerConfigError(f"unsupported declarative trigger schema: {schema}")
        metric_ref = _required_text(definition, "metric_ref")
        operator = _required_text(definition, "operator").upper()
        if operator not in _SUPPORTED_OPERATORS:
            raise DeclarativeTriggerConfigError(f"unsupported operator: {operator}")
        threshold = _required_text(definition, "threshold")
        raw_states = definition.get("output_states")
        if not isinstance(raw_states, (list, tuple)) or not raw_states:
            raise DeclarativeTriggerConfigError("output_states must be a non-empty list")
        output_states = tuple(str(item).upper() for item in raw_states)
        unsupported_states = set(output_states) - _ALLOWED_OUTPUT_STATES
        if unsupported_states:
            raise DeclarativeTriggerConfigError(f"unsupported output state(s): {sorted(unsupported_states)}")
        return cls(
            metric_ref=metric_ref,
            operator=operator,
            threshold=threshold,
            output_states=output_states,
            direction_applicability=None
            if definition.get("direction_applicability") in {None, ""}
            else str(definition.get("direction_applicability")),
            freshness_semantics=None
            if definition.get("freshness_semantics") in {None, ""}
            else str(definition.get("freshness_semantics")),
        )


@dataclass(frozen=True)
class DeclarativeMetricPredicateTrigger:
    rule: RuleDefinition

    def __post_init__(self) -> None:
        DeclarativeMetricPredicateConfig.from_rule(self.rule)

    def evaluate(self, context: DeclarativeTriggerContext) -> Signal:
        config = DeclarativeMetricPredicateConfig.from_rule(self.rule)
        raw_value = context.metric_values.get(config.metric_ref)
        snapshot = {
            "implementation_key": DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY,
            "metric_ref": config.metric_ref,
            "operator": config.operator,
            "threshold": config.threshold,
            "metric_value": "" if raw_value is None else str(raw_value),
            "source": context.source,
        }
        if _is_unavailable(raw_value):
            return self._signal(context, snapshot | {"output_state": "UNAVAILABLE"}, False, SignalType.NO_SIGNAL, "metric_unavailable")
        try:
            matched = _compare(raw_value, config.operator, config.threshold)
        except DeclarativeTriggerConfigError as exc:
            return self._signal(context, snapshot | {"output_state": "UNAVAILABLE"}, False, SignalType.NO_SIGNAL, str(exc))
        output_state = _output_state(raw_value, matched, config)
        signal_type = _signal_type(matched, output_state)
        reason = _reason(matched, output_state)
        return self._signal(context, snapshot | {"output_state": output_state}, matched, signal_type, reason)

    def _signal(
        self,
        context: DeclarativeTriggerContext,
        snapshot: Mapping[str, str],
        condition_result: bool,
        signal_type: SignalType,
        reason: str,
    ) -> Signal:
        observed = _iso(context.observed_at)
        signal_id = _signal_id(self.rule, context, snapshot)
        return Signal(
            signal_id=signal_id,
            trigger_rule_id=self.rule.rule_id,
            trigger_rule_version=self.rule.version,
            symbol=context.symbol,
            observed_at=observed,
            window=context.window,
            input_snapshot=snapshot,
            condition_result=condition_result,
            signal_type=signal_type,
            reason=reason,
            lane=context.lane,
            trigger_set_id=context.trigger_set_id,
            trigger_set_version=context.trigger_set_version,
        )


def _compare(raw_value: object, operator: str, threshold: str) -> bool:
    if operator == "EQ":
        left_decimal = _decimal_or_none(raw_value)
        right_decimal = _decimal_or_none(threshold)
        if left_decimal is not None and right_decimal is not None:
            return left_decimal == right_decimal
        return str(raw_value).upper() == str(threshold).upper()
    left = _decimal_or_none(raw_value)
    right = _decimal_or_none(threshold)
    if left is None or right is None:
        raise DeclarativeTriggerConfigError("numeric_comparison_requires_numeric_operands")
    if operator == "GTE":
        return left >= right
    if operator == "LTE":
        return left <= right
    if operator == "GT":
        return left > right
    if operator == "LT":
        return left < right
    raise DeclarativeTriggerConfigError(f"unsupported operator: {operator}")


def _output_state(raw_value: object, matched: bool, config: DeclarativeMetricPredicateConfig) -> str:
    raw_text = str(raw_value).upper()
    if raw_text == "NONE":
        return "NONE"
    value_decimal = _decimal_or_none(raw_value)
    if value_decimal == Decimal("0") and "ZERO" in config.output_states:
        return "ZERO"
    if not matched:
        return "FALSE"
    for preferred in ("LONG", "SHORT", "TRUE"):
        if preferred in config.output_states:
            return preferred
    return "TRUE"


def _signal_type(matched: bool, output_state: str) -> SignalType:
    if not matched or output_state in {"ZERO", "NONE", "UNAVAILABLE"}:
        return SignalType.NO_SIGNAL
    if output_state == "LONG":
        return SignalType.BUY_CANDIDATE
    return SignalType.CONFIRMED


def _reason(matched: bool, output_state: str) -> str:
    if output_state == "ZERO":
        return "zero"
    if output_state == "UNAVAILABLE":
        return "metric_unavailable"
    return "predicate_true" if matched else "predicate_false"


def _required_text(definition: Mapping[str, object], key: str) -> str:
    value = definition.get(key)
    if value in {None, ""}:
        raise DeclarativeTriggerConfigError(f"{key} is required")
    return str(value)


def _decimal_or_none(value: object) -> Decimal | None:
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _is_unavailable(value: object) -> bool:
    return value is None or str(value).upper() in _UNAVAILABLE_VALUES


def _signal_id(rule: RuleDefinition, context: DeclarativeTriggerContext, snapshot: Mapping[str, str]) -> str:
    raw = "|".join(
        [
            rule.rule_id,
            rule.version,
            context.symbol,
            _iso(context.observed_at),
            context.window,
            repr(sorted((str(key), str(value)) for key, value in snapshot.items())),
        ]
    )
    return f"rtrig-{sha256(raw.encode('utf-8')).hexdigest()[:24]}"


def _iso(value: datetime) -> str:
    if value.tzinfo is None:
        value = value.replace(tzinfo=UTC)
    return value.astimezone(UTC).isoformat()

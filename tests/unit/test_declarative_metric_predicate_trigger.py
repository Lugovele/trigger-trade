from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType
from triggertrade.triggers import (
    DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY,
    DECLARATIVE_METRIC_PREDICATE_SCHEMA,
    DeclarativeMetricPredicateTrigger,
    DeclarativeTriggerConfigError,
    DeclarativeTriggerContext,
    SignalType,
    implementation_exists,
)


IMPORT_PACKAGE = Path("docs/research-import/triggers/RESEARCH_V1_TRIGGERS_WEB_IMPORT.json")


def test_research_v1_web_import_records_are_supported_by_generic_runtime():
    records = _import_records()

    assert len(records) == 31
    assert all(record["rule_definition"]["definition"]["implementation_key"] == DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY for record in records)
    assert implementation_exists(DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY)

    for record in records:
        rule = _rule(record["rule_definition"])
        trigger = DeclarativeMetricPredicateTrigger(rule)
        config = rule.definition
        context = _context(metric_ref=str(config["metric_ref"]), value=_matching_value(str(config["operator"]), str(config["threshold"])))

        signal = trigger.evaluate(context)

        assert signal.trigger_rule_id == rule.rule_id
        assert signal.trigger_rule_version == "1.0.0"
        assert signal.trigger_set_id == "research-v1-test"
        assert signal.trigger_set_version == "v1"
        assert signal.condition_result is True
        assert signal.input_snapshot["implementation_key"] == DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY
        assert signal.input_snapshot["metric_ref"] == config["metric_ref"]


def test_declarative_metric_predicate_preserves_numeric_edges_and_unavailable_state():
    rule = _declarative_rule(
        "TR-R-EDGE",
        {
            "metric_ref": "DE",
            "operator": "GTE",
            "threshold": "0.30",
            "output_states": ["TRUE", "FALSE", "UNAVAILABLE"],
        },
    )
    trigger = DeclarativeMetricPredicateTrigger(rule)

    true_signal = trigger.evaluate(_context(metric_ref="DE", value="0.30"))
    false_signal = trigger.evaluate(_context(metric_ref="DE", value="0.29"))
    unavailable_signal = trigger.evaluate(_context(metric_ref="DE", value=None))

    assert true_signal.condition_result is True
    assert true_signal.signal_type is SignalType.CONFIRMED
    assert true_signal.reason == "predicate_true"
    assert false_signal.condition_result is False
    assert false_signal.signal_type is SignalType.NO_SIGNAL
    assert false_signal.reason == "predicate_false"
    assert unavailable_signal.condition_result is False
    assert unavailable_signal.signal_type is SignalType.NO_SIGNAL
    assert unavailable_signal.input_snapshot["output_state"] == "UNAVAILABLE"
    assert unavailable_signal.reason == "metric_unavailable"


def test_btc_return_direction_preserves_long_short_zero_and_unavailable_states():
    long_rule = _declarative_rule(
        "TR-R-BTC-LONG",
        {
            "metric_ref": "RETURN(asset,5m)",
            "operator": "GT",
            "threshold": "0",
            "output_states": ["LONG", "ZERO", "UNAVAILABLE"],
        },
    )
    short_rule = _declarative_rule(
        "TR-R-BTC-SHORT",
        {
            "metric_ref": "RETURN(asset,5m)",
            "operator": "LT",
            "threshold": "0",
            "output_states": ["SHORT", "ZERO", "UNAVAILABLE"],
        },
    )

    long_signal = DeclarativeMetricPredicateTrigger(long_rule).evaluate(_context(metric_ref="RETURN(asset,5m)", value="0.01"))
    short_signal = DeclarativeMetricPredicateTrigger(short_rule).evaluate(_context(metric_ref="RETURN(asset,5m)", value="-0.01"))
    zero_signal = DeclarativeMetricPredicateTrigger(long_rule).evaluate(_context(metric_ref="RETURN(asset,5m)", value="0"))
    unavailable_signal = DeclarativeMetricPredicateTrigger(long_rule).evaluate(_context(metric_ref="RETURN(asset,5m)", value="UNAVAILABLE"))
    explicit_zero_rule = _declarative_rule(
        "TR-R-BTC-ZERO",
        {
            "metric_ref": "RETURN(asset,5m)",
            "operator": "EQ",
            "threshold": "0",
            "output_states": ["ZERO", "UNAVAILABLE"],
        },
    )
    explicit_zero_signal = DeclarativeMetricPredicateTrigger(explicit_zero_rule).evaluate(_context(metric_ref="RETURN(asset,5m)", value="0"))

    assert long_signal.input_snapshot["output_state"] == "LONG"
    assert long_signal.signal_type is SignalType.BUY_CANDIDATE
    assert short_signal.input_snapshot["output_state"] == "SHORT"
    assert short_signal.signal_type is SignalType.CONFIRMED
    assert zero_signal.input_snapshot["output_state"] == "ZERO"
    assert zero_signal.signal_type is SignalType.NO_SIGNAL
    assert explicit_zero_signal.condition_result is True
    assert explicit_zero_signal.input_snapshot["output_state"] == "ZERO"
    assert explicit_zero_signal.signal_type is SignalType.NO_SIGNAL
    assert unavailable_signal.input_snapshot["output_state"] == "UNAVAILABLE"
    assert unavailable_signal.signal_type is SignalType.NO_SIGNAL


def test_declarative_metric_predicate_rejects_unsupported_config():
    with pytest.raises(DeclarativeTriggerConfigError, match="unsupported operator"):
        DeclarativeMetricPredicateTrigger(
            _declarative_rule(
                "TR-R-BAD",
                {
                    "metric_ref": "DE",
                    "operator": "BETWEEN",
                    "threshold": "0.30",
                    "output_states": ["TRUE", "FALSE", "UNAVAILABLE"],
                },
            )
        )


def test_declarative_metric_predicate_signal_id_is_deterministic():
    rule = _declarative_rule(
        "TR-R-DETERMINISTIC",
        {
            "metric_ref": "classifier_direction",
            "operator": "EQ",
            "threshold": "LONG",
            "output_states": ["TRUE", "FALSE", "UNAVAILABLE"],
        },
    )
    context = _context(metric_ref="classifier_direction", value="LONG")
    trigger = DeclarativeMetricPredicateTrigger(rule)

    first = trigger.evaluate(context)
    second = trigger.evaluate(context)

    assert first == second


def _import_records() -> list[dict]:
    return json.loads(IMPORT_PACKAGE.read_text(encoding="utf-8"))["records"]


def _rule(payload: dict) -> RuleDefinition:
    return RuleDefinition(
        rule_id=str(payload["rule_id"]),
        version=str(payload["version"]),
        name=str(payload["name"]),
        status=RuleStatus(str(payload["status"])),
        asset_scope=str(payload["asset_scope"]),
        rule_type=RuleType(str(payload["rule_type"])),
        condition=str(payload["condition"]),
        definition=dict(payload["definition"]),
        created_at=str(payload["created_at"]),
        provenance=str(payload["provenance"]),
        logical_name=payload.get("logical_name"),
        description=payload.get("description"),
        formula=payload.get("formula"),
        parameter_snapshot=payload.get("parameter_snapshot"),
        input_contract=payload.get("input_contract"),
        output_contract=payload.get("output_contract"),
        boundary_semantics=payload.get("boundary_semantics"),
        stale_data_semantics=payload.get("stale_data_semantics"),
        missing_data_semantics=payload.get("missing_data_semantics"),
    )


def _declarative_rule(rule_id: str, definition: dict[str, object]) -> RuleDefinition:
    return RuleDefinition(
        rule_id=rule_id,
        version="1.0.0",
        name=rule_id,
        status=RuleStatus.DRAFT,
        asset_scope="BTCUSDT",
        rule_type=RuleType.TRIGGER,
        condition=f"{definition['metric_ref']} {definition['operator']} {definition['threshold']}",
        definition={
            "implementation_key": DECLARATIVE_METRIC_PREDICATE_IMPLEMENTATION_KEY,
            "schema": DECLARATIVE_METRIC_PREDICATE_SCHEMA,
            **definition,
        },
        created_at="2026-09-27T00:00:00+00:00",
        provenance="unit test",
    )


def _context(*, metric_ref: str, value: object) -> DeclarativeTriggerContext:
    return DeclarativeTriggerContext(
        symbol="BTCUSDT",
        observed_at=datetime(2026, 9, 27, 12, 0, tzinfo=UTC),
        window="1m",
        metric_values={metric_ref: value},
        source="unit-test",
        lane="TEST",
        trigger_set_id="research-v1-test",
        trigger_set_version="v1",
    )


def _matching_value(operator: str, threshold: str) -> object:
    if operator == "EQ":
        return threshold
    threshold_decimal = Decimal(threshold)
    if operator in {"GTE", "LTE"}:
        return threshold
    if operator == "GT":
        return str(threshold_decimal + Decimal("1"))
    if operator == "LT":
        return str(threshold_decimal - Decimal("1"))
    raise AssertionError(f"unexpected operator: {operator}")

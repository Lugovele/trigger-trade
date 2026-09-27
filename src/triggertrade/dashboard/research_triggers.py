"""Read-only Research trigger projections for the dashboard."""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Iterable

from triggertrade.dashboard.metrics_library import get_metric
from triggertrade.trigger_sets import RuleDefinition, RuleType


RESEARCH_TRIGGER_PREFIXES = ("TR-R-", "TR-R-BTC-")


def research_trigger_payload(rules: Iterable[RuleDefinition]) -> dict[str, object]:
    """Return the immutable Research trigger list/detail payload."""

    triggers = tuple(_trigger_payload(rule) for rule in _research_trigger_rules(rules))
    return {
        "triggers": triggers,
        "count": len(triggers),
    }


def research_trigger_detail_payload(rule: RuleDefinition | None) -> dict[str, object] | None:
    """Return one dashboard-safe trigger detail payload."""

    if rule is None or not _is_research_trigger(rule):
        return None
    return _trigger_payload(rule)


def _research_trigger_rules(rules: Iterable[RuleDefinition]) -> tuple[RuleDefinition, ...]:
    return tuple(
        sorted(
            (rule for rule in rules if _is_research_trigger(rule)),
            key=lambda rule: (rule.rule_id, rule.version),
        )
    )


def _is_research_trigger(rule: RuleDefinition) -> bool:
    return rule.rule_type is RuleType.TRIGGER and str(rule.rule_id).startswith(RESEARCH_TRIGGER_PREFIXES)


def _trigger_payload(rule: RuleDefinition) -> dict[str, object]:
    definition = dict(rule.definition or {})
    metric_refs = _metric_refs(definition)
    condition = _condition_text(definition, fallback=rule.condition)
    output_states = tuple(str(value) for value in _list_value(definition.get("output_states")))
    return {
        "trigger_id": rule.rule_id,
        "rule_id": rule.rule_id,
        "version": rule.version,
        "display_name": rule.name,
        "name": rule.name,
        "implementation_key": str(definition.get("implementation_key") or ""),
        "family": _trigger_family(rule, definition),
        "metric": ", ".join(metric_refs) if metric_refs else str(definition.get("metric_ref") or ""),
        "metric_refs": metric_refs,
        "metric_links": tuple(_metric_link(metric_id) for metric_id in _metric_ids(definition)),
        "operator": str(definition.get("operator") or ""),
        "threshold": str(definition.get("threshold") or ""),
        "condition": condition,
        "what_it_checks": condition,
        "formula_text": _formula_text(definition, fallback=condition),
        "output": ", ".join(output_states) if output_states else "TRUE / FALSE / UNAVAILABLE",
        "output_states": output_states,
        "applicability": _applicability(definition),
        "scope": _applicability(definition),
        "status": rule.status.value,
        "canonical_digest": rule.semantic_hash or "",
        "canonical_trigger_id": str(definition.get("canonical_trigger_id") or rule.rule_id),
        "how_it_works": _how_it_works(definition, condition=condition),
        "unavailable_reason": _unavailable_behavior(definition),
        "zero_none_unavailable": _zero_none_unavailable(definition),
        "parameters": _parameters(definition),
        "used_in": (),
        "version_history": (
            {
                "version": rule.version,
                "created_at": rule.created_at,
                "change_summary": _change_summary(rule),
            },
        ),
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
        "immutable": True,
        "raw_definition": _safe_definition(definition),
    }


def _metric_refs(definition: dict[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    metric_ref = str(definition.get("metric_ref") or "").strip()
    if metric_ref:
        refs.append(metric_ref)
    for metric_id in _metric_ids(definition):
        if metric_id not in refs:
            refs.append(metric_id)
    return tuple(refs)


def _metric_ids(definition: dict[str, Any]) -> tuple[str, ...]:
    return tuple(str(value) for value in _list_value(definition.get("current_metric_ids")) if str(value).strip())


def _metric_link(metric_id: str) -> dict[str, object]:
    metric = get_metric(metric_id)
    return {
        "id": metric_id,
        "name": metric.get("name") if metric else metric_id,
        "available": metric is not None,
    }


def _condition_text(definition: dict[str, Any], *, fallback: str) -> str:
    metric = str(definition.get("metric_ref") or "").strip()
    operator = _operator_label(str(definition.get("operator") or "").strip())
    threshold = str(definition.get("threshold") or "").strip()
    if metric and operator and threshold:
        return f"{metric} {operator} {threshold}"
    return fallback


def _operator_label(operator: str) -> str:
    return {
        "EQ": "=",
        "NE": "!=",
        "GTE": ">=",
        "LTE": "<=",
        "GT": ">",
        "LT": "<",
    }.get(operator, operator)


def _formula_text(definition: dict[str, Any], *, fallback: str) -> str:
    parts = [fallback]
    direction = str(definition.get("direction_applicability") or "").strip()
    if direction:
        parts.append(f"Applicability: {direction}")
    output = ", ".join(str(value) for value in _list_value(definition.get("output_states")))
    if output:
        parts.append(f"Output states: {output}")
    freshness = str(definition.get("freshness_semantics") or "").strip()
    if freshness:
        parts.append(f"Unavailable handling: {freshness}")
    return "\n".join(parts)


def _how_it_works(definition: dict[str, Any], *, condition: str) -> str:
    metric_refs = ", ".join(_metric_refs(definition)) or "the configured metric"
    lines = [
        f"Read {metric_refs} at the encoded Research V1 cutoff.",
        f"Evaluate {condition}.",
        f"Emit one of {_join_or(_list_value(definition.get('output_states')))} without substituting missing data.",
    ]
    applicability = _applicability(definition)
    if applicability:
        lines.append(f"Scope: {applicability}.")
    return "\n".join(lines)


def _unavailable_behavior(definition: dict[str, Any]) -> str:
    freshness = str(definition.get("freshness_semantics") or "").strip()
    if freshness:
        return freshness
    outputs = {str(value).upper() for value in _list_value(definition.get("output_states"))}
    if "UNAVAILABLE" in outputs:
        return "UNAVAILABLE is preserved by the trigger output contract."
    return "Unavailable behavior is encoded in the raw trigger definition."


def _zero_none_unavailable(definition: dict[str, Any]) -> str:
    text = json.dumps(definition, sort_keys=True)
    labels = [label for label in ("ZERO", "NONE", "UNAVAILABLE") if label in text]
    return ", ".join(labels) if labels else "No ZERO/NONE/UNAVAILABLE special token encoded."


def _applicability(definition: dict[str, Any]) -> str:
    direction = str(definition.get("direction_applicability") or "").strip()
    included = tuple(str(value) for value in _list_value(definition.get("applicable_coins")))
    excluded = tuple(str(value) for value in _list_value(definition.get("excluded_coins")))
    parts = []
    if direction:
        parts.append(direction)
    if included:
        parts.append("coins: " + ", ".join(included))
    if excluded:
        parts.append("excluded: " + ", ".join(excluded))
    return "; ".join(parts)


def _trigger_family(rule: RuleDefinition, definition: dict[str, Any]) -> str:
    if str(rule.rule_id).startswith("TR-R-BTC-"):
        return "Research V1 BTC/context"
    direction = str(definition.get("direction_applicability") or "")
    if direction in {"LONG", "SHORT"}:
        return f"Research V1 {direction}"
    return "Research V1"


def _parameters(definition: dict[str, Any]) -> tuple[dict[str, str], ...]:
    params = definition.get("params")
    rows: list[dict[str, str]] = []
    if isinstance(params, dict):
        rows.extend(
            {"name": str(key), "value": str(value), "meaning": "Research V1 parameter"}
            for key, value in sorted(params.items())
        )
    for key in ("timeframe_context", "freshness_semantics", "direction_applicability"):
        value = definition.get(key)
        if value:
            rows.append({"name": key, "value": str(value), "meaning": "declarative trigger config"})
    return tuple(rows)


def _change_summary(rule: RuleDefinition) -> str:
    if rule.change_summary:
        return json.dumps(rule.change_summary, sort_keys=True)
    return "Imported Research V1 trigger definition"


def _safe_definition(definition: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(definition)


def _list_value(value: object) -> tuple[object, ...]:
    if value is None:
        return ()
    if isinstance(value, (list, tuple)):
        return tuple(value)
    return (value,)


def _join_or(values: Iterable[object]) -> str:
    items = tuple(str(value) for value in values)
    return ", ".join(items) if items else "the configured output states"

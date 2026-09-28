"""Read-only Research trigger projections for the dashboard."""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any, Iterable

from triggertrade.dashboard.metrics_library import get_metric
from triggertrade.trigger_sets import RuleDefinition, RuleType


RESEARCH_TRIGGER_PREFIXES = ("TR-R-", "TR-R-BTC-")


def research_trigger_payload(rules: Iterable[RuleDefinition], *, research_sets: Iterable[object] = ()) -> dict[str, object]:
    """Return the immutable Research trigger list/detail payload."""

    trigger_rules = _research_trigger_rules(rules)
    latest_versions = _latest_versions_by_rule_id(trigger_rules)
    version_history = _version_history_by_rule_id(trigger_rules)
    used_in = _used_in_by_trigger(research_sets)
    triggers = tuple(
        _trigger_payload(
            rule,
            version_state=_version_state(rule, latest_versions),
            version_history=version_history.get(rule.rule_id, ()),
            used_in=used_in.get((rule.rule_id, rule.version), ()),
        )
        for rule in trigger_rules
    )
    return {
        "triggers": triggers,
        "count": len(triggers),
    }


def research_trigger_detail_payload(
    rule: RuleDefinition | None,
    *,
    all_rules: Iterable[RuleDefinition] = (),
    research_sets: Iterable[object] = (),
) -> dict[str, object] | None:
    """Return one dashboard-safe trigger detail payload."""

    if rule is None or not _is_research_trigger(rule):
        return None
    trigger_rules = _research_trigger_rules(all_rules)
    if not trigger_rules:
        trigger_rules = (rule,)
    latest_versions = _latest_versions_by_rule_id(trigger_rules)
    version_history = _version_history_by_rule_id(trigger_rules)
    used_in = _used_in_by_trigger(research_sets)
    return _trigger_payload(
        rule,
        version_state=_version_state(rule, latest_versions),
        version_history=version_history.get(rule.rule_id, ()),
        used_in=used_in.get((rule.rule_id, rule.version), ()),
    )


def _research_trigger_rules(rules: Iterable[RuleDefinition]) -> tuple[RuleDefinition, ...]:
    return tuple(
        sorted(
            (rule for rule in rules if _is_research_trigger(rule)),
            key=lambda rule: (rule.rule_id, _descending_version_key(rule.version)),
        )
    )


def _is_research_trigger(rule: RuleDefinition) -> bool:
    return rule.rule_type is RuleType.TRIGGER and str(rule.rule_id).startswith(RESEARCH_TRIGGER_PREFIXES)


def _trigger_payload(
    rule: RuleDefinition,
    *,
    version_state: str = "CURRENT",
    version_history: tuple[dict[str, object], ...] = (),
    used_in: tuple[dict[str, object], ...] = (),
) -> dict[str, object]:
    definition = dict(rule.definition or {})
    metric_refs, formula_refs = _metric_formula_refs(definition)
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
        "formula": ", ".join(formula_refs),
        "metric_refs": metric_refs,
        "formula_refs": formula_refs,
        "metric_links": tuple(_metric_link(metric_id) for metric_id in metric_refs),
        "operator": str(definition.get("operator") or ""),
        "threshold": str(definition.get("threshold") or ""),
        "condition": condition,
        "what_it_checks": condition,
        "formula_text": _formula_text(definition, fallback=condition),
        "output": ", ".join(output_states) if output_states else "TRUE / FALSE / UNAVAILABLE",
        "output_states": output_states,
        "timeframe_context": str(definition.get("timeframe_context") or ""),
        "evaluation_semantics": str(definition.get("freshness_semantics") or ""),
        "applicability": _applicability(definition),
        "scope": _applicability(definition),
        "direction_applicability": str(definition.get("direction_applicability") or ""),
        "coin_applicability": tuple(str(value) for value in _list_value(definition.get("applicable_coins"))),
        "excluded_coins": tuple(str(value) for value in _list_value(definition.get("excluded_coins"))),
        "status": rule.status.value,
        "version_state": version_state,
        "canonical_digest": rule.semantic_hash or "",
        "canonical_trigger_id": str(definition.get("canonical_trigger_id") or rule.rule_id),
        "how_it_works": _how_it_works(definition, condition=condition),
        "unavailable_reason": _unavailable_behavior(definition),
        "zero_none_unavailable": _zero_none_unavailable(definition),
        "parameters": _parameters(definition),
        "used_in": used_in,
        "version_history": version_history
        or (
            {
                "version": rule.version,
                "version_state": version_state,
                "created_at": rule.created_at,
                "change_summary": _change_summary(rule),
            },
        ),
        "created_at": rule.created_at,
        "updated_at": rule.updated_at,
        "immutable": True,
        "raw_definition": _safe_definition(definition),
    }


def _metric_formula_refs(definition: dict[str, Any]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    metrics: list[str] = []
    formulas: list[str] = []
    for value in (
        definition.get("metric_ref"),
        *_list_value(definition.get("metric_references")),
        *_list_value(definition.get("metric_refs")),
    ):
        _add_metric_formula_value(value, metrics, formulas)
    for value in (
        *_list_value(definition.get("current_metric_ids")),
        *_list_value(definition.get("formula_references")),
        *_list_value(definition.get("formula_refs")),
    ):
        _add_formula_value(value, formulas)
    return tuple(metrics), tuple(formulas)


def _add_metric_formula_value(value: object, metrics: list[str], formulas: list[str]) -> None:
    token = str(value or "").strip()
    if not token:
        return
    formula_match = re.match(r"^(F-\d{3})(?:\s+(.+))?$", token)
    if formula_match:
        _append_unique(formulas, formula_match.group(1))
        label = str(formula_match.group(2) or "").strip()
        if label:
            _append_unique(metrics, label)
        return
    if re.fullmatch(r"F-\d{3}", token):
        _append_unique(formulas, token)
        return
    _append_unique(metrics, token)


def _add_formula_value(value: object, formulas: list[str]) -> None:
    token = str(value or "").strip()
    if not token:
        return
    for match in re.findall(r"F-\d{3}", token):
        _append_unique(formulas, match)


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
    metric_refs = ", ".join(_metric_formula_refs(definition)[0]) or "the configured metric"
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


def _latest_versions_by_rule_id(rules: Iterable[RuleDefinition]) -> dict[str, str]:
    latest: dict[str, str] = {}
    for rule in rules:
        current = latest.get(rule.rule_id)
        if current is None or _version_key(rule.version) > _version_key(current):
            latest[rule.rule_id] = rule.version
    return latest


def _version_state(rule: RuleDefinition, latest_versions: dict[str, str]) -> str:
    return "CURRENT" if latest_versions.get(rule.rule_id) == rule.version else "HISTORICAL"


def _version_history_by_rule_id(rules: Iterable[RuleDefinition]) -> dict[str, tuple[dict[str, object], ...]]:
    grouped: dict[str, list[RuleDefinition]] = {}
    for rule in rules:
        grouped.setdefault(rule.rule_id, []).append(rule)
    latest = _latest_versions_by_rule_id(rule for rules_for_id in grouped.values() for rule in rules_for_id)
    return {
        rule_id: tuple(
            {
                "version": rule.version,
                "version_state": _version_state(rule, latest),
                "created_at": rule.created_at,
                "change_summary": _change_summary(rule),
            }
            for rule in sorted(rules_for_id, key=lambda value: _version_key(value.version), reverse=True)
        )
        for rule_id, rules_for_id in grouped.items()
    }


def _used_in_by_trigger(research_sets: Iterable[object]) -> dict[tuple[str, str], tuple[dict[str, object], ...]]:
    rows: dict[tuple[str, str], list[dict[str, object]]] = {}
    set_versions = tuple(research_sets)
    latest_sets = _latest_set_versions_by_id(set_versions)
    for research_set in set_versions:
        set_id = str(getattr(research_set, "set_id", "") or "")
        set_version = str(getattr(research_set, "set_version", getattr(research_set, "version", "")) or "")
        version_state = "CURRENT" if latest_sets.get(set_id) == set_version else "HISTORICAL"
        for member in getattr(research_set, "trigger_members", ()) or ():
            trigger_id = str(getattr(member, "trigger_id", "") or "")
            trigger_version = str(getattr(member, "trigger_version", getattr(member, "version", "")) or "")
            rows.setdefault((trigger_id, trigger_version), []).append(
                {
                    "set_id": set_id,
                    "set_version": set_version,
                    "set_status": str(getattr(research_set, "status", "") or ""),
                    "version_state": version_state,
                    "role": str(getattr(member, "role", "") or ""),
                    "position": int(getattr(member, "position", 0) or 0),
                }
            )
    return {key: tuple(sorted(value, key=lambda item: (str(item["set_id"]), str(item["set_version"]), int(item["position"])))) for key, value in rows.items()}


def _latest_set_versions_by_id(research_sets: Iterable[object]) -> dict[str, str]:
    latest: dict[str, str] = {}
    for research_set in research_sets:
        set_id = str(getattr(research_set, "set_id", "") or "")
        set_version = str(getattr(research_set, "set_version", getattr(research_set, "version", "")) or "")
        current = latest.get(set_id)
        if set_id and (current is None or _version_key(set_version) > _version_key(current)):
            latest[set_id] = set_version
    return latest


def _version_key(version: str) -> tuple[int, ...]:
    numbers = tuple(int(value) for value in re.findall(r"\d+", str(version or "")))
    return numbers or (0,)


def _descending_version_key(version: str) -> tuple[int, ...]:
    return tuple(-part for part in _version_key(version))


def _append_unique(values: list[str], value: str) -> None:
    if value and value not in values:
        values.append(value)

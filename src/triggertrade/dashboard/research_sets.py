"""Read-only Research Set projections for the dashboard."""

from __future__ import annotations

from copy import deepcopy
import re
from typing import Any, Iterable, Mapping

from triggertrade.persistence import ResearchSetTriggerMember, ResearchSetVersion, research_set_digest, research_set_payload


def research_sets_payload(
    research_sets: Iterable[ResearchSetVersion],
    *,
    trigger_lookup: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
) -> dict[str, object]:
    """Return the immutable Research Set list/detail payload."""

    records = _research_set_versions(research_sets)
    latest_versions = _latest_versions_by_set_id(records)
    sets = tuple(
        _set_payload(
            record,
            version_state=_version_state(record, latest_versions),
            version_history=_version_history(record.set_id, records, latest_versions),
            trigger_lookup=trigger_lookup or {},
        )
        for record in records
    )
    return {"sets": sets, "count": len(sets)}


def research_set_detail_payload(
    research_set: ResearchSetVersion | None,
    *,
    all_sets: Iterable[ResearchSetVersion] = (),
    trigger_lookup: Mapping[tuple[str, str], Mapping[str, Any]] | None = None,
) -> dict[str, object] | None:
    """Return one dashboard-safe Research Set detail payload."""

    if research_set is None:
        return None
    records = _research_set_versions(all_sets)
    if not records:
        records = (research_set,)
    latest_versions = _latest_versions_by_set_id(records)
    return _set_payload(
        research_set,
        version_state=_version_state(research_set, latest_versions),
        version_history=_version_history(research_set.set_id, records, latest_versions),
        trigger_lookup=trigger_lookup or {},
    )


def trigger_lookup_from_payloads(triggers: Iterable[Mapping[str, Any]]) -> dict[tuple[str, str], Mapping[str, Any]]:
    return {
        (str(trigger.get("trigger_id") or trigger.get("rule_id") or ""), str(trigger.get("version") or "")): trigger
        for trigger in triggers
    }


def _research_set_versions(research_sets: Iterable[ResearchSetVersion]) -> tuple[ResearchSetVersion, ...]:
    return tuple(sorted(research_sets, key=lambda record: (record.set_id, _descending_version_key(record.set_version))))


def _set_payload(
    research_set: ResearchSetVersion,
    *,
    version_state: str,
    version_history: tuple[dict[str, object], ...],
    trigger_lookup: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, object]:
    trigger_versions = tuple(_member_payload(member, trigger_lookup) for member in research_set.trigger_members)
    raw_payload = research_set_payload(research_set)
    return {
        "set_id": research_set.set_id,
        "version": research_set.set_version,
        "set_version": research_set.set_version,
        "display_name": research_set.display_name,
        "status": research_set.status,
        "version_state": version_state,
        "hypothesis": ", ".join(research_set.source_hypothesis_ids),
        "hypothesis_ids": research_set.source_hypothesis_ids,
        "source_candidate_ids": research_set.source_candidate_ids,
        "source_position_ids": research_set.source_position_ids,
        "source_portfolio_ids": research_set.source_portfolio_ids,
        "direction": _direction_label(research_set.direction_semantics),
        "direction_semantics": research_set.direction_semantics,
        "coin_scope": ", ".join(research_set.coin_applicability) if research_set.coin_applicability else "ALL",
        "coin_applicability": research_set.coin_applicability,
        "excluded_coins": research_set.excluded_coins,
        "segment_applicability": research_set.segment_applicability,
        "timeframe": research_set.timeframe,
        "profile_applicability": research_set.profile_applicability,
        "trigger_count": len(trigger_versions),
        "trigger_versions": trigger_versions,
        "trigger_members": trigger_versions,
        "trigger_composition_logic": research_set.trigger_composition_logic,
        "composition": research_set.trigger_composition_logic,
        "edge_behavior": deepcopy(dict(research_set.edge_behavior)),
        "provenance": deepcopy(dict(research_set.provenance)),
        "backend_mapping": deepcopy(dict(research_set.backend_mapping)),
        "source_yaml_excerpt": research_set.source_yaml_excerpt,
        "canonical_digest": research_set.semantic_hash or research_set_digest(research_set),
        "created_at": research_set.created_at,
        "version_history": version_history,
        "immutable": True,
        "raw_definition": raw_payload,
    }


def _member_payload(
    member: ResearchSetTriggerMember,
    trigger_lookup: Mapping[tuple[str, str], Mapping[str, Any]],
) -> dict[str, object]:
    trigger = trigger_lookup.get((member.trigger_id, member.trigger_version), {})
    condition = member.condition or str(trigger.get("condition") or trigger.get("what_it_checks") or "")
    return {
        "position": member.position,
        "trigger_id": member.trigger_id,
        "version": member.trigger_version,
        "trigger_version": member.trigger_version,
        "display_name": str(trigger.get("display_name") or member.trigger_id),
        "role": member.role,
        "direction_applicability": member.direction_applicability,
        "condition": condition,
        "condition_summary": condition,
        "operator": member.operator,
        "threshold": member.threshold,
        "threshold_unit": member.threshold_unit,
        "metric_references": member.metric_references,
        "formula_references": member.formula_references,
        "output_states": member.output_states,
        "required": member.required,
    }


def _latest_versions_by_set_id(research_sets: Iterable[ResearchSetVersion]) -> dict[str, str]:
    latest: dict[str, str] = {}
    for research_set in research_sets:
        current = latest.get(research_set.set_id)
        if current is None or _version_key(research_set.set_version) > _version_key(current):
            latest[research_set.set_id] = research_set.set_version
    return latest


def _version_state(research_set: ResearchSetVersion, latest_versions: Mapping[str, str]) -> str:
    return "CURRENT" if latest_versions.get(research_set.set_id) == research_set.set_version else "HISTORICAL"


def _version_history(
    set_id: str,
    research_sets: Iterable[ResearchSetVersion],
    latest_versions: Mapping[str, str],
) -> tuple[dict[str, object], ...]:
    versions = [record for record in research_sets if record.set_id == set_id]
    return tuple(
        {
            "version": record.set_version,
            "version_state": _version_state(record, latest_versions),
            "status": record.status,
            "created_at": record.created_at,
        }
        for record in sorted(versions, key=lambda value: _version_key(value.set_version), reverse=True)
    )


def _direction_label(direction_semantics: str) -> str:
    text = str(direction_semantics or "").upper()
    if "LONG" in text and "SHORT" in text:
        return "LONG / SHORT"
    if "LONG" in text:
        return "LONG"
    if "SHORT" in text:
        return "SHORT"
    return "NONE"


def _version_key(version: str) -> tuple[int, ...]:
    numbers = tuple(int(value) for value in re.findall(r"\d+", str(version or "")))
    return numbers or (0,)


def _descending_version_key(version: str) -> tuple[int, ...]:
    return tuple(-part for part in _version_key(version))

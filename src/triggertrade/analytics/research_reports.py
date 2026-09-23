"""Read-only Research diagnostic report assembly.

These helpers assemble immutable diagnostic reports from already-retained
source evidence. They do not compute canonical trading decisions and their
outputs have no live feedback authority.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from triggertrade.canonical_json import canonical_json_digest
from triggertrade.persistence.research_store import ResearchDiagnosticDatasetRecord


class ResearchReportError(ValueError):
    pass


ENTRY_REPORT_ITEMS: tuple[str, ...] = tuple(f"ENTRY-RPT-{index:02d}" for index in range(1, 16))
TAKE_PROFIT_REPORT_ITEMS: tuple[str, ...] = tuple(f"TP-RPT-{index:02d}" for index in range(1, 18))
ENTRY_SOURCE_ROWS: tuple[str, ...] = tuple(f"E{index:02d}" for index in range(1, 20))
TAKE_PROFIT_SOURCE_ROWS: tuple[str, ...] = tuple(f"T{index:02d}" for index in range(1, 18))

REPORT_STATUS_VALUES = {"AVAILABLE", "UNAVAILABLE", "INCOMPLETE", "NOT_APPLICABLE"}


@dataclass(frozen=True)
class AssembledResearchReport:
    report_kind: str
    report_definition: dict[str, Any]
    report_payload: dict[str, Any]
    semantic_digest: str


def assemble_entry_report(
    *,
    dataset: ResearchDiagnosticDatasetRecord,
    source_payload: Mapping[str, Any],
    report_config: Mapping[str, Any] | None = None,
) -> AssembledResearchReport:
    return _assemble_report(
        report_kind="ENTRY_REPORT",
        report_version="ENTRY_REPORT_V1",
        dataset=dataset,
        source_payload=source_payload,
        report_config=report_config or {},
        section_name="entry_report",
        items=ENTRY_REPORT_ITEMS,
        source_rows=ENTRY_SOURCE_ROWS,
    )


def assemble_take_profit_report(
    *,
    dataset: ResearchDiagnosticDatasetRecord,
    source_payload: Mapping[str, Any],
    report_config: Mapping[str, Any] | None = None,
) -> AssembledResearchReport:
    return _assemble_report(
        report_kind="TAKE_PROFIT_REPORT",
        report_version="TP_REPORT_V1",
        dataset=dataset,
        source_payload=source_payload,
        report_config=report_config or {},
        section_name="take_profit_report",
        items=TAKE_PROFIT_REPORT_ITEMS,
        source_rows=TAKE_PROFIT_SOURCE_ROWS,
    )


def _assemble_report(
    *,
    report_kind: str,
    report_version: str,
    dataset: ResearchDiagnosticDatasetRecord,
    source_payload: Mapping[str, Any],
    report_config: Mapping[str, Any],
    section_name: str,
    items: tuple[str, ...],
    source_rows: tuple[str, ...],
) -> AssembledResearchReport:
    section = source_payload.get(section_name)
    if not isinstance(section, Mapping):
        raise ResearchReportError(f"{section_name} source section is required")
    clean_rows = _complete_mapping(section.get("source_rows"), required=source_rows, label=f"{section_name}.source_rows")
    for row_id, row in clean_rows.items():
        row_items = row.get("report_items")
        if not isinstance(row_items, list) or not row_items:
            raise ResearchReportError(f"{row_id} report_items must be non-empty")
        unknown = sorted(set(row_items) - set(items))
        if unknown:
            raise ResearchReportError(f"{row_id} references unknown report items: {', '.join(unknown)}")
        _status(row.get("status"), label=f"{row_id}.status")
    availability: dict[str, str] = {}
    _ensure_each_item_has_source(clean_rows, items)
    clean_config = _jsonable(report_config)
    if not isinstance(clean_config, dict):
        raise ResearchReportError("report_config must be an object")
    outputs = _build_outputs(clean_rows, items, report_config=clean_config)
    for item_id, output in outputs.items():
        availability[item_id] = output["status"]
    definition = {
        "methodology_revision": "v1.2.15",
        "report_kind": report_kind,
        "report_version": report_version,
        "source_dataset_id": dataset.dataset_id,
        "dataset_manifest_digest": dataset.manifest_digest,
        "items": list(items),
        "source_rows": list(source_rows),
        "report_config": clean_config,
        "calculation_policy": "read_only_diagnostic_no_canonical_feedback",
    }
    payload = {
        "canonical_feedback": False,
        "report_kind": report_kind,
        "report_version": report_version,
        "source_dataset_id": dataset.dataset_id,
        "dataset_content_digest": dataset.content_digest,
        "dataset_manifest_digest": dataset.manifest_digest,
        "members": _members(clean_rows),
        "source_rows": clean_rows,
        "availability": availability,
        "outputs": outputs,
    }
    semantic_digest = canonical_json_digest(
        {
            "definition": definition,
            "payload": payload,
        }
    )
    return AssembledResearchReport(
        report_kind=report_kind,
        report_definition=definition,
        report_payload=payload,
        semantic_digest=semantic_digest,
    )


def _complete_mapping(value: Any, *, required: tuple[str, ...], label: str) -> dict[str, dict[str, Any]]:
    if not isinstance(value, Mapping):
        raise ResearchReportError(f"{label} must be an object")
    actual = set(value)
    expected = set(required)
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    if missing:
        raise ResearchReportError(f"{label} missing required entries: {', '.join(missing)}")
    if extra:
        raise ResearchReportError(f"{label} has unknown entries: {', '.join(extra)}")
    clean: dict[str, dict[str, Any]] = {}
    for key in required:
        item = _jsonable(value[key])
        if not isinstance(item, dict):
            raise ResearchReportError(f"{label}.{key} must be an object")
        clean[key] = item
    return clean


def _ensure_each_item_has_source(rows: Mapping[str, Mapping[str, Any]], items: tuple[str, ...]) -> None:
    coverage = {item: 0 for item in items}
    for row in rows.values():
        for item in row["report_items"]:
            coverage[item] += 1
    missing = [item for item, count in coverage.items() if count == 0]
    if missing:
        raise ResearchReportError(f"report items lack source rows: {', '.join(missing)}")


def _build_outputs(
    rows: Mapping[str, Mapping[str, Any]],
    items: tuple[str, ...],
    *,
    report_config: Mapping[str, Any],
) -> dict[str, dict[str, Any]]:
    outputs: dict[str, dict[str, Any]] = {}
    for item in items:
        item_rows = {row_id: row for row_id, row in rows.items() if item in row["report_items"]}
        status = _combined_status(tuple(row["status"] for row in item_rows.values()))
        output: dict[str, Any] = {
            "status": status,
            "source_rows": list(item_rows),
            "member_count": str(len(_members(item_rows))),
        }
        ratio = _sum_ratios(item_rows.values())
        if ratio is not None:
            numerator, denominator = ratio
            output["ratio"] = {"numerator": str(numerator), "denominator": str(denominator)}
        mean = _mean_values(item_rows.values())
        if mean is not None:
            numerator, denominator = mean
            output["mean"] = {"numerator": str(numerator), "denominator": str(denominator)}
        excursion = _path_excursion(item_rows.values())
        if excursion is not None:
            output["path_extrema"] = excursion
        if item in {"ENTRY-RPT-13", "TP-RPT-14", "TP-RPT-15", "TP-RPT-16"}:
            output["report_config_digest"] = canonical_json_digest(_jsonable(report_config))
            output["report_config"] = _jsonable(report_config)
        sensitivity = _sensitivity_output(item=item, rows=item_rows.values(), report_config=report_config)
        if sensitivity is not None:
            output["sensitivity"] = sensitivity
        outputs[item] = output
    return outputs


def _combined_status(statuses: tuple[Any, ...]) -> str:
    clean = tuple(_status(value, label="source_row.status") for value in statuses)
    if not clean:
        return "UNAVAILABLE"
    if any(value == "INCOMPLETE" for value in clean):
        return "INCOMPLETE"
    if any(value == "UNAVAILABLE" for value in clean):
        return "UNAVAILABLE" if all(value == "UNAVAILABLE" for value in clean) else "INCOMPLETE"
    if all(value == "NOT_APPLICABLE" for value in clean):
        return "NOT_APPLICABLE"
    return "AVAILABLE"


def _sum_ratios(rows: Any) -> tuple[int, int] | None:
    numerator = 0
    denominator = 0
    found = False
    for row in rows:
        ratio = row.get("ratio")
        if not isinstance(ratio, Mapping):
            continue
        n = _int_value(ratio.get("numerator"), label="ratio.numerator")
        d = _int_value(ratio.get("denominator"), label="ratio.denominator")
        if d <= 0:
            raise ResearchReportError("ratio denominator must be positive")
        numerator += n
        denominator += d
        found = True
    return None if not found else (numerator, denominator)


def _mean_values(rows: Any) -> tuple[int, int] | None:
    values: list[int] = []
    scale = 10**18
    for row in rows:
        for value in row.get("values", []):
            values.append(_scaled_decimal(value, scale=scale))
    if not values:
        return None
    return sum(values), len(values) * scale


def _path_excursion(rows: Any) -> dict[str, str] | None:
    adverse: list[int] = []
    favorable: list[int] = []
    scale = 10**18
    for row in rows:
        path = row.get("path")
        if not isinstance(path, Mapping):
            continue
        anchor = _scaled_decimal(path.get("anchor_price"), scale=scale)
        direction = path.get("direction")
        if direction not in {"LONG", "SHORT"}:
            raise ResearchReportError("path direction must be LONG or SHORT")
        prices = path.get("prices")
        if not isinstance(prices, list) or not prices:
            raise ResearchReportError("path prices must be a non-empty list")
        signed_moves: list[int] = []
        for price in prices:
            delta = _scaled_decimal(price, scale=scale) - anchor
            signed_moves.append(delta if direction == "LONG" else -delta)
        adverse.append(max(0, -min(signed_moves)))
        favorable.append(max(0, max(signed_moves)))
    if not adverse:
        return None
    return {
        "adverse_numerator": str(max(adverse)),
        "favorable_numerator": str(max(favorable)),
        "denominator": str(scale),
    }


def _sensitivity_output(
    *,
    item: str,
    rows: Any,
    report_config: Mapping[str, Any],
) -> dict[str, Any] | None:
    config_key = None
    if item == "TP-RPT-14":
        config_key = "minimum_distance_alternatives"
    elif item == "TP-RPT-15":
        config_key = "maximum_distance_alternatives"
    if config_key is None:
        return None
    alternatives = report_config.get(config_key)
    if alternatives is None:
        return {"status": "UNAVAILABLE", "reason": f"{config_key}_not_supplied"}
    if not isinstance(alternatives, list) or not alternatives:
        raise ResearchReportError(f"{config_key} must be a non-empty list")
    baseline_values = _baseline_distances(rows)
    if not baseline_values:
        return {"status": "UNAVAILABLE", "reason": "baseline_distances_unavailable"}
    scale = 10**18
    results = []
    for alternative in alternatives:
        threshold = _scaled_decimal(alternative, scale=scale)
        if config_key == "minimum_distance_alternatives":
            selected = [value for value in baseline_values if value >= threshold]
        else:
            selected = [value for value in baseline_values if value <= threshold]
        results.append(
            {
                "alternative": str(alternative),
                "selected_count": str(len(selected)),
                "candidate_count": str(len(baseline_values)),
            }
        )
    return {
        "status": "AVAILABLE",
        "axis": "minimum_distance" if config_key == "minimum_distance_alternatives" else "maximum_distance",
        "results": results,
    }


def _baseline_distances(rows: Any) -> list[int]:
    values: list[int] = []
    scale = 10**18
    for row in rows:
        for value in row.get("baseline_distances", []):
            values.append(_scaled_decimal(value, scale=scale))
    return values


def _int_value(value: Any, *, label: str) -> int:
    if isinstance(value, bool) or (not isinstance(value, int) and not (isinstance(value, str) and value.lstrip("-").isdigit())):
        raise ResearchReportError(f"{label} must be an integer")
    return int(value)


def _scaled_decimal(value: Any, *, scale: int) -> int:
    if isinstance(value, float) or isinstance(value, bool):
        raise ResearchReportError("diagnostic decimal must be exact text or integer")
    text = str(value)
    if not text or "e" in text.lower():
        raise ResearchReportError("diagnostic decimal must be plain text")
    negative = text.startswith("-")
    body = text[1:] if negative else text
    whole, dot, frac = body.partition(".")
    if not whole.isdigit() or (dot and not frac.isdigit()):
        raise ResearchReportError("diagnostic decimal must be numeric text")
    if len(frac) > 18:
        raise ResearchReportError("diagnostic decimal has too much precision")
    raw = int(whole) * scale + int(frac.ljust(18, "0") or "0")
    return -raw if negative else raw


def _members(rows: Mapping[str, Mapping[str, Any]]) -> list[dict[str, Any]]:
    members: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row_id, row in rows.items():
        member_ids = row.get("member_ids", [])
        if not isinstance(member_ids, list):
            raise ResearchReportError(f"{row_id}.member_ids must be a list")
        for member_id in member_ids:
            if not isinstance(member_id, str) or not member_id:
                raise ResearchReportError(f"{row_id}.member_ids must contain strings")
            key = f"{row_id}:{member_id}"
            if key not in seen:
                seen.add(key)
                members.append({"source_row": row_id, "member_id": member_id})
    return members


def _status(value: Any, *, label: str) -> str:
    if value not in REPORT_STATUS_VALUES:
        raise ResearchReportError(f"{label} has unsupported status")
    return str(value)


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if value.__class__.__name__ == "Decimal":
        return str(value)
    return value

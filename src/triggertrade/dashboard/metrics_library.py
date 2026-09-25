"""Read-only Metrics Library projection for the dashboard."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
from typing import Any


FAMILY_ORDER = ("F", "A", "M", "N", "S")
EXPECTED_COUNTS = {"F": 16, "A": 9, "M": 8, "N": 8, "S": 6}
METRICS_LIBRARY_PATH = Path(__file__).resolve().parents[3] / "docs" / "metrics_library_v1.json"


def _metric_sort_key(metric: dict[str, Any]) -> tuple[int, int]:
    prefix, _, number = str(metric.get("id") or "").partition("-")
    return (FAMILY_ORDER.index(prefix), int(number))


def _validate_metrics_registry(payload: dict[str, Any]) -> None:
    metrics = payload.get("metrics")
    if not isinstance(metrics, list):
        raise ValueError("Metrics registry must contain a metrics list")
    ids = [str(item.get("id") or "") for item in metrics]
    if len(metrics) != 47 or len(set(ids)) != 47:
        raise ValueError("Metrics registry must contain exactly 47 unique records")
    if any(metric_id.startswith("T-") for metric_id in ids):
        raise ValueError("Metrics registry must not contain T-series records")
    counts = {family: sum(metric_id.startswith(f"{family}-") for metric_id in ids) for family in FAMILY_ORDER}
    if counts != EXPECTED_COUNTS:
        raise ValueError(f"Metrics registry family counts are invalid: {counts}")
    expected_ids = {
        f"{family}-{index:03d}"
        for family, total in EXPECTED_COUNTS.items()
        for index in range(1, total + 1)
    }
    if set(ids) != expected_ids:
        raise ValueError("Metrics registry IDs do not match the approved Metrics Library inventory")


@lru_cache(maxsize=1)
def _load_metrics_registry() -> dict[str, Any]:
    payload = json.loads(METRICS_LIBRARY_PATH.read_text(encoding="utf-8"))
    _validate_metrics_registry(payload)
    payload["metrics"] = sorted(payload["metrics"], key=_metric_sort_key)
    return payload


def metrics_payload() -> dict[str, Any]:
    """Return the immutable Metrics Library API payload."""

    return deepcopy(_load_metrics_registry())


def list_metrics() -> list[dict[str, Any]]:
    """Return all Metrics Library records in approved display order."""

    return metrics_payload()["metrics"]


def get_metric(metric_id: str) -> dict[str, Any] | None:
    """Return one Metrics Library record by canonical ID."""

    wanted = str(metric_id or "").strip().upper()
    for metric in _load_metrics_registry()["metrics"]:
        if metric["id"] == wanted:
            return deepcopy(metric)
    return None

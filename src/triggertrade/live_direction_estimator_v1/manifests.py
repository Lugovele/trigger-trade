"""Deterministic caller-supplied row manifests; no market or label readers."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta
from hashlib import sha256
import json
from math import isfinite
from typing import Iterable

from . import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from .calendar import FIT_DEFINITIONS, H1_START, Horizon, iso, origin
from .features import RawFeatureRow
from .model import CLASSES
from .source import SYMBOLS


def canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def digest(value: object) -> str:
    return sha256(canonical_json(value).encode("utf-8")).hexdigest()


def feature_row_identity(row: RawFeatureRow) -> str:
    t = origin(row.prediction_origin)
    if (row.physical_symbol not in SYMBOLS or row.feature_timestamp != t - timedelta(minutes=1) or
            not row.source_snapshot_id or len(row.values) != 35 or not all(isfinite(v) for v in row.values)):
        raise ValueError("invalid 35-column feature row identity")
    expected_indicators = tuple(float(row.physical_symbol == s) for s in SYMBOLS[1:])
    if tuple(row.values[32:]) != expected_indicators:
        raise ValueError("physical-symbol indicators do not match feature row")
    return digest({"feature_registry": FEATURE_REGISTRY, "symbol": row.physical_symbol,
                   "origin": iso(t), "feature_timestamp": iso(row.feature_timestamp),
                   "source_snapshot_id": row.source_snapshot_id, "values": row.values})


@dataclass(frozen=True)
class RowMetadata:
    physical_symbol: str
    prediction_origin: datetime
    horizon_minutes: int
    feature_status: str
    target_status: str
    canonical_class: str | None
    feature_row: RawFeatureRow | None
    trailing_h_sign: int | None = None
    feature_reasons: tuple[str, ...] = ()
    target_reason: str | None = None

    def __post_init__(self) -> None:
        Horizon(self.horizon_minutes)
        origin(self.prediction_origin)
        if self.physical_symbol not in SYMBOLS:
            raise ValueError("unsupported physical symbol")
        if self.feature_status not in {"AVAILABLE", "UNAVAILABLE"}:
            raise ValueError("invalid feature status")
        if self.target_status not in {"VALID", "UNAVAILABLE", "PENDING"}:
            raise ValueError("invalid target status")
        if self.target_status == "VALID" and self.canonical_class not in CLASSES:
            raise ValueError("VALID target requires exact canonical class")
        if self.target_status != "VALID" and self.canonical_class is not None:
            raise ValueError("unavailable target cannot carry a canonical class")
        if self.feature_status == "AVAILABLE":
            if self.feature_row is None or self.feature_row.physical_symbol != self.physical_symbol or self.feature_row.prediction_origin != self.prediction_origin:
                raise ValueError("AVAILABLE metadata requires matching feature row")
            feature_row_identity(self.feature_row)
        if self.trailing_h_sign is not None and self.trailing_h_sign not in (-1, 0, 1):
            raise ValueError("invalid trailing-H sign")
        if self.feature_status == "AVAILABLE" and self.trailing_h_sign is not None:
            raw_momentum = self.feature_row.values[3 if self.horizon_minutes == 60 else 4]
            if self.trailing_h_sign != (raw_momentum > 0) - (raw_momentum < 0):
                raise ValueError("trailing-H sign disagrees with raw offset-grid momentum")

    @property
    def key(self) -> tuple[str, str]:
        return iso(self.prediction_origin), self.physical_symbol


@dataclass(frozen=True)
class ManifestMember:
    prediction_origin: str
    physical_symbol: str
    canonical_class: str
    feature_row_sha256: str
    source_snapshot_id: str
    trailing_h_sign: int | None

    @property
    def key(self) -> tuple[str, str]:
        return self.prediction_origin, self.physical_symbol


@dataclass(frozen=True)
class ManifestExclusion:
    prediction_origin: str
    physical_symbol: str
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class RowManifest:
    spec_id: str
    spec_version: str
    feature_registry: str
    horizon_minutes: int
    fit_id: str
    segment_type: str
    nominal_start: str
    nominal_end: str
    eligibility_inequality: str
    selected: tuple[ManifestMember, ...]
    excluded: tuple[ManifestExclusion, ...]
    counts_by_symbol: tuple[int, int, int, int]
    counts_by_class: tuple[int, int, int]
    exclusions_by_reason: tuple[tuple[str, int], ...]
    manifest_sha256: str

    def body(self) -> dict[str, object]:
        value = asdict(self)
        value.pop("manifest_sha256")
        return value

    def to_json(self) -> str:
        return canonical_json(asdict(self))

    @classmethod
    def from_json(cls, data: str) -> RowManifest:
        d = json.loads(data)
        d["selected"] = tuple(ManifestMember(**item) for item in d["selected"])
        d["excluded"] = tuple(ManifestExclusion(item["prediction_origin"], item["physical_symbol"],
                                                 tuple(item["reasons"])) for item in d["excluded"])
        d["counts_by_symbol"] = tuple(d["counts_by_symbol"])
        d["counts_by_class"] = tuple(d["counts_by_class"])
        d["exclusions_by_reason"] = tuple(tuple(item) for item in d["exclusions_by_reason"])
        result = cls(**d)
        if result.spec_id != SPEC_ID or result.spec_version != SPEC_VERSION or digest(result.body()) != result.manifest_sha256:
            raise ValueError("manifest integrity or specification mismatch")
        return result


def build_manifest(rows: Iterable[RowMetadata], *, horizon_minutes: int,
                   fit_id: str, segment_type: str) -> RowManifest:
    Horizon(horizon_minutes)
    if fit_id not in FIT_DEFINITIONS:
        raise ValueError("unsupported fit ID")
    segment = FIT_DEFINITIONS[fit_id].segment(segment_type)
    candidates = tuple(rows)
    if any(row.horizon_minutes != horizon_minutes for row in candidates):
        raise ValueError("cross-horizon row in manifest")
    if any(origin(row.prediction_origin) >= H1_START for row in candidates):
        raise ValueError("H1/prospective rows forbidden in development fit manifests")
    ordered = tuple(sorted(candidates, key=lambda r: (r.prediction_origin, SYMBOLS.index(r.physical_symbol))))
    if len({r.key for r in ordered}) != len(ordered):
        raise ValueError("duplicate symbol-origin-horizon manifest key")
    selected: list[ManifestMember] = []
    excluded: list[ManifestExclusion] = []
    reason_counts: dict[str, int] = {}
    symbols = [0, 0, 0, 0]
    classes = [0, 0, 0]
    for row in ordered:
        reasons = []
        if not segment.contains(row.prediction_origin):
            reasons.append("OUTSIDE_SEGMENT")
        if row.feature_status != "AVAILABLE":
            reasons.append("FEATURE_UNAVAILABLE")
            reasons.extend(row.feature_reasons)
        if row.target_status != "VALID":
            reasons.append(f"TARGET_{row.target_status}")
            if row.target_reason:
                reasons.append(row.target_reason)
        if reasons:
            reasons = list(dict.fromkeys(reasons))
            excluded.append(ManifestExclusion(*row.key, tuple(reasons)))
            for reason in reasons:
                reason_counts[reason] = reason_counts.get(reason, 0) + 1
            continue
        if segment_type in {"BASE", "SCORE"} and row.trailing_h_sign is None:
            raise ValueError("selected base/scored row requires causal trailing-H sign")
        raw = row.feature_row
        selected.append(ManifestMember(*row.key, row.canonical_class, feature_row_identity(raw),
                                       raw.source_snapshot_id, row.trailing_h_sign))
        symbols[SYMBOLS.index(row.physical_symbol)] += 1
        classes[CLASSES.index(row.canonical_class)] += 1
    provisional = RowManifest(SPEC_ID, SPEC_VERSION, FEATURE_REGISTRY, horizon_minutes, fit_id,
                              segment_type, iso(segment.nominal_start), iso(segment.nominal_end),
                              segment.inequality, tuple(selected), tuple(excluded), tuple(symbols),
                              tuple(classes), tuple(sorted(reason_counts.items())), "")
    return replace(provisional, manifest_sha256=digest(provisional.body()))

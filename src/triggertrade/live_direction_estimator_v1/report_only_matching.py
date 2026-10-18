"""Match diagnostic scores to actual sealed primary outputs, never native keys."""

from __future__ import annotations

from typing import Iterable

from .manifests import ManifestMember, RowManifest, RowMetadata
from .orchestration import FitBundle, ScoredRow, _assert_manifest


def matched_primary_rows(*, primary: FitBundle, scored_manifest: RowManifest,
                         scored_rows: Iterable[RowMetadata],
                         primary_scored_rows: Iterable[ScoredRow]
                         ) -> tuple[tuple[RowMetadata, ManifestMember], ...]:
    """Only keys with an actual same-bundle primary ScoredRow may be reported."""
    if (scored_manifest.segment_type != "SCORE" or
            scored_manifest.fit_id != primary.manifest.fit_id or
            scored_manifest.horizon_minutes != primary.manifest.horizon_minutes):
        raise ValueError("matched primary SCORE manifest required")
    primary.verify_hashes()
    source = _assert_manifest(scored_manifest, tuple(scored_rows))
    supplied = tuple(primary_scored_rows)
    by_key = {(item.prediction_origin, item.physical_symbol): item for item in supplied}
    if len(by_key) != len(supplied):
        raise ValueError("duplicate primary scored key")
    members = {member.key: member for member in scored_manifest.selected}
    for key, actual in by_key.items():
        member = members.get(key)
        if (member is None or actual.horizon_minutes != scored_manifest.horizon_minutes or
                actual.bundle_sha256 != primary.manifest.bundle_sha256 or
                actual.feature_row_sha256 != member.feature_row_sha256 or
                actual.source_snapshot_id != member.source_snapshot_id):
            raise ValueError("primary scored record differs from sealed manifest/bundle")
    return tuple((row, member) for row, member in zip(source, scored_manifest.selected)
                 if member.key in by_key)

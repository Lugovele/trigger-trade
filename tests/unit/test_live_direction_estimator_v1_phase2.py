"""Bounded source/provenance conformance; no corpus scan or fitting."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
import gzip
from io import StringIO
from itertools import islice
import csv
import json
from pathlib import Path

import pytest

from triggertrade.live_direction_estimator_v1.historical_source import (
    HistoricalMember, HistoricalSourceContract, HistoricalSourceError, adapt_historical_row, adapt_historical_rows,
    adapt_verified_historical_member_bytes,
    authenticate_historical_manifest, authenticate_historical_manifest_bytes, build_historical_snapshot,
    with_verified_member_digest,
)
from triggertrade.live_direction_estimator_v1.prospective_source import (
    AuthenticatedSupersession, AvailabilityEvidence, ProspectiveSourceVersion,
    build_prospective_snapshot,
)
from triggertrade.live_direction_estimator_v1.snapshot import ASOF_VERIFIED, EVENT_TIME_ONLY

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "runtime/data/direction-regime-history/manifest.json"
FIRST = datetime(2024, 9, 30, 7, 20, tzinfo=UTC)
T = datetime(2024, 10, 1, 7, 30, tzinfo=UTC)
MINUTE = timedelta(minutes=1)


def tiny_rows(count=2):
    # Reads only the header and count rows from one existing gzip member.
    with gzip.open(ROOT / "runtime/data/direction-regime-history/BTCUSDT_1m.csv.gz",
                   "rt", encoding="utf-8", newline="") as stream:
        return tuple(islice(csv.DictReader(stream), count))


def prospective_rows():
    rows = []
    first = T - timedelta(minutes=1446)
    for i in range(1445):
        start = first + i * MINUTE
        price = 100 + i * 0.001
        rows.append(ProspectiveSourceVersion(
            "BTCUSDT", start, start + MINUTE, price, price + 0.1, price - 0.1, price,
            "bybit", "linear-1m", f"v{i}", True, start + MINUTE,
            f"receipt-{i}", (AvailabilityEvidence("FINALIZATION", f"final-{i}", start + MINUTE),),
            ("FINALIZATION",), "collector-final-v1", raw_payload_ref=f"payload-{i}",
        ))
    return tuple(rows)


def test_historical_manifest_authentication_and_member_hook():
    contract = authenticate_historical_manifest(MANIFEST)
    assert contract.provenance_mode == EVENT_TIME_ONLY
    assert contract.member("BTCUSDT").member_bytes_verified is False
    verified = with_verified_member_digest(contract, "BTCUSDT", contract.member("BTCUSDT").declared_sha256)
    assert verified.member("BTCUSDT").member_bytes_verified is True
    with pytest.raises(HistoricalSourceError, match="member SHA-256 mismatch"):
        with_verified_member_digest(contract, "BTCUSDT", "0" * 64)
    with pytest.raises(HistoricalSourceError, match="manifest SHA-256 mismatch"):
        authenticate_historical_manifest_bytes(MANIFEST.read_bytes() + b"\n")


def test_historical_row_completion_identity_and_null_availability():
    contract = authenticate_historical_manifest(MANIFEST)
    row = tiny_rows(1)[0]
    a = adapt_historical_row(row, contract=contract, physical_symbol="BTCUSDT", row_number=1)
    b = adapt_historical_row(row, contract=contract, physical_symbol="BTCUSDT", row_number=1)
    assert a == b
    assert a.provenance_mode == EVENT_TIME_ONLY
    assert a.minute.completed and a.minute.source_available_at is None
    assert a.minute.collector_received_at is None and a.minute.evidence_available_at == ()
    assert a.to_dict()["source_available_at"] is None
    assert a.to_dict()["member_bytes_verified"] is False
    changed = dict(row, close="64596.6")
    assert adapt_historical_row(changed, contract=contract, physical_symbol="BTCUSDT", row_number=1).minute.version_id != a.minute.version_id
    with pytest.raises(HistoricalSourceError, match="row number"):
        adapt_historical_row(row, contract=contract, physical_symbol="BTCUSDT", row_number=2)


def test_historical_completion_and_duplicate_fail_closed():
    contract = authenticate_historical_manifest(MANIFEST)
    first, second = tiny_rows(2)
    with pytest.raises(HistoricalSourceError, match="interval/OHLC"):
        adapt_historical_row(dict(first, high="1"), contract=contract, physical_symbol="BTCUSDT", row_number=1)
    with pytest.raises(HistoricalSourceError, match="schema/identity"):
        adapt_historical_row(dict(first, timeframe="5m"), contract=contract, physical_symbol="BTCUSDT", row_number=1)
    with pytest.raises(HistoricalSourceError, match="duplicate"):
        adapt_historical_rows(((1, first), (1, first)), contract=contract, physical_symbol="BTCUSDT")
    assert len(adapt_historical_rows(((1, first), (2, second)), contract=contract, physical_symbol="BTCUSDT")) == 2


def test_manifest_completion_contract_must_be_pass():
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["integrity"]["BTCUSDT"]["status"] = "FAIL"
    raw = json.dumps(data).encode()
    from hashlib import sha256
    with pytest.raises(HistoricalSourceError, match="completion/member"):
        authenticate_historical_manifest_bytes(raw, expected_sha256=sha256(raw).hexdigest())


def test_prospective_cutoff_finalization_and_missing_receipt():
    rows = prospective_rows()
    snap = build_prospective_snapshot("BTCUSDT", T, rows).snapshot
    assert snap is not None and snap.provenance_mode == ASOF_VERIFIED
    assert rows[-1].source_available_at == T - MINUTE
    at_t = replace(rows[0], collector_received_at=T,
                   evidence=(AvailabilityEvidence("FINALIZATION", "at-t", T),))
    assert build_prospective_snapshot("BTCUSDT", T, (at_t,) + rows[1:]).snapshot
    late = replace(rows[0], collector_received_at=T + MINUTE)
    assert build_prospective_snapshot("BTCUSDT", T, (late,) + rows[1:]).reasons == ("DATA_LATE",)
    missing_receipt = replace(rows[0], collector_received_at=None)
    assert missing_receipt.to_dict()["provenance_mode"] is None
    assert "UNVERIFIED_AVAILABILITY" in build_prospective_snapshot("BTCUSDT", T, (missing_receipt,) + rows[1:]).reasons
    missing_final = replace(rows[0], evidence=())
    assert missing_final.source_available_at is None
    assert "UNVERIFIED_AVAILABILITY" in build_prospective_snapshot("BTCUSDT", T, (missing_final,) + rows[1:]).reasons


def test_prospective_required_evidence_max_and_serialization():
    row = prospective_rows()[0]
    row = replace(row, evidence=(AvailabilityEvidence("PUBLICATION", "pub", row.interval_end),
                                 AvailabilityEvidence("FINALIZATION", "final", T)),
                  required_evidence_kinds=("PUBLICATION", "FINALIZATION"))
    assert row.source_available_at == T
    assert row.to_source_minute().source_available_at == T
    assert json.loads(json.dumps(row.to_dict()))["source_available_at"] == T.isoformat()
    missing = replace(row, evidence=row.evidence[:1])
    assert missing.source_available_at is None


def test_authenticated_supersession_and_immutable_snapshot():
    rows = prospective_rows()
    base = build_prospective_snapshot("BTCUSDT", T, rows).snapshot
    audit = json.loads(json.dumps(base.to_audit_dict()))
    assert audit["provenance_mode"] == ASOF_VERIFIED
    assert audit["source_snapshot_id"] == base.source_snapshot_id
    assert audit["local_minutes"][0]["collector_receipt_ref"] == "receipt-0"
    correction = replace(rows[0], provider_version_id="v0-corrected", close=rows[0].close + 0.01,
                         supersedes_version_id=rows[0].provider_version_id,
                         supersession_evidence_ref="provider-correction-1")
    assert "SOURCE_VERSION_CONFLICT" in build_prospective_snapshot("BTCUSDT", T, rows + (correction,)).reasons
    attestation = AuthenticatedSupersession("bybit-corrections-v1", "provider-rule-1", T,
                                           ((rows[0].canonical_version_id, 1), (correction.canonical_version_id, 2)))
    corrected = build_prospective_snapshot("BTCUSDT", T, rows + (correction,), supersession=attestation).snapshot
    assert corrected.local_minutes[0].version_id == correction.canonical_version_id
    assert corrected.to_audit_dict()["supersession_audit"]["authority_ref"] == "provider-rule-1"
    assert corrected.source_snapshot_id != base.source_snapshot_id
    post_t = replace(correction, collector_received_at=T + MINUTE)
    unchanged = build_prospective_snapshot("BTCUSDT", T, rows + (post_t,), supersession=attestation).snapshot
    assert unchanged == base
    assert base.local_minutes[0].version_id == rows[0].canonical_version_id
    future_attestation = replace(attestation, authenticated_at=T + MINUTE)
    assert "SOURCE_VERSION_CONFLICT" in build_prospective_snapshot(
        "BTCUSDT", T, rows + (correction,), supersession=future_attestation).reasons


def test_historical_and_prospective_evidence_do_not_mix():
    first = T - timedelta(minutes=1446)
    rows = []
    for i in range(1445):
        start = first + i * MINUTE
        price = 100 + i * 0.001
        rows.append({
            "open_time": start.isoformat().replace("+00:00", "Z"),
            "close_time": (start + MINUTE).isoformat().replace("+00:00", "Z"),
            "symbol": "BTCUSDT", "logical_symbol": "BTCUSDT", "category": "linear", "timeframe": "1m",
            "open": str(price), "high": str(price + 0.1), "low": str(price - 0.1),
            "close": str(price), "volume": "1", "turnover": "1",
        })
    stream = StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=tuple(rows[0]))
    writer.writeheader()
    writer.writerows(rows)
    member_bytes = gzip.compress(stream.getvalue().encode("utf-8"), mtime=0)
    from hashlib import sha256
    member = HistoricalMember("BTCUSDT", "BTCUSDT", "fixture/BTCUSDT_1m.csv.gz",
                              sha256(member_bytes).hexdigest(), 1445,
                              rows[0]["open_time"], rows[-1]["close_time"])
    contract = HistoricalSourceContract("fixture-corpus", "fixture-manifest", "fixture-final-vintage", (member,))
    verified = with_verified_member_digest(contract, "BTCUSDT", member.declared_sha256)
    unbound = adapt_historical_row(rows[0], contract=verified, physical_symbol="BTCUSDT", row_number=1)
    with pytest.raises(HistoricalSourceError, match="unverified"):
        build_historical_snapshot("BTCUSDT", T, (unbound,), contract=verified)
    verified, observations = adapt_verified_historical_member_bytes(
        member_bytes, contract=contract, physical_symbol="BTCUSDT", row_numbers=range(1, 1446))
    assert all(o.minute.source_available_at is None for o in observations)
    with pytest.raises(HistoricalSourceError, match="unverified"):
        build_historical_snapshot("BTCUSDT", T, observations, contract=contract)
    historical = build_historical_snapshot("BTCUSDT", T, observations, contract=verified)
    assert historical.snapshot is not None
    assert historical.snapshot.provenance_mode == EVENT_TIME_ONLY
    audit = json.loads(json.dumps(historical.snapshot.to_audit_dict()))
    assert audit["local_minutes"][0]["source_available_at"] is None
    assert audit["local_minutes"][0]["collector_received_at"] is None
    from triggertrade.live_direction_estimator_v1.snapshot import build_snapshot
    assert "UNVERIFIED_AVAILABILITY" in build_snapshot(
        "BTCUSDT", T, (o.minute for o in observations), mode=ASOF_VERIFIED).reasons

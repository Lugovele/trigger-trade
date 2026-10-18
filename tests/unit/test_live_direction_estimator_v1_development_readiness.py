"""Bounded development-readiness contracts; no model fitting or corpus scans."""

from __future__ import annotations

from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
import gzip
from pathlib import Path

import pytest
import pyarrow as pa
import pyarrow.parquet as pq
import triggertrade.live_direction_estimator_v1.development_readiness as dr

from triggertrade.live_direction_estimator_v1.development_readiness import (
    ARCHITECTURE_SHA256, CONFIGURATION_SHA256, FREEZE_SHA256, HARNESS_SHA256,
    LOGICAL, RELEASE_SHA256, SOURCE_SHA256, AuthenticatedInputs, BoundedAssembly,
    CanonicalTarget, DevelopmentInputError, DevelopmentPreRunRegistration,
    SerializerIdentity, assemble_bounded_real_inputs, authenticate_generation_manifest_bytes,
    authenticate_output_lock_binding_bytes, authenticate_release_manifest_bytes,
    build_development_environment,
    bounded_manifest_smoke, candidate_origins, construct_features_without_targets,
    join_canonical_targets, main, read_label_range, read_source_range, trailing_h_sign,
    validate_current_development_readiness, validate_development_readiness,
)
from triggertrade.live_direction_estimator_v1.experiment_ledger import ExperimentLedger
from triggertrade.live_direction_estimator_v1.historical_source import (
    HistoricalMember, HistoricalObservation, HistoricalSourceContract,
    authenticate_historical_manifest,
)
from triggertrade.live_direction_estimator_v1.manifests import canonical_json, digest
from triggertrade.live_direction_estimator_v1.snapshot import EVENT_TIME_ONLY
from triggertrade.live_direction_estimator_v1.source import SourceMinute

ROOT = Path(__file__).resolve().parents[2]
SPEC = Path("C:/Users/Елена/Downloads/LIVE_DIRECTION_ESTIMATOR_V1_FINAL.md")
SOURCE = ROOT / "runtime/data/direction-regime-history/manifest.json"
RELEASE = ROOT / "runtime/audit/V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z/CANONICAL_RELEASE_MANIFEST.json"
GENERATION = ROOT / "runtime/data/canonical_direction_labels/V2_GPT6PRO/20261017T054006Z/canonical_generation_manifest.json"
BINDING = ROOT / "runtime/audit/V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z/CANONICAL_RELEASE_BINDING.json"
T = datetime(2024, 10, 2, tzinfo=UTC)
MINUTE = timedelta(minutes=1)


def _environment():
    return build_development_environment(repo=ROOT, spec_path=SPEC)


def _contract() -> HistoricalSourceContract:
    symbols = ("BTCUSDT", "AVAXUSDT", "SUIUSDT", "1000PEPEUSDT")
    members = tuple(HistoricalMember(s, LOGICAL[s], f"{s}.csv.gz", s[:1] * 64, 1445,
                                     "2024-10-01T00:00:00Z", "2024-10-03T00:00:00Z", True)
                    for s in symbols)
    return HistoricalSourceContract("fixture", "a" * 64, "fixture-complete", members)


def _observations(symbol="BTCUSDT", direction=1):
    contract = _contract()
    result = []
    first = T - timedelta(minutes=1446)
    for i in range(1445):
        start = first + i * MINUTE
        price = 100 + direction * i * 0.001 if direction else 100 + (min(i, 1300) // 5) * 0.001
        minute = SourceMinute(symbol, start, start + MINUTE, price, price + .1,
                              price - .1, price, f"v{i}", True,
                              completion_contract_id=contract.completion_contract_id)
        result.append(HistoricalObservation(minute, contract.corpus_id,
                                            contract.manifest_sha256,
                                            contract.member(symbol).declared_sha256,
                                            True, True, i + 1, sha256(str(i).encode()).hexdigest()))
    return contract, tuple(result)


def test_serializer_identity_and_environment_lock_binding():
    serializer = SerializerIdentity.frozen()
    serializer.verify()
    assert serializer == SerializerIdentity.frozen()
    env = _environment()
    env.verify()
    assert env.dependency_lock_sha256 == "bb3235c514f4065e70bc369c6b72dcbdfe0eb7ccdeb1e933c9c8bca369b67b24"
    assert env.numpy_version == "2.2.5" and env.pandas_version == "2.2.3"
    assert env.pyarrow_version == "25.0.1" and env.serializer_id == serializer.serializer_id
    for field in ("dependency_lock_sha256", "numpy_version", "source_manifest_sha256"):
        body = env.body()
        body[field] = "0" * 64 if field != "numpy_version" else "2.2.6"
        changed = replace(env, **{field: body[field]}, identity_sha256=digest(body))
        assert changed.identity_sha256 != env.identity_sha256
        with pytest.raises(DevelopmentInputError):
            changed.verify()


def test_registered_source_release_generation_identity_fail_closed():
    source = authenticate_historical_manifest(SOURCE)
    release = RELEASE.read_bytes()
    generation = GENERATION.read_bytes()
    binding = BINDING.read_bytes()
    authenticate_release_manifest_bytes(release, source_contract=source)
    authenticate_generation_manifest_bytes(generation, source_contract=source)
    authenticate_output_lock_binding_bytes(binding)
    with pytest.raises(DevelopmentInputError, match="SHA-256 mismatch"):
        authenticate_release_manifest_bytes(release + b" ", source_contract=source)
    with pytest.raises(DevelopmentInputError, match="SHA-256 mismatch"):
        authenticate_generation_manifest_bytes(generation + b" ", source_contract=source)
    with pytest.raises(DevelopmentInputError, match="SHA-256 mismatch"):
        authenticate_output_lock_binding_bytes(binding + b" ")
    with pytest.raises(DevelopmentInputError, match="release identity"):
        authenticate_release_manifest_bytes(release, source_contract=replace(source, manifest_sha256="0" * 64))
    for name, value in (("architecture_identity", ARCHITECTURE_SHA256),
                        ("configuration_identity", CONFIGURATION_SHA256),
                        ("freeze_identity", FREEZE_SHA256),
                        ("harness_identity", HARNESS_SHA256)):
        data = json.loads(generation)
        data[name]["sha256"] = "0" * 64
        raw = json.dumps(data).encode()
        with pytest.raises(DevelopmentInputError, match="generation identity"):
            authenticate_generation_manifest_bytes(raw, source_contract=source,
                                                   expected_sha256=sha256(raw).hexdigest())


def test_mapping_candidates_bounds_and_h1_firewall():
    assert LOGICAL["1000PEPEUSDT"] == "PEPEUSDT"
    assert candidate_origins(start=T, end=T + timedelta(minutes=10), max_origins=2) == (T, T + timedelta(minutes=5))
    with pytest.raises(DevelopmentInputError):
        candidate_origins(start=T, end=T + timedelta(minutes=10), max_origins=1)
    with pytest.raises(DevelopmentInputError):
        candidate_origins(start=datetime(2026, 7, 1, tzinfo=UTC),
                          end=datetime(2026, 7, 1, 0, 5, tzinfo=UTC), max_origins=1)
    with pytest.raises(SystemExit):
        main([])


@pytest.mark.parametrize("direction,expected", [(1, 1), (-1, -1), (0, 0)])
def test_exact_causal_trailing_sign(direction, expected):
    contract, btc = _observations(direction=direction)
    features = construct_features_without_targets(origins=(T,), symbols=("BTCUSDT",),
                                                  observations={"BTCUSDT": btc}, contract=contract)
    assert features[0].row is not None
    assert features[0].row.feature_timestamp == T - MINUTE
    assert trailing_h_sign(local_minutes=tuple(x.minute for x in btc), horizon_minutes=60) == expected
    assert trailing_h_sign(local_minutes=tuple(x.minute for x in btc), horizon_minutes=120) == expected
    assert all(x.minute.interval_end != T for x in btc)


def test_join_horizon_independence_target_unavailable_and_missing_minute():
    contract, btc = _observations()
    features = construct_features_without_targets(origins=(T,), symbols=("BTCUSDT",),
                                                  observations={"BTCUSDT": btc}, contract=contract)
    targets60 = {("BTCUSDT", T, 60): CanonicalTarget("BTCUSDT", T, 60, "VALID", "LONG_FAVORED", None)}
    targets120 = {("BTCUSDT", T, 120): CanonicalTarget("BTCUSDT", T, 120, "UNAVAILABLE", None, "fixture")}
    common = dict(feature_rows=features, contract=contract,
                  release_manifest_sha256=RELEASE_SHA256, label_member_sha256="b" * 64)
    r60 = join_canonical_targets(**common, targets=targets60, horizon_minutes=60)
    r120 = join_canonical_targets(**common, targets=targets120, horizon_minutes=120)
    assert r60[0].metadata.target_status == "VALID"
    assert r120[0].metadata.target_status == "UNAVAILABLE"
    assert r60[0].metadata.feature_row == r120[0].metadata.feature_row
    assert r60[0].metadata.trailing_h_sign == 1
    assert r60[0].provenance_mode == EVENT_TIME_ONLY
    assert r60[0].metadata.feature_row.source_snapshot_id == r120[0].source_snapshot_id
    assert join_canonical_targets(**common, targets={}, horizon_minutes=60)[0].metadata.target_reason == "MISSING_CANONICAL_TARGET"
    absent = btc[:400] + btc[401:]
    missing_features = construct_features_without_targets(origins=(T,), symbols=("BTCUSDT",),
                                                          observations={"BTCUSDT": absent}, contract=contract)
    retained = join_canonical_targets(feature_rows=missing_features, targets=targets60,
                                      contract=contract,
                                      release_manifest_sha256=RELEASE_SHA256,
                                      label_member_sha256="b" * 64, horizon_minutes=60)
    assert retained[0].metadata.feature_status == "UNAVAILABLE"
    assert "MISSING_REQUIRED_MINUTE" in retained[0].metadata.feature_reasons
    with pytest.raises(DevelopmentInputError, match="duplicate assembled key"):
        join_canonical_targets(**{**common, "feature_rows": features + features},
                               targets=targets60, horizon_minutes=60)


def test_bounded_fixture_manifest_and_readiness(tmp_path):
    contract, btc = _observations()
    features = construct_features_without_targets(origins=(T,), symbols=("BTCUSDT",),
                                                  observations={"BTCUSDT": btc}, contract=contract)
    env = _environment()
    registration = DevelopmentPreRunRegistration.from_environment(env)
    ledger = ExperimentLedger(tmp_path / "ledger", clock=lambda: datetime(2026, 10, 18, tzinfo=UTC))
    entry = registration.append_to(ledger, horizon_minutes=60, actor="test")
    assert entry.action == "DEVELOPMENT_PREFLIGHT_REGISTERED"
    assert entry.partition_accessed == "F1_F5_DEVELOPMENT"
    assert all("MODEL_FITTED" not in e.action and "FOLD_SCORED" not in e.action for e in ledger.read_all())
    assert registration.h1_governance_status == "CLEANLINESS_UNVERIFIED"
    assert registration.h1_not_used_for_fitting and registration.prospective_not_used_for_fitting
    assemblies = []
    manifests = []
    for horizon, label_hash in ((60, "d8f60429d25cffde767c5ee244f125114ca872666c9f6884c893f1ada285c5ed"),
                                (120, "f4161b32784539376f3148b867f5658d98c05d9ea891b01e1996d7107c60b06b")):
        targets = {("BTCUSDT", T, horizon): CanonicalTarget("BTCUSDT", T, horizon, "VALID", "LONG_FAVORED", None)}
        rows = join_canonical_targets(feature_rows=features, targets=targets,
                                      contract=contract,
                                      release_manifest_sha256=RELEASE_SHA256,
                                      label_member_sha256=label_hash, horizon_minutes=horizon)
        assembly = BoundedAssembly(rows, horizon, ("BTCUSDT",), T, T + timedelta(minutes=5),
                                   SOURCE_SHA256, RELEASE_SHA256, (("BTCUSDT", "a" * 64),), label_hash, 0)
        assemblies.append(assembly)
        manifests.append(bounded_manifest_smoke(assembly))
    ready = validate_development_readiness(environment=env, e60=assemblies[0], e120=assemblies[1],
                                           e60_manifest=manifests[0], e120_manifest=manifests[1],
                                           tracked_files_clean=True, registration=registration)
    assert ready.status == "BLOCKED"
    assert ready.e60_status == ready.e120_status == "BLOCKED"
    assert not assemblies[0].report()["source_identity_verified"]
    assert validate_current_development_readiness(
        repo=ROOT, spec_path=SPEC, e60=assemblies[0], e120=assemblies[1],
        e60_manifest=manifests[0], e120_manifest=manifests[1]).status == "BLOCKED"
    assert validate_development_readiness(environment=env, e60=assemblies[0], e120=None,
        e60_manifest=manifests[0], e120_manifest=None, tracked_files_clean=True,
        registration=registration).status == "BLOCKED"
    assert validate_development_readiness(environment=env, e60=assemblies[0], e120=assemblies[1],
        e60_manifest=manifests[0], e120_manifest=manifests[1], tracked_files_clean=False,
        registration=registration).status == "BLOCKED"


def test_bounded_gzip_reader_authenticates_exact_bytes_and_order(tmp_path):
    source_root = tmp_path / "runtime/data/direction-regime-history"
    source_root.mkdir(parents=True)
    path = source_root / "BTCUSDT_1m.csv.gz"
    first = T - timedelta(minutes=1446)
    header = "open_time,close_time,symbol,logical_symbol,category,timeframe,open,high,low,close,volume,turnover\n"
    def line(t):
        return f"{t.isoformat().replace('+00:00','Z')},{(t+MINUTE).isoformat().replace('+00:00','Z')},BTCUSDT,BTCUSDT,linear,1m,100,101,99,100,0,0\n"
    path.write_bytes(gzip.compress((header + line(first) + line(first + MINUTE)).encode()))
    member = HistoricalMember("BTCUSDT", "BTCUSDT",
                              "runtime/data/direction-regime-history/BTCUSDT_1m.csv.gz",
                              sha256(path.read_bytes()).hexdigest(), 2,
                              first.isoformat().replace("+00:00", "Z"),
                              (first + 2 * MINUTE).isoformat().replace("+00:00", "Z"))
    contract = HistoricalSourceContract("fixture", "a" * 64, "fixture-complete", (member,))
    inputs = AuthenticatedInputs(contract, RELEASE_SHA256, "b" * 64, 60,
                                 source_root, tmp_path / "unused.parquet")
    verified, rows = read_source_range(inputs, physical_symbol="BTCUSDT", start=first,
                                       end=first + 2 * MINUTE, max_scanned_rows=3)
    assert verified.member("BTCUSDT").member_bytes_verified
    assert len(rows) == 2 and all(row.row_membership_verified for row in rows)
    assert rows[0].minute.source_available_at is None
    with pytest.raises(DevelopmentInputError, match="prefix budget"):
        read_source_range(inputs, physical_symbol="BTCUSDT", start=first,
                          end=first + 2 * MINUTE, max_scanned_rows=1)
    path.write_bytes(path.read_bytes() + b"x")
    with pytest.raises(DevelopmentInputError, match="SHA-256 mismatch"):
        read_source_range(inputs, physical_symbol="BTCUSDT", start=first,
                          end=first + 2 * MINUTE, max_scanned_rows=3)


def test_hard_authentication_byte_cap_and_preflight_caps(tmp_path, monkeypatch):
    source_root = tmp_path / "runtime/data/direction-regime-history"
    source_root.mkdir(parents=True)
    path = source_root / "BTCUSDT_1m.csv.gz"
    path.write_bytes(b"123")
    member = HistoricalMember("BTCUSDT", "BTCUSDT",
                              "runtime/data/direction-regime-history/BTCUSDT_1m.csv.gz",
                              sha256(b"123").hexdigest(), 1,
                              "2024-10-01T00:00:00Z", "2024-10-01T00:01:00Z")
    inputs = AuthenticatedInputs(HistoricalSourceContract("fixture", "a" * 64,
                                  "fixture-complete", (member,)), RELEASE_SHA256,
                                  "b" * 64, 60, source_root, tmp_path / "labels.parquet")
    monkeypatch.setattr(dr, "MAX_SOURCE_MEMBER_BYTES", 2)
    with pytest.raises(DevelopmentInputError, match="byte budget"):
        read_source_range(inputs, physical_symbol="BTCUSDT", start=T, end=T + MINUTE,
                          max_scanned_rows=1)
    with pytest.raises(DevelopmentInputError, match="preflight budget"):
        assemble_bounded_real_inputs(repo=ROOT, start=T, end=T + 5 * MINUTE,
                                     horizon_minutes=60, symbols=("BTCUSDT",),
                                     max_origins=dr.MAX_PREFLIGHT_ORIGINS + 1,
                                     max_source_rows=1, max_label_row_groups=1)


def test_bounded_parquet_reader_join_schema_duplicates_and_hash(tmp_path):
    contract = _contract()
    rows = []
    for i, (status, label, reasons) in enumerate((("VALID", "NO_DIRECTION", "[]"),
                                                   ("UNAVAILABLE", None, '["NO_FUTURE"]'))):
        rows.append(dict(symbol="BTCUSDT", physical_symbol="BTCUSDT",
                         origin_utc=(T + timedelta(minutes=5 * i)).strftime("%Y-%m-%dT%H:%M:%SZ"),
                         horizon_minutes=60, label=label, status=status,
                         reason_codes_json=reasons, configuration_sha256=CONFIGURATION_SHA256,
                         architecture_sha256=ARCHITECTURE_SHA256,
                         freeze_amendment_sha256=FREEZE_SHA256, harness_sha256=HARNESS_SHA256,
                         source_identity=contract.corpus_id, canonical_protocol_id="V2_GPT6PRO",
                         canonical_release_id="V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z",
                         calculation_version="v2_gpt6pro_canonical_089d6128f26c311c"))
    path = tmp_path / "labels.parquet"
    pq.write_table(pa.Table.from_pylist(rows), path, row_group_size=1)
    inputs = AuthenticatedInputs(contract, RELEASE_SHA256, sha256(path.read_bytes()).hexdigest(),
                                 60, tmp_path, path)
    selected = read_label_range(inputs, symbols=("BTCUSDT",), start=T,
                                end=T + timedelta(minutes=10), max_row_groups=2)
    assert selected[("BTCUSDT", T, 60)].label == "NO_DIRECTION"
    assert selected[("BTCUSDT", T + timedelta(minutes=5), 60)].reason == "NO_FUTURE"
    with pytest.raises(DevelopmentInputError, match="row-group budget"):
        read_label_range(inputs, symbols=("BTCUSDT",), start=T,
                         end=T + timedelta(minutes=10), max_row_groups=1)
    pq.write_table(pa.Table.from_pylist(rows + [rows[-1]]), path, row_group_size=1)
    duplicate = replace(inputs, label_member_sha256=sha256(path.read_bytes()).hexdigest())
    with pytest.raises(DevelopmentInputError, match="duplicate or unordered"):
        read_label_range(duplicate, symbols=("BTCUSDT",), start=T,
                         end=T + timedelta(minutes=10), max_row_groups=3)
    with pytest.raises(DevelopmentInputError, match="SHA-256 mismatch"):
        read_label_range(inputs, symbols=("BTCUSDT",), start=T,
                         end=T + timedelta(minutes=10), max_row_groups=3)

"""Read-only, bounded historical-development input and identity contracts.

This module does not fit or score an estimator. Compressed member and Parquet
bytes are authenticated before any selected row is released to the assembler.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import asdict, dataclass, field, replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import csv
import gzip
from io import TextIOWrapper
import json
from math import log
import platform
from pathlib import Path
import re
import subprocess

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from . import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from .calendar import D0, H1_START, Horizon, origin, iso
from .experiment_ledger import ExperimentLedger, ExperimentEntry
from .features import RawFeatureRow, aggregates, compute_features
from .historical_source import (HistoricalObservation, HistoricalSourceContract,
                                adapt_historical_row, authenticate_historical_manifest,
                                build_historical_snapshot, with_verified_member_digest)
from .manifests import RowMetadata, RowManifest, build_manifest, canonical_json, digest, feature_row_identity
from .registry_identity import EnvironmentIdentity, SpecificationBytes, frozen_registry
from .snapshot import EVENT_TIME_ONLY
from .source import MINUTE, SYMBOLS

SPEC_SHA256 = "f6a3cac18041c5890e5b7bbdc11b325e31e7dad6369261974c227f496fc65662"
LOCK_SHA256 = "bb3235c514f4065e70bc369c6b72dcbdfe0eb7ccdeb1e933c9c8bca369b67b24"
SOURCE_SHA256 = "f600c0546344259911075f479de583c69d88435321e06c41e0e61acbf49bf45e"
RELEASE_SHA256 = "a19d8a4de209582b07a71f78659b1cb848b4a4d1ebb67bf64ca62c1854d4609f"
GENERATION_SHA256 = "33443e4924a7c65bb9ce904dea7d00ded00f15a1483447087df3da2f57f2cb72"
OUTPUT_BINDING_SHA256 = "68bd344d8fe6a61f69a0c3ffbd90e696c6c36ff8a1664c49f419da3ff3e8e94e"
ARCHITECTURE_SHA256 = "7d5af8dde65fc7a3ead814e3bfa57e8ec19fa9bc3f5d2c923258da9732a0e799"
CONFIGURATION_SHA256 = "fb194d06cf2b79db113f74cec495fe96c61c6fde1cc33981d678332bdd919f99"
FREEZE_SHA256 = "9cc5d4ea6485b59227a94e4fbef54dda3fbc43e725e746b53c9d8b03a5942134"
HARNESS_SHA256 = "a06e678b2f21898ba38868c505c92e9056fc85692966fd62b614dc6e6c348477"
RELEASE_ID = "V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z"
CALCULATION_VERSION = "v2_gpt6pro_canonical_089d6128f26c311c"
SERIALIZER_ID = "LDE_V1_CANONICAL_JSON_V1"
SERIALIZER_VERSION = "1"
LOGICAL = {"BTCUSDT": "BTCUSDT", "AVAXUSDT": "AVAXUSDT", "SUIUSDT": "SUIUSDT",
           "1000PEPEUSDT": "PEPEUSDT"}
_GIT_SHA = re.compile(r"[0-9a-f]{40}\Z")
_VERIFIED_READER_MARKER = object()
MAX_PREFLIGHT_ORIGINS = 12
MAX_PREFLIGHT_SOURCE_ROWS = 20_000
MAX_PREFLIGHT_LABEL_GROUPS = 64
MAX_SOURCE_MEMBER_BYTES = 32 * 1024 * 1024
MAX_LABEL_MEMBER_BYTES = 16 * 1024 * 1024
MAX_TOTAL_AUTH_BYTES = 128 * 1024 * 1024


class DevelopmentInputError(ValueError):
    """A required identity or bounded input contract failed closed."""


def _stream_sha256(stream) -> str:
    h = sha256()
    while chunk := stream.read(1024 * 1024):
        h.update(chunk)
    return h.hexdigest()


def _file_sha256(path: Path) -> str:
    """Stream exact compressed/Parquet bytes; never materialize the corpus."""
    with path.open("rb") as stream:
        return _stream_sha256(stream)


@dataclass(frozen=True)
class SerializerIdentity:
    serializer_id: str
    version: str
    canonical_json_contract: str
    legacy_artifact_json_contract: str
    reconstruction_contract: str
    identity_sha256: str

    @classmethod
    def frozen(cls) -> SerializerIdentity:
        # manifests.canonical_json and digest govern new development artifacts.
        # Older model/calibrator JSON uses the same sorting/separators/NaN rule,
        # but json.dumps's default ensure_ascii=True; durable captures have a
        # separate byte protocol. Neither is silently rewritten here.
        body = dict(serializer_id=SERIALIZER_ID, version=SERIALIZER_VERSION,
                    canonical_json_contract=("json.dumps(sort_keys=True,separators=(',', ':'),"
                                             "ensure_ascii=False,allow_nan=False);UTF-8;"
                                             "Python binary64 shortest-roundtrip float text;"
                                             "tuples normalize to JSON arrays"),
                    legacy_artifact_json_contract=(
                        "ModelArtifact,ScalarCalibrator,BaselineState/B0/B1/B3:"
                        "json.dumps(sort_keys=True,separators=(',', ':'),"
                        "allow_nan=False,ensure_ascii=True default);"
                        "durable capture is a separate exact-byte protocol"),
                    reconstruction_contract=(
                        "RowManifest.from_json restores selected/excluded/count tuples;"
                        "ModelArtifact.from_json restores coefficient arrays;"
                        "ScalarCalibrator.from_json restores scalar state;"
                        "BaselineState/B0/B1/B3.from_json restore count tuples;"
                        "FitBundleManifest,ComparatorArtifact,ShadowArtifact,"
                        "OriginRecord,ProspectiveSeal use their explicit from_json reconstructors"))
        return cls(**body, identity_sha256=digest(body))

    def verify(self) -> None:
        if self != self.frozen():
            raise DevelopmentInputError("serializer identity mismatch")
        sample = {"z": (1.25, -0.0), "a": "é"}
        if canonical_json(sample) != '{"a":"é","z":[1.25,-0.0]}':
            raise DevelopmentInputError("canonical JSON behavior changed")
        try:
            canonical_json(float("nan"))
        except ValueError:
            pass
        else:
            raise DevelopmentInputError("canonical JSON permits NaN")


@dataclass(frozen=True)
class DevelopmentEnvironmentManifest:
    source_revision: str
    spec_sha256: str
    registry_sha256: str
    dependency_lock_path: str
    dependency_lock_sha256: str
    serializer_id: str
    serializer_version: str
    serializer_identity_sha256: str
    python_version: str
    numpy_version: str
    pandas_version: str
    pyarrow_version: str
    platform_identity: str
    model_numerical_runtime: str
    comparator_numerical_runtime: str
    source_manifest_sha256: str
    canonical_release_manifest_sha256: str
    architecture_sha256: str
    configuration_sha256: str
    freeze_sha256: str
    harness_sha256: str
    phase10_environment_sha256: str
    implementation_sha256: str
    readiness_test_sha256: str
    identity_sha256: str

    def body(self) -> dict[str, object]:
        body = asdict(self)
        body.pop("identity_sha256")
        return body

    def verify(self) -> None:
        if self.identity_sha256 != digest(self.body()):
            raise DevelopmentInputError("environment identity hash mismatch")
        expected = (SPEC_SHA256, frozen_registry().descriptor_sha256, LOCK_SHA256,
                    SOURCE_SHA256, RELEASE_SHA256, ARCHITECTURE_SHA256,
                    CONFIGURATION_SHA256, FREEZE_SHA256, HARNESS_SHA256)
        actual = (self.spec_sha256, self.registry_sha256, self.dependency_lock_sha256,
                  self.source_manifest_sha256, self.canonical_release_manifest_sha256,
                  self.architecture_sha256, self.configuration_sha256,
                  self.freeze_sha256, self.harness_sha256)
        if actual != expected or self.serializer_id != SERIALIZER_ID or self.serializer_version != SERIALIZER_VERSION:
            raise DevelopmentInputError("registered environment identity mismatch")
        if (self.serializer_identity_sha256 != SerializerIdentity.frozen().identity_sha256 or
                self.dependency_lock_path != "requirements-lde-v1.lock"):
            raise DevelopmentInputError("serializer or lock reference mismatch")
        if (self.python_version != "3.13.3" or self.numpy_version != "2.2.5" or
                self.pandas_version != "2.2.3" or self.pyarrow_version != "25.0.1"):
            raise DevelopmentInputError("registered runtime version mismatch")
        if not _GIT_SHA.fullmatch(self.source_revision) or not self.platform_identity:
            raise DevelopmentInputError("source revision or platform identity missing")
        if self.implementation_sha256 != _file_sha256(Path(__file__)):
            raise DevelopmentInputError("development implementation source changed")
        test_file = Path(__file__).resolve().parents[3] / "tests/unit/test_live_direction_estimator_v1_development_readiness.py"
        if self.readiness_test_sha256 != _file_sha256(test_file):
            raise DevelopmentInputError("development readiness test source changed")


def build_development_environment(*, repo: Path, spec_path: Path,
                                  source_revision: str | None = None) -> DevelopmentEnvironmentManifest:
    repo = repo.resolve()
    lock = repo / "requirements-lde-v1.lock"
    if _file_sha256(lock) != LOCK_SHA256:
        raise DevelopmentInputError("dependency lock SHA-256 mismatch")
    spec = SpecificationBytes.from_bytes(spec_path.read_bytes(),
                                          file_identity=spec_path.name,
                                          materialization_ref=str(spec_path))
    if spec.sha256 != SPEC_SHA256:
        raise DevelopmentInputError("specification SHA-256 mismatch")
    serializer = SerializerIdentity.frozen()
    serializer.verify()
    revision = source_revision or subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
    phase10 = EnvironmentIdentity.build(
        source_revision=revision, serializer_version=SERIALIZER_VERSION,
        model_numerical_runtime="numpy.float64;Python math;deterministic Newton",
        comparator_numerical_runtime="numpy.float64;registered shallow RF",
        dependency_lock_bytes=lock.read_bytes(), dependency_lock_ref="requirements-lde-v1.lock")
    body = dict(source_revision=revision, spec_sha256=spec.sha256,
                registry_sha256=frozen_registry().descriptor_sha256,
                dependency_lock_path="requirements-lde-v1.lock", dependency_lock_sha256=LOCK_SHA256,
                serializer_id=serializer.serializer_id, serializer_version=serializer.version,
                serializer_identity_sha256=serializer.identity_sha256,
                python_version=platform.python_version(), numpy_version=np.__version__,
                pandas_version=pd.__version__, pyarrow_version=pa.__version__,
                platform_identity=platform.platform(),
                model_numerical_runtime=phase10.model_numerical_runtime,
                comparator_numerical_runtime=phase10.comparator_numerical_runtime,
                source_manifest_sha256=SOURCE_SHA256,
                canonical_release_manifest_sha256=RELEASE_SHA256,
                architecture_sha256=ARCHITECTURE_SHA256,
                configuration_sha256=CONFIGURATION_SHA256,
                freeze_sha256=FREEZE_SHA256, harness_sha256=HARNESS_SHA256,
                phase10_environment_sha256=phase10.identity_sha256,
                implementation_sha256=_file_sha256(Path(__file__)),
                readiness_test_sha256=_file_sha256(
                    repo / "tests/unit/test_live_direction_estimator_v1_development_readiness.py"))
    result = DevelopmentEnvironmentManifest(**body, identity_sha256=digest(body))
    result.verify()
    return result


_LABEL_HASHES = {60: "d8f60429d25cffde767c5ee244f125114ca872666c9f6884c893f1ada285c5ed",
                 120: "f4161b32784539376f3148b867f5658d98c05d9ea891b01e1996d7107c60b06b"}
_LABEL_COLUMNS = ("symbol", "physical_symbol", "origin_utc", "horizon_minutes",
                  "label", "status", "reason_codes_json", "configuration_sha256",
                  "architecture_sha256", "freeze_amendment_sha256", "harness_sha256",
                  "source_identity", "canonical_protocol_id", "canonical_release_id",
                  "calculation_version")


@dataclass(frozen=True)
class AuthenticatedInputs:
    source_contract: HistoricalSourceContract
    release_manifest_sha256: str
    label_member_sha256: str
    horizon_minutes: int
    source_root: Path
    label_file: Path


def authenticate_release_manifest_bytes(raw: bytes, *, expected_sha256: str = RELEASE_SHA256,
                                        source_contract: HistoricalSourceContract) -> dict[str, object]:
    if sha256(raw).hexdigest() != expected_sha256:
        raise DevelopmentInputError("canonical release manifest SHA-256 mismatch")
    try:
        data = json.loads(raw)
        members = {m.physical_symbol: m.declared_sha256 for m in source_contract.members}
        checks = ((data["protocol_id"], "V2_GPT6PRO"),
                  (data["release_id"], RELEASE_ID),
                  (data["architecture_identity"]["sha256"], ARCHITECTURE_SHA256),
                  (data["configuration_identity"]["configuration_sha256"], CONFIGURATION_SHA256),
                  (data["freeze_identity"]["sha256"], FREEZE_SHA256),
                  (data["harness_identity"]["sha256"], HARNESS_SHA256),
                  (data["source_identity"]["source_manifest_sha256"], source_contract.manifest_sha256),
                  (data["source_identity"]["corpus_id"], source_contract.corpus_id),
                  ({item["physical_symbol"]: item["sha256"]
                    for item in data["source_identity"]["physical_source_files"]}, members),
                  (data["source_identity"]["logical_physical_mapping"],
                   {logical: physical for physical, logical in LOGICAL.items()}))
        if any(actual != expected for actual, expected in checks):
            raise DevelopmentInputError("canonical release identity mismatch")
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        if isinstance(exc, DevelopmentInputError):
            raise
        raise DevelopmentInputError("invalid canonical release manifest schema") from exc
    return data


def authenticate_generation_manifest_bytes(raw: bytes, *,
                                           source_contract: HistoricalSourceContract,
                                           expected_sha256: str = GENERATION_SHA256) -> dict[str, object]:
    if sha256(raw).hexdigest() != expected_sha256:
        raise DevelopmentInputError("canonical generation manifest SHA-256 mismatch")
    try:
        data = json.loads(raw)
        checks = ((data["canonical_protocol_id"], "V2_GPT6PRO"),
                  (data["canonical_release_id"], RELEASE_ID),
                  (data["calculation_version"], CALCULATION_VERSION),
                  (data["release_manifest_sha256"], RELEASE_SHA256),
                  (data["architecture_identity"]["sha256"], ARCHITECTURE_SHA256),
                  (data["configuration_identity"]["sha256"], CONFIGURATION_SHA256),
                  (data["freeze_identity"]["sha256"], FREEZE_SHA256),
                  (data["harness_identity"]["sha256"], HARNESS_SHA256),
                  (data["source_identity"]["manifest_sha256"], source_contract.manifest_sha256),
                  (data["source_identity"]["corpus_id"], source_contract.corpus_id),
                  (data["input_file_hashes"],
                   {m.physical_symbol: m.declared_sha256 for m in source_contract.members}),
                  (tuple(data["canonical_horizons_minutes"]), (60, 120)),
                  (data["horizon_relationship"], "INDEPENDENT"))
        if any(actual != expected for actual, expected in checks):
            raise DevelopmentInputError("canonical generation identity mismatch")
        for horizon, expected in _LABEL_HASHES.items():
            if data["output_file_hashes"].get(f"canonical_labels_{horizon}m.parquet") != expected:
                raise DevelopmentInputError("canonical label member identity mismatch")
    except (ValueError, KeyError, TypeError, AttributeError) as exc:
        if isinstance(exc, DevelopmentInputError):
            raise
        raise DevelopmentInputError("invalid canonical generation manifest schema") from exc
    return data


def authenticate_output_lock_binding_bytes(raw: bytes, *,
                                           expected_sha256: str = OUTPUT_BINDING_SHA256) -> dict[str, object]:
    if sha256(raw).hexdigest() != expected_sha256:
        raise DevelopmentInputError("canonical output-lock binding SHA-256 mismatch")
    try:
        binding = json.loads(raw)
        if (binding["binding_status"] != "PASS" or binding["protocol_id"] != "V2_GPT6PRO" or
                binding["formal_release"]["release_manifest_sha256"] != RELEASE_SHA256 or
                binding["canonical_output"]["generation_manifest_sha256"] != GENERATION_SHA256 or
                binding["canonical_output"]["canonical_run_id"] != "20261017T054006Z" or
                binding["configuration_sha256"] != CONFIGURATION_SHA256 or
                binding["harness_sha256"] != HARNESS_SHA256):
            raise DevelopmentInputError("canonical output-lock/release identity mismatch")
    except (ValueError, KeyError, TypeError) as exc:
        if isinstance(exc, DevelopmentInputError):
            raise
        raise DevelopmentInputError("invalid canonical output-lock binding schema") from exc
    return binding


def authenticate_inputs(repo: Path, *, horizon_minutes: int) -> AuthenticatedInputs:
    Horizon(horizon_minutes)
    repo = repo.resolve()
    source_root = repo / "runtime/data/direction-regime-history"
    release_root = repo / "runtime/data/canonical_direction_labels/V2_GPT6PRO/20261017T054006Z"
    source = authenticate_historical_manifest(source_root / "manifest.json",
                                              expected_sha256=SOURCE_SHA256)
    raw_release = (repo / "runtime/audit/V2_GPT6PRO_CANONICAL_RELEASE_20261017T043556Z"
                   / "CANONICAL_RELEASE_MANIFEST.json").read_bytes()
    authenticate_release_manifest_bytes(raw_release, source_contract=source)
    authenticate_output_lock_binding_bytes(
        (repo / "runtime/audit/V2_GPT6PRO_CANONICAL_OUTPUT_LOCK_20261017T070831Z"
         / "CANONICAL_RELEASE_BINDING.json").read_bytes())
    authenticate_generation_manifest_bytes(
        (release_root / "canonical_generation_manifest.json").read_bytes(),
        source_contract=source)
    return AuthenticatedInputs(source, sha256(raw_release).hexdigest(),
                               _LABEL_HASHES[horizon_minutes], horizon_minutes,
                               source_root, release_root / f"canonical_labels_{horizon_minutes}m.parquet")


def _verified_observation(row: dict[str, str], *, number: int,
                          contract: HistoricalSourceContract,
                          physical_symbol: str) -> HistoricalObservation:
    observation = adapt_historical_row(row, contract=contract,
                                       physical_symbol=physical_symbol, row_number=number)
    minute = replace(observation.minute, audit_fields=tuple(
        (key, "True") if key == "row_membership_verified" else (key, value)
        for key, value in observation.minute.audit_fields))
    return replace(observation, minute=minute, row_membership_verified=True)


def read_source_range(inputs: AuthenticatedInputs, *, physical_symbol: str,
                      start: datetime, end: datetime,
                      max_scanned_rows: int) -> tuple[HistoricalSourceContract, tuple[HistoricalObservation, ...]]:
    """Authenticate exact gzip bytes, then decompress only a bounded prefix.

    The byte hash streams the whole compressed member to establish authority;
    the CSV reader stops at end and never scans later market rows. A later
    full-study executor must explicitly raise the prefix budget or supply a
    separately authenticated seek index.
    """
    if physical_symbol not in SYMBOLS or max_scanned_rows <= 0 or start >= end:
        raise DevelopmentInputError("invalid bounded source request")
    member = inputs.source_contract.member(physical_symbol)
    path = inputs.source_root.parent.parent.parent / member.local_path
    if not path.is_file() or path.is_symlink():
        raise DevelopmentInputError("historical source member SHA-256 mismatch")
    if path.stat().st_size > MAX_SOURCE_MEMBER_BYTES:
        raise DevelopmentInputError("historical source authentication byte budget exceeded")
    selected: list[HistoricalObservation] = []
    last: datetime | None = None
    scanned = 0
    try:
        with path.open("rb") as raw:
            actual = _stream_sha256(raw)
            if actual != member.declared_sha256:
                raise DevelopmentInputError("historical source member SHA-256 mismatch")
            contract = with_verified_member_digest(inputs.source_contract, physical_symbol, actual)
            raw.seek(0)
            with gzip.GzipFile(fileobj=raw, mode="rb") as compressed:
                with TextIOWrapper(compressed, encoding="utf-8", newline="") as text:
                    reader = csv.DictReader(text)
                    for number, row in enumerate(reader, 1):
                        scanned = number
                        if scanned > max_scanned_rows:
                            raise DevelopmentInputError("bounded source prefix budget exceeded")
                        stamp = datetime.fromisoformat(row["open_time"].replace("Z", "+00:00"))
                        if stamp >= end:
                            break
                        if stamp < start:
                            continue
                        if last is not None and stamp <= last:
                            raise DevelopmentInputError("duplicate or unordered source key")
                        selected.append(_verified_observation(row, number=number, contract=contract,
                                                              physical_symbol=physical_symbol))
                        last = stamp
    except (OSError, UnicodeError, csv.Error, KeyError, ValueError) as exc:
        if isinstance(exc, DevelopmentInputError):
            raise
        raise DevelopmentInputError("invalid historical source member rows") from exc
    return contract, tuple(selected)


@dataclass(frozen=True)
class CanonicalTarget:
    physical_symbol: str
    prediction_origin: datetime
    horizon_minutes: int
    status: str
    label: str | None
    reason: str | None


def read_label_range(inputs: AuthenticatedInputs, *, symbols: tuple[str, ...],
                     start: datetime, end: datetime,
                     max_row_groups: int) -> dict[tuple[str, datetime, int], CanonicalTarget]:
    """Authenticate exact Parquet bytes, then read only matching row groups."""
    path = inputs.label_file
    if not path.is_file() or path.is_symlink():
        raise DevelopmentInputError("canonical label member SHA-256 mismatch")
    if path.stat().st_size > MAX_LABEL_MEMBER_BYTES:
        raise DevelopmentInputError("canonical label authentication byte budget exceeded")
    result: dict[tuple[str, datetime, int], CanonicalTarget] = {}
    last_key: tuple[str, datetime] | None = None
    groups_read = 0
    with path.open("rb") as raw:
        if _stream_sha256(raw) != inputs.label_member_sha256:
            raise DevelopmentInputError("canonical label member SHA-256 mismatch")
        raw.seek(0)
        parquet = pq.ParquetFile(raw)
        if not set(_LABEL_COLUMNS) <= set(parquet.schema_arrow.names):
            raise DevelopmentInputError("unexpected canonical target schema")
        origin_column = parquet.schema_arrow.names.index("origin_utc")
        symbol_column = parquet.schema_arrow.names.index("physical_symbol")
        lower = start.strftime("%Y-%m-%dT%H:%M:%SZ")
        upper = end.strftime("%Y-%m-%dT%H:%M:%SZ")
        for index in range(parquet.metadata.num_row_groups):
            group = parquet.metadata.row_group(index)
            origin_stats = group.column(origin_column).statistics
            symbol_stats = group.column(symbol_column).statistics
            if origin_stats is None or symbol_stats is None or not origin_stats.has_min_max or not symbol_stats.has_min_max:
                raise DevelopmentInputError("canonical row-group range statistics unavailable")
            if origin_stats.max < lower or origin_stats.min >= upper:
                continue
            if all(not symbol_stats.min <= symbol <= symbol_stats.max for symbol in symbols):
                continue
            groups_read += 1
            if groups_read > max_row_groups:
                raise DevelopmentInputError("bounded canonical row-group budget exceeded")
            rows = parquet.read_row_group(index, columns=list(_LABEL_COLUMNS)).to_pylist()
            for row in rows:
                physical = row["physical_symbol"]
                t = datetime.fromisoformat(row["origin_utc"].replace("Z", "+00:00"))
                key = (physical, t)
                if last_key is not None and key <= last_key:
                    raise DevelopmentInputError("duplicate or unordered canonical key")
                last_key = key
                if physical not in symbols or not start <= t < end:
                    continue
                if (row["symbol"] != LOGICAL.get(physical) or
                        row["horizon_minutes"] != inputs.horizon_minutes or
                        row["canonical_protocol_id"] != "V2_GPT6PRO" or
                        row["canonical_release_id"] != RELEASE_ID or
                        row["calculation_version"] != CALCULATION_VERSION or
                        row["source_identity"] != inputs.source_contract.corpus_id or
                        row["architecture_sha256"] != ARCHITECTURE_SHA256 or
                        row["configuration_sha256"] != CONFIGURATION_SHA256 or
                        row["freeze_amendment_sha256"] != FREEZE_SHA256 or
                        row["harness_sha256"] != HARNESS_SHA256):
                    raise DevelopmentInputError("canonical target row identity mismatch")
                status, label = row["status"], row["label"]
                if ((status == "VALID" and (label not in {"LONG_FAVORED", "SHORT_FAVORED", "NO_DIRECTION"}
                                            or row["reason_codes_json"] != "[]")) or
                        (status == "UNAVAILABLE" and label is not None) or
                        status not in {"VALID", "UNAVAILABLE"}):
                    raise DevelopmentInputError("invalid canonical target status/class")
                reasons = json.loads(row["reason_codes_json"])
                if not isinstance(reasons, list) or not all(isinstance(v, str) for v in reasons):
                    raise DevelopmentInputError("invalid canonical target reasons")
                joined = (physical, t, inputs.horizon_minutes)
                if joined in result:
                    raise DevelopmentInputError("duplicate canonical joined key")
                result[joined] = CanonicalTarget(physical, t, inputs.horizon_minutes,
                                                 status, label, ";".join(reasons) or None)
    return result


def candidate_origins(*, start: datetime, end: datetime,
                      max_origins: int) -> tuple[datetime, ...]:
    first, stop = origin(start), origin(end)
    if first < D0 or stop > H1_START or first >= stop or max_origins <= 0:
        raise DevelopmentInputError("explicit bounded development interval required")
    count = int((stop - first) / timedelta(minutes=5))
    if count > max_origins:
        raise DevelopmentInputError("origin count exceeds explicit bound")
    return tuple(first + timedelta(minutes=5 * n) for n in range(count))


@dataclass(frozen=True)
class FeatureAssembly:
    physical_symbol: str
    prediction_origin: datetime
    row: RawFeatureRow | None
    reasons: tuple[str, ...]
    source_snapshot_id: str | None
    trailing_sign_60: int | None
    trailing_sign_120: int | None


def construct_features_without_targets(*, origins: tuple[datetime, ...],
                                       symbols: tuple[str, ...],
                                       observations: dict[str, tuple[HistoricalObservation, ...]],
                                       contract: HistoricalSourceContract) -> tuple[FeatureAssembly, ...]:
    """Feature API has no label or target argument, including in fixtures."""
    output = []
    for t in origins:
        for symbol in symbols:
            required = observations[symbol]
            if symbol != "BTCUSDT":
                required += observations["BTCUSDT"]
            snapshot = build_historical_snapshot(symbol, t, required, contract=contract)
            if snapshot.snapshot is None:
                output.append(FeatureAssembly(symbol, t, None, snapshot.reasons, None, None, None))
            else:
                result = compute_features(snapshot.snapshot)
                local = snapshot.snapshot.local_minutes
                output.append(FeatureAssembly(symbol, t, result.row, result.reasons,
                                              snapshot.snapshot.source_snapshot_id,
                                              trailing_h_sign(local_minutes=local, horizon_minutes=60)
                                              if result.row else None,
                                              trailing_h_sign(local_minutes=local, horizon_minutes=120)
                                              if result.row else None))
    return tuple(output)


def trailing_h_sign(*, local_minutes: tuple, horizon_minutes: int) -> int:
    """Causal offset-grid close comparison at k=0 and k=H/5, both ending by U."""
    Horizon(horizon_minutes)
    bars = aggregates(local_minutes)
    difference = log(bars[0].close) - log(bars[horizon_minutes // 5].close)
    return (difference > 0) - (difference < 0)


@dataclass(frozen=True)
class AssembledHistoricalRow:
    metadata: RowMetadata
    logical_symbol: str
    provenance_mode: str
    source_manifest_sha256: str
    source_member_sha256: str
    btc_member_sha256: str
    canonical_release_manifest_sha256: str
    canonical_label_member_sha256: str
    source_snapshot_id: str | None
    feature_row_sha256: str | None


def join_canonical_targets(*, feature_rows: tuple[FeatureAssembly, ...],
                           targets: dict[tuple[str, datetime, int], CanonicalTarget],
                           contract: HistoricalSourceContract,
                           release_manifest_sha256: str,
                           label_member_sha256: str,
                           horizon_minutes: int) -> tuple[AssembledHistoricalRow, ...]:
    Horizon(horizon_minutes)
    result = []
    seen = set()
    for feature in feature_rows:
        key = (feature.physical_symbol, feature.prediction_origin, horizon_minutes)
        if key in seen:
            raise DevelopmentInputError("duplicate assembled key")
        seen.add(key)
        target = targets.get(key)
        if target is None:
            status, label, reason = "UNAVAILABLE", None, "MISSING_CANONICAL_TARGET"
        else:
            status, label, reason = target.status, target.label, target.reason
        sign = feature.trailing_sign_60 if horizon_minutes == 60 else feature.trailing_sign_120
        metadata = RowMetadata(feature.physical_symbol, feature.prediction_origin,
                               horizon_minutes, "AVAILABLE" if feature.row else "UNAVAILABLE",
                               status, label, feature.row, trailing_h_sign=sign,
                               feature_reasons=feature.reasons, target_reason=reason)
        result.append(AssembledHistoricalRow(
            metadata, LOGICAL[feature.physical_symbol], EVENT_TIME_ONLY,
            contract.manifest_sha256, contract.member(feature.physical_symbol).declared_sha256,
            contract.member("BTCUSDT").declared_sha256, release_manifest_sha256,
            label_member_sha256, feature.source_snapshot_id,
            feature_row_identity(feature.row) if feature.row else None))
    return tuple(result)


@dataclass(frozen=True)
class VerifiedInputCertificate:
    """Process-local proof issued only after the bounded readers authenticated bytes.

    It is intentionally not serializable as an authority. Persisted hashes are
    audit identities; a fresh process must re-read authenticated inputs.
    """

    assembly_sha256: str
    _marker: object = field(repr=False, compare=False)

    def verifies(self, assembly: BoundedAssembly) -> bool:
        return self._marker is _VERIFIED_READER_MARKER and self.assembly_sha256 == _assembly_digest(assembly)


def _assembly_digest(assembly: BoundedAssembly) -> str:
    return digest({
        "horizon": assembly.horizon_minutes, "symbols": assembly.symbols,
        "start": iso(assembly.start), "end": iso(assembly.end),
        "source_manifest": assembly.source_manifest_sha256,
        "release_manifest": assembly.canonical_release_manifest_sha256,
        "source_members": assembly.source_member_hashes,
        "label_member": assembly.canonical_label_member_sha256,
        "missing_targets": assembly.missing_target_keys,
        "rows": tuple((r.metadata.physical_symbol, iso(r.metadata.prediction_origin),
                       r.metadata.horizon_minutes, r.metadata.feature_status,
                       r.metadata.target_status, r.metadata.canonical_class,
                       r.metadata.feature_reasons, r.metadata.target_reason,
                       r.source_snapshot_id, r.feature_row_sha256,
                       feature_row_identity(r.metadata.feature_row)
                       if r.metadata.feature_row else None,
                       r.metadata.trailing_h_sign) for r in assembly.rows),
    })


@dataclass(frozen=True)
class BoundedAssembly:
    rows: tuple[AssembledHistoricalRow, ...]
    horizon_minutes: int
    symbols: tuple[str, ...]
    start: datetime
    end: datetime
    source_manifest_sha256: str
    canonical_release_manifest_sha256: str
    source_member_hashes: tuple[tuple[str, str], ...]
    canonical_label_member_sha256: str
    missing_target_keys: int
    certificate: VerifiedInputCertificate | None = None

    @property
    def authenticated(self) -> bool:
        return self.certificate is not None and self.certificate.verifies(self)

    def report(self) -> dict[str, object]:
        features = Counter(r.metadata.feature_status for r in self.rows)
        targets = Counter(r.metadata.target_status for r in self.rows)
        return {
            "source_identity_verified": self.authenticated,
            "canonical_release_identity_verified": self.authenticated,
            "horizon_minutes": self.horizon_minutes,
            "physical_symbols": self.symbols,
            "requested_start": iso(self.start), "requested_end": iso(self.end),
            "candidate_origin_count": len({r.metadata.prediction_origin for r in self.rows}),
            "assembled_row_count": len(self.rows),
            "feature_available": features["AVAILABLE"],
            "feature_unavailable": features["UNAVAILABLE"],
            "feature_unavailable_reasons": dict(sorted(Counter(
                reason for r in self.rows for reason in r.metadata.feature_reasons).items())),
            "target_valid": targets["VALID"],
            "target_unavailable": targets["UNAVAILABLE"],
            "target_unavailable_reasons": dict(sorted(Counter(
                r.metadata.target_reason for r in self.rows
                if r.metadata.target_status != "VALID" and r.metadata.target_reason).items())),
            "duplicate_key_count": 0,
            "unmatched_source_target_key_count": self.missing_target_keys,
            "source_manifest_sha256": self.source_manifest_sha256,
            "source_member_hashes": self.source_member_hashes,
            "canonical_release_manifest_sha256": self.canonical_release_manifest_sha256,
            "canonical_label_member_sha256": self.canonical_label_member_sha256,
        }


def assemble_bounded_real_inputs(*, repo: Path, start: datetime, end: datetime,
                                 horizon_minutes: int, symbols: tuple[str, ...],
                                 max_origins: int, max_source_rows: int,
                                 max_label_row_groups: int) -> BoundedAssembly:
    if (not 1 <= max_origins <= MAX_PREFLIGHT_ORIGINS or
            not 1 <= max_source_rows <= MAX_PREFLIGHT_SOURCE_ROWS or
            not 1 <= max_label_row_groups <= MAX_PREFLIGHT_LABEL_GROUPS):
        raise DevelopmentInputError("bounded preflight budget exceeded")
    origins = candidate_origins(start=start, end=end, max_origins=max_origins)
    if not symbols or len(set(symbols)) != len(symbols) or any(s not in SYMBOLS for s in symbols):
        raise DevelopmentInputError("unsupported or duplicate physical symbol")
    inputs = authenticate_inputs(repo, horizon_minutes=horizon_minutes)
    needed = tuple(s for s in SYMBOLS if s in symbols or s == "BTCUSDT")
    source_paths = tuple(repo.resolve() / inputs.source_contract.member(s).local_path for s in needed)
    if (any(p.is_symlink() or not p.is_file() or p.stat().st_size > MAX_SOURCE_MEMBER_BYTES
            for p in source_paths) or inputs.label_file.is_symlink() or
            not inputs.label_file.is_file() or
            inputs.label_file.stat().st_size > MAX_LABEL_MEMBER_BYTES or
            sum(p.stat().st_size for p in source_paths) + inputs.label_file.stat().st_size > MAX_TOTAL_AUTH_BYTES):
        raise DevelopmentInputError("bounded authentication byte budget exceeded")
    source_start = origins[0] - timedelta(minutes=1446)
    source_end = origins[-1] - MINUTE
    observations = {}
    contract = inputs.source_contract
    for symbol in needed:
        current = replace(inputs, source_contract=contract)
        contract, observations[symbol] = read_source_range(
            current, physical_symbol=symbol, start=source_start, end=source_end,
            max_scanned_rows=max_source_rows)
    # The source/feature path runs to completion before opening target Parquet.
    feature_rows = construct_features_without_targets(origins=origins, symbols=symbols,
                                                      observations=observations, contract=contract)
    targets = read_label_range(inputs, symbols=symbols, start=origins[0], end=end,
                               max_row_groups=max_label_row_groups)
    rows = join_canonical_targets(feature_rows=feature_rows, targets=targets,
                                  contract=contract,
                                  release_manifest_sha256=inputs.release_manifest_sha256,
                                  label_member_sha256=inputs.label_member_sha256,
                                  horizon_minutes=horizon_minutes)
    missing = sum((r.metadata.physical_symbol, r.metadata.prediction_origin, horizon_minutes)
                  not in targets for r in rows)
    assembly = BoundedAssembly(rows, horizon_minutes, symbols, start, end,
                               contract.manifest_sha256, inputs.release_manifest_sha256,
                               tuple((s, contract.member(s).declared_sha256) for s in needed),
                               inputs.label_member_sha256, missing)
    return replace(assembly, certificate=VerifiedInputCertificate(
        _assembly_digest(assembly), _VERIFIED_READER_MARKER))


def bounded_manifest_smoke(assembly: BoundedAssembly, *, fit_id: str = "F1",
                           segment_type: str = "BASE") -> RowManifest:
    return build_manifest((r.metadata for r in assembly.rows),
                          horizon_minutes=assembly.horizon_minutes,
                          fit_id=fit_id, segment_type=segment_type)


@dataclass(frozen=True)
class DevelopmentPreRunRegistration:
    spec_id: str
    spec_version: str
    spec_sha256: str
    source_revision: str
    registry_sha256: str
    dependency_lock_sha256: str
    serializer_environment_sha256: str
    historical_source_manifest_sha256: str
    canonical_release_manifest_sha256: str
    architecture_sha256: str
    configuration_sha256: str
    freeze_sha256: str
    harness_sha256: str
    h1_governance_status: str
    h1_not_used_for_fitting: bool
    prospective_not_used_for_fitting: bool
    action: str = "DEVELOPMENT_PREFLIGHT_REGISTERED"
    scope: str = "F1_F5_DEVELOPMENT"

    @classmethod
    def from_environment(cls, environment: DevelopmentEnvironmentManifest) -> DevelopmentPreRunRegistration:
        environment.verify()
        return cls(SPEC_ID, SPEC_VERSION, environment.spec_sha256,
                   environment.source_revision, environment.registry_sha256,
                   environment.dependency_lock_sha256, environment.identity_sha256,
                   SOURCE_SHA256, RELEASE_SHA256, ARCHITECTURE_SHA256,
                   CONFIGURATION_SHA256, FREEZE_SHA256, HARNESS_SHA256,
                   "CLEANLINESS_UNVERIFIED", True, True)

    @property
    def identity_sha256(self) -> str:
        return digest(asdict(self))

    def append_to(self, ledger: ExperimentLedger, *, horizon_minutes: int,
                  actor: str) -> ExperimentEntry:
        Horizon(horizon_minutes)
        if (self.action != "DEVELOPMENT_PREFLIGHT_REGISTERED" or
                self.scope != "F1_F5_DEVELOPMENT" or
                self.h1_governance_status != "CLEANLINESS_UNVERIFIED" or
                not self.h1_not_used_for_fitting or not self.prospective_not_used_for_fitting):
            raise DevelopmentInputError("invalid pre-run registration contract")
        manifests = tuple(sorted((
            ("canonical_release", self.canonical_release_manifest_sha256),
            ("historical_source", self.historical_source_manifest_sha256),
            ("specification", self.spec_sha256),
            ("h1_cleanliness_unverified", digest(self.h1_governance_status)),
            ("h1_not_used_for_fitting", digest(True)),
            ("prospective_not_used_for_fitting", digest(True)),
        )))
        artifacts = tuple(sorted((
            ("pre_run_registration", self.identity_sha256),
            ("registry", self.registry_sha256),
            ("dependency_lock", self.dependency_lock_sha256),
            ("serializer_environment", self.serializer_environment_sha256),
            ("target_architecture", self.architecture_sha256),
            ("target_configuration", self.configuration_sha256),
            ("target_freeze", self.freeze_sha256),
            ("target_harness", self.harness_sha256),
        )))
        return ledger.append(actor=actor, action=self.action,
                             horizon_minutes=horizon_minutes,
                             fit_or_cohort_id=self.scope,
                             partition_accessed="F1_F5_DEVELOPMENT",
                             manifest_hashes=manifests, artifact_hashes=artifacts,
                             code_revision_or_hash=self.source_revision)


@dataclass(frozen=True)
class DevelopmentReadiness:
    status: str
    reasons: tuple[str, ...]
    environment_identity_sha256: str
    e60_manifest_sha256: str | None
    e120_manifest_sha256: str | None
    e60_status: str
    e120_status: str


def validate_development_readiness(*, environment: DevelopmentEnvironmentManifest,
                                   e60: BoundedAssembly | None,
                                   e120: BoundedAssembly | None,
                                   e60_manifest: RowManifest | None,
                                   e120_manifest: RowManifest | None,
                                   tracked_files_clean: bool,
                                   registration: DevelopmentPreRunRegistration | None) -> DevelopmentReadiness:
    reasons = []
    try:
        environment.verify()
    except DevelopmentInputError as exc:
        reasons.append(str(exc))
    if not tracked_files_clean:
        reasons.append("tracked implementation files dirty")
    if (registration is None or registration.serializer_environment_sha256 != environment.identity_sha256 or
            registration.source_revision != environment.source_revision or
            registration.dependency_lock_sha256 != environment.dependency_lock_sha256 or
            registration.historical_source_manifest_sha256 != SOURCE_SHA256 or
            registration.canonical_release_manifest_sha256 != RELEASE_SHA256 or
            not registration.h1_not_used_for_fitting or
            not registration.prospective_not_used_for_fitting):
        reasons.append("pre-run ledger registration contract unavailable")
    elif (registration.action != "DEVELOPMENT_PREFLIGHT_REGISTERED" or
          registration.h1_governance_status != "CLEANLINESS_UNVERIFIED"):
        reasons.append("H1 governance or pre-run action invalid")
    horizon_status = {}
    for horizon, assembly, manifest in ((60, e60, e60_manifest), (120, e120, e120_manifest)):
        if (assembly is None or manifest is None or assembly.horizon_minutes != horizon or
                not assembly.authenticated or
                manifest.horizon_minutes != horizon or
                assembly.source_manifest_sha256 != SOURCE_SHA256 or
                assembly.canonical_release_manifest_sha256 != RELEASE_SHA256 or
                assembly.canonical_label_member_sha256 != _LABEL_HASHES[horizon] or
                len(assembly.rows) != len(assembly.symbols) * len(
                    candidate_origins(start=assembly.start, end=assembly.end,
                                      max_origins=len(assembly.rows))) or
                manifest.manifest_sha256 != bounded_manifest_smoke(assembly).manifest_sha256):
            reasons.append(f"E{horizon} bounded assembly/manifest integration failed")
            horizon_status[horizon] = "BLOCKED"
        else:
            horizon_status[horizon] = "READY"
    if any(not reason.startswith(("E60 ", "E120 ")) for reason in reasons):
        horizon_status = {60: "BLOCKED", 120: "BLOCKED"}
    return DevelopmentReadiness("READY" if not reasons else "BLOCKED", tuple(reasons),
                                environment.identity_sha256,
                                e60_manifest.manifest_sha256 if e60_manifest else None,
                                e120_manifest.manifest_sha256 if e120_manifest else None,
                                horizon_status[60], horizon_status[120])


def validate_current_development_readiness(*, repo: Path, spec_path: Path,
                                           e60: BoundedAssembly, e120: BoundedAssembly,
                                           e60_manifest: RowManifest,
                                           e120_manifest: RowManifest) -> DevelopmentReadiness:
    """Perform filesystem/runtime/git checks rather than trusting caller flags."""
    repo = repo.resolve()
    environment = build_development_environment(repo=repo, spec_path=spec_path)
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD", "--",
         "src/triggertrade/live_direction_estimator_v1",
         "tests/unit/test_live_direction_estimator_v1_phase1.py",
         "tests/unit/test_live_direction_estimator_v1_phase2.py",
         "tests/unit/test_live_direction_estimator_v1_phase3.py",
         "tests/unit/test_live_direction_estimator_v1_phase4.py",
         "tests/unit/test_live_direction_estimator_v1_phase5.py",
         "tests/unit/test_live_direction_estimator_v1_phase6.py",
         "tests/unit/test_live_direction_estimator_v1_phase7.py",
         "tests/unit/test_live_direction_estimator_v1_phase8.py",
         "tests/unit/test_live_direction_estimator_v1_phase9.py",
         "tests/unit/test_live_direction_estimator_v1_phase10.py"],
        cwd=repo, text=True).strip()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard", "--",
         "src/triggertrade/live_direction_estimator_v1",
         "tests/unit/test_live_direction_estimator_v1*"],
        cwd=repo, text=True).splitlines()
    bound_new_files = {
        "src/triggertrade/live_direction_estimator_v1/development_readiness.py",
        "tests/unit/test_live_direction_estimator_v1_development_readiness.py",
    }
    unbound = any(path.replace("\\", "/") not in bound_new_files for path in untracked)
    return validate_development_readiness(
        environment=environment, e60=e60, e120=e120,
        e60_manifest=e60_manifest, e120_manifest=e120_manifest,
        tracked_files_clean=not changed and not unbound,
        registration=DevelopmentPreRunRegistration.from_environment(environment))


def _parse_utc(text: str) -> datetime:
    value = datetime.fromisoformat(text.replace("Z", "+00:00"))
    return origin(value)


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Bounded read-only LDE V1 development input preflight")
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--start", required=True, type=_parse_utc)
    parser.add_argument("--end", required=True, type=_parse_utc)
    parser.add_argument("--horizon", required=True, type=int, choices=(60, 120))
    parser.add_argument("--symbols", nargs="+", required=True)
    parser.add_argument("--max-origins", type=int, required=True)
    parser.add_argument("--max-source-rows", type=int, required=True)
    parser.add_argument("--max-label-row-groups", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        result = assemble_bounded_real_inputs(
            repo=args.repo, start=args.start, end=args.end,
            horizon_minutes=args.horizon, symbols=tuple(args.symbols),
            max_origins=args.max_origins, max_source_rows=args.max_source_rows,
            max_label_row_groups=args.max_label_row_groups)
        report = result.report()
        report["f1_base_manifest_sha256"] = bounded_manifest_smoke(result).manifest_sha256
        print(canonical_json(report))
        return 0
    except (DevelopmentInputError, OSError, ValueError) as exc:
        print(canonical_json({"status": "FAIL_CLOSED", "reason": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

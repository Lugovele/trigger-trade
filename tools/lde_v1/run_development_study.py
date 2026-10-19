"""Manual LDE V1 F1–F5 development runner. Importing this module has no effects.

Only --execute or --resume can fit. --dry-run authenticates a tiny early
development fixture and prints the frozen plan without creating run evidence.
"""

from __future__ import annotations

import argparse
import ast
from concurrent.futures import ProcessPoolExecutor, as_completed
from contextlib import ExitStack, contextmanager
import csv
from dataclasses import asdict, dataclass, is_dataclass
from datetime import UTC, datetime, timedelta
import gzip
from hashlib import sha256
import json
from pathlib import Path
import re
import stat
import sys
import tempfile
from collections import deque
import os
from uuid import uuid4

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from triggertrade.live_direction_estimator_v1 import FEATURE_REGISTRY, SPEC_ID, SPEC_VERSION
from triggertrade.live_direction_estimator_v1.calendar import D0, FOLDS, H1_START, PURGE, iso
from triggertrade.live_direction_estimator_v1.development_readiness import (
    RELEASE_ID, SOURCE_SHA256, RELEASE_SHA256, DevelopmentInputError,
    DevelopmentPreRunRegistration, _file_sha256, _verified_observation,
    assemble_bounded_real_inputs, authenticate_inputs, bounded_manifest_smoke,
    build_development_environment, construct_features_without_targets,
    join_canonical_targets, read_label_range, validate_current_development_readiness,
    FeatureAssembly, CanonicalTarget,
)
from triggertrade.live_direction_estimator_v1.historical_source import with_verified_member_digest
from triggertrade.live_direction_estimator_v1.source import SYMBOLS, MINUTE
from triggertrade.live_direction_estimator_v1.features import RawFeatureRow
from triggertrade.live_direction_estimator_v1.features import NAMES as FEATURE_NAMES
from triggertrade.live_direction_estimator_v1.manifests import (
    RowManifest, build_manifest, canonical_json, digest,
)
from triggertrade.live_direction_estimator_v1.orchestration import (
    FitBundle, FitBundleManifest, IdentityReferences, ScoredRow, fit_pipeline, score_bundle,
)
from triggertrade.live_direction_estimator_v1.comparator import (
    ComparatorArtifact, fit_comparator, score_comparator,
)
from triggertrade.live_direction_estimator_v1.preprocessing import (
    ColumnDomainState, PreprocessingState,
)
from triggertrade.live_direction_estimator_v1.model import ModelArtifact, RawPrediction
from triggertrade.live_direction_estimator_v1.calibration import (
    CalibratedPrediction, ScalarCalibrator,
)
from triggertrade.live_direction_estimator_v1.baselines import BaselineState
from triggertrade.live_direction_estimator_v1.rolling_shadow import fit_shadow, score_shadow
from triggertrade.live_direction_estimator_v1.report_only_status import seal_report_only_status
from triggertrade.live_direction_estimator_v1.evaluation_metrics import (
    ProbabilityState, SealedPrediction, JoinedTruth, EvaluationRecord, hard_class,
)
from triggertrade.live_direction_estimator_v1.evaluation_stage import PhaseGrid, StageEvidence, compute_stage
from triggertrade.live_direction_estimator_v1.evaluation_bootstrap import registered_bootstrap
from triggertrade.live_direction_estimator_v1.evaluation_decision import StageDossier, decide_horizon
from triggertrade.live_direction_estimator_v1.evaluation_coverage import coverage_report
from triggertrade.live_direction_estimator_v1.stability_diagnostics import symbol_time_report
from triggertrade.live_direction_estimator_v1.calendar import H1Governance
from triggertrade.live_direction_estimator_v1.experiment_ledger import ExperimentLedger

SPEC = Path("C:/Users/Елена/Downloads/LIVE_DIRECTION_ESTIMATOR_V1_FINAL.md")
RUN_ROOT = REPO / "runtime/lde_v1/development"
LEDGER_ROOT = RUN_ROOT / "experiment_ledger"
EARLY_ORIGIN = datetime(2024, 10, 3, tzinfo=UTC)
FEATURE_STOP = H1_START  # Exclusive: retain the final purge rows for manifest accounting.
RUN_ID = re.compile(r"[0-9]{8}T[0-9]{6}[0-9]{6}Z_[0-9a-f]{8}\Z")
PRODUCER_RUN_ID = "20261018T112509949034Z_a4936aa1"
PRODUCER_REVISION = "a4936aa118f66659a8c89e86a3f714655bb7c293"
PRODUCER_ENVIRONMENT_SHA256 = "54eaf648c7b55d1f74796549aeda4479bb0017e4a32534b252953b802eef0ca2"
PRODUCER_FEATURE_SHA256 = "489e73111eb9e004d793b6fb883c54691765391be025a5cc9182e1442f588297"
PRODUCER_FEATURE_ROWS = 733_824
PRODUCER_RUN_MANIFEST_SHA256 = "936ac081889f78f264d0dd0afbf86489e2660d7a1cc43576d6e30586368eb9c6"
PRODUCER_FEATURE_SEAL_SHA256 = "601ae083e1fa3fae1af01ee73eebff3ed996b9b98206dafa3e2afff1bed0e4e0"
FEATURE_CODE_FILES = (
    "src/triggertrade/live_direction_estimator_v1/__init__.py",
    "src/triggertrade/live_direction_estimator_v1/calendar.py",
    "src/triggertrade/live_direction_estimator_v1/source.py",
    "src/triggertrade/live_direction_estimator_v1/snapshot.py",
    "src/triggertrade/live_direction_estimator_v1/features.py",
    "src/triggertrade/live_direction_estimator_v1/historical_source.py",
    "src/triggertrade/live_direction_estimator_v1/manifests.py",
    "src/triggertrade/live_direction_estimator_v1/registry_identity.py",
    "src/triggertrade/live_direction_estimator_v1/development_readiness.py",
)
FEATURE_RUNNER_FUNCTIONS = (
    "_wire", "_iter_member", "_feature_rows_from_authenticated_sources",
    "_feature_wire", "_materialize_features",
)
COMPARATOR_WORKERS_DEFAULT = 1
COMPARATOR_WORKERS_MAX = 4
_FOLD_RUNTIME_WEIGHT = {"F1": 56, "F2": 94, "F3": 134, "F4": 173, "F5": 213}


def _log(*items: object) -> None:
    print(iso(datetime.now(UTC)), *items, flush=True)


def _wire(value):
    if is_dataclass(value):
        return _wire(asdict(value))
    if isinstance(value, datetime):
        return iso(value)
    if isinstance(value, dict):
        return {str(k) if isinstance(k, str) else canonical_json(_wire(k)): _wire(v)
                for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [_wire(v) for v in value]
    return value


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _reject_reparse_components(path: Path) -> None:
    """Reject redirected evidence paths, including Windows junctions."""
    for component in (path, *path.parents):
        try:
            info = component.lstat()
        except FileNotFoundError:
            continue
        if (component.is_symlink() or
                getattr(info, "st_file_attributes", 0) &
                getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)):
            raise DevelopmentInputError(f"redirected evidence path: {component}")


def _guard_run_dir(run_dir: Path) -> None:
    if run_dir.parent != RUN_ROOT:
        raise DevelopmentInputError("run directory outside registered root")
    try:
        RUN_ROOT.absolute().relative_to(REPO.absolute())
    except ValueError as exc:
        raise DevelopmentInputError("run root outside repository") from exc
    _reject_reparse_components(run_dir)


def _write_immutable(path: Path, payload: bytes) -> str:
    """Write a new complete file; never replace an existing artifact."""
    _reject_reparse_components(path.parent)
    if path.exists() or path.is_symlink():
        raise DevelopmentInputError(f"artifact already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".incomplete-", delete=False) as stream:
        temporary = Path(stream.name)
        stream.write(payload)
        stream.flush()
        import os
        os.fsync(stream.fileno())
    try:
        # Windows rename refuses an existing destination; POSIX uses hard-link.
        if sys.platform == "win32":
            temporary.rename(path)
        else:
            import os
            os.link(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
    return sha256(payload).hexdigest()


def _sealed_write(path: Path, payload: bytes, *, parents: dict[str, str]) -> str:
    _reject_reparse_components(path.parent)
    artifact_sha = _write_immutable(path, payload)
    seal = {"artifact": path.name, "sha256": artifact_sha, "parents": parents,
            "completed_at": iso(datetime.now(UTC))}
    _write_immutable(path.with_name(path.name + ".seal.json"), canonical_json(seal).encode())
    return artifact_sha


def _sealed_read(path: Path, *, parents: dict[str, str],
                 read_payload: bool = True) -> bytes | None:
    seal_path = path.with_name(path.name + ".seal.json")
    _reject_reparse_components(path)
    _reject_reparse_components(seal_path)
    if not path.exists() and not seal_path.exists():
        return None
    if not path.is_file() or not seal_path.is_file() or path.is_symlink() or seal_path.is_symlink():
        raise DevelopmentInputError(f"partial stage: {path}")
    seal = _read_json(seal_path)
    if (seal.get("artifact") != path.name or seal.get("parents") != parents or
            _file_sha256(path) != seal.get("sha256")):
        raise DevelopmentInputError(f"stage seal mismatch: {path}")
    return path.read_bytes() if read_payload else b""


def _preflight() -> tuple[object, object]:
    env = build_development_environment(repo=REPO, spec_path=SPEC)
    env.verify()
    assemblies = {}
    manifests = {}
    for horizon in (60, 120):
        assembly = assemble_bounded_real_inputs(
            repo=REPO, start=EARLY_ORIGIN, end=EARLY_ORIGIN + timedelta(minutes=5),
            horizon_minutes=horizon, symbols=SYMBOLS, max_origins=1,
            max_source_rows=20_000, max_label_row_groups=8)
        if len(assembly.rows) != 4 or not assembly.authenticated:
            raise DevelopmentInputError(f"E{horizon} bounded preflight failed")
        assemblies[horizon] = assembly
        manifests[horizon] = bounded_manifest_smoke(assembly)
    readiness = validate_current_development_readiness(
        repo=REPO, spec_path=SPEC, e60=assemblies[60], e120=assemblies[120],
        e60_manifest=manifests[60], e120_manifest=manifests[120])
    if (readiness.status, readiness.e60_status, readiness.e120_status) != ("READY", "READY", "READY"):
        raise DevelopmentInputError(f"development readiness blocked: {readiness.reasons}")
    return env, readiness


def _plan(env) -> dict:
    return {"spec_id": SPEC_ID, "spec_version": SPEC_VERSION,
            "feature_registry": FEATURE_REGISTRY, "environment_sha256": env.identity_sha256,
            "spec_sha256": env.spec_sha256, "registry_sha256": env.registry_sha256,
            "source_revision": env.source_revision,
            "horizons": [60, 120], "h1_governance_status": "CLEANLINESS_UNVERIFIED",
            "folds": [{"fit_id": f.fit_id,
                       "base": f.base.inequality,
                       "calibration": f.calibration.inequality,
                       "score": f.score.inequality} for f in FOLDS],
            "stage_graph": ["AUTHENTICATE", "MATERIALIZE_FEATURES",
                            "SEAL_E60_E120_PRIMARY_F1_F5",
                            "PARALLEL_REPORT_ONLY_COMPARATORS",
                            "CANONICAL_FOLD_ASSEMBLY", "E60_EVALUATION_BOOTSTRAP",
                            "E120_EVALUATION_BOOTSTRAP", "DOSSIER"]}


def dry_run(*, reuse_features_from_run: str | None = None) -> dict:
    env, _ = _preflight()
    plan = _plan(env)
    reuse = None
    if reuse_features_from_run is not None:
        inputs = authenticate_inputs(REPO, horizon_minutes=60)
        reuse = _authenticate_feature_reuse(
            producer_run_id=reuse_features_from_run, env=env,
            source_contract=inputs.source_contract)
    proposed = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "_" + env.source_revision[:8]
    return {"mode": "DRY_RUN", "plan": plan,
            "would_create": str(RUN_ROOT / proposed),
            "feature_reuse": reuse,
            "permanent_ledger_entries": 0, "model_fits": 0}


def _committed_runner() -> str:
    """Require Git-clean runner content and identify the committed HEAD blob."""
    import subprocess
    relative = "tools/lde_v1/run_development_study.py"
    registered_path = REPO / relative
    _reject_reparse_components(registered_path)
    runner_path = Path(__file__).resolve()
    if runner_path != registered_path.resolve() or not runner_path.is_relative_to(REPO.resolve()):
        raise DevelopmentInputError("executed runner is outside the registered path")

    def git(*args: str) -> bytes:
        result = subprocess.run(["git", *args], cwd=REPO, capture_output=True, check=False)
        if result.returncode != 0:
            raise DevelopmentInputError(f"runner Git identity check failed: {' '.join(args)}")
        return result.stdout

    # A custom content filter could hide changed executable code. Git's standard
    # text/eol conversion remains allowed, including Windows CRLF checkout.
    attributes = git("check-attr", "-z", "filter", "--", relative).split(b"\0")
    if len(attributes) != 4 or attributes[1:3] != [b"filter", b"unspecified"]:
        raise DevelopmentInputError("runner has an unsupported custom Git filter")
    committed_oid = git("rev-parse", "--verify", f"HEAD:{relative}").strip()
    if git("cat-file", "-t", committed_oid.decode("ascii")).strip() != b"blob":
        raise DevelopmentInputError("committed runner is not a blob")
    working_oid = git("hash-object", f"--path={relative}", "--", str(runner_path)).strip()
    if working_oid != committed_oid:
        raise DevelopmentInputError("runner differs from committed HEAD")
    cleanliness = subprocess.run(
        ["git", "diff", "--no-ext-diff", "--quiet", "HEAD", "--", relative],
        cwd=REPO, capture_output=True, check=False)
    if cleanliness.returncode != 0:
        raise DevelopmentInputError("runner differs from committed HEAD")
    committed = git("cat-file", "blob", committed_oid.decode("ascii"))
    return sha256(committed).hexdigest()


def _git_bytes(revision: str, relative: str) -> bytes:
    import subprocess
    result = subprocess.run(["git", "show", f"{revision}:{relative}"], cwd=REPO,
                            capture_output=True, check=False)
    if result.returncode != 0:
        raise DevelopmentInputError(f"feature contract source unavailable: {revision}:{relative}")
    return result.stdout


def _runner_feature_ast(source: bytes) -> str:
    module = ast.parse(source.decode("utf-8"))
    functions = {node.name: node for node in module.body if isinstance(node, ast.FunctionDef)}
    if set(FEATURE_RUNNER_FUNCTIONS) - functions.keys():
        raise DevelopmentInputError("feature materialization function missing")
    return digest(tuple(ast.dump(functions[name], include_attributes=False)
                        for name in FEATURE_RUNNER_FUNCTIONS))


def _feature_contract_identity(*, producer_revision: str, current_revision: str,
                               source_contract, spec_sha256: str,
                               registry_sha256: str) -> tuple[str, dict[str, object]]:
    producer_files = {path: sha256(_git_bytes(producer_revision, path)).hexdigest()
                      for path in FEATURE_CODE_FILES}
    current_files = {path: sha256(_git_bytes(current_revision, path)).hexdigest()
                     for path in FEATURE_CODE_FILES}
    runner_path = "tools/lde_v1/run_development_study.py"
    producer_runner = _runner_feature_ast(_git_bytes(producer_revision, runner_path))
    current_runner = _runner_feature_ast(_git_bytes(current_revision, runner_path))
    if producer_files != current_files or producer_runner != current_runner:
        raise DevelopmentInputError("feature-generation code contract changed")
    descriptor = {
        "spec_id": SPEC_ID, "spec_version": SPEC_VERSION, "spec_sha256": spec_sha256,
        "feature_registry": FEATURE_REGISTRY, "registry_sha256": registry_sha256,
        "feature_names": FEATURE_NAMES, "feature_artifact_sha256": PRODUCER_FEATURE_SHA256,
        "historical_corpus_id": source_contract.corpus_id,
        "historical_source_manifest_sha256": source_contract.manifest_sha256,
        "source_members": tuple((m.physical_symbol, m.declared_sha256)
                                for m in source_contract.members),
        "feature_origin_range": (iso(D0), iso(FEATURE_STOP)),
        "feature_watermark": "U = T - 1m", "provenance_mode": "EVENT_TIME_ONLY",
        "snapshot_contract": "IMMUTABLE_ORIGIN_T;INFORMATION_CUTOFF_T;NO_ENDPOINT_FALLBACK",
        "support_minutes": 1445, "target_fields": "ABSENT",
        "code_files": tuple(sorted(producer_files.items())),
        "runner_feature_ast_sha256": producer_runner,
    }
    return digest(descriptor), descriptor


def _authenticate_feature_reuse(*, producer_run_id: str, env, source_contract) -> dict[str, object]:
    if producer_run_id != PRODUCER_RUN_ID:
        raise DevelopmentInputError("feature producer run is not registered")
    producer_dir = RUN_ROOT / producer_run_id
    _guard_run_dir(producer_dir)
    manifest_path = producer_dir / "run_manifest.json"
    artifact_name = f"features_{PRODUCER_FEATURE_SHA256}.jsonl.gz"
    artifact_path = producer_dir / artifact_name
    seal_path = producer_dir / f"{artifact_name}.seal.json"
    for path in (manifest_path, artifact_path, seal_path):
        _reject_reparse_components(path)
        if not path.is_file():
            raise DevelopmentInputError(f"producer feature evidence missing: {path.name}")
    manifest = _read_json(manifest_path)
    if not isinstance(manifest, dict) or not isinstance(manifest.get("plan"), dict):
        raise DevelopmentInputError("producer run manifest is malformed")
    plan = manifest.get("plan", {})
    committed_runner_sha = sha256(_git_bytes(
        PRODUCER_REVISION, "tools/lde_v1/run_development_study.py")).hexdigest()
    if (_file_sha256(manifest_path) != PRODUCER_RUN_MANIFEST_SHA256 or
            manifest.get("run_id") != producer_run_id or
            plan.get("source_revision") != PRODUCER_REVISION or
            plan.get("environment_sha256") != PRODUCER_ENVIRONMENT_SHA256 or
            plan.get("spec_id") != SPEC_ID or plan.get("spec_version") != SPEC_VERSION or
            plan.get("feature_registry") != FEATURE_REGISTRY or
            manifest.get("historical_source_manifest_sha256") != SOURCE_SHA256 or
            manifest.get("feature_end_exclusive") != iso(FEATURE_STOP) or
            manifest.get("runner_sha256") != committed_runner_sha):
        raise DevelopmentInputError("producer run manifest identity mismatch")
    seal = _read_json(seal_path)
    if not isinstance(seal, dict) or not isinstance(seal.get("parents"), dict):
        raise DevelopmentInputError("producer feature seal is malformed")
    try:
        completed_at = datetime.fromisoformat(
            str(seal["completed_at"]).replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError) as exc:
        raise DevelopmentInputError("producer feature seal is malformed") from exc
    if completed_at.utcoffset() != timedelta(0):
        raise DevelopmentInputError("producer feature seal is not UTC")
    origin_range = digest((iso(D0), iso(FEATURE_STOP)))
    expected_parents = {
        "environment": PRODUCER_ENVIRONMENT_SHA256,
        "runner": manifest.get("runner_sha256"), "source": SOURCE_SHA256,
        "registry": env.registry_sha256, "spec": env.spec_sha256,
        "origin_range": origin_range,
    }
    if (_file_sha256(seal_path) != PRODUCER_FEATURE_SEAL_SHA256 or
            seal.get("artifact") != artifact_name or seal.get("sha256") != PRODUCER_FEATURE_SHA256 or
            seal.get("parents") != expected_parents or
            _file_sha256(artifact_path) != PRODUCER_FEATURE_SHA256):
        raise DevelopmentInputError("producer feature artifact or seal mismatch")
    contract_sha, contract = _feature_contract_identity(
        producer_revision=PRODUCER_REVISION, current_revision=env.source_revision,
        source_contract=source_contract, spec_sha256=env.spec_sha256,
        registry_sha256=env.registry_sha256)
    return {
        "feature_materialization_mode": "REUSED_AUTHENTICATED",
        "producer_run_id": producer_run_id,
        "producer_source_revision": PRODUCER_REVISION,
        "producer_feature_rows": PRODUCER_FEATURE_ROWS,
        "producer_feature_sha256": PRODUCER_FEATURE_SHA256,
        "producer_run_manifest_sha256": _file_sha256(manifest_path),
        "producer_feature_seal_sha256": _file_sha256(seal_path),
        "current_feature_contract_identity": contract_sha,
        "feature_contract": contract,
        "compatibility_verdict": "PASS",
        "producer_artifact_path": str(artifact_path),
    }


def _registration(env, horizon: int):
    registration = DevelopmentPreRunRegistration.from_environment(env)
    _reject_reparse_components(LEDGER_ROOT)
    ledger = ExperimentLedger(LEDGER_ROOT)
    entries = [e for e in ledger.read_all()
               if e.action == registration.action and e.horizon_minutes == horizon and
               e.fit_or_cohort_id == registration.scope]
    current = [e for e in entries if e.code_revision_or_hash == env.source_revision]
    if any(dict(e.artifact_hashes).get("pre_run_registration") !=
           registration.identity_sha256 for e in current):
        raise DevelopmentInputError("conflicting permanent pre-run registration for current revision")
    if len(current) > 1:
        raise DevelopmentInputError("duplicate permanent pre-run registration for current revision")
    if current:
        return current[0]
    return registration.append_to(ledger, horizon_minutes=horizon, actor="manual-lde-v1-runner")


def _preserve_registration(*, run_dir: Path, env, runner_sha: str,
                           horizon: int, entry) -> str:
    """Bind this run to the exact permanent entry present before fitting."""
    path = run_dir / f"E{horizon}_pre_run_ledger.json"
    reference = {
        "run_id": run_dir.name, "horizon": horizon,
        "entry_sha256": entry.entry_sha256,
        "registration_identity_sha256": DevelopmentPreRunRegistration.from_environment(
            env).identity_sha256,
        "environment_sha256": env.identity_sha256,
        "source_revision": env.source_revision,
    }
    parents = {"run_manifest": _file_sha256(run_dir / "run_manifest.json"),
               "runner": runner_sha, "permanent_ledger_entry": entry.entry_sha256}
    payload = canonical_json(reference).encode("utf-8")
    existing = _sealed_read(path, parents=parents)
    if existing is None:
        _sealed_write(path, payload, parents=parents)
    elif existing != payload:
        raise DevelopmentInputError("pre-run ledger reference mismatch")
    return _file_sha256(path)


def _seal_temp(temporary: Path, final: Path, *, parents: dict[str, str]) -> str:
    _reject_reparse_components(final.parent)
    if final.exists() or final.is_symlink():
        raise DevelopmentInputError(f"artifact already exists: {final}")
    artifact_sha = _file_sha256(temporary)
    if sys.platform == "win32":
        temporary.rename(final)
    else:
        os.link(temporary, final)
        temporary.unlink()
    seal = {"artifact": final.name, "sha256": artifact_sha, "parents": parents,
            "completed_at": iso(datetime.now(UTC))}
    _write_immutable(final.with_name(final.name + ".seal.json"), canonical_json(seal).encode())
    return artifact_sha


def _iter_member(path: Path, *, symbol: str, contract, stack: ExitStack):
    text = stack.enter_context(gzip.open(path, "rt", encoding="utf-8", newline=""))
    reader = csv.DictReader(text)
    previous = None
    for number, row in enumerate(reader, 1):
        observation = _verified_observation(row, number=number, contract=contract,
                                            physical_symbol=symbol)
        stamp = observation.minute.interval_start
        if previous is not None and stamp <= previous:
            raise DevelopmentInputError(f"unordered/duplicate source minute: {symbol}")
        previous = stamp
        yield observation


def _feature_rows_from_authenticated_sources(inputs):
    """Single streaming pass, four rolling 1,445-minute windows, no targets."""
    contract = inputs.source_contract
    paths = {}
    for symbol in SYMBOLS:
        member = contract.member(symbol)
        path = REPO / member.local_path
        if not path.is_file() or path.is_symlink() or _file_sha256(path) != member.declared_sha256:
            raise DevelopmentInputError(f"source member authentication failed: {symbol}")
        paths[symbol] = path
        contract = with_verified_member_digest(contract, symbol, member.declared_sha256)
    # All four exact member byte hashes are verified before the first row is released.
    with ExitStack() as stack:
        iterators = {s: iter(_iter_member(paths[s], symbol=s, contract=contract, stack=stack))
                     for s in SYMBOLS}
        pending = {s: next(iterators[s], None) for s in SYMBOLS}
        windows = {s: deque(maxlen=1445) for s in SYMBOLS}
        t = D0
        while t < FEATURE_STOP:
            u = t - MINUTE
            for symbol in SYMBOLS:
                while pending[symbol] is not None and pending[symbol].minute.interval_start < u:
                    windows[symbol].append(pending[symbol])
                    pending[symbol] = next(iterators[symbol], None)
            yield from construct_features_without_targets(
                origins=(t,), symbols=SYMBOLS,
                observations={s: tuple(windows[s]) for s in SYMBOLS}, contract=contract)
            t += timedelta(minutes=5)


def _feature_wire(row: FeatureAssembly) -> dict:
    return {"symbol": row.physical_symbol, "origin": iso(row.prediction_origin),
            "values": list(row.row.values) if row.row else None,
            "feature_timestamp": iso(row.row.feature_timestamp) if row.row else None,
            "snapshot_id": row.source_snapshot_id, "reasons": row.reasons,
            "sign_60": row.trailing_sign_60, "sign_120": row.trailing_sign_120}


def _materialize_features(run_dir: Path, inputs, parents: dict[str, str]) -> tuple[Path, str]:
    existing = sorted(run_dir.glob("features_*.jsonl.gz"))
    if existing:
        if len(existing) != 1:
            raise DevelopmentInputError("multiple feature materializations")
        path = existing[0]
        payload = _sealed_read(path, parents=parents, read_payload=False)
        content_sha = _file_sha256(path)
        if payload is None or path.stem.split("_")[-1].split(".")[0] != content_sha:
            raise DevelopmentInputError("feature materialization identity mismatch")
        return path, content_sha
    with tempfile.NamedTemporaryFile(dir=run_dir, prefix=".features-incomplete-", delete=False) as raw:
        temporary = Path(raw.name)
        with gzip.GzipFile(fileobj=raw, mode="wb", filename="", mtime=0) as compressed:
            count = 0
            for row in _feature_rows_from_authenticated_sources(inputs):
                compressed.write((canonical_json(_feature_wire(row)) + "\n").encode("utf-8"))
                count += 1
                if count % 100_000 == 0:
                    _log("FEATURES", "rows", count)
        raw.flush(); os.fsync(raw.fileno())
    content_sha = _file_sha256(temporary)
    final = run_dir / f"features_{content_sha}.jsonl.gz"
    _seal_temp(temporary, final, parents=parents)
    _log("FEATURES", "complete", count, content_sha)
    return final, content_sha


def _import_features(run_dir: Path, evidence: dict[str, object],
                     feature_parents: dict[str, str]) -> tuple[Path, str]:
    source = Path(str(evidence["producer_artifact_path"]))
    _reject_reparse_components(source)
    if _file_sha256(source) != PRODUCER_FEATURE_SHA256:
        raise DevelopmentInputError("producer feature bytes changed before import")
    parents = dict(feature_parents)
    parents.update({
        "materialization_mode": "REUSED_AUTHENTICATED",
        "producer_run_manifest": str(evidence["producer_run_manifest_sha256"]),
        "producer_feature_seal": str(evidence["producer_feature_seal_sha256"]),
        "producer_feature_artifact": PRODUCER_FEATURE_SHA256,
        "feature_contract": str(evidence["current_feature_contract_identity"]),
    })
    final = run_dir / f"features_{PRODUCER_FEATURE_SHA256}.jsonl.gz"
    existing = _sealed_read(final, parents=parents, read_payload=False)
    if existing is not None:
        if _file_sha256(final) != PRODUCER_FEATURE_SHA256:
            raise DevelopmentInputError("imported feature artifact identity mismatch")
        return final, PRODUCER_FEATURE_SHA256
    if final.exists() or final.is_symlink():
        raise DevelopmentInputError("imported feature artifact cannot be overwritten")
    with tempfile.NamedTemporaryFile(dir=run_dir, prefix=".features-import-incomplete-",
                                     delete=False) as output:
        temporary = Path(output.name)
        _reject_reparse_components(temporary)
        copied = sha256()
        with source.open("rb") as input_stream:
            while chunk := input_stream.read(1024 * 1024):
                output.write(chunk)
                copied.update(chunk)
        output.flush(); os.fsync(output.fileno())
    if copied.hexdigest() != PRODUCER_FEATURE_SHA256:
        raise DevelopmentInputError("feature import copy hash mismatch")
    _seal_temp(temporary, final, parents=parents)
    if _file_sha256(final) != PRODUCER_FEATURE_SHA256:
        raise DevelopmentInputError("imported feature post-seal hash mismatch")
    _log("FEATURES", "reused authenticated", PRODUCER_FEATURE_ROWS, PRODUCER_FEATURE_SHA256,
         "producer", evidence["producer_run_id"])
    return final, PRODUCER_FEATURE_SHA256


def _read_features(path: Path):
    with gzip.open(path, "rt", encoding="utf-8") as stream:
        for line in stream:
            value = json.loads(line)
            t = datetime.fromisoformat(value["origin"].replace("Z", "+00:00"))
            raw = (RawFeatureRow(value["symbol"], t,
                   datetime.fromisoformat(value["feature_timestamp"].replace("Z", "+00:00")),
                   value["snapshot_id"], tuple(value["values"]))
                   if value["values"] is not None else None)
            yield FeatureAssembly(value["symbol"], t, raw, tuple(value["reasons"]),
                                  value["snapshot_id"], value["sign_60"], value["sign_120"])


def _fold_rows(feature_path: Path, fold, targets: dict, contract, inputs):
    """Join a horizon's authenticated targets only after feature materialization."""
    segments = {"BASE": [], "CALIBRATION": [], "SCORE": []}
    for feature in _read_features(feature_path):
        t = feature.prediction_origin
        if t < fold.calibration.nominal_start:
            segments["BASE"].append(feature)
        elif t < fold.score.nominal_start:
            segments["CALIBRATION"].append(feature)
        elif t < fold.score.nominal_end:
            segments["SCORE"].append(feature)
        else:
            break
    joined = {}
    manifests = {}
    for kind, features in segments.items():
        rows = join_canonical_targets(
            feature_rows=tuple(features), targets=targets, contract=contract,
            release_manifest_sha256=inputs.release_manifest_sha256,
            label_member_sha256=inputs.label_member_sha256,
            horizon_minutes=inputs.horizon_minutes)
        metadata = tuple(r.metadata for r in rows)
        joined[kind] = metadata
        manifests[kind] = build_manifest(metadata, horizon_minutes=inputs.horizon_minutes,
                                         fit_id=fold.fit_id, segment_type=kind)
    return joined, manifests


def _probability_state(probabilities, log_probabilities, logits) -> ProbabilityState:
    return ProbabilityState(tuple(probabilities), tuple(log_probabilities),
                            hard_class(tuple(logits)), tuple(logits))


def _evaluation_record(*, row, score, fit_id: str, horizon: int) -> EvaluationRecord:
    if score is None:
        prediction = SealedPrediction(
            row.prediction_origin, row.physical_symbol, horizon, fit_id, None,
            None, None, None, None, None, None, False, None, "EVENT_TIME_ONLY",
            tuple(row.feature_reasons) or ((row.target_reason or "NOT_SCORED"),),
            feature_status=row.feature_status)
    else:
        prediction = SealedPrediction(
            row.prediction_origin, row.physical_symbol, horizon, fit_id,
            score.bundle_sha256,
            _probability_state(score.calibrated.probabilities,
                               score.calibrated.log_probabilities, score.calibrated.logits),
            _probability_state(score.raw.probabilities,
                               score.raw.log_probabilities, score.raw.logits),
            score.b0_hard_class,
            ProbabilityState.from_probabilities(score.b1_probabilities),
            score.b2_hard_class,
            ProbabilityState.from_probabilities(score.b3_probabilities),
            True, None, "EVENT_TIME_ONLY", feature_status="AVAILABLE")
    truth = JoinedTruth(
        row.prediction_origin, row.physical_symbol, horizon,
        digest((row.physical_symbol, iso(row.prediction_origin), horizon, RELEASE_ID)),
        RELEASE_ID, SOURCE_SHA256, row.target_status, row.canonical_class,
        (row.target_reason,) if row.target_reason else ())
    return EvaluationRecord(prediction, truth)


def _restore_record(value: dict) -> EvaluationRecord:
    p = value["prediction"]
    p["prediction_origin"] = datetime.fromisoformat(p["prediction_origin"].replace("Z", "+00:00"))
    for name in ("calibrated", "raw", "b1", "b3"):
        if p[name] is not None:
            state = p[name]
            p[name] = ProbabilityState(tuple(state["probabilities"]),
                                       tuple(state["log_probabilities"]),
                                       state["hard_class"], tuple(state["ranking_scores"]))
    p["unavailable_reasons"] = tuple(p["unavailable_reasons"])
    prediction = SealedPrediction(**p)
    truth = value["truth"]
    if truth is not None:
        truth["prediction_origin"] = datetime.fromisoformat(
            truth["prediction_origin"].replace("Z", "+00:00"))
        truth["unavailable_reasons"] = tuple(truth["unavailable_reasons"])
        truth = JoinedTruth(**truth)
    return EvaluationRecord(prediction, truth, value["frozen_causal_volatility_stratum"])


def _stage_ledger(*, env, run_id: str, horizon: int, stage: str,
                  artifact_sha: str, parents: dict[str, str]) -> None:
    _reject_reparse_components(LEDGER_ROOT)
    ledger = ExperimentLedger(LEDGER_ROOT)
    action = "DEVELOPMENT_STAGE_COMPLETE"
    fit_scope = f"{run_id}:{stage}"
    matching = [e for e in ledger.read_all() if e.action == action and
                e.horizon_minutes == horizon and e.fit_or_cohort_id == fit_scope]
    artifact_hashes = tuple(sorted((("stage_artifact", artifact_sha),
                                     ("environment", env.identity_sha256))))
    # Seal parents may carry a semantic stage label. Keep that seal identity
    # intact, but commit the label as a digest in the ledger's SHA-only field.
    manifest_hashes = tuple(sorted(
        (name, digest((value, horizon, stage)) if name == "stage" else value)
        for name, value in parents.items()))
    if matching:
        if (len(matching) != 1 or matching[0].artifact_hashes != artifact_hashes or
                matching[0].manifest_hashes != manifest_hashes):
            raise DevelopmentInputError("stage ledger collision")
        return
    ledger.append(actor="manual-lde-v1-runner", action=action,
                  horizon_minutes=horizon, fit_or_cohort_id=fit_scope,
                  partition_accessed="F1_F5_DEVELOPMENT", manifest_hashes=manifest_hashes,
                  artifact_hashes=artifact_hashes,
                  code_revision_or_hash=env.source_revision)


def _fold_stage(*, run_dir: Path, env, runner_sha: str, feature_path: Path,
                feature_sha: str, inputs, targets: dict, fold, horizon: int,
                pre_run_reference_sha: str | None = None) -> PhaseGrid:
    """Sequential bounded compatibility path using the durable staged architecture."""
    _, primary_sha = _prepare_primary_stage(
        run_dir=run_dir, env=env, runner_sha=runner_sha, feature_path=feature_path,
        feature_sha=feature_sha, inputs=inputs, targets=targets, fold=fold, horizon=horizon,
        pre_run_reference_sha=pre_run_reference_sha)
    job = ComparatorJob(
        str(REPO), str(run_dir), runner_sha, str(feature_path), feature_sha,
        horizon, fold.fit_id, pre_run_reference_sha, primary_sha,
        env.identity_sha256, inputs.label_member_sha256, ())
    comparator_dir = _comparator_stage_dir(run_dir, horizon, fold.fit_id)
    if not comparator_dir.exists():
        parents = _job_parents(job)
        primary_output, bundle, primary_scores = _read_primary_stage(
            _primary_path(run_dir, horizon, fold.fit_id), parents=parents,
            horizon=horizon, fit_id=fold.fit_id)
        joined, manifests = _fold_rows(feature_path, fold, targets, inputs.source_contract, inputs)
        for kind in ("BASE", "CALIBRATION", "SCORE"):
            if json.loads(manifests[kind].to_json()) != primary_output["manifests"][kind]:
                raise DevelopmentInputError("comparator rows differ from primary stage")
        work = ComparatorWork(
            horizon, fold.fit_id, bundle, manifests["BASE"], manifests["CALIBRATION"],
            manifests["SCORE"], joined["BASE"], joined["CALIBRATION"], joined["SCORE"],
            primary_scores)
        result = _fit_comparator_work(work, log_progress=True)
        output = {"horizon": horizon, "fit_id": fold.fit_id,
                  "parents": _comparator_parents(job),
                  "primary_bundle_sha256": bundle.manifest.bundle_sha256, **result}
        _publish_comparator_stage(_write_comparator_temp(job, output), job=job)
    phase = _assemble_staged_fold(
        run_dir=run_dir, env=env, runner_sha=runner_sha, feature_path=feature_path,
        feature_sha=feature_sha, inputs=inputs, targets=targets, fold=fold, horizon=horizon,
        primary_sha=primary_sha, comparator_job=job,
        pre_run_reference_sha=pre_run_reference_sha)
    _, comparator_sha = _read_comparator_stage(comparator_dir, job=job)
    final_parents = {**_job_parents(job), "primary_stage": primary_sha,
                     "comparator_stage": comparator_sha}
    final = run_dir / f"E{horizon}_{fold.fit_id}.json.gz"
    _stage_ledger(env=env, run_id=run_dir.name, horizon=horizon, stage=fold.fit_id,
                  artifact_sha=_file_sha256(final), parents=final_parents)
    return phase


def _fold_parents(*, env, runner_sha: str, feature_sha: str, inputs, fold,
                  horizon: int, pre_run_reference_sha: str | None) -> dict[str, str]:
    parents = {"environment": env.identity_sha256, "runner": runner_sha,
               "features": feature_sha, "canonical_label": inputs.label_member_sha256,
               "source": SOURCE_SHA256, "release": RELEASE_SHA256,
               "fit": digest((fold.fit_id, horizon))}
    if pre_run_reference_sha is not None:
        parents["pre_run_registration"] = pre_run_reference_sha
    return parents


def _restore_preprocessing(value: dict) -> PreprocessingState:
    data = dict(value)
    data["physical_mapping"] = tuple(tuple(v) for v in data["physical_mapping"])
    data["btc_context_mask_indices"] = tuple(data["btc_context_mask_indices"])
    data["domains"] = tuple(ColumnDomainState(**v) for v in data["domains"])
    data["zero_slope_state_indices"] = tuple(data["zero_slope_state_indices"])
    return PreprocessingState(**data)


def _restore_bundle(output: dict) -> FitBundle:
    bundle = FitBundle(
        FitBundleManifest.from_json(canonical_json(output["bundle_manifest"])),
        _restore_preprocessing(output["preprocessing"]),
        ModelArtifact.from_json(canonical_json(output["model"])),
        ScalarCalibrator.from_json(canonical_json(output["calibrator"])),
        BaselineState.from_json(canonical_json(output["baselines"])),
    )
    bundle.verify_hashes()
    return bundle


def _restore_scored(value: dict) -> ScoredRow:
    raw = dict(value["raw"])
    calibrated = dict(value["calibrated"])
    for state in (raw, calibrated):
        for key in ("logits", "log_probabilities", "probabilities"):
            state[key] = tuple(state[key])
    data = dict(value)
    data["raw"] = RawPrediction(**raw)
    data["calibrated"] = CalibratedPrediction(**calibrated)
    data["b1_probabilities"] = tuple(data["b1_probabilities"])
    data["b3_probabilities"] = tuple(data["b3_probabilities"])
    return ScoredRow(**data)


def _primary_path(run_dir: Path, horizon: int, fit_id: str) -> Path:
    return run_dir / f"E{horizon}_{fit_id}.primary.json.gz"


def _primary_parents(parents: dict[str, str]) -> dict[str, str]:
    return {**parents, "stage": "PRIMARY_FOLD"}


def _read_primary_stage(path: Path, *, parents: dict[str, str], horizon: int,
                        fit_id: str) -> tuple[dict, FitBundle, tuple[ScoredRow, ...]]:
    payload = _sealed_read(path, parents=_primary_parents(parents))
    if payload is None:
        raise DevelopmentInputError(f"missing primary stage: E{horizon} {fit_id}")
    output = json.loads(gzip.decompress(payload))
    if (output.get("horizon") != horizon or output.get("fit_id") != fit_id or
            output.get("parents") != parents):
        raise DevelopmentInputError("primary stage identity mismatch")
    bundle = _restore_bundle(output)
    scores = tuple(_restore_scored(v) for v in output["primary_scores"])
    return output, bundle, scores


def _prepare_primary_stage(*, run_dir: Path, env, runner_sha: str, feature_path: Path,
                           feature_sha: str, inputs, targets: dict, fold, horizon: int,
                           pre_run_reference_sha: str | None = None) -> tuple[Path, str]:
    parents = _fold_parents(env=env, runner_sha=runner_sha, feature_sha=feature_sha,
                            inputs=inputs, fold=fold, horizon=horizon,
                            pre_run_reference_sha=pre_run_reference_sha)
    path = _primary_path(run_dir, horizon, fold.fit_id)
    if _sealed_read(path, parents=_primary_parents(parents), read_payload=False) is not None:
        _read_primary_stage(path, parents=parents, horizon=horizon, fit_id=fold.fit_id)
        artifact_sha = _file_sha256(path)
        _log(f"E{horizon}", fold.fit_id, "primary reused", artifact_sha)
        return path, artifact_sha
    _log(f"E{horizon}", fold.fit_id, "primary manifest rows start")
    joined, manifests = _fold_rows(feature_path, fold, targets, inputs.source_contract, inputs)
    identities = IdentityReferences(SOURCE_SHA256, RELEASE_ID, inputs.label_member_sha256)
    bundle = fit_pipeline(base_manifest=manifests["BASE"],
                          calibration_manifest=manifests["CALIBRATION"],
                          base_rows=joined["BASE"], calibration_rows=joined["CALIBRATION"],
                          identities=identities)
    primary = score_bundle(bundle, scored_manifest=manifests["SCORE"],
                           scored_rows=joined["SCORE"])
    output = {"fit_id": fold.fit_id, "horizon": horizon, "parents": parents,
              "manifests": {key: json.loads(m.to_json()) for key, m in manifests.items()},
              "bundle_manifest": json.loads(bundle.manifest.to_json()),
              "preprocessing": bundle.preprocessing.to_dict(),
              "model": json.loads(bundle.model.to_json()),
              "calibrator": json.loads(bundle.calibrator.to_json()),
              "baselines": _wire(bundle.baselines), "primary_scores": _wire(primary)}
    payload = gzip.compress(canonical_json(output).encode("utf-8"), mtime=0)
    artifact_sha = _sealed_write(path, payload, parents=_primary_parents(parents))
    _read_primary_stage(path, parents=parents, horizon=horizon, fit_id=fold.fit_id)
    _log(f"E{horizon}", fold.fit_id, "primary durable complete", artifact_sha)
    return path, artifact_sha


@dataclass(frozen=True)
class ComparatorWork:
    horizon: int
    fit_id: str
    primary: FitBundle
    base_manifest: RowManifest
    calibration_manifest: RowManifest
    score_manifest: RowManifest
    base_rows: tuple
    calibration_rows: tuple
    score_rows: tuple
    primary_scores: tuple[ScoredRow, ...]


def _fit_comparator_work(work: ComparatorWork, *, log_progress: bool = False) -> dict:
    """Invoke the frozen comparator with a new per-fit RNG owned by this call."""
    try:
        comparator = fit_comparator(
            primary=work.primary, base_manifest=work.base_manifest,
            calibration_manifest=work.calibration_manifest, base_rows=work.base_rows,
            calibration_rows=work.calibration_rows,
            progress=(lambda done, total: _log(
                f"E{work.horizon}", work.fit_id, f"comparator worker {os.getpid()}",
                "trees", f"{done}/{total}")) if log_progress else None)
    except (ValueError, ArithmeticError, RuntimeError) as exc:
        return {"comparator": None, "comparator_scores": [],
                "fit_error": f"{type(exc).__name__}: {exc}"[:500],
                "completed_at": iso(datetime.now(UTC))}
    scores = score_comparator(
        comparator, primary=work.primary, scored_manifest=work.score_manifest,
        scored_rows=work.score_rows, primary_scored_rows=work.primary_scores)
    return {"comparator": json.loads(comparator.to_json()),
            "comparator_scores": _wire(scores), "fit_error": None,
            "completed_at": iso(datetime.now(UTC))}


@dataclass(frozen=True)
class ComparatorJob:
    repo: str
    run_dir: str
    runner_sha: str
    feature_path: str
    feature_sha: str
    horizon: int
    fit_id: str
    pre_run_reference_sha: str | None
    primary_sha: str
    environment_sha: str
    canonical_label_sha: str
    feature_parents: tuple[tuple[str, str], ...]

    @property
    def key(self) -> tuple[int, str]:
        return self.horizon, self.fit_id


def _job_fold(job: ComparatorJob):
    try:
        return next(fold for fold in FOLDS if fold.fit_id == job.fit_id)
    except StopIteration as exc:
        raise DevelopmentInputError("unknown comparator fold") from exc


def _job_parents(job: ComparatorJob) -> dict[str, str]:
    parents = {"environment": job.environment_sha, "runner": job.runner_sha,
               "features": job.feature_sha, "canonical_label": job.canonical_label_sha,
               "source": SOURCE_SHA256, "release": RELEASE_SHA256,
               "fit": digest((job.fit_id, job.horizon))}
    if job.pre_run_reference_sha is not None:
        parents["pre_run_registration"] = job.pre_run_reference_sha
    return parents


def _comparator_parents(job: ComparatorJob) -> dict[str, str]:
    return {**_job_parents(job), "stage": "REPORT_ONLY_COMPARATOR",
            "primary_stage": job.primary_sha}


def _comparator_stage_dir(run_dir: Path, horizon: int, fit_id: str) -> Path:
    return run_dir / f"E{horizon}_{fit_id}.comparator.stage"


def _read_comparator_stage(directory: Path, *, job: ComparatorJob,
                           allow_temporary: bool = False) -> tuple[dict, str]:
    _reject_reparse_components(directory)
    expected = _comparator_stage_dir(Path(job.run_dir), job.horizon, job.fit_id)
    if not allow_temporary and directory != expected:
        raise DevelopmentInputError("comparator stage path mismatch")
    if not directory.is_dir() or directory.is_symlink():
        raise DevelopmentInputError("missing or invalid comparator stage directory")
    artifact, seal_path = directory / "artifact.json.gz", directory / "seal.json"
    _reject_reparse_components(artifact)
    _reject_reparse_components(seal_path)
    if not artifact.is_file() or not seal_path.is_file():
        raise DevelopmentInputError("partial comparator stage")
    seal = _read_json(seal_path)
    artifact_sha = _file_sha256(artifact)
    if (seal.get("job_key") != [job.horizon, job.fit_id] or
            seal.get("artifact") != artifact.name or
            seal.get("parents") != _comparator_parents(job) or
            seal.get("sha256") != artifact_sha):
        raise DevelopmentInputError("comparator stage seal mismatch")
    output = json.loads(gzip.decompress(artifact.read_bytes()))
    if (output.get("horizon") != job.horizon or output.get("fit_id") != job.fit_id or
            output.get("parents") != _comparator_parents(job)):
        raise DevelopmentInputError("comparator stage identity mismatch")
    if output["comparator"] is not None:
        comparator = ComparatorArtifact.from_json(canonical_json(output["comparator"]))
        if comparator.primary_bundle_sha256 != output["primary_bundle_sha256"]:
            raise DevelopmentInputError("comparator primary identity mismatch")
    elif not output.get("fit_error"):
        raise DevelopmentInputError("comparator stage lacks result")
    return output, artifact_sha


def _write_comparator_temp(job: ComparatorJob, output: dict) -> Path:
    run_dir = Path(job.run_dir)
    temporary = run_dir / (f".E{job.horizon}_{job.fit_id}.comparator-incomplete-" + uuid4().hex)
    temporary.mkdir(exist_ok=False)
    _reject_reparse_components(temporary)
    payload = gzip.compress(canonical_json(output).encode("utf-8"), mtime=0)
    artifact = temporary / "artifact.json.gz"
    artifact_sha = _write_immutable(artifact, payload)
    seal = {"job_key": [job.horizon, job.fit_id], "artifact": artifact.name,
            "sha256": artifact_sha, "parents": _comparator_parents(job),
            "completed_at": output["completed_at"]}
    _write_immutable(temporary / "seal.json", canonical_json(seal).encode())
    _read_comparator_stage(temporary, job=job, allow_temporary=True)
    return temporary


def _verify_worker_identity(job: ComparatorJob) -> None:
    if _committed_runner() != job.runner_sha:
        raise DevelopmentInputError("comparator worker runner identity mismatch")
    environment = build_development_environment(repo=Path(job.repo), spec_path=SPEC)
    environment.verify()
    if environment.identity_sha256 != job.environment_sha:
        raise DevelopmentInputError("comparator worker environment identity mismatch")


def _comparator_worker(job: ComparatorJob) -> str:
    """Process worker: reauthenticate immutable inputs and write only isolated output."""
    repo = Path(job.repo)
    run_dir = Path(job.run_dir)
    feature_path = Path(job.feature_path)
    if repo.absolute() != REPO.absolute() or run_dir.parent != RUN_ROOT or feature_path.parent != run_dir:
        raise DevelopmentInputError("comparator worker path identity mismatch")
    _guard_run_dir(run_dir)
    _verify_worker_identity(job)
    _reject_reparse_components(feature_path)
    fold = _job_fold(job)
    inputs = authenticate_inputs(repo, horizon_minutes=job.horizon)
    if inputs.label_member_sha256 != job.canonical_label_sha:
        raise DevelopmentInputError("comparator canonical label identity mismatch")
    if (_sealed_read(feature_path, parents=dict(job.feature_parents), read_payload=False) is None or
            _file_sha256(feature_path) != job.feature_sha):
        raise DevelopmentInputError("comparator feature identity mismatch")
    primary_path = _primary_path(run_dir, job.horizon, job.fit_id)
    primary_output, bundle, primary_scores = _read_primary_stage(
        primary_path, parents=_job_parents(job), horizon=job.horizon, fit_id=job.fit_id)
    if _file_sha256(primary_path) != job.primary_sha:
        raise DevelopmentInputError("comparator primary stage hash mismatch")
    targets = read_label_range(inputs, symbols=SYMBOLS, start=D0,
                               end=H1_START, max_row_groups=2_000)
    joined, manifests = _fold_rows(feature_path, fold, targets, inputs.source_contract, inputs)
    for kind in ("BASE", "CALIBRATION", "SCORE"):
        if json.loads(manifests[kind].to_json()) != primary_output["manifests"][kind]:
            raise DevelopmentInputError("comparator rows differ from primary stage")
    work = ComparatorWork(job.horizon, job.fit_id, bundle, manifests["BASE"],
                          manifests["CALIBRATION"], manifests["SCORE"], joined["BASE"],
                          joined["CALIBRATION"], joined["SCORE"], primary_scores)
    result = _fit_comparator_work(work, log_progress=True)
    output = {"horizon": job.horizon, "fit_id": job.fit_id,
              "parents": _comparator_parents(job),
              "primary_bundle_sha256": bundle.manifest.bundle_sha256, **result}
    return str(_write_comparator_temp(job, output))


@contextmanager
def _comparator_publish_lock(job: ComparatorJob):
    """Cross-process exclusive lock; the OS releases it if a coordinator dies."""
    lock_path = Path(job.run_dir) / f".E{job.horizon}_{job.fit_id}.comparator-publish.lock"
    _reject_reparse_components(lock_path)
    flags = os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        raise DevelopmentInputError("invalid comparator publish lock") from exc
    try:
        _reject_reparse_components(lock_path)
        opened, named = os.fstat(descriptor), lock_path.stat()
        if (not stat.S_ISREG(opened.st_mode) or
                (opened.st_dev, opened.st_ino) != (named.st_dev, named.st_ino)):
            raise DevelopmentInputError("invalid comparator publish lock")
    except Exception:
        os.close(descriptor)
        raise
    with os.fdopen(descriptor, "r+b") as stream:
        if stream.seek(0, os.SEEK_END) == 0:
            stream.write(b"\0"); stream.flush(); os.fsync(stream.fileno())
        stream.seek(0)
        try:
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise DevelopmentInputError("comparator stage publish collision") from exc
        try:
            yield
        finally:
            stream.seek(0)
            if sys.platform == "win32":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _publish_comparator_stage(temporary: Path, *, job: ComparatorJob) -> tuple[dict, str]:
    run_dir = Path(job.run_dir)
    prefix = f".E{job.horizon}_{job.fit_id}.comparator-incomplete-"
    if (temporary.parent != run_dir or not temporary.name.startswith(prefix) or
            not re.fullmatch(re.escape(prefix) + r"[0-9a-f]{32}", temporary.name)):
        raise DevelopmentInputError("invalid comparator worker temporary path")
    output, artifact_sha = _read_comparator_stage(temporary, job=job, allow_temporary=True)
    final = _comparator_stage_dir(run_dir, job.horizon, job.fit_id)
    with _comparator_publish_lock(job):
        if final.exists() or final.is_symlink():
            raise DevelopmentInputError(f"comparator stage already exists: {final}")
        temporary.rename(final)
    verified, verified_sha = _read_comparator_stage(final, job=job)
    if verified != output or verified_sha != artifact_sha:
        raise DevelopmentInputError("published comparator stage differs from worker output")
    return verified, verified_sha


def _validate_worker_count(workers: int) -> int:
    if isinstance(workers, bool) or not isinstance(workers, int) or not 1 <= workers <= 4:
        raise DevelopmentInputError("comparator workers must be an integer in [1,4]")
    return workers


def _schedule_comparator_jobs(jobs: tuple[ComparatorJob, ...], *, workers: int) -> tuple[dict, dict]:
    """Execute longest first; retain infrastructure failures by independent job key."""
    _validate_worker_count(workers)
    if len({job.key for job in jobs}) != len(jobs):
        raise DevelopmentInputError("duplicate comparator job key")
    results, failures, missing = {}, {}, []
    for job in jobs:
        final = _comparator_stage_dir(Path(job.run_dir), job.horizon, job.fit_id)
        if final.exists() or final.is_symlink():
            try:
                results[job.key] = _read_comparator_stage(final, job=job)
            except Exception as exc:
                failures[job.key] = exc
            else:
                _log(f"E{job.horizon}", job.fit_id, "comparator reused")
        else:
            missing.append(job)
    ordered = sorted(missing, key=lambda j: (-_FOLD_RUNTIME_WEIGHT[j.fit_id], j.horizon))
    if workers == 1:
        for job in ordered:
            try:
                results[job.key] = _publish_comparator_stage(
                    Path(_comparator_worker(job)), job=job)
            except Exception as exc:
                failures[job.key] = exc
    elif ordered:
        with ProcessPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(_comparator_worker, job): job for job in ordered}
            for future in as_completed(futures):
                job = futures[future]
                try:
                    results[job.key] = _publish_comparator_stage(Path(future.result()), job=job)
                except Exception as exc:
                    failures[job.key] = exc
    return ({job.key: results[job.key] for job in jobs if job.key in results},
            {job.key: failures[job.key] for job in jobs if job.key in failures})


def _assemble_staged_fold(*, run_dir: Path, env, runner_sha: str, feature_path: Path,
                          feature_sha: str, inputs, targets: dict, fold, horizon: int,
                          primary_sha: str, comparator_job: ComparatorJob,
                          pre_run_reference_sha: str | None = None) -> PhaseGrid:
    """Combine sealed primary/comparator evidence and sequential shadow into the legacy fold."""
    path = run_dir / f"E{horizon}_{fold.fit_id}.json.gz"
    base_parents = _fold_parents(env=env, runner_sha=runner_sha, feature_sha=feature_sha,
                                 inputs=inputs, fold=fold, horizon=horizon,
                                 pre_run_reference_sha=pre_run_reference_sha)
    primary_path = _primary_path(run_dir, horizon, fold.fit_id)
    primary_output, bundle, primary = _read_primary_stage(
        primary_path, parents=base_parents, horizon=horizon, fit_id=fold.fit_id)
    if _file_sha256(primary_path) != primary_sha:
        raise DevelopmentInputError("primary stage changed before final assembly")
    comparator_output, comparator_sha = _read_comparator_stage(
        _comparator_stage_dir(run_dir, horizon, fold.fit_id), job=comparator_job)
    parents = {**base_parents, "primary_stage": primary_sha,
               "comparator_stage": comparator_sha}
    existing = _sealed_read(path, parents=parents)
    if existing is not None:
        output = json.loads(gzip.decompress(existing))
        if (output["horizon"] != horizon or output["fit_id"] != fold.fit_id or
                output["parents"] != parents):
            raise DevelopmentInputError("resume fold identity mismatch")
        positions = tuple(fold.score.nominal_start + PURGE + i * timedelta(minutes=5)
                          for i in range(int((fold.score.nominal_end - PURGE -
                                              (fold.score.nominal_start + PURGE)) /
                                             timedelta(minutes=5))))
        return PhaseGrid(fold.fit_id, positions,
                         tuple(_restore_record(v) for v in output["records"]))
    joined, manifests = _fold_rows(feature_path, fold, targets, inputs.source_contract, inputs)
    for kind in ("BASE", "CALIBRATION", "SCORE"):
        if json.loads(manifests[kind].to_json()) != primary_output["manifests"][kind]:
            raise DevelopmentInputError("final assembly rows differ from primary stage")
    if comparator_output["comparator"] is None:
        comparator_status = seal_report_only_status(
            role="C1_SHALLOW_RF", horizon_minutes=horizon, fit_id=fold.fit_id,
            status="FIT_FAILED", reason=comparator_output["fit_error"],
            primary_bundle_sha256=bundle.manifest.bundle_sha256)
    else:
        comparator = ComparatorArtifact.from_json(canonical_json(comparator_output["comparator"]))
        comparator_status = seal_report_only_status(
            role="C1_SHALLOW_RF", horizon_minutes=horizon, fit_id=fold.fit_id,
            status="FITTED", reason="", primary_bundle_sha256=bundle.manifest.bundle_sha256,
            artifact_sha256=comparator.artifact_sha256,
            artifact_available_at=datetime.fromisoformat(
                comparator_output["completed_at"].replace("Z", "+00:00")),
            evidence_ref=f"{run_dir.name}/E{horizon}_{fold.fit_id}.json.gz:comparator")
    _log(f"E{horizon}", fold.fit_id, "shadow fit start")
    try:
        shadow = fit_shadow(primary=bundle, primary_base_manifest=manifests["BASE"],
                            calibration_manifest=manifests["CALIBRATION"],
                            base_rows=joined["BASE"], calibration_rows=joined["CALIBRATION"])
    except (ValueError, ArithmeticError, RuntimeError) as exc:
        shadow = None
        shadow_scores = ()
        shadow_status = seal_report_only_status(
            role="SIX_MONTH_ROLLING_SHADOW", horizon_minutes=horizon, fit_id=fold.fit_id,
            status="FIT_FAILED", reason=f"{type(exc).__name__}: {exc}"[:500],
            primary_bundle_sha256=bundle.manifest.bundle_sha256)
    else:
        shadow_scores = score_shadow(shadow, primary=bundle,
            scored_manifest=manifests["SCORE"], scored_rows=joined["SCORE"],
            primary_scored_rows=primary)
        shadow_status = seal_report_only_status(
            role="SIX_MONTH_ROLLING_SHADOW", horizon_minutes=horizon, fit_id=fold.fit_id,
            status="FITTED", reason="", primary_bundle_sha256=bundle.manifest.bundle_sha256,
            artifact_sha256=shadow.artifact_sha256, artifact_available_at=datetime.now(UTC),
            evidence_ref=f"{run_dir.name}/E{horizon}_{fold.fit_id}.json.gz:shadow")
    score_by_key = {(s.physical_symbol, s.prediction_origin): s for s in primary}
    rows_by_key = {(r.physical_symbol, iso(r.prediction_origin)): r for r in joined["SCORE"]}
    positions = tuple(fold.score.nominal_start + PURGE + i * timedelta(minutes=5)
                      for i in range(int((fold.score.nominal_end - PURGE -
                                          (fold.score.nominal_start + PURGE)) /
                                         timedelta(minutes=5))))
    records = []
    for t in positions:
        for symbol in SYMBOLS:
            row = rows_by_key.get((symbol, iso(t)))
            if row is None:
                raise DevelopmentInputError("scored grid row missing")
            records.append(_evaluation_record(row=row, score=score_by_key.get((symbol, iso(t))),
                                              fit_id=fold.fit_id, horizon=horizon))
    output = {**primary_output, "parents": parents,
              "comparator": comparator_output["comparator"],
              "shadow": json.loads(shadow.to_json()) if shadow else None,
              "comparator_status": json.loads(comparator_status.to_json()),
              "shadow_status": json.loads(shadow_status.to_json()),
              "comparator_scores": comparator_output["comparator_scores"],
              "shadow_scores": _wire(shadow_scores), "records": _wire(records)}
    payload = gzip.compress(canonical_json(output).encode("utf-8"), mtime=0)
    artifact_sha = _sealed_write(path, payload, parents=parents)
    _log(f"E{horizon}", fold.fit_id, "durable complete", artifact_sha)
    return PhaseGrid(fold.fit_id, positions, tuple(records))


def _finish_horizon(*, run_dir: Path, env, runner_sha: str, horizon: int,
                    phases: tuple[PhaseGrid, ...], feature_sha: str,
                    label_sha: str, pre_run_reference_sha: str | None = None) -> str:
    path = run_dir / f"E{horizon}_development_dossier.json.gz"
    fold_hashes = tuple((fold.fit_id, _file_sha256(run_dir / f"E{horizon}_{fold.fit_id}.json.gz"))
                        for fold in FOLDS)
    parents = {"environment": env.identity_sha256, "runner": runner_sha,
               "features": feature_sha, "canonical_label": label_sha,
               "folds": digest(fold_hashes)}
    if pre_run_reference_sha is not None:
        parents["pre_run_registration"] = pre_run_reference_sha
    existing = _sealed_read(path, parents=parents)
    if existing is not None:
        _stage_ledger(env=env, run_id=run_dir.name, horizon=horizon,
                      stage="DOSSIER", artifact_sha=sha256(existing).hexdigest(), parents=parents)
        _log("E" + str(horizon), "dossier reused")
        return sha256(existing).hexdigest()
    stage = StageEvidence(horizon, "D", phases, contract_mode="REGISTERED")
    if not stage.registered_grid_complete:
        raise DevelopmentInputError("registered development grid incomplete")
    _log("E" + str(horizon), "evaluation start")
    metrics = compute_stage(stage)
    coverage = coverage_report(stage)
    symbol_time = symbol_time_report(stage)
    _log("E" + str(horizon), "evaluation complete; 10000x7d/14d bootstrap start")
    uncertainty = registered_bootstrap(stage)
    _log("E" + str(horizon), "registered bootstrap complete")
    dossier = StageDossier(metrics, uncertainty)
    decision = decide_horizon(horizon_minutes=horizon, development=dossier,
                              prospective=None, h1_governance=H1Governance(), h1=None,
                              prospective_coverage=None, prospective_target_sealed=False,
                              ledger_and_artifacts_sealed=False)
    output = {"horizon": horizon, "stage": "D", "parents": parents,
              "metrics": _wire(metrics), "coverage": _wire(coverage),
              "symbol_time": _wire(symbol_time), "uncertainty": _wire(uncertainty),
              "development_decision_trace": _wire(decision),
              "h1_governance_status": "CLEANLINESS_UNVERIFIED",
              "prospective_accept_claimed": False}
    payload = gzip.compress(canonical_json(output).encode("utf-8"), mtime=0)
    artifact_sha = _sealed_write(path, payload, parents=parents)
    _stage_ledger(env=env, run_id=run_dir.name, horizon=horizon,
                  stage="DOSSIER", artifact_sha=artifact_sha, parents=parents)
    _log("E" + str(horizon), "dossier durable complete", artifact_sha)
    return artifact_sha


def _prepare_horizon_stages(*, run_dir: Path, env, runner_sha: str,
                            feature_path: Path, feature_sha: str,
                            feature_parents: dict[str, str], horizon: int):
    inputs = authenticate_inputs(REPO, horizon_minutes=horizon)
    _log(f"E{horizon}", "canonical target authentication start")
    targets = read_label_range(inputs, symbols=SYMBOLS, start=D0,
                               end=H1_START, max_row_groups=2_000)
    _log(f"E{horizon}", "canonical target authentication complete", len(targets))
    entry = _registration(env, horizon)
    _log(f"E{horizon}", "pre-run registration", entry.entry_sha256)
    pre_run_reference_sha = _preserve_registration(
        run_dir=run_dir, env=env, runner_sha=runner_sha,
        horizon=horizon, entry=entry)
    primary_hashes, horizon_jobs = {}, []
    for fold in FOLDS:
        _, primary_sha = _prepare_primary_stage(
            run_dir=run_dir, env=env, runner_sha=runner_sha,
            feature_path=feature_path, feature_sha=feature_sha, inputs=inputs,
            targets=targets, fold=fold, horizon=horizon,
            pre_run_reference_sha=pre_run_reference_sha)
        primary_hashes[fold.fit_id] = primary_sha
        primary_parents = _primary_parents(_fold_parents(
            env=env, runner_sha=runner_sha, feature_sha=feature_sha, inputs=inputs,
            fold=fold, horizon=horizon,
            pre_run_reference_sha=pre_run_reference_sha))
        _stage_ledger(env=env, run_id=run_dir.name, horizon=horizon,
                      stage=f"{fold.fit_id}_PRIMARY", artifact_sha=primary_sha,
                      parents=primary_parents)
        horizon_jobs.append(ComparatorJob(
            str(REPO), str(run_dir), runner_sha, str(feature_path), feature_sha,
            horizon, fold.fit_id, pre_run_reference_sha, primary_sha,
            env.identity_sha256, inputs.label_member_sha256,
            tuple(sorted(feature_parents.items()))))
    return inputs, pre_run_reference_sha, primary_hashes, tuple(horizon_jobs)


def _prepare_independent_horizons(prepare):
    """Retain completed E60 work if independent E120 preparation fails."""
    contexts, jobs, deferred_e120_error = {}, [], None
    for horizon in (60, 120):
        try:
            inputs, pre_run_reference_sha, primary_hashes, horizon_jobs = prepare(horizon)
        except Exception as exc:
            if horizon == 60:
                raise
            deferred_e120_error = exc
            _log("E120", "primary preparation failed; completing independent E60 evidence",
                 f"{type(exc).__name__}: {exc}")
            break
        contexts[horizon] = (inputs, pre_run_reference_sha, primary_hashes)
        jobs.extend(horizon_jobs)
    return contexts, tuple(jobs), deferred_e120_error


def _run(*, resume_id: str | None = None,
         reuse_features_from_run: str | None = None,
         comparator_workers: int = COMPARATOR_WORKERS_DEFAULT) -> dict:
    _validate_worker_count(comparator_workers)
    env, _ = _preflight()
    runner_sha = _committed_runner()
    run_id = resume_id or (datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") +
                           "_" + env.source_revision[:8])
    if not RUN_ID.fullmatch(run_id):
        raise DevelopmentInputError("invalid UTC run ID")
    run_dir = RUN_ROOT / run_id
    _guard_run_dir(run_dir)
    plan = _plan(env)
    source_inputs = authenticate_inputs(REPO, horizon_minutes=60)
    reuse_evidence = (_authenticate_feature_reuse(
        producer_run_id=reuse_features_from_run, env=env,
        source_contract=source_inputs.source_contract)
        if reuse_features_from_run is not None else None)
    manifest_reuse = ({key: value for key, value in reuse_evidence.items()
                       if key != "producer_artifact_path"}
                      if reuse_evidence is not None else
                      {"feature_materialization_mode": "GENERATED_CURRENT"})
    expected_manifest = {"run_id": run_id, "plan": plan,
                         "runner_sha256": runner_sha,
                         "historical_source_manifest_sha256": SOURCE_SHA256,
                         "canonical_release_manifest_sha256": RELEASE_SHA256,
                         "label_members": {str(h): authenticate_inputs(REPO, horizon_minutes=h).label_member_sha256
                                           for h in (60, 120)},
                         "feature_end_exclusive": iso(FEATURE_STOP),
                         "feature_materialization": manifest_reuse}
    if resume_id is None:
        RUN_ROOT.mkdir(parents=True, exist_ok=True)
        _guard_run_dir(run_dir)
        run_dir.mkdir(exist_ok=False)
        _guard_run_dir(run_dir)
        _write_immutable(run_dir / "run_manifest.json", canonical_json(expected_manifest).encode())
    else:
        _reject_reparse_components(run_dir / "run_manifest.json")
        if _read_json(run_dir / "run_manifest.json") != expected_manifest:
            raise DevelopmentInputError("resume run manifest/parent identity mismatch")
    if (any(run_dir.glob("*.tmp")) or any(run_dir.glob(".incomplete-*")) or
            any(run_dir.glob(".features-incomplete-*")) or
            any(run_dir.glob(".features-import-incomplete-*"))):
        raise DevelopmentInputError("incomplete temporary stage present; manual audit required")
    _log("run", run_id, "authenticated plan", env.identity_sha256)
    feature_parents = {"environment": env.identity_sha256, "runner": runner_sha,
                       "source": SOURCE_SHA256, "registry": env.registry_sha256,
                       "spec": env.spec_sha256, "origin_range": digest((iso(D0), iso(FEATURE_STOP)))}
    if reuse_evidence is None:
        feature_path, feature_sha = _materialize_features(run_dir, source_inputs, feature_parents)
    else:
        feature_path, feature_sha = _import_features(run_dir, reuse_evidence, feature_parents)
    contexts, jobs, deferred_e120_error = _prepare_independent_horizons(
        lambda horizon: _prepare_horizon_stages(
            run_dir=run_dir, env=env, runner_sha=runner_sha,
            feature_path=feature_path, feature_sha=feature_sha,
            feature_parents=feature_parents, horizon=horizon))
    _log("comparators", "all primary stages durable", "workers", comparator_workers)
    comparator_results, comparator_failures = _schedule_comparator_jobs(
        tuple(jobs), workers=comparator_workers)
    results = {}
    failed_horizons = {horizon for horizon, _fit_id in comparator_failures}
    horizon_errors = {}
    for horizon in (60, 120):
        if horizon not in contexts or horizon in failed_horizons:
            continue
        try:
            inputs, pre_run_reference_sha, primary_hashes = contexts[horizon]
            horizon_jobs = {job.fit_id: job for job in jobs if job.horizon == horizon}
            for fold in FOLDS:
                job = horizon_jobs[fold.fit_id]
                _, artifact_sha = comparator_results[job.key]
                _stage_ledger(env=env, run_id=run_id, horizon=horizon,
                              stage=f"{fold.fit_id}_COMPARATOR", artifact_sha=artifact_sha,
                              parents=_comparator_parents(job))
            targets = read_label_range(inputs, symbols=SYMBOLS, start=D0,
                                       end=H1_START, max_row_groups=2_000)
            phases = []
            for fold in FOLDS:
                phase = _assemble_staged_fold(
                    run_dir=run_dir, env=env, runner_sha=runner_sha,
                    feature_path=feature_path, feature_sha=feature_sha, inputs=inputs,
                    targets=targets, fold=fold, horizon=horizon,
                    primary_sha=primary_hashes[fold.fit_id],
                    comparator_job=horizon_jobs[fold.fit_id],
                    pre_run_reference_sha=pre_run_reference_sha)
                phases.append(phase)
                parents = _fold_parents(
                    env=env, runner_sha=runner_sha, feature_sha=feature_sha, inputs=inputs,
                    fold=fold, horizon=horizon,
                    pre_run_reference_sha=pre_run_reference_sha)
                parents = {**parents, "primary_stage": primary_hashes[fold.fit_id],
                           "comparator_stage": comparator_results[(horizon, fold.fit_id)][1]}
                _stage_ledger(
                    env=env, run_id=run_id, horizon=horizon, stage=fold.fit_id,
                    artifact_sha=_file_sha256(run_dir / f"E{horizon}_{fold.fit_id}.json.gz"),
                    parents=parents)
            results[str(horizon)] = _finish_horizon(
                run_dir=run_dir, env=env, runner_sha=runner_sha, horizon=horizon,
                phases=tuple(phases), feature_sha=feature_sha,
                label_sha=inputs.label_member_sha256,
                pre_run_reference_sha=pre_run_reference_sha)
        except Exception as exc:
            horizon_errors[horizon] = exc
    deferred_errors = [
        (horizon, next(i for i, fold in enumerate(FOLDS) if fold.fit_id == fit_id), exc)
        for (horizon, fit_id), exc in comparator_failures.items()]
    deferred_errors.extend((horizon, len(FOLDS), exc)
                           for horizon, exc in horizon_errors.items())
    if deferred_e120_error is not None:
        deferred_errors.append((120, len(FOLDS) + 1, deferred_e120_error))
    if deferred_errors:
        raise min(deferred_errors, key=lambda value: (value[0], value[1]))[2]
    _log("run", run_id, "development dossiers complete")
    return {"run_id": run_id, "run_dir": str(run_dir), "dossier_sha256": results}


def _status(run_id: str) -> dict:
    if not RUN_ID.fullmatch(run_id):
        raise DevelopmentInputError("invalid UTC run ID")
    run_dir = RUN_ROOT / run_id
    _guard_run_dir(run_dir)
    _reject_reparse_components(run_dir / "run_manifest.json")
    manifest = _read_json(run_dir / "run_manifest.json")
    if manifest.get("run_id") != run_id:
        raise DevelopmentInputError("run manifest ID mismatch")
    stages = {}
    stage_seals = {}
    for path in sorted(run_dir.glob("*.seal.json")):
        _reject_reparse_components(path)
        seal = _read_json(path)
        expected_name = path.name.removesuffix(".seal.json")
        if seal.get("artifact") != expected_name or not Path(expected_name).name == expected_name:
            raise DevelopmentInputError(f"invalid run artifact identity: {path}")
        artifact = run_dir / expected_name
        _reject_reparse_components(artifact)
        if not artifact.is_file() or artifact.is_symlink() or _file_sha256(artifact) != seal["sha256"]:
            raise DevelopmentInputError(f"corrupted run artifact: {artifact}")
        stages[artifact.name] = seal["sha256"]
        stage_seals[artifact.name] = seal
    feature_materialization = manifest.get("feature_materialization", {})
    if feature_materialization.get("feature_materialization_mode") == "REUSED_AUTHENTICATED":
        feature_name = f"features_{PRODUCER_FEATURE_SHA256}.jsonl.gz"
        expected_reuse = {
            "producer_run_id": PRODUCER_RUN_ID,
            "producer_source_revision": PRODUCER_REVISION,
            "producer_feature_rows": PRODUCER_FEATURE_ROWS,
            "producer_feature_sha256": PRODUCER_FEATURE_SHA256,
            "producer_run_manifest_sha256": PRODUCER_RUN_MANIFEST_SHA256,
            "producer_feature_seal_sha256": PRODUCER_FEATURE_SEAL_SHA256,
            "compatibility_verdict": "PASS",
        }
        if (any(feature_materialization.get(key) != value
                for key, value in expected_reuse.items()) or
                feature_materialization.get("producer_artifact_path") is not None or
                stages.get(feature_name) != PRODUCER_FEATURE_SHA256):
            raise DevelopmentInputError("reused feature provenance mismatch")
        expected_parents = {
            "environment": manifest["plan"]["environment_sha256"],
            "runner": manifest["runner_sha256"], "source": SOURCE_SHA256,
            "registry": manifest["plan"]["registry_sha256"],
            "spec": manifest["plan"]["spec_sha256"],
            "origin_range": digest((iso(D0), iso(FEATURE_STOP))),
            "materialization_mode": "REUSED_AUTHENTICATED",
            "producer_run_manifest": PRODUCER_RUN_MANIFEST_SHA256,
            "producer_feature_seal": PRODUCER_FEATURE_SEAL_SHA256,
            "producer_feature_artifact": PRODUCER_FEATURE_SHA256,
            "feature_contract": feature_materialization.get(
                "current_feature_contract_identity"),
        }
        if stage_seals[feature_name].get("parents") != expected_parents:
            raise DevelopmentInputError("reused feature seal provenance mismatch")
    registrations = {}
    for horizon in (60, 120):
        name = f"E{horizon}_pre_run_ledger.json"
        reference_path = run_dir / name
        if name not in stages:
            if (reference_path.exists() or
                    any(key.startswith(f"E{horizon}_F") for key in stages) or
                    f"E{horizon}_development_dossier.json.gz" in stages):
                raise DevelopmentInputError(f"missing sealed pre-run registration: E{horizon}")
            continue
        reference = _read_json(reference_path)
        entry_sha = reference.get("entry_sha256")
        parents = {"run_manifest": _file_sha256(run_dir / "run_manifest.json"),
                   "runner": manifest["runner_sha256"],
                   "permanent_ledger_entry": entry_sha}
        _sealed_read(reference_path, parents=parents)
        if (reference.get("run_id") != run_id or reference.get("horizon") != horizon or
                reference.get("environment_sha256") != manifest["plan"]["environment_sha256"] or
                reference.get("source_revision") != manifest["plan"]["source_revision"]):
            raise DevelopmentInputError("pre-run registration scope mismatch")
        _reject_reparse_components(LEDGER_ROOT)
        entries = ExperimentLedger(LEDGER_ROOT).read_all()
        if not any(e.entry_sha256 == entry_sha and e.horizon_minutes == horizon and
                   e.action == "DEVELOPMENT_PREFLIGHT_REGISTERED" and
                   dict(e.artifact_hashes).get("pre_run_registration") ==
                   reference.get("registration_identity_sha256") and
                   e.code_revision_or_hash == reference["source_revision"]
                   for e in entries):
            raise DevelopmentInputError("permanent pre-run ledger entry missing")
        for stage_name, stage_seal in stage_seals.items():
            if (re.fullmatch(rf"E{horizon}_F[1-5]\.json\.gz", stage_name) or
                    stage_name == f"E{horizon}_development_dossier.json.gz"):
                if stage_seal.get("parents", {}).get("pre_run_registration") != stages[name]:
                    raise DevelopmentInputError("stage pre-run registration parent mismatch")
        registrations[str(horizon)] = entry_sha
    comparator_stages = {}
    feature_names = [name for name in stages if name.startswith("features_") and name.endswith(".jsonl.gz")]
    for directory in sorted(run_dir.glob("E*_F*.comparator.stage")):
        match = re.fullmatch(r"E(60|120)_(F[1-5])\.comparator\.stage", directory.name)
        if match is None or len(feature_names) != 1:
            raise DevelopmentInputError(f"invalid comparator stage identity: {directory}")
        horizon, fit_id = int(match.group(1)), match.group(2)
        primary = _primary_path(run_dir, horizon, fit_id)
        if not primary.is_file():
            raise DevelopmentInputError("comparator stage missing primary parent")
        job = ComparatorJob(
            str(REPO), str(run_dir), manifest["runner_sha256"],
            str(run_dir / feature_names[0]), stages[feature_names[0]], horizon, fit_id,
            stages.get(f"E{horizon}_pre_run_ledger.json"), _file_sha256(primary),
            manifest["plan"]["environment_sha256"], manifest["label_members"][str(horizon)],
            tuple(sorted(stage_seals[feature_names[0]]["parents"].items())))
        _read_primary_stage(primary, parents=_job_parents(job), horizon=horizon, fit_id=fit_id)
        _, artifact_sha = _read_comparator_stage(directory, job=job)
        comparator_stages[directory.name] = artifact_sha
        final_name = f"E{horizon}_{fit_id}.json.gz"
        if final_name in stage_seals:
            final_parents = stage_seals[final_name].get("parents", {})
            if (final_parents.get("primary_stage") != job.primary_sha or
                    final_parents.get("comparator_stage") != artifact_sha):
                raise DevelopmentInputError("final fold staged provenance mismatch")
    interrupted = []
    for path in sorted(run_dir.glob(".E*_F*.comparator-incomplete-*")):
        _reject_reparse_components(path)
        if not path.is_dir() or path.is_symlink():
            raise DevelopmentInputError(f"invalid comparator temporary path: {path}")
        interrupted.append(path.name)
    return {"run_id": run_id, "environment_sha256": manifest["plan"]["environment_sha256"],
            "hash_verified_files": stages, "pre_run_ledger_entries": registrations,
            "hash_verified_comparator_stages": comparator_stages,
            "interrupted_comparator_work": interrupted,
            "feature_materialization_mode": feature_materialization.get(
                "feature_materialization_mode", "LEGACY_UNDECLARED"),
            "dossier_files_present_and_hashed": all(
                f"E{h}_development_dossier.json.gz" in stages for h in (60, 120))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manual LDE V1 development study runner")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--resume", metavar="RUN_ID")
    mode.add_argument("--status", metavar="RUN_ID")
    parser.add_argument("--reuse-features-from-run", metavar="PRODUCER_RUN_ID")
    parser.add_argument("--comparator-workers", type=int, default=COMPARATOR_WORKERS_DEFAULT,
                        help="explicit process workers for independent comparators (1-4; default 1)")
    args = parser.parse_args(argv)
    try:
        _validate_worker_count(args.comparator_workers)
        if args.dry_run:
            result = dry_run(reuse_features_from_run=args.reuse_features_from_run)
        elif args.execute:
            result = _run(reuse_features_from_run=args.reuse_features_from_run,
                          comparator_workers=args.comparator_workers)
        elif args.resume:
            result = _run(resume_id=args.resume,
                          reuse_features_from_run=args.reuse_features_from_run,
                          comparator_workers=args.comparator_workers)
        else:
            if args.reuse_features_from_run is not None or args.comparator_workers != 1:
                raise DevelopmentInputError("execution options are invalid with status")
            result = _status(args.status)
        print(canonical_json(result), flush=True)
        return 0
    except (DevelopmentInputError, OSError, ValueError, KeyError) as exc:
        print(f"LDE_V1_RUN_BLOCKED: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

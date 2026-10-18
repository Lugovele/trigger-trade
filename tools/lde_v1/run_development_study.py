"""Manual LDE V1 F1–F5 development runner. Importing this module has no effects.

Only --execute or --resume can fit. --dry-run authenticates a tiny early
development fixture and prints the frozen plan without creating run evidence.
"""

from __future__ import annotations

import argparse
from contextlib import ExitStack
import csv
from dataclasses import asdict, is_dataclass
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
from triggertrade.live_direction_estimator_v1.manifests import build_manifest, canonical_json, digest
from triggertrade.live_direction_estimator_v1.orchestration import (
    IdentityReferences, fit_pipeline, score_bundle,
)
from triggertrade.live_direction_estimator_v1.comparator import fit_comparator, score_comparator
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
            "source_revision": env.source_revision,
            "horizons": [60, 120], "h1_governance_status": "CLEANLINESS_UNVERIFIED",
            "folds": [{"fit_id": f.fit_id,
                       "base": f.base.inequality,
                       "calibration": f.calibration.inequality,
                       "score": f.score.inequality} for f in FOLDS],
            "stage_graph": ["AUTHENTICATE", "MATERIALIZE_FEATURES", "E60_F1_F5",
                            "E60_EVALUATION_BOOTSTRAP", "E120_F1_F5",
                            "E120_EVALUATION_BOOTSTRAP", "DOSSIER"]}


def dry_run() -> dict:
    env, _ = _preflight()
    plan = _plan(env)
    proposed = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") + "_" + env.source_revision[:8]
    return {"mode": "DRY_RUN", "plan": plan,
            "would_create": str(RUN_ROOT / proposed),
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


def _registration(env, horizon: int):
    registration = DevelopmentPreRunRegistration.from_environment(env)
    _reject_reparse_components(LEDGER_ROOT)
    ledger = ExperimentLedger(LEDGER_ROOT)
    entries = [e for e in ledger.read_all()
               if e.action == registration.action and e.horizon_minutes == horizon and
               e.fit_or_cohort_id == registration.scope]
    if entries:
        if (len(entries) != 1 or dict(entries[0].artifact_hashes).get("pre_run_registration") !=
                registration.identity_sha256 or entries[0].code_revision_or_hash != env.source_revision):
            raise DevelopmentInputError("conflicting or duplicate permanent pre-run registration")
        return entries[0]
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
    manifest_hashes = tuple(sorted(parents.items()))
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
    path = run_dir / f"E{horizon}_{fold.fit_id}.json.gz"
    parents = {"environment": env.identity_sha256, "runner": runner_sha,
               "features": feature_sha, "canonical_label": inputs.label_member_sha256,
               "source": SOURCE_SHA256, "release": RELEASE_SHA256,
               "fit": digest((fold.fit_id, horizon))}
    if pre_run_reference_sha is not None:
        parents["pre_run_registration"] = pre_run_reference_sha
    existing = _sealed_read(path, parents=parents)
    if existing is not None:
        output = json.loads(gzip.decompress(existing))
        if (output["horizon"] != horizon or output["fit_id"] != fold.fit_id or
                output["parents"] != parents):
            raise DevelopmentInputError("resume fold identity mismatch")
        _stage_ledger(env=env, run_id=run_dir.name, horizon=horizon,
                      stage=fold.fit_id, artifact_sha=sha256(existing).hexdigest(), parents=parents)
        _log("E" + str(horizon), fold.fit_id, "reused", len(output["records"]), "records")
        positions = tuple(fold.score.nominal_start + PURGE + i * timedelta(minutes=5)
                          for i in range(int((fold.score.nominal_end - PURGE -
                                              (fold.score.nominal_start + PURGE)) /
                                             timedelta(minutes=5))))
        return PhaseGrid(fold.fit_id, positions,
                         tuple(_restore_record(v) for v in output["records"]))

    _log("E" + str(horizon), fold.fit_id, "manifest rows start")
    joined, manifests = _fold_rows(feature_path, fold, targets, inputs.source_contract, inputs)
    _log("E" + str(horizon), fold.fit_id, "selected",
         *(f"{kind}={len(manifests[kind].selected)}" for kind in ("BASE", "CALIBRATION", "SCORE")))
    identities = IdentityReferences(SOURCE_SHA256, RELEASE_ID, inputs.label_member_sha256)
    _log("E" + str(horizon), fold.fit_id, "primary fit start")
    bundle = fit_pipeline(base_manifest=manifests["BASE"],
                          calibration_manifest=manifests["CALIBRATION"],
                          base_rows=joined["BASE"], calibration_rows=joined["CALIBRATION"],
                          identities=identities)
    _log("E" + str(horizon), fold.fit_id, "primary fit/calibration complete")
    primary = score_bundle(bundle, scored_manifest=manifests["SCORE"],
                           scored_rows=joined["SCORE"])
    _log("E" + str(horizon), fold.fit_id, "score complete", len(primary))
    _log("E" + str(horizon), fold.fit_id, "comparator fit start")
    try:
        comparator = fit_comparator(primary=bundle, base_manifest=manifests["BASE"],
                                    calibration_manifest=manifests["CALIBRATION"],
                                    base_rows=joined["BASE"], calibration_rows=joined["CALIBRATION"])
    except (ValueError, ArithmeticError, RuntimeError) as exc:
        comparator = None
        comparator_scores = ()
        comparator_status = seal_report_only_status(
            role="C1_SHALLOW_RF", horizon_minutes=horizon, fit_id=fold.fit_id,
            status="FIT_FAILED", reason=f"{type(exc).__name__}: {exc}"[:500],
            primary_bundle_sha256=bundle.manifest.bundle_sha256)
        _log("E" + str(horizon), fold.fit_id, "comparator FIT_FAILED", comparator_status.reason)
    else:
        comparator_scores = score_comparator(comparator, primary=bundle,
            scored_manifest=manifests["SCORE"], scored_rows=joined["SCORE"],
            primary_scored_rows=primary)
        comparator_status = seal_report_only_status(
            role="C1_SHALLOW_RF", horizon_minutes=horizon, fit_id=fold.fit_id,
            status="FITTED", reason="", primary_bundle_sha256=bundle.manifest.bundle_sha256,
            artifact_sha256=comparator.artifact_sha256, artifact_available_at=datetime.now(UTC),
            evidence_ref=f"{run_dir.name}/E{horizon}_{fold.fit_id}.json.gz:comparator")
        _log("E" + str(horizon), fold.fit_id, "comparator complete", len(comparator_scores))
    _log("E" + str(horizon), fold.fit_id, "shadow fit start")
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
        _log("E" + str(horizon), fold.fit_id, "shadow FIT_FAILED", shadow_status.reason)
    else:
        shadow_scores = score_shadow(shadow, primary=bundle,
            scored_manifest=manifests["SCORE"], scored_rows=joined["SCORE"],
            primary_scored_rows=primary)
        shadow_status = seal_report_only_status(
            role="SIX_MONTH_ROLLING_SHADOW", horizon_minutes=horizon, fit_id=fold.fit_id,
            status="FITTED", reason="", primary_bundle_sha256=bundle.manifest.bundle_sha256,
            artifact_sha256=shadow.artifact_sha256, artifact_available_at=datetime.now(UTC),
            evidence_ref=f"{run_dir.name}/E{horizon}_{fold.fit_id}.json.gz:shadow")
        _log("E" + str(horizon), fold.fit_id, "shadow complete", len(shadow_scores))
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
    output = {"fit_id": fold.fit_id, "horizon": horizon, "parents": parents,
              "manifests": {key: json.loads(m.to_json()) for key, m in manifests.items()},
              "bundle_manifest": json.loads(bundle.manifest.to_json()),
              "preprocessing": bundle.preprocessing.to_dict(),
              "model": json.loads(bundle.model.to_json()),
              "calibrator": json.loads(bundle.calibrator.to_json()),
              "baselines": _wire(bundle.baselines),
              "comparator": json.loads(comparator.to_json()) if comparator else None,
              "shadow": json.loads(shadow.to_json()) if shadow else None,
              "comparator_status": json.loads(comparator_status.to_json()),
              "shadow_status": json.loads(shadow_status.to_json()),
              "primary_scores": _wire(primary),
              "comparator_scores": _wire(comparator_scores),
              "shadow_scores": _wire(shadow_scores),
              "records": _wire(records)}
    payload = gzip.compress(canonical_json(output).encode("utf-8"), mtime=0)
    artifact_sha = _sealed_write(path, payload, parents=parents)
    _stage_ledger(env=env, run_id=run_dir.name, horizon=horizon,
                  stage=fold.fit_id, artifact_sha=artifact_sha, parents=parents)
    _log("E" + str(horizon), fold.fit_id, "durable complete", artifact_sha)
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


def _run(*, resume_id: str | None = None) -> dict:
    env, _ = _preflight()
    runner_sha = _committed_runner()
    run_id = resume_id or (datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ") +
                           "_" + env.source_revision[:8])
    if not RUN_ID.fullmatch(run_id):
        raise DevelopmentInputError("invalid UTC run ID")
    run_dir = RUN_ROOT / run_id
    _guard_run_dir(run_dir)
    plan = _plan(env)
    expected_manifest = {"run_id": run_id, "plan": plan,
                         "runner_sha256": runner_sha,
                         "historical_source_manifest_sha256": SOURCE_SHA256,
                         "canonical_release_manifest_sha256": RELEASE_SHA256,
                         "label_members": {str(h): authenticate_inputs(REPO, horizon_minutes=h).label_member_sha256
                                           for h in (60, 120)},
                         "feature_end_exclusive": iso(FEATURE_STOP)}
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
            any(run_dir.glob(".features-incomplete-*"))):
        raise DevelopmentInputError("incomplete temporary stage present; manual audit required")
    _log("run", run_id, "authenticated plan", env.identity_sha256)
    source_inputs = authenticate_inputs(REPO, horizon_minutes=60)
    feature_parents = {"environment": env.identity_sha256, "runner": runner_sha,
                       "source": SOURCE_SHA256, "registry": env.registry_sha256,
                       "spec": env.spec_sha256, "origin_range": digest((iso(D0), iso(FEATURE_STOP)))}
    feature_path, feature_sha = _materialize_features(run_dir, source_inputs, feature_parents)
    results = {}
    for horizon in (60, 120):
        inputs = authenticate_inputs(REPO, horizon_minutes=horizon)
        _log("E" + str(horizon), "canonical target authentication start")
        targets = read_label_range(inputs, symbols=SYMBOLS, start=D0,
                                   end=H1_START, max_row_groups=2_000)
        _log("E" + str(horizon), "canonical target authentication complete", len(targets))
        entry = _registration(env, horizon)
        _log("E" + str(horizon), "pre-run registration", entry.entry_sha256)
        pre_run_reference_sha = _preserve_registration(
            run_dir=run_dir, env=env, runner_sha=runner_sha,
            horizon=horizon, entry=entry)
        phases = tuple(_fold_stage(run_dir=run_dir, env=env, runner_sha=runner_sha,
                                   feature_path=feature_path, feature_sha=feature_sha,
                                   inputs=inputs, targets=targets, fold=fold, horizon=horizon,
                                   pre_run_reference_sha=pre_run_reference_sha)
                       for fold in FOLDS)
        results[str(horizon)] = _finish_horizon(run_dir=run_dir, env=env, runner_sha=runner_sha,
                                                horizon=horizon, phases=phases,
                                                feature_sha=feature_sha,
                                                label_sha=inputs.label_member_sha256,
                                                pre_run_reference_sha=pre_run_reference_sha)
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
    return {"run_id": run_id, "environment_sha256": manifest["plan"]["environment_sha256"],
            "hash_verified_files": stages, "pre_run_ledger_entries": registrations,
            "dossier_files_present_and_hashed": all(
                f"E{h}_development_dossier.json.gz" in stages for h in (60, 120))}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Manual LDE V1 development study runner")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--execute", action="store_true")
    mode.add_argument("--resume", metavar="RUN_ID")
    mode.add_argument("--status", metavar="RUN_ID")
    args = parser.parse_args(argv)
    try:
        if args.dry_run:
            result = dry_run()
        elif args.execute:
            result = _run()
        elif args.resume:
            result = _run(resume_id=args.resume)
        else:
            result = _status(args.status)
        print(canonical_json(result), flush=True)
        return 0
    except (DevelopmentInputError, OSError, ValueError, KeyError) as exc:
        print(f"LDE_V1_RUN_BLOCKED: {exc}", file=sys.stderr, flush=True)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

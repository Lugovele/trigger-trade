"""Bounded stage reuse contracts; no real fitting or corpus reads."""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import gzip

import pytest

from tools.lde_v1 import run_development_study as runner
from triggertrade.live_direction_estimator_v1.development_readiness import DevelopmentInputError


REVISION = "8d702cc"
CURRENT = "2679f91"
FEATURE = "a" * 64
LABEL = "b" * 64
PRIMARY = "c" * 64


def contract(kind, revision, **kwargs):
    return runner._stage_compatibility(
        kind=kind, revision=revision, feature_sha=FEATURE, label_sha=LABEL,
        horizon=60, fold=runner.FOLDS[0],
        primary_sha=PRIMARY if kind == "COMPARATOR_STAGE" else None, **kwargs)


def test_primary_compatibility_cross_revision_excludes_downstream_fixes():
    assert contract("PRIMARY_FOLD", REVISION) == contract("PRIMARY_FOLD", CURRENT)


def test_primary_relevant_code_change_invalidates(monkeypatch):
    original = runner._git_bytes
    def changed(revision, path):
        value = original(revision, path)
        return value + b"\n# changed primary math\n" if (
            revision == CURRENT and path.endswith("/model.py")) else value
    before = contract("PRIMARY_FOLD", REVISION)
    monkeypatch.setattr(runner, "_git_bytes", changed)
    assert before != contract("PRIMARY_FOLD", CURRENT)


def test_comparator_training_compatibility_excludes_scoring_fix():
    assert contract("COMPARATOR_STAGE", REVISION) == contract("COMPARATOR_STAGE", CURRENT)
    assert runner._comparator_training_code(REVISION) == runner._comparator_training_code(CURRENT)
    assert runner._git_bytes(REVISION,
        "src/triggertrade/live_direction_estimator_v1/comparator.py") != runner._git_bytes(
            CURRENT, "src/triggertrade/live_direction_estimator_v1/comparator.py")
    assert runner._comparator_scoring_code(REVISION) == runner._comparator_scoring_code(CURRENT)


def test_changed_stored_score_semantics_are_detected(monkeypatch):
    original = runner._git_bytes
    path = "src/triggertrade/live_direction_estimator_v1/comparator.py"
    before = runner._comparator_scoring_code(REVISION)
    def changed(revision, relative):
        value = original(revision, relative)
        if revision == CURRENT and relative == path:
            return value.replace(b"return ComparatorPrediction(probabilities, logits, logits,",
                                 b"return ComparatorPrediction(probabilities, logits, probabilities,")
        return value
    monkeypatch.setattr(runner, "_git_bytes", changed)
    assert before != runner._comparator_scoring_code(CURRENT)


@pytest.mark.parametrize("suffix,old,new", [
    ("/comparator.py", b"TREES = 256", b"TREES = 257"),
    ("/evaluation_bootstrap.py", b"UINT64 = 1 << 64", b"UINT64 = 1 << 63"),
])
def test_comparator_training_or_rng_change_invalidates(monkeypatch, suffix, old, new):
    original = runner._git_bytes
    before = contract("COMPARATOR_STAGE", REVISION)
    def changed(revision, path):
        value = original(revision, path)
        return value.replace(old, new) if revision == CURRENT and path.endswith(suffix) else value
    monkeypatch.setattr(runner, "_git_bytes", changed)
    assert before != contract("COMPARATOR_STAGE", CURRENT)


def test_comparator_primary_parent_change_invalidates():
    first = contract("COMPARATOR_STAGE", REVISION)
    second = runner._stage_compatibility(
        kind="COMPARATOR_STAGE", revision=REVISION, feature_sha=FEATURE,
        label_sha=LABEL, horizon=60, fold=runner.FOLDS[0], primary_sha="d" * 64)
    assert first != second


@pytest.fixture
def import_fixture(tmp_path):
    source = tmp_path / "source.json.gz"
    source.write_bytes(b"synthetic sealed bytes")
    seal = tmp_path / "source.seal.json"
    seal.write_bytes(b"synthetic producer seal")
    evidence = {
        "kind": "PRIMARY_FOLD", "horizon": 60, "fit_id": "F1",
        "producer_run_id": "20261019T151610975545Z_8d702cc6",
        "producer_source_revision": "8d702cc" + "0" * 33,
        "producer_artifact_sha256": sha256(source.read_bytes()).hexdigest(),
        "producer_seal_sha256": sha256(seal.read_bytes()).hexdigest(),
        "producer_stage_identity": "e" * 64,
        "compatibility_identity": "f" * 64,
        "producer_payload_parents": {"legacy": "a" * 64},
        "producer_artifact_path": str(source), "producer_seal_path": str(seal),
    }
    return source, seal, evidence, tmp_path / "imported.primary.json.gz"


def test_import_exact_bytes_new_provenance_and_untouched_source(import_fixture):
    source, seal, evidence, destination = import_fixture
    source_before, seal_before = source.read_bytes(), seal.read_bytes()
    copied = runner._import_stage(evidence, destination, {"stage": "PRIMARY_FOLD"})
    assert copied == evidence["producer_artifact_sha256"]
    assert destination.read_bytes() == source_before
    assert source.read_bytes() == source_before and seal.read_bytes() == seal_before
    parents, imported = runner._effective_stage_parents(
        destination, {"stage": "PRIMARY_FOLD"})
    assert imported["producer_run_id"] == evidence["producer_run_id"]
    assert parents["import_provenance"] == runner.digest(imported)
    assert runner._sealed_read(destination, parents=parents) == source_before


def test_same_import_is_idempotent_but_changed_parent_fails(import_fixture):
    _, _, evidence, destination = import_fixture
    parents = {"stage": "PRIMARY_FOLD"}
    first = runner._import_stage(evidence, destination, parents)
    assert runner._import_stage(evidence, destination, parents) == first
    with pytest.raises(DevelopmentInputError, match="existing import provenance mismatch"):
        runner._import_stage(evidence, destination, {"stage": "OTHER"})


def test_imported_current_ledger_is_required(import_fixture):
    _, _, evidence, destination = import_fixture
    runner._import_stage(evidence, destination, {"stage": "PRIMARY_FOLD"})
    parents, _ = runner._effective_stage_parents(destination, {"stage": "PRIMARY_FOLD"})
    with pytest.raises(DevelopmentInputError, match="current imported stage ledger"):
        runner._verify_stage_ledger_existing(
            entries=(), run_id="20261021T000000000000Z_2679f912", horizon=60,
            stage="F1_PRIMARY", artifact_sha=evidence["producer_artifact_sha256"],
            parents=parents, environment_sha="a" * 64, revision=CURRENT)


@pytest.fixture(params=["PRIMARY", "COMPARATOR"])
def published_import(import_fixture, tmp_path, monkeypatch, request):
    source, seal, evidence, _ = import_fixture
    kind = request.param
    run_id = "20261021T000000000000Z_464ba257"
    monkeypatch.setattr(runner, "RUN_ROOT", tmp_path / "runs")
    monkeypatch.setattr(runner, "LEDGER_ROOT", tmp_path / "ledger")
    run_dir = runner.RUN_ROOT / run_id
    run_dir.mkdir(parents=True)
    stage = f"F1_{kind}"
    if kind == "PRIMARY":
        destination = runner._primary_path(run_dir, 60, "F1")
        base = {"stage": "PRIMARY_FOLD", "environment": "a" * 64}
    else:
        destination = runner._comparator_stage_dir(run_dir, 60, "F1")
        base = {"stage": "REPORT_ONLY_COMPARATOR", "environment": "a" * 64,
                "primary_stage": "b" * 64}
        evidence = {**evidence, "kind": "COMPARATOR_STAGE",
                    "primary_parent_sha256": "b" * 64}
    artifact_sha = runner._import_stage(
        evidence, destination, base, comparator=kind == "COMPARATOR")
    parents, imported = runner._effective_stage_parents(destination, base)
    env = SimpleNamespace(identity_sha256="a" * 64, source_revision="4" * 40)
    runner._stage_ledger(env=env, run_id=run_id, horizon=60, stage=stage,
                         artifact_sha=artifact_sha, parents=parents)
    entries = runner.ExperimentLedger(runner.LEDGER_ROOT).read_all()
    return run_id, stage, destination, base, parents, imported, artifact_sha, env, entries


def verify_published(published_import, **overrides):
    run_id, stage, _, _, parents, _, artifact_sha, env, entries = published_import
    args = dict(entries=entries, run_id=run_id, horizon=60, stage=stage,
                artifact_sha=artifact_sha, parents=parents,
                environment_sha=env.identity_sha256, revision=env.source_revision)
    args.update(overrides)
    runner._verify_stage_ledger_existing(**args)


def test_status_accepts_execution_published_import_and_canonical_identity(published_import):
    run_id, stage, _, _, parents, _, artifact_sha, env, entries = published_import
    verify_published(published_import)
    expected = runner._stage_ledger_identity(
        run_id=run_id, horizon=60, stage=stage, artifact_sha=artifact_sha,
        parents=parents, environment_sha=env.identity_sha256)
    assert (entries[0].artifact_hashes, entries[0].manifest_hashes) == expected


def test_status_waits_for_live_import_ledger_then_authenticates(published_import, monkeypatch):
    monkeypatch.setattr(runner.time, "sleep", lambda _: None)
    entries = published_import[-1]
    verify_published(published_import, entries=(), live_ledger_reader=lambda: entries)


def test_status_never_accepts_missing_import_ledger(published_import, monkeypatch):
    monkeypatch.setattr(runner.time, "sleep", lambda _: None)
    with pytest.raises(DevelopmentInputError, match="current imported stage ledger"):
        verify_published(published_import, entries=(), live_ledger_reader=lambda: ())


def test_status_rejects_changed_import_ledger_evidence(published_import):
    with pytest.raises(DevelopmentInputError, match="current imported stage ledger"):
        verify_published(published_import, artifact_sha="f" * 64)


@pytest.mark.parametrize("field", ["producer_seal_sha256", "compatibility_identity"])
def test_status_rejects_changed_import_provenance(published_import, field):
    _, _, destination, base, _, _, _, _, _ = published_import
    seal_path = (destination / "seal.json" if destination.is_dir() else
                 destination.with_name(destination.name + ".seal.json"))
    seal = runner._read_json(seal_path)
    seal["imported"][field] = "0" * 64
    seal_path.write_text(runner.canonical_json(seal), encoding="utf-8")
    with pytest.raises(DevelopmentInputError, match="imported stage provenance mismatch"):
        runner._effective_stage_parents(destination, base)


def test_status_rejects_comparator_primary_parent_mismatch(published_import):
    _, stage, destination, base, _, _, _, _, _ = published_import
    if stage != "F1_COMPARATOR":
        pytest.skip("comparator only")
    with pytest.raises(DevelopmentInputError, match="imported stage provenance mismatch"):
        runner._effective_stage_parents(destination, {**base, "primary_stage": "f" * 64})


@pytest.mark.parametrize("target", ["bytes", "seal"])
def test_producer_tamper_fails_before_copy(import_fixture, target):
    source, seal, evidence, destination = import_fixture
    (source if target == "bytes" else seal).write_bytes(b"tampered")
    with pytest.raises(DevelopmentInputError, match="producer evidence changed"):
        runner._import_stage(evidence, destination, {"stage": "PRIMARY_FOLD"})
    assert not destination.exists()


def test_copy_race_fails_closed(import_fixture, monkeypatch):
    source, seal, evidence, destination = import_fixture
    actual_hash = runner._file_sha256
    def mutate_after_seal(path: Path):
        result = actual_hash(path)
        if path == seal:
            source.write_bytes(b"changed during copy")
        return result
    monkeypatch.setattr(runner, "_file_sha256", mutate_after_seal)
    with pytest.raises(DevelopmentInputError, match="copy hash mismatch"):
        runner._import_stage(evidence, destination, {"stage": "PRIMARY_FOLD"})


def test_imported_seal_parent_tamper_fails(import_fixture):
    _, _, evidence, destination = import_fixture
    runner._import_stage(evidence, destination, {"stage": "PRIMARY_FOLD"})
    seal_path = destination.with_name(destination.name + ".seal.json")
    value = runner._read_json(seal_path)
    value["imported"]["producer_run_id"] = "other"
    seal_path.write_text(runner.canonical_json(value), encoding="utf-8")
    with pytest.raises(DevelopmentInputError, match="provenance mismatch"):
        runner._effective_stage_parents(destination, {"stage": "PRIMARY_FOLD"})


def test_explicit_reuse_failure_has_no_fit_fallback(monkeypatch):
    monkeypatch.setattr(runner, "_verify_stage_worktree", lambda _revision: None)
    monkeypatch.setattr(runner.ExperimentLedger, "read_all", lambda self: ())
    monkeypatch.setattr(runner, "authenticate_inputs", lambda *_a, **_kw:
                        type("Inputs", (), {"label_member_sha256": LABEL})())
    monkeypatch.setattr(runner, "_producer_stage", lambda **_kw:
                        (_ for _ in ()).throw(DevelopmentInputError("incompatible")))
    monkeypatch.setattr(runner, "fit_pipeline", lambda **_kw:
                        pytest.fail("fit must not start"))
    with pytest.raises(DevelopmentInputError, match="incompatible"):
        runner._planned_stage_reuse(
            env=type("Env", (), {"source_revision": CURRENT})(), feature_sha=FEATURE,
            primary_run="20261019T151610975545Z_8d702cc6", comparator_run=None)


def test_ten_by_ten_plan_starts_at_shadow_without_fitting(monkeypatch):
    monkeypatch.setattr(runner, "_verify_stage_worktree", lambda _revision: None)
    monkeypatch.setattr(runner.ExperimentLedger, "read_all", lambda self: ())
    monkeypatch.setattr(runner, "authenticate_inputs", lambda *_a, **_kw:
                        type("Inputs", (), {"label_member_sha256": LABEL})())
    def evidence(**kwargs):
        return {"kind": kwargs["kind"], "horizon": kwargs["horizon"],
                "fit_id": kwargs["fold"].fit_id,
                "producer_artifact_sha256": PRIMARY,
                "primary_bundle_sha256": "d" * 64,
                "producer_run_id": kwargs["run_id"]}
    monkeypatch.setattr(runner, "_producer_stage", evidence)
    monkeypatch.setattr(runner, "fit_pipeline", lambda **_kw:
                        pytest.fail("primary fitting started"))
    monkeypatch.setattr(runner, "fit_comparator", lambda **_kw:
                        pytest.fail("comparator training started"))
    plan = runner._planned_stage_reuse(
        env=type("Env", (), {"source_revision": CURRENT})(), feature_sha=FEATURE,
        primary_run="20261019T151610975545Z_8d702cc6",
        comparator_run="20261019T151610975545Z_8d702cc6")
    assert len(plan["primary"]) == len(plan["comparators"]) == 10
    assert plan["first_compute_stage"] == "E60 F1 SHADOW / FINAL FOLD"
    assert "final_folds" not in plan


@pytest.fixture
def synthetic_producer(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    root = repo / "runtime/lde_v1/development"
    revision = "a" * 40
    run_id = "20261019T151610975545Z_aaaaaaaa"
    run_dir = root / run_id
    run_dir.mkdir(parents=True)
    spec = repo / "spec.md"
    spec.write_text("synthetic spec", encoding="utf-8")
    monkeypatch.setattr(runner, "REPO", repo)
    monkeypatch.setattr(runner, "RUN_ROOT", root)
    monkeypatch.setattr(runner, "SPEC", spec)
    monkeypatch.setattr(runner, "_git_bytes", lambda _revision, _path: b"synthetic runner")
    monkeypatch.setattr(runner, "_stage_compatibility", lambda **_kw: "f" * 64)
    monkeypatch.setattr(runner, "_comparator_scoring_code", lambda _revision: "e" * 64)
    runner_sha = sha256(b"synthetic runner").hexdigest()
    environment = "1" * 64
    feature_bytes = b"synthetic feature bytes"
    feature_sha = sha256(feature_bytes).hexdigest()
    manifest = {
        "run_id": run_id, "runner_sha256": runner_sha,
        "historical_source_manifest_sha256": runner.SOURCE_SHA256,
        "canonical_release_manifest_sha256": runner.RELEASE_SHA256,
        "label_members": {"60": LABEL},
        "plan": {"source_revision": revision, "environment_sha256": environment,
                 "spec_sha256": runner._file_sha256(spec),
                 "registry_sha256": "2" * 64,
                 "feature_registry": runner.FEATURE_REGISTRY},
        "feature_materialization": {"feature_materialization_mode": "GENERATED_CURRENT"},
    }
    manifest_path = run_dir / "run_manifest.json"
    manifest_path.write_text(runner.canonical_json(manifest), encoding="utf-8")
    feature_path = run_dir / f"features_{feature_sha}.jsonl.gz"
    runner._sealed_write(feature_path, feature_bytes, parents={
        "environment": environment, "runner": runner_sha,
        "source": runner.SOURCE_SHA256, "registry": "2" * 64,
        "spec": runner._file_sha256(spec),
        "origin_range": runner.digest((runner.iso(runner.D0), runner.iso(runner.FEATURE_STOP))),
    })
    registration_entry = "3" * 64
    registration_path = run_dir / "E60_pre_run_ledger.json"
    runner._sealed_write(registration_path, runner.canonical_json({
        "run_id": run_id, "horizon": 60, "source_revision": revision,
        "environment_sha256": environment, "entry_sha256": registration_entry,
    }).encode(), parents={
        "run_manifest": runner._file_sha256(manifest_path), "runner": runner_sha,
        "permanent_ledger_entry": registration_entry,
    })
    base = {"environment": environment, "runner": runner_sha,
            "features": feature_sha, "canonical_label": LABEL,
            "source": runner.SOURCE_SHA256, "release": runner.RELEASE_SHA256,
            "fit": runner.digest(("F1", 60)),
            "pre_run_registration": runner._file_sha256(registration_path)}
    registration_ledger = SimpleNamespace(
        entry_sha256=registration_entry, action="DEVELOPMENT_PREFLIGHT_REGISTERED",
        horizon_minutes=60, code_revision_or_hash=revision)

    def stage_ledger(stage, artifact_sha, seal_path, parents):
        return SimpleNamespace(
            action="DEVELOPMENT_STAGE_COMPLETE", horizon_minutes=60,
            fit_or_cohort_id=f"{run_id}:{stage}", code_revision_or_hash=revision,
            artifact_hashes=tuple(sorted((
                ("stage_artifact", artifact_sha), ("environment", environment),
                ("stage_seal", runner._file_sha256(seal_path))))),
            manifest_hashes=tuple(sorted(
                (name, runner.digest((value, 60, stage)) if name == "stage" else value)
                for name, value in parents.items())))

    return SimpleNamespace(run_dir=run_dir, run_id=run_id, revision=revision,
                           feature_sha=feature_sha, base=base,
                           registration_ledger=registration_ledger,
                           stage_ledger=stage_ledger)


def test_direct_producer_seal_byte_change_fails_closed(synthetic_producer, monkeypatch):
    fixture = synthetic_producer
    parents = runner._primary_parents(fixture.base)
    path = runner._primary_path(fixture.run_dir, 60, "F1")
    manifest_sha = "4" * 64
    output = {"horizon": 60, "fit_id": "F1", "parents": fixture.base,
              "manifests": {name: {"manifest_sha256": manifest_sha}
                            for name in ("BASE", "CALIBRATION", "SCORE")}}
    artifact_sha = runner._sealed_write(
        path, gzip.compress(runner.canonical_json(output).encode(), mtime=0), parents=parents)
    seal_path = path.with_name(path.name + ".seal.json")
    ledger = fixture.stage_ledger("F1_PRIMARY", artifact_sha, seal_path, parents)
    monkeypatch.setattr(runner, "_restore_bundle", lambda _output:
                        SimpleNamespace(manifest=SimpleNamespace(
                            base_manifest_sha256=manifest_sha,
                            calibration_manifest_sha256=manifest_sha,
                            bundle_sha256="5" * 64)))
    kwargs = dict(run_id=fixture.run_id, kind="PRIMARY_FOLD", horizon=60,
                  fold=runner.FOLDS[0], feature_sha=fixture.feature_sha,
                  label_sha=LABEL, current_revision=CURRENT,
                  ledger_entries=(fixture.registration_ledger, ledger))
    assert runner._producer_stage(**kwargs)["producer_artifact_sha256"] == artifact_sha
    with pytest.raises(DevelopmentInputError, match="ledger evidence missing"):
        runner._producer_stage(**{**kwargs,
            "ledger_entries": (fixture.registration_ledger,)})
    seal = runner._read_json(seal_path)
    seal["completed_at"] = "2026-10-20T00:00:00.000000Z"
    seal_path.write_text(runner.canonical_json(seal), encoding="utf-8")
    with pytest.raises(DevelopmentInputError, match="ledger evidence mismatched"):
        runner._producer_stage(**kwargs)


def test_direct_comparator_selected_primary_bundle_mismatch(synthetic_producer):
    fixture = synthetic_producer
    primary_sha = "6" * 64
    parents = {**fixture.base, "stage": "REPORT_ONLY_COMPARATOR",
               "primary_stage": primary_sha}
    directory = runner._comparator_stage_dir(fixture.run_dir, 60, "F1")
    directory.mkdir()
    completed = "2026-10-20T00:00:00.000000Z"
    output = {"horizon": 60, "fit_id": "F1", "parents": parents,
              "primary_bundle_sha256": "7" * 64, "comparator": {},
              "fit_error": None, "completed_at": completed}
    artifact = directory / "artifact.json.gz"
    artifact_sha = runner._write_immutable(
        artifact, gzip.compress(runner.canonical_json(output).encode(), mtime=0))
    seal_path = directory / "seal.json"
    runner._write_immutable(seal_path, runner.canonical_json({
        "artifact": artifact.name, "sha256": artifact_sha, "parents": parents,
        "job_key": [60, "F1"], "completed_at": completed,
    }).encode())
    ledger = fixture.stage_ledger("F1_COMPARATOR", artifact_sha, seal_path, parents)
    with pytest.raises(DevelopmentInputError, match="selected primary bundle mismatch"):
        runner._producer_stage(
            run_id=fixture.run_id, kind="COMPARATOR_STAGE", horizon=60,
            fold=runner.FOLDS[0], feature_sha=fixture.feature_sha,
            label_sha=LABEL, current_revision=CURRENT, primary_sha=primary_sha,
            primary_bundle_sha="8" * 64,
            ledger_entries=(fixture.registration_ledger, ledger))

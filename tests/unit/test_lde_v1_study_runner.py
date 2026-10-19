"""Only synthetic runner contracts; never invoke --execute on retained data."""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
import gzip
import json
import re
import subprocess

import pytest

from tools.lde_v1 import run_development_study as runner
from triggertrade.live_direction_estimator_v1.historical_source import (
    HistoricalMember, HistoricalSourceContract,
)
from triggertrade.live_direction_estimator_v1.development_readiness import (
    AuthenticatedInputs, DevelopmentInputError, DevelopmentPreRunRegistration,
)
from triggertrade.live_direction_estimator_v1.experiment_ledger import ExperimentLedger


@pytest.fixture
def committed_runner_repo(tmp_path, monkeypatch):
    """An isolated synthetic Git repo; never commits to TriggerTrade."""
    repo = tmp_path / "fixture-repo"
    repo.mkdir()

    def git(*args):
        return subprocess.run(["git", *args], cwd=repo, capture_output=True,
                              check=True).stdout

    git("init", "-q")
    path = repo / "tools/lde_v1/run_development_study.py"
    path.parent.mkdir(parents=True)
    committed = b"print('committed runner')\n"
    path.write_bytes(committed)
    (repo / ".gitattributes").write_text(
        "tools/lde_v1/run_development_study.py text\n", encoding="utf-8")
    (repo / "other.txt").write_text("original\n", encoding="utf-8")
    git("add", ".gitattributes", "tools/lde_v1/run_development_study.py", "other.txt")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "commit", "-q", "-m", "synthetic fixture")
    monkeypatch.setattr(runner, "REPO", repo)
    monkeypatch.setattr(runner, "__file__", str(path))
    return repo, path, sha256(committed).hexdigest()


def test_committed_runner_unchanged_passes(committed_runner_repo):
    _repo, _path, expected = committed_runner_repo
    assert runner._committed_runner() == expected


def test_committed_runner_crlf_checkout_passes(committed_runner_repo):
    _repo, path, expected = committed_runner_repo
    path.write_bytes(path.read_bytes().replace(b"\n", b"\r\n"))
    assert runner._committed_runner() == expected


def test_committed_runner_source_modification_fails_closed(committed_runner_repo):
    _repo, path, _expected = committed_runner_repo
    path.write_bytes(path.read_bytes() + b"print('modified')\n")
    with pytest.raises(DevelopmentInputError, match="runner differs from committed HEAD"):
        runner._committed_runner()


def test_committed_runner_ignores_unrelated_dirty_file(committed_runner_repo):
    repo, _path, expected = committed_runner_repo
    (repo / "other.txt").write_text("dirty\n", encoding="utf-8")
    assert runner._committed_runner() == expected


def test_committed_runner_rejects_custom_clean_filter(committed_runner_repo):
    repo, _path, _expected = committed_runner_repo
    (repo / ".gitattributes").write_text(
        "tools/lde_v1/run_development_study.py filter=untrusted\n", encoding="utf-8")
    with pytest.raises(DevelopmentInputError, match="unsupported custom Git filter"):
        runner._committed_runner()


def test_committed_runner_rejects_redirected_registered_path(committed_runner_repo, monkeypatch):
    _repo, path, _expected = committed_runner_repo
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda candidate:
                        candidate == path or original_is_symlink(candidate))
    with pytest.raises(DevelopmentInputError, match="redirected evidence path"):
        runner._committed_runner()


def test_dry_run_builds_frozen_plan_without_writes(tmp_path, monkeypatch):
    env = SimpleNamespace(identity_sha256="a" * 64, source_revision="b" * 40,
                          spec_sha256="c" * 64, registry_sha256="d" * 64)
    monkeypatch.setattr(runner, "_preflight", lambda: (env, object()))
    monkeypatch.setattr(runner, "RUN_ROOT", tmp_path / "uncreated")
    result = runner.dry_run()
    assert result["mode"] == "DRY_RUN"
    assert result["model_fits"] == result["permanent_ledger_entries"] == 0
    assert [f["fit_id"] for f in result["plan"]["folds"]] == ["F1", "F2", "F3", "F4", "F5"]
    assert result["plan"]["horizons"] == [60, 120]
    assert not runner.RUN_ROOT.exists()


def test_sealed_stage_resume_integrity_and_no_overwrite(tmp_path):
    path = tmp_path / "fold.json"
    parents = {"environment": "a" * 64}
    payload = b'{"exact":"bytes"}'
    assert runner._sealed_write(path, payload, parents=parents) == sha256(payload).hexdigest()
    assert runner._sealed_read(path, parents=parents) == payload
    with pytest.raises(DevelopmentInputError, match="already exists"):
        runner._sealed_write(path, b"replacement", parents=parents)
    with pytest.raises(DevelopmentInputError, match="seal mismatch"):
        runner._sealed_read(path, parents={"environment": "b" * 64})
    path.write_bytes(b"tampered")
    with pytest.raises(DevelopmentInputError, match="seal mismatch"):
        runner._sealed_read(path, parents=parents)
    partial = tmp_path / "partial.json"
    partial.write_bytes(b"unsealed")
    with pytest.raises(DevelopmentInputError, match="partial stage"):
        runner._sealed_read(partial, parents=parents)


def test_staged_ledger_hash_fields_and_append_only_identity(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "LEDGER_ROOT", tmp_path / "ledger")
    env = SimpleNamespace(identity_sha256="a" * 64, source_revision="b" * 40)
    common = {"environment": env.identity_sha256, "fit": "c" * 64,
              "runner": "d" * 64}
    cases = (
        ("F1_PRIMARY", {**common, "stage": "PRIMARY_FOLD"}),
        ("F1_COMPARATOR", {**common, "stage": "REPORT_ONLY_COMPARATOR",
                           "primary_stage": "e" * 64}),
        ("F1", {**common, "primary_stage": "e" * 64,
                "comparator_stage": "f" * 64}),
        ("DOSSIER", {"environment": env.identity_sha256, "folds": "1" * 64,
                     "runner": "d" * 64}),
    )
    for index, (stage, parents) in enumerate(cases):
        original_parents = parents.copy()
        runner._stage_ledger(env=env, run_id="synthetic", horizon=60, stage=stage,
                             artifact_sha=f"{index + 2:x}" * 64, parents=parents)
        assert parents == original_parents
        entry = ExperimentLedger(runner.LEDGER_ROOT).read_all()[-1]
        assert entry.fit_or_cohort_id == f"synthetic:{stage}"
        for pairs in (entry.manifest_hashes, entry.artifact_hashes):
            assert pairs == tuple(sorted(pairs))
            assert len({name for name, _ in pairs}) == len(pairs)
            assert all(re.fullmatch(r"[0-9a-f]{64}", value) for _, value in pairs)
        if "stage" in parents:
            assert dict(entry.manifest_hashes)["stage"] == runner.digest(
                (parents["stage"], 60, stage))
        else:
            assert "stage" not in dict(entry.manifest_hashes)
        assert dict(entry.artifact_hashes)["stage_artifact"] == f"{index + 2:x}" * 64
        runner._stage_ledger(env=env, run_id="synthetic", horizon=60, stage=stage,
                             artifact_sha=f"{index + 2:x}" * 64, parents=parents)
        assert len(ExperimentLedger(runner.LEDGER_ROOT).read_all()) == index + 1
    entries = ExperimentLedger(runner.LEDGER_ROOT).read_all()
    assert all(entry.previous_entry_sha256 == previous.entry_sha256
               for previous, entry in zip(entries, entries[1:]))
    with pytest.raises(ValueError, match="sorted unique SHA-256 identity pairs"):
        runner._stage_ledger(env=env, run_id="synthetic", horizon=60,
                             stage="INVALID", artifact_sha="9" * 64,
                             parents={**common, "unexpected": "semantic literal"})
    assert len(ExperimentLedger(runner.LEDGER_ROOT).read_all()) == 4


def test_synthetic_primary_completion_reaches_comparator_scheduling_boundary(
        tmp_path, monkeypatch):
    run_dir = tmp_path / "synthetic-run"
    run_dir.mkdir()
    monkeypatch.setattr(runner, "REPO", tmp_path)
    monkeypatch.setattr(runner, "RUN_ROOT", tmp_path)
    monkeypatch.setattr(runner, "LEDGER_ROOT", tmp_path / "ledger")
    monkeypatch.setattr(runner, "FOLDS", (SimpleNamespace(fit_id="F1"),))
    inputs = SimpleNamespace(label_member_sha256="c" * 64)
    env = SimpleNamespace(identity_sha256="a" * 64, source_revision="b" * 40)
    monkeypatch.setattr(runner, "authenticate_inputs", lambda *_args, **_kwargs: inputs)
    monkeypatch.setattr(runner, "read_label_range", lambda *_args, **_kwargs: {})
    monkeypatch.setattr(runner, "_registration", lambda *_args: SimpleNamespace(
        entry_sha256="d" * 64))
    monkeypatch.setattr(runner, "_preserve_registration", lambda **_kwargs: "e" * 64)
    events = []
    monkeypatch.setattr(runner, "_log", lambda *args: events.append(args))

    def sealed_primary(*, run_dir, env, runner_sha, feature_sha, inputs, fold,
                       horizon, pre_run_reference_sha, **_kwargs):
        parents = runner._fold_parents(
            env=env, runner_sha=runner_sha, feature_sha=feature_sha,
            inputs=inputs, fold=fold, horizon=horizon,
            pre_run_reference_sha=pre_run_reference_sha)
        path = runner._primary_path(run_dir, horizon, fold.fit_id)
        sha = runner._sealed_write(path, b"synthetic primary", parents=runner._primary_parents(parents))
        events.append(("PRIMARY DURABLE COMPLETE", sha))
        return path, sha

    monkeypatch.setattr(runner, "_prepare_primary_stage", sealed_primary)
    feature_parents = {"environment": env.identity_sha256, "runner": "f" * 64,
                       "source": runner.SOURCE_SHA256, "registry": "2" * 64,
                       "spec": "3" * 64, "origin_range": "4" * 64,
                       "materialization_mode": "REUSED_AUTHENTICATED",
                       "producer_run_manifest": "5" * 64,
                       "producer_feature_seal": "6" * 64,
                       "producer_feature_artifact": "7" * 64,
                       "feature_contract": "8" * 64}
    feature_path = run_dir / "features_synthetic.jsonl.gz"
    feature_sha = runner._sealed_write(feature_path, b"synthetic feature",
                                       parents=feature_parents)
    verified_parents = runner._feature_seal_parents(
        feature_path, expected=feature_parents, artifact_sha=feature_sha)
    inputs_out, reference, primary_hashes, jobs = runner._prepare_horizon_stages(
        run_dir=run_dir, env=env, runner_sha="f" * 64,
        feature_path=feature_path, feature_sha=feature_sha,
        feature_parents=verified_parents, horizon=60)
    assert inputs_out is inputs and reference == "e" * 64
    assert events[-1][0] == "PRIMARY DURABLE COMPLETE"
    entries = ExperimentLedger(runner.LEDGER_ROOT).read_all()
    assert len(entries) == 1 and entries[0].fit_or_cohort_id == "synthetic-run:F1_PRIMARY"
    assert primary_hashes == {"F1": jobs[0].primary_sha}
    assert jobs[0].feature_parents == tuple(sorted(feature_parents.items()))
    seal = json.loads((run_dir / "E60_F1.primary.json.gz.seal.json").read_text())
    assert seal["parents"]["stage"] == "PRIMARY_FOLD"
    scheduled = []
    monkeypatch.setattr(runner, "_schedule_comparator_jobs",
                        lambda queued, *, workers: (scheduled.extend(queued) or {}, {}))
    runner._schedule_comparator_jobs(jobs, workers=1)
    assert scheduled == list(jobs)
    monkeypatch.setattr(runner, "_verify_worker_identity", lambda _job: None)
    monkeypatch.setattr(runner, "_read_primary_stage", lambda *_args, **_kwargs:
                        (_ for _ in ()).throw(RuntimeError("authenticated scheduling boundary")))
    monkeypatch.setattr(runner, "_fit_comparator_work", lambda *_args, **_kwargs:
                        (_ for _ in ()).throw(AssertionError("comparator fit executed")))
    with pytest.raises(RuntimeError, match="authenticated scheduling boundary"):
        runner._comparator_worker(jobs[0])


@pytest.mark.parametrize("partial_name", [
    ".incomplete-abc", ".features-incomplete-abc",
    ".features-import-incomplete-abc", "half.tmp",
])
def test_resume_refuses_interrupted_stage_files(tmp_path, monkeypatch, partial_name):
    env = SimpleNamespace(identity_sha256="a" * 64, source_revision="b" * 40,
                          registry_sha256="c" * 64, spec_sha256="d" * 64)
    monkeypatch.setattr(runner, "_preflight", lambda: (env, object()))
    monkeypatch.setattr(runner, "_committed_runner", lambda: "e" * 64)
    monkeypatch.setattr(runner, "authenticate_inputs", lambda *_args, **_kwargs:
                        SimpleNamespace(label_member_sha256="f" * 64))
    monkeypatch.setattr(runner, "RUN_ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPO", tmp_path)
    run_id = "20261018T100000000000Z_bbbbbbbb"
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    expected = {"run_id": run_id, "plan": runner._plan(env),
        "runner_sha256": "e" * 64,
        "historical_source_manifest_sha256": runner.SOURCE_SHA256,
        "canonical_release_manifest_sha256": runner.RELEASE_SHA256,
        "label_members": {"60": "f" * 64, "120": "f" * 64},
        "feature_end_exclusive": runner.iso(runner.FEATURE_STOP),
        "feature_materialization": {"feature_materialization_mode": "GENERATED_CURRENT"}}
    (run_dir / "run_manifest.json").write_text(runner.canonical_json(expected), encoding="utf-8")
    (run_dir / partial_name).write_bytes(b"partial")
    with pytest.raises(DevelopmentInputError, match="incomplete temporary stage"):
        runner._run(resume_id=run_id)


def _feature_reuse_fixture(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    run_root = repo / "runtime/lde_v1/development"
    producer_id = "20261018T112509949034Z_a4936aa1"
    producer_revision = "a" * 40
    producer_environment = "b" * 64
    artifact_bytes = b"exact-gzip-shaped-feature-bytes\x00\xff"
    artifact_sha = sha256(artifact_bytes).hexdigest()
    monkeypatch.setattr(runner, "REPO", repo)
    monkeypatch.setattr(runner, "RUN_ROOT", run_root)
    monkeypatch.setattr(runner, "PRODUCER_RUN_ID", producer_id)
    monkeypatch.setattr(runner, "PRODUCER_REVISION", producer_revision)
    monkeypatch.setattr(runner, "PRODUCER_ENVIRONMENT_SHA256", producer_environment)
    monkeypatch.setattr(runner, "PRODUCER_FEATURE_SHA256", artifact_sha)
    monkeypatch.setattr(runner, "PRODUCER_FEATURE_ROWS", 2)
    producer_runner = b"print('sealed producer runner')\n"
    monkeypatch.setattr(runner, "_git_bytes", lambda revision, relative: producer_runner)
    contract_identity = "c" * 64
    contract_descriptor = {
        "feature_watermark": "U = T - 1m", "provenance_mode": "EVENT_TIME_ONLY",
        "support_minutes": 1445, "target_fields": "ABSENT",
    }
    monkeypatch.setattr(runner, "_feature_contract_identity", lambda **_kwargs:
                        (contract_identity, contract_descriptor))
    env = SimpleNamespace(identity_sha256="d" * 64, source_revision="e" * 40,
                          registry_sha256="f" * 64, spec_sha256="1" * 64)
    source_contract = SimpleNamespace(corpus_id="synthetic-corpus",
        manifest_sha256=runner.SOURCE_SHA256, members=(
        SimpleNamespace(physical_symbol="BTCUSDT", declared_sha256="2" * 64),))
    producer_dir = run_root / producer_id
    producer_dir.mkdir(parents=True)
    artifact_name = f"features_{artifact_sha}.jsonl.gz"
    artifact_path = producer_dir / artifact_name
    artifact_path.write_bytes(artifact_bytes)
    manifest = {
        "run_id": producer_id,
        "plan": {"source_revision": producer_revision,
                 "environment_sha256": producer_environment,
                 "spec_id": runner.SPEC_ID, "spec_version": runner.SPEC_VERSION,
                 "feature_registry": runner.FEATURE_REGISTRY},
        "runner_sha256": sha256(producer_runner).hexdigest(),
        "historical_source_manifest_sha256": runner.SOURCE_SHA256,
        "feature_end_exclusive": runner.iso(runner.FEATURE_STOP),
    }
    manifest_path = producer_dir / "run_manifest.json"
    seal_path = producer_dir / f"{artifact_name}.seal.json"

    def write_manifest(value=manifest):
        manifest_path.write_text(runner.canonical_json(value), encoding="utf-8")
        monkeypatch.setattr(runner, "PRODUCER_RUN_MANIFEST_SHA256",
                            sha256(manifest_path.read_bytes()).hexdigest())

    seal = {
        "artifact": artifact_name, "sha256": artifact_sha,
        "parents": {"environment": producer_environment,
                    "runner": manifest["runner_sha256"], "source": runner.SOURCE_SHA256,
                    "registry": env.registry_sha256, "spec": env.spec_sha256,
                    "origin_range": runner.digest((runner.iso(runner.D0),
                                                    runner.iso(runner.FEATURE_STOP)))},
        "completed_at": "2026-10-18T11:25:09Z",
    }

    def write_seal(value=seal):
        seal_path.write_text(runner.canonical_json(value), encoding="utf-8")
        monkeypatch.setattr(runner, "PRODUCER_FEATURE_SEAL_SHA256",
                            sha256(seal_path.read_bytes()).hexdigest())

    write_manifest()
    write_seal()
    return SimpleNamespace(
        repo=repo, run_root=run_root, producer_id=producer_id, producer_dir=producer_dir,
        artifact_path=artifact_path, artifact_bytes=artifact_bytes, artifact_sha=artifact_sha,
        manifest=manifest, manifest_path=manifest_path, seal=seal, seal_path=seal_path,
        write_manifest=write_manifest, write_seal=write_seal, env=env,
        source_contract=source_contract, contract_identity=contract_identity,
    )


def _feature_worker_boundary(monkeypatch, *, repo, run_root, path, artifact_sha,
                             parents, label_sha="a" * 64):
    monkeypatch.setattr(runner, "REPO", repo)
    monkeypatch.setattr(runner, "RUN_ROOT", run_root)
    monkeypatch.setattr(runner, "_verify_worker_identity", lambda _job: None)
    monkeypatch.setattr(runner, "authenticate_inputs", lambda *_args, **_kwargs:
                        SimpleNamespace(label_member_sha256=label_sha))
    monkeypatch.setattr(runner, "_read_primary_stage", lambda *_args, **_kwargs:
                        (_ for _ in ()).throw(RuntimeError("authenticated feature boundary")))
    monkeypatch.setattr(runner, "_fit_comparator_work", lambda *_args, **_kwargs:
                        (_ for _ in ()).throw(AssertionError("comparator fit executed")))
    return runner.ComparatorJob(
        str(repo), str(path.parent), parents["runner"], str(path), artifact_sha,
        60, "F1", None, "b" * 64, parents["environment"], label_sha,
        tuple(sorted(parents.items())))


def test_reused_feature_worker_accepts_exact_imported_parents(tmp_path, monkeypatch):
    fixture = _feature_reuse_fixture(tmp_path, monkeypatch)
    evidence = runner._authenticate_feature_reuse(
        producer_run_id=fixture.producer_id, env=fixture.env,
        source_contract=fixture.source_contract)
    run_dir = fixture.run_root / "20261019T100000000000Z_eeeeeeee"
    run_dir.mkdir()
    base = {"environment": fixture.env.identity_sha256, "runner": "3" * 64,
            "source": runner.SOURCE_SHA256, "registry": fixture.env.registry_sha256,
            "spec": fixture.env.spec_sha256,
            "origin_range": runner.digest((runner.iso(runner.D0), runner.iso(runner.FEATURE_STOP)))}
    path, artifact_sha = runner._import_features(run_dir, evidence, base)
    parents = runner._feature_seal_parents(
        path, expected=runner._expected_feature_parents(base, evidence),
        artifact_sha=artifact_sha)
    assert parents == json.loads(path.with_name(path.name + ".seal.json").read_text())["parents"]
    job = _feature_worker_boundary(monkeypatch, repo=fixture.repo,
                                   run_root=fixture.run_root, path=path,
                                   artifact_sha=artifact_sha, parents=parents)
    with pytest.raises(RuntimeError, match="authenticated feature boundary"):
        runner._comparator_worker(job)


def test_generated_feature_worker_accepts_exact_generated_parents(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    run_root = repo / "runs"
    run_dir = run_root / "20261019T100000000000Z_eeeeeeee"
    run_dir.mkdir(parents=True)
    monkeypatch.setattr(runner, "_feature_rows_from_authenticated_sources",
                        lambda _inputs: iter(()))
    base = {"environment": "a" * 64, "runner": "b" * 64,
            "source": runner.SOURCE_SHA256, "registry": "c" * 64,
            "spec": "d" * 64,
            "origin_range": runner.digest((runner.iso(runner.D0),
                                           runner.iso(runner.FEATURE_STOP)))}
    path, artifact_sha = runner._materialize_features(run_dir, object(), base)
    parents = runner._feature_seal_parents(path, expected=base, artifact_sha=artifact_sha)
    assert parents == base
    job = _feature_worker_boundary(monkeypatch, repo=repo, run_root=run_root,
                                   path=path, artifact_sha=artifact_sha, parents=parents)
    with pytest.raises(RuntimeError, match="authenticated feature boundary"):
        runner._comparator_worker(job)
    (run_dir / "run_manifest.json").write_text(runner.canonical_json({
        "run_id": run_dir.name, "runner_sha256": base["runner"],
        "plan": {"environment_sha256": base["environment"],
                 "registry_sha256": base["registry"], "spec_sha256": base["spec"]},
        "feature_materialization": {"feature_materialization_mode": "GENERATED_CURRENT"},
    }), encoding="utf-8")
    assert runner._status(run_dir.name)["hash_verified_files"][path.name] == artifact_sha
    seal_path = path.with_name(path.name + ".seal.json")
    seal = json.loads(seal_path.read_text())
    seal["parents"]["runner"] = "0" * 64
    seal_path.write_text(runner.canonical_json(seal), encoding="utf-8")
    with pytest.raises(DevelopmentInputError, match="stage seal mismatch"):
        runner._status(run_dir.name)


@pytest.mark.parametrize("changed_parent", [
    "missing_reuse", "producer_run_manifest", "producer_feature_seal",
    "producer_feature_artifact", "feature_contract", "environment",
])
def test_reused_feature_worker_rejects_inexact_parents(tmp_path, monkeypatch,
                                                        changed_parent):
    fixture = _feature_reuse_fixture(tmp_path, monkeypatch)
    evidence = runner._authenticate_feature_reuse(
        producer_run_id=fixture.producer_id, env=fixture.env,
        source_contract=fixture.source_contract)
    run_dir = fixture.run_root / "20261019T100000000000Z_eeeeeeee"
    run_dir.mkdir()
    base = {"environment": fixture.env.identity_sha256, "runner": "3" * 64,
            "source": runner.SOURCE_SHA256, "registry": fixture.env.registry_sha256,
            "spec": fixture.env.spec_sha256,
            "origin_range": runner.digest((runner.iso(runner.D0), runner.iso(runner.FEATURE_STOP)))}
    path, artifact_sha = runner._import_features(run_dir, evidence, base)
    parents = runner._feature_seal_parents(
        path, expected=runner._expected_feature_parents(base, evidence),
        artifact_sha=artifact_sha)
    altered = dict(parents)
    if changed_parent == "missing_reuse":
        altered.pop("producer_run_manifest")
    else:
        altered[changed_parent] = "0" * 64
    job = _feature_worker_boundary(monkeypatch, repo=fixture.repo,
                                   run_root=fixture.run_root, path=path,
                                   artifact_sha=artifact_sha, parents=altered)
    with pytest.raises(DevelopmentInputError, match="stage seal mismatch"):
        runner._comparator_worker(job)


@pytest.mark.parametrize("reuse", [False, True])
def test_run_passes_current_run_exact_seal_parents_to_preparation(tmp_path, monkeypatch,
                                                                   reuse):
    fixture = _feature_reuse_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(runner, "_preflight", lambda: (fixture.env, object()))
    monkeypatch.setattr(runner, "_committed_runner", lambda: "3" * 64)
    inputs = SimpleNamespace(label_member_sha256="a" * 64,
                             source_contract=fixture.source_contract)
    monkeypatch.setattr(runner, "authenticate_inputs", lambda *_args, **_kwargs: inputs)
    monkeypatch.setattr(runner, "_feature_rows_from_authenticated_sources",
                        lambda _inputs: iter(()))
    captured = []

    def capture_prepare(**kwargs):
        path = kwargs["feature_path"]
        seal = json.loads(path.with_name(path.name + ".seal.json").read_text())
        assert kwargs["feature_parents"] == seal["parents"]
        assert runner._feature_seal_parents(
            path, expected=kwargs["feature_parents"],
            artifact_sha=kwargs["feature_sha"]) == seal["parents"]
        captured.append(tuple(sorted(kwargs["feature_parents"].items())))
        return None

    monkeypatch.setattr(runner, "_prepare_horizon_stages", capture_prepare)
    monkeypatch.setattr(runner, "_prepare_independent_horizons",
                        lambda prepare: (prepare(60) or {}, (), None))
    monkeypatch.setattr(runner, "_schedule_comparator_jobs",
                        lambda jobs, *, workers: ({}, {}))
    runner._run(reuse_features_from_run=fixture.producer_id if reuse else None)
    assert len(captured) == 1
    assert len(captured[0]) == (11 if reuse else 6)


def test_authenticated_feature_reuse_accepts_exact_producer_and_imports_exact_bytes(
        tmp_path, monkeypatch):
    fixture = _feature_reuse_fixture(tmp_path, monkeypatch)
    evidence = runner._authenticate_feature_reuse(
        producer_run_id=fixture.producer_id, env=fixture.env,
        source_contract=fixture.source_contract)
    assert evidence["compatibility_verdict"] == "PASS"
    assert evidence["producer_feature_sha256"] == fixture.artifact_sha
    assert evidence["feature_contract"]["target_fields"] == "ABSENT"
    new_run = fixture.run_root / "20261019T100000000000Z_eeeeeeee"
    new_run.mkdir()
    parents = {"environment": fixture.env.identity_sha256, "runner": "3" * 64,
               "source": runner.SOURCE_SHA256, "registry": fixture.env.registry_sha256,
               "spec": fixture.env.spec_sha256,
               "origin_range": runner.digest((runner.iso(runner.D0), runner.iso(runner.FEATURE_STOP)))}
    imported, imported_sha = runner._import_features(new_run, evidence, parents)
    assert imported.read_bytes() == fixture.artifact_bytes
    assert imported_sha == fixture.artifact_sha
    imported_seal = json.loads(imported.with_name(imported.name + ".seal.json").read_text())
    assert imported_seal["parents"]["producer_run_manifest"] == \
        evidence["producer_run_manifest_sha256"]
    assert imported_seal["parents"]["producer_feature_seal"] == \
        evidence["producer_feature_seal_sha256"]
    assert imported_seal["parents"]["feature_contract"] == fixture.contract_identity
    assert not any(path.name.startswith("E60_F1") for path in new_run.iterdir())
    assert "E60" not in imported.name and "E120" not in imported.name
    assert runner._import_features(new_run, evidence, parents) == (imported, imported_sha)
    manifest_evidence = {key: value for key, value in evidence.items()
                         if key != "producer_artifact_path"}
    (new_run / "run_manifest.json").write_text(runner.canonical_json({
        "run_id": new_run.name,
        "runner_sha256": parents["runner"],
        "plan": {"environment_sha256": fixture.env.identity_sha256,
                 "source_revision": fixture.env.source_revision,
                 "registry_sha256": fixture.env.registry_sha256,
                 "spec_sha256": fixture.env.spec_sha256},
        "feature_materialization": manifest_evidence,
    }), encoding="utf-8")
    seen_parents = []
    original_feature_seal_parents = runner._feature_seal_parents

    def capture_status_parents(path, *, expected, artifact_sha):
        actual = original_feature_seal_parents(
            path, expected=expected, artifact_sha=artifact_sha)
        seen_parents.append(actual)
        return actual

    monkeypatch.setattr(runner, "_feature_seal_parents", capture_status_parents)
    status = runner._status(new_run.name)
    assert status["feature_materialization_mode"] == "REUSED_AUTHENTICATED"
    assert status["hash_verified_files"][imported.name] == fixture.artifact_sha
    assert seen_parents == [imported_seal["parents"]]
    missing_contract = dict(manifest_evidence)
    missing_contract.pop("current_feature_contract_identity")
    with pytest.raises(DevelopmentInputError, match="missing or invalid feature reuse parent"):
        runner._expected_feature_parents(parents, missing_contract)
    imported_seal["parents"].pop("producer_feature_seal")
    imported.with_name(imported.name + ".seal.json").write_text(
        runner.canonical_json(imported_seal), encoding="utf-8")
    with pytest.raises(DevelopmentInputError, match="stage seal mismatch"):
        runner._status(new_run.name)


@pytest.mark.parametrize("failure", [
    "wrong_feature", "missing_seal", "modified_seal", "wrong_manifest",
    "wrong_source", "wrong_registry", "wrong_spec", "wrong_origin",
])
def test_authenticated_feature_reuse_rejects_tampered_evidence(
        tmp_path, monkeypatch, failure):
    fixture = _feature_reuse_fixture(tmp_path, monkeypatch)
    if failure == "wrong_feature":
        fixture.artifact_path.write_bytes(fixture.artifact_bytes + b"x")
    elif failure == "missing_seal":
        fixture.seal_path.unlink()
    elif failure == "modified_seal":
        fixture.seal_path.write_bytes(fixture.seal_path.read_bytes() + b" ")
    elif failure == "wrong_manifest":
        fixture.manifest_path.write_bytes(fixture.manifest_path.read_bytes() + b" ")
    elif failure == "wrong_source":
        fixture.manifest["historical_source_manifest_sha256"] = "9" * 64
        fixture.write_manifest()
    elif failure == "wrong_registry":
        fixture.seal["parents"]["registry"] = "9" * 64
        fixture.write_seal()
    elif failure == "wrong_spec":
        fixture.seal["parents"]["spec"] = "9" * 64
        fixture.write_seal()
    elif failure == "wrong_origin":
        fixture.seal["parents"]["origin_range"] = "9" * 64
        fixture.write_seal()
    with pytest.raises(DevelopmentInputError):
        runner._authenticate_feature_reuse(
            producer_run_id=fixture.producer_id, env=fixture.env,
            source_contract=fixture.source_contract)


def test_feature_reuse_rejects_contract_change_but_ignores_comparator_only_change(
        tmp_path, monkeypatch):
    feature_contract_identity = runner._feature_contract_identity
    fixture = _feature_reuse_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(runner, "_feature_contract_identity", lambda **_kwargs:
                        (_ for _ in ()).throw(DevelopmentInputError(
                            "feature-generation code contract changed")))
    with pytest.raises(DevelopmentInputError, match="feature-generation code contract changed"):
        runner._authenticate_feature_reuse(
            producer_run_id=fixture.producer_id, env=fixture.env,
            source_contract=fixture.source_contract)

    function_source = ("\n".join(f"def {name}():\n    return 1"
                                   for name in runner.FEATURE_RUNNER_FUNCTIONS) + "\n").encode()
    feature_bytes = b"same feature code\n"
    def git_bytes(revision, relative):
        if relative == "tools/lde_v1/run_development_study.py":
            return function_source
        assert relative in runner.FEATURE_CODE_FILES
        return feature_bytes
    monkeypatch.setattr(runner, "_git_bytes", git_bytes)
    monkeypatch.setattr(runner, "_feature_contract_identity", feature_contract_identity)
    identity, descriptor = feature_contract_identity(
        producer_revision="a" * 40, current_revision="b" * 40,
        source_contract=fixture.source_contract, spec_sha256="1" * 64,
        registry_sha256="f" * 64)
    assert len(identity) == 64 and descriptor["target_fields"] == "ABSENT"

    def changed_git_bytes(revision, relative):
        data = git_bytes(revision, relative)
        if revision == "b" * 40 and relative == runner.FEATURE_CODE_FILES[0]:
            return data + b"changed"
        return data
    monkeypatch.setattr(runner, "_git_bytes", changed_git_bytes)
    with pytest.raises(DevelopmentInputError, match="feature-generation code contract changed"):
        feature_contract_identity(
            producer_revision="a" * 40, current_revision="b" * 40,
            source_contract=fixture.source_contract, spec_sha256="1" * 64,
            registry_sha256="f" * 64)


def test_feature_import_rejects_overwrite_and_redirected_producer(tmp_path, monkeypatch):
    fixture = _feature_reuse_fixture(tmp_path, monkeypatch)
    evidence = runner._authenticate_feature_reuse(
        producer_run_id=fixture.producer_id, env=fixture.env,
        source_contract=fixture.source_contract)
    new_run = fixture.run_root / "20261019T100000000000Z_eeeeeeee"
    new_run.mkdir()
    final = new_run / f"features_{fixture.artifact_sha}.jsonl.gz"
    final.write_bytes(b"different")
    with pytest.raises(DevelopmentInputError, match="partial stage|cannot be overwritten"):
        runner._import_features(new_run, evidence, {})

    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path:
                        path == fixture.artifact_path or original_is_symlink(path))
    with pytest.raises(DevelopmentInputError, match="redirected evidence path"):
        runner._authenticate_feature_reuse(
            producer_run_id=fixture.producer_id, env=fixture.env,
            source_contract=fixture.source_contract)


def test_reuse_dry_run_is_explicit_read_only_and_new_run_id(tmp_path, monkeypatch):
    env = SimpleNamespace(identity_sha256="a" * 64, source_revision="b" * 40,
                          registry_sha256="c" * 64, spec_sha256="d" * 64)
    monkeypatch.setattr(runner, "_preflight", lambda: (env, object()))
    monkeypatch.setattr(runner, "RUN_ROOT", tmp_path / "uncreated")
    monkeypatch.setattr(runner, "authenticate_inputs", lambda *_args, **_kwargs:
                        SimpleNamespace(source_contract=object()))
    calls = []
    monkeypatch.setattr(runner, "_authenticate_feature_reuse", lambda **kwargs:
                        calls.append(kwargs) or {"compatibility_verdict": "PASS"})
    result = runner.dry_run(reuse_features_from_run=runner.PRODUCER_RUN_ID)
    assert calls and result["feature_reuse"]["compatibility_verdict"] == "PASS"
    assert runner.PRODUCER_RUN_ID not in result["would_create"]
    assert not runner.RUN_ROOT.exists()


def test_old_interrupted_run_cannot_resume_under_changed_manifest(tmp_path, monkeypatch):
    env = SimpleNamespace(identity_sha256="a" * 64, source_revision="new" + "b" * 37,
                          registry_sha256="c" * 64, spec_sha256="d" * 64)
    monkeypatch.setattr(runner, "_preflight", lambda: (env, object()))
    monkeypatch.setattr(runner, "_committed_runner", lambda: "e" * 64)
    inputs = SimpleNamespace(label_member_sha256="f" * 64, source_contract=object())
    monkeypatch.setattr(runner, "authenticate_inputs", lambda *_args, **_kwargs: inputs)
    monkeypatch.setattr(runner, "RUN_ROOT", tmp_path)
    monkeypatch.setattr(runner, "REPO", tmp_path)
    old = tmp_path / runner.PRODUCER_RUN_ID
    old.mkdir()
    (old / "run_manifest.json").write_text(runner.canonical_json({
        "run_id": runner.PRODUCER_RUN_ID,
        "plan": {"source_revision": runner.PRODUCER_REVISION},
    }), encoding="utf-8")
    with pytest.raises(DevelopmentInputError, match="resume run manifest/parent identity mismatch"):
        runner._run(resume_id=runner.PRODUCER_RUN_ID)


def test_status_rejects_seal_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "REPO", tmp_path)
    monkeypatch.setattr(runner, "RUN_ROOT", tmp_path / "runs")
    run_id = "20261018T100000000000Z_bbbbbbbb"
    run_dir = runner.RUN_ROOT / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(json.dumps({
        "run_id": run_id, "plan": {"environment_sha256": "a" * 64},
    }), encoding="utf-8")
    (run_dir / "fold.json.seal.json").write_text(json.dumps({
        "artifact": "../outside.json", "sha256": "b" * 64,
    }), encoding="utf-8")
    with pytest.raises(DevelopmentInputError, match="invalid run artifact identity"):
        runner._status(run_id)


def test_run_root_and_run_directory_reject_redirected_paths(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    link = repo / "redirected"
    link.mkdir()
    original_is_symlink = Path.is_symlink
    redirected = {link}
    monkeypatch.setattr(Path, "is_symlink", lambda path:
                        path in redirected or original_is_symlink(path))
    monkeypatch.setattr(runner, "REPO", repo)
    run_id = "20261018T100000000000Z_bbbbbbbb"
    monkeypatch.setattr(runner, "RUN_ROOT", link)
    with pytest.raises(DevelopmentInputError, match="redirected evidence path"):
        runner._status(run_id)
    actual_root = repo / "runtime"
    actual_root.mkdir()
    redirected.add(actual_root / run_id)
    (actual_root / run_id).mkdir()
    monkeypatch.setattr(runner, "RUN_ROOT", actual_root)
    with pytest.raises(DevelopmentInputError, match="redirected evidence path"):
        runner._status(run_id)


def test_sealed_read_rejects_redirected_parent(tmp_path, monkeypatch):
    link = tmp_path / "redirected"
    link.mkdir()
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path:
                        path == link or original_is_symlink(path))
    with pytest.raises(DevelopmentInputError, match="redirected evidence path"):
        runner._sealed_read(link / "fold.json", parents={})


def test_sealed_read_and_status_reject_reparse_artifact_leaves(tmp_path, monkeypatch):
    monkeypatch.setattr(runner, "REPO", tmp_path)
    monkeypatch.setattr(runner, "RUN_ROOT", tmp_path / "runs")
    run_id = "20261018T100000000000Z_bbbbbbbb"
    run_dir = runner.RUN_ROOT / run_id
    run_dir.mkdir(parents=True)
    (run_dir / "run_manifest.json").write_text(json.dumps({
        "run_id": run_id, "plan": {"environment_sha256": "a" * 64},
    }), encoding="utf-8")
    artifact = run_dir / "fold.json"
    runner._sealed_write(artifact, b"exact", parents={})
    original_lstat = Path.lstat

    def reparse_lstat(path):
        result = original_lstat(path)
        if path == artifact:
            return SimpleNamespace(st_mode=result.st_mode, st_file_attributes=0x400)
        return result

    monkeypatch.setattr(Path, "lstat", reparse_lstat)
    with pytest.raises(DevelopmentInputError, match="redirected evidence path"):
        runner._sealed_read(artifact, parents={})
    with pytest.raises(DevelopmentInputError, match="redirected evidence path"):
        runner._status(run_id)


def test_pre_run_ledger_reference_is_sealed_and_resume_checks_identity(tmp_path, monkeypatch):
    run_id = "20261018T100000000000Z_bbbbbbbb"
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    (run_dir / "run_manifest.json").write_text(json.dumps({
        "run_id": run_id, "runner_sha256": "e" * 64,
        "plan": {"environment_sha256": "a" * 64, "source_revision": "b" * 40},
    }), encoding="utf-8")
    env = SimpleNamespace(identity_sha256="a" * 64, source_revision="b" * 40)
    monkeypatch.setattr(runner.DevelopmentPreRunRegistration, "from_environment",
                        staticmethod(lambda _env: SimpleNamespace(identity_sha256="c" * 64)))
    entry = SimpleNamespace(entry_sha256="d" * 64)
    identity = runner._preserve_registration(
        run_dir=run_dir, env=env, runner_sha="e" * 64, horizon=60, entry=entry)
    assert identity == sha256((run_dir / "E60_pre_run_ledger.json").read_bytes()).hexdigest()
    assert runner._preserve_registration(
        run_dir=run_dir, env=env, runner_sha="e" * 64, horizon=60, entry=entry) == identity
    monkeypatch.setattr(runner, "REPO", tmp_path)
    monkeypatch.setattr(runner, "RUN_ROOT", tmp_path)
    monkeypatch.setattr(runner, "LEDGER_ROOT", tmp_path / "ledger")
    good_entry = SimpleNamespace(entry_sha256="d" * 64, horizon_minutes=60,
                                 action="DEVELOPMENT_PREFLIGHT_REGISTERED",
                                 artifact_hashes=(("pre_run_registration", "c" * 64),),
                                 code_revision_or_hash="b" * 40)
    monkeypatch.setattr(runner, "ExperimentLedger", lambda *_args:
                        SimpleNamespace(read_all=lambda: (good_entry,)))
    assert runner._status(run_id)["pre_run_ledger_entries"] == {"60": "d" * 64}
    assert runner._status(run_id)["dossier_files_present_and_hashed"] is False
    other_entry = SimpleNamespace(**{**vars(good_entry), "entry_sha256": "e" * 64})
    monkeypatch.setattr(runner, "ExperimentLedger", lambda *_args:
                        SimpleNamespace(read_all=lambda: (other_entry, good_entry)))
    assert runner._status(run_id)["pre_run_ledger_entries"] == {"60": "d" * 64}
    monkeypatch.setattr(runner, "ExperimentLedger", lambda *_args:
                        SimpleNamespace(read_all=lambda: (other_entry,)))
    with pytest.raises(DevelopmentInputError, match="ledger entry missing"):
        runner._status(run_id)
    bad_entry = SimpleNamespace(entry_sha256="d" * 64, horizon_minutes=60,
                                action="DEVELOPMENT_PREFLIGHT_REGISTERED",
                                artifact_hashes=(("pre_run_registration", "f" * 64),),
                                code_revision_or_hash="b" * 40)
    monkeypatch.setattr(runner, "ExperimentLedger", lambda *_args:
                        SimpleNamespace(read_all=lambda: (bad_entry,)))
    with pytest.raises(DevelopmentInputError, match="ledger entry missing"):
        runner._status(run_id)
    monkeypatch.setattr(runner, "ExperimentLedger", lambda *_args:
                        SimpleNamespace(read_all=lambda: (good_entry,)))
    runner._sealed_write(run_dir / "E60_F1.json.gz", b"fold", parents={
        "pre_run_registration": "f" * 64,
    })
    with pytest.raises(DevelopmentInputError, match="registration parent mismatch"):
        runner._status(run_id)
    monkeypatch.setattr(runner, "ExperimentLedger", lambda *_args:
                        SimpleNamespace(read_all=lambda: ()))
    with pytest.raises(DevelopmentInputError, match="ledger entry missing"):
        runner._status(run_id)
    with pytest.raises(DevelopmentInputError, match="stage seal mismatch"):
        runner._preserve_registration(
            run_dir=run_dir, env=env, runner_sha="e" * 64, horizon=60,
            entry=SimpleNamespace(entry_sha256="f" * 64))


def _registration_fixture(revision: str, *, configuration: str = "a" * 64):
    return DevelopmentPreRunRegistration(
        spec_id=runner.SPEC_ID, spec_version=runner.SPEC_VERSION,
        spec_sha256="b" * 64, source_revision=revision,
        registry_sha256="c" * 64, dependency_lock_sha256="d" * 64,
        serializer_environment_sha256="e" * 64,
        historical_source_manifest_sha256="f" * 64,
        canonical_release_manifest_sha256="1" * 64,
        architecture_sha256="2" * 64, configuration_sha256=configuration,
        freeze_sha256="3" * 64, harness_sha256="4" * 64,
        h1_governance_status="CLEANLINESS_UNVERIFIED",
        h1_not_used_for_fitting=True, prospective_not_used_for_fitting=True)


@pytest.mark.parametrize("prior_revisions,include_current", [
    ((), False),
    ((), True),
    (("a" * 40,), False),
    (("a" * 40, "b" * 40), False),
    (("a" * 40,), True),
])
def test_registration_revision_scope_and_append_only(
        tmp_path, monkeypatch, prior_revisions, include_current):
    root = tmp_path / "ledger"
    monkeypatch.setattr(runner, "LEDGER_ROOT", root)
    current = _registration_fixture("c" * 40)
    for revision in prior_revisions:
        _registration_fixture(revision).append_to(
            ExperimentLedger(root), horizon_minutes=60, actor="test")
    exact = (current.append_to(ExperimentLedger(root), horizon_minutes=60,
                               actor="test") if include_current else None)
    before = {path.name: path.read_bytes() for path in root.glob("*.json")}
    monkeypatch.setattr(runner.DevelopmentPreRunRegistration, "from_environment",
                        staticmethod(lambda _env: current))
    selected = runner._registration(SimpleNamespace(source_revision=current.source_revision), 60)
    after = {path.name: path.read_bytes() for path in root.glob("*.json")}
    assert all(after[name] == contents for name, contents in before.items())
    assert len(after) == len(before) + (0 if include_current else 1)
    assert selected.code_revision_or_hash == current.source_revision
    assert dict(selected.artifact_hashes)["pre_run_registration"] == current.identity_sha256
    if exact is not None:
        assert selected.entry_sha256 == exact.entry_sha256
    else:
        assert selected.entry_sha256 == ExperimentLedger(root).read_all()[-1].entry_sha256


def test_duplicate_current_registration_fails_closed_without_ledger_mutation(tmp_path, monkeypatch):
    root = tmp_path / "ledger"
    monkeypatch.setattr(runner, "LEDGER_ROOT", root)
    current = _registration_fixture("c" * 40)
    for _ in range(2):
        current.append_to(ExperimentLedger(root), horizon_minutes=60, actor="test")
    before = {path.name: path.read_bytes() for path in root.glob("*.json")}
    monkeypatch.setattr(runner.DevelopmentPreRunRegistration, "from_environment",
                        staticmethod(lambda _env: current))
    with pytest.raises(DevelopmentInputError, match="duplicate permanent pre-run registration"):
        runner._registration(SimpleNamespace(source_revision=current.source_revision), 60)
    assert before == {path.name: path.read_bytes() for path in root.glob("*.json")}


def test_same_revision_conflicting_registration_fails_closed_without_ledger_mutation(
        tmp_path, monkeypatch):
    root = tmp_path / "ledger"
    monkeypatch.setattr(runner, "LEDGER_ROOT", root)
    current = _registration_fixture("c" * 40)
    conflicting = replace(current, configuration_sha256="9" * 64)
    conflicting.append_to(ExperimentLedger(root), horizon_minutes=60, actor="test")
    before = {path.name: path.read_bytes() for path in root.glob("*.json")}
    monkeypatch.setattr(runner.DevelopmentPreRunRegistration, "from_environment",
                        staticmethod(lambda _env: current))
    with pytest.raises(DevelopmentInputError, match="conflicting permanent pre-run registration"):
        runner._registration(SimpleNamespace(source_revision=current.source_revision), 60)
    assert before == {path.name: path.read_bytes() for path in root.glob("*.json")}


def test_retained_pre_run_ledger_is_read_only_historical_evidence(tmp_path, monkeypatch):
    root = runner.REPO / "runtime/lde_v1/development/experiment_ledger"
    if not root.is_dir():
        pytest.skip("retained local ledger unavailable")
    before = {path.name: path.read_bytes() for path in root.glob("*.json")}
    entries = ExperimentLedger(root).read_all()
    assert any(entry.action == "DEVELOPMENT_PREFLIGHT_REGISTERED" and
               entry.horizon_minutes == 60 and
               entry.fit_or_cohort_id == "F1_F5_DEVELOPMENT" and
               entry.code_revision_or_hash == runner.PRODUCER_REVISION
               for entry in entries)
    copied_root = tmp_path / "ledger-copy"
    copied_root.mkdir()
    for name, contents in before.items():
        (copied_root / name).write_bytes(contents)
    monkeypatch.setattr(runner, "LEDGER_ROOT", copied_root)
    current = _registration_fixture("c" * 40)
    monkeypatch.setattr(runner.DevelopmentPreRunRegistration, "from_environment",
                        staticmethod(lambda _env: current))
    selected = runner._registration(SimpleNamespace(source_revision=current.source_revision), 60)
    assert selected.sequence == len(entries) + 1
    assert selected.code_revision_or_hash == current.source_revision
    assert before == {path.name: path.read_bytes() for path in root.glob("*.json")}


def test_historical_evaluation_record_roundtrip_without_asof_claim():
    t = datetime(2025, 4, 1, 2, tzinfo=UTC)
    unavailable = SimpleNamespace(prediction_origin=t, physical_symbol="BTCUSDT",
        target_status="UNAVAILABLE", canonical_class=None, target_reason="NO_TARGET",
        feature_reasons=("MISSING_REQUIRED_MINUTE",), feature_status="UNAVAILABLE")
    row = runner._evaluation_record(row=unavailable, score=None, fit_id="F1", horizon=60)
    restored = runner._restore_record(runner._wire(row))
    assert restored == row
    assert restored.prediction.provenance_mode == "EVENT_TIME_ONLY"
    assert not restored.prediction.emitted and restored.truth.target_status == "UNAVAILABLE"


def test_scored_record_roundtrip_uses_sealed_primary_and_baselines():
    t = datetime(2025, 4, 1, 2, tzinfo=UTC)
    valid = SimpleNamespace(prediction_origin=t, physical_symbol="BTCUSDT",
        target_status="VALID", canonical_class="NO_DIRECTION", target_reason=None,
        feature_reasons=(), feature_status="AVAILABLE")
    probabilities = (1 / 3, 1 / 3, 1 / 3)
    from math import log
    state = SimpleNamespace(probabilities=probabilities,
                            log_probabilities=(log(1 / 3),) * 3,
                            logits=(0.0, 0.0, 0.0))
    score = SimpleNamespace(bundle_sha256="a" * 64, raw=state, calibrated=state,
        b0_hard_class="NO_DIRECTION", b1_probabilities=probabilities,
        b2_hard_class="NO_DIRECTION", b3_probabilities=probabilities)
    row = runner._evaluation_record(row=valid, score=score, fit_id="F1", horizon=60)
    assert row.matched and row.prediction.emitted
    assert runner._restore_record(runner._wire(row)) == row


def test_source_stream_one_origin_keeps_feature_target_firewall(tmp_path, monkeypatch):
    origin = datetime(2024, 10, 2, tzinfo=UTC)
    first = origin - timedelta(minutes=1446)
    root = tmp_path / "runtime/data/direction-regime-history"
    root.mkdir(parents=True)
    members = []
    for symbol in runner.SYMBOLS:
        logical = "PEPEUSDT" if symbol == "1000PEPEUSDT" else symbol
        header = "open_time,close_time,symbol,logical_symbol,category,timeframe,open,high,low,close,volume,turnover\n"
        lines = []
        for i in range(1445):
            t = first + i * timedelta(minutes=1)
            stamp = t.isoformat().replace("+00:00", "Z")
            close = (t + timedelta(minutes=1)).isoformat().replace("+00:00", "Z")
            price = 100 + i * .001
            lines.append(f"{stamp},{close},{symbol},{logical},linear,1m,{price},{price+.1},{price-.1},{price},0,0\n")
        path = root / f"{symbol}_1m.csv.gz"
        path.write_bytes(gzip.compress((header + "".join(lines)).encode(), mtime=0))
        members.append(HistoricalMember(symbol, logical,
            f"runtime/data/direction-regime-history/{symbol}_1m.csv.gz",
            sha256(path.read_bytes()).hexdigest(), 1445,
            first.isoformat().replace("+00:00", "Z"),
            (first + timedelta(minutes=1445)).isoformat().replace("+00:00", "Z")))
    contract = HistoricalSourceContract("fixture", "a" * 64, "fixture-complete", tuple(members))
    inputs = AuthenticatedInputs(contract, "b" * 64, "c" * 64, 60, root, tmp_path / "no-label.parquet")
    monkeypatch.setattr(runner, "REPO", tmp_path)
    monkeypatch.setattr(runner, "D0", origin)
    monkeypatch.setattr(runner, "FEATURE_STOP", origin + timedelta(minutes=5))
    features = tuple(runner._feature_rows_from_authenticated_sources(inputs))
    assert len(features) == 4
    assert all(f.row is not None and f.row.feature_timestamp == origin - timedelta(minutes=1)
               for f in features)
    assert all(f.trailing_sign_60 is not None and f.trailing_sign_120 is not None for f in features)
    assert not inputs.label_file.exists()


def test_tiny_fold_wires_primary_comparator_shadow_and_resume(tmp_path, monkeypatch):
    from triggertrade.live_direction_estimator_v1.calendar import (
        D0, FIT_DEFINITIONS, FOLDS, FoldDefinition, SegmentDefinition,
    )
    from triggertrade.live_direction_estimator_v1.features import RawFeatureRow
    from triggertrade.live_direction_estimator_v1.model import CLASSES
    from triggertrade.live_direction_estimator_v1.manifests import feature_row_identity
    from triggertrade.live_direction_estimator_v1.development_readiness import (
        CanonicalTarget, FeatureAssembly,
    )
    c, v = FOLDS[0].calibration.nominal_start, FOLDS[0].score.nominal_start
    fold = FoldDefinition("F1", FOLDS[0].base, FOLDS[0].calibration,
        SegmentDefinition("SCORE", v, v + timedelta(minutes=245), True, True))
    monkeypatch.setitem(FIT_DEFINITIONS, "F1", fold)
    rows = []
    targets = {}
    for si, symbol in enumerate(runner.SYMBOLS):
        for ci in range(3):
            rows.append((symbol, D0 + timedelta(days=2, minutes=5 * (3 * si + ci)),
                         CLASSES[ci], ci - 1, si * .07 + ci * .03))
        rows.append((symbol, c + timedelta(minutes=120 + si * 5),
                     CLASSES[si % 3], si % 3 - 1, .11 + si * .04))
        rows.append((symbol, v + timedelta(minutes=120),
                     CLASSES[si % 3], si % 3 - 1, .14 + si * .04))
    features = []
    for symbol, t, label, sign, value in sorted(rows, key=lambda x: (x[1], runner.SYMBOLS.index(x[0]))):
        values = [0.1 * (j + 1) + value for j in range(32)]
        values[3] = sign * (0.1 + abs(value))
        values[14] = 0.0
        values[30:32] = (0.0, 1.0)
        values += [float(symbol == s) for s in runner.SYMBOLS[1:]]
        raw = RawFeatureRow(symbol, t, t - timedelta(minutes=1),
                            f"synthetic:{symbol}:{t.isoformat()}:{value}", tuple(values))
        features.append(FeatureAssembly(symbol, t, raw, (), raw.source_snapshot_id, sign, sign))
        targets[(symbol, t, 60)] = CanonicalTarget(symbol, t, 60, "VALID", label, None)
    feature_path = tmp_path / "synthetic_features.jsonl.gz"
    with gzip.open(feature_path, "wt", encoding="utf-8") as stream:
        for feature in features:
            stream.write(runner.canonical_json(runner._feature_wire(feature)) + "\n")
    members = tuple(HistoricalMember(symbol, "PEPEUSDT" if symbol == "1000PEPEUSDT" else symbol,
        f"{symbol}.csv.gz", "a" * 64, 1445, "2024-10-01T00:00:00Z",
        "2024-10-03T00:00:00Z", True) for symbol in runner.SYMBOLS)
    contract = HistoricalSourceContract("fixture", "b" * 64, "fixture-complete", members)
    inputs = AuthenticatedInputs(contract, "c" * 64, "d" * 64, 60,
                                 tmp_path, tmp_path / "not-opened.parquet")
    run_id = "20261018T100000000000Z_ba64f4bc"
    run_dir = tmp_path / run_id
    run_dir.mkdir()
    monkeypatch.setattr(runner, "LEDGER_ROOT", tmp_path / "ledger")
    env = SimpleNamespace(identity_sha256="e" * 64, source_revision="f" * 40)
    primary_path, primary_sha = runner._prepare_primary_stage(
        run_dir=run_dir, env=env, runner_sha="1" * 64, feature_path=feature_path,
        feature_sha=sha256(feature_path.read_bytes()).hexdigest(), inputs=inputs,
        targets=targets, fold=fold, horizon=60)
    assert primary_path.is_file() and len(primary_sha) == 64
    assert not (run_dir / "E60_F1.json.gz").exists()
    original_fit_pipeline = runner.fit_pipeline
    monkeypatch.setattr(runner, "fit_pipeline", lambda **_kwargs:
                        (_ for _ in ()).throw(AssertionError("sealed primary was recomputed")))
    assert runner._prepare_primary_stage(
        run_dir=run_dir, env=env, runner_sha="1" * 64, feature_path=feature_path,
        feature_sha=sha256(feature_path.read_bytes()).hexdigest(), inputs=inputs,
        targets=targets, fold=fold, horizon=60)[1] == primary_sha
    monkeypatch.setattr(runner, "fit_pipeline", original_fit_pipeline)
    phase = runner._fold_stage(run_dir=run_dir, env=env, runner_sha="1" * 64,
        feature_path=feature_path, feature_sha=sha256(feature_path.read_bytes()).hexdigest(),
        inputs=inputs, targets=targets, fold=fold, horizon=60)
    assert len(phase.positions) == 1 and len(phase.records) == 4
    assert all(record.matched for record in phase.records)
    persisted = json.loads(gzip.decompress((run_dir / "E60_F1.json.gz").read_bytes()))
    assert len(persisted["primary_scores"]) == len(persisted["comparator_scores"]) == len(persisted["shadow_scores"]) == 4
    before = (run_dir / "E60_F1.json.gz").read_bytes()
    reused = runner._fold_stage(run_dir=run_dir, env=env, runner_sha="1" * 64,
        feature_path=feature_path, feature_sha=sha256(feature_path.read_bytes()).hexdigest(),
        inputs=inputs, targets=targets, fold=fold, horizon=60)
    assert reused == phase and (run_dir / "E60_F1.json.gz").read_bytes() == before
    failed_run = tmp_path / "20261018T100001000000Z_ba64f4bc"
    failed_run.mkdir()
    failed_primary, failed_primary_sha = runner._prepare_primary_stage(
        run_dir=failed_run, env=env, runner_sha="1" * 64, feature_path=feature_path,
        feature_sha=sha256(feature_path.read_bytes()).hexdigest(), inputs=inputs,
        targets=targets, fold=fold, horizon=60)
    def comparator_failure(**_kwargs):
        raise ValueError("synthetic comparator failure")
    monkeypatch.setattr(runner, "fit_comparator", comparator_failure)
    primary_phase = runner._fold_stage(run_dir=failed_run, env=env, runner_sha="1" * 64,
        feature_path=feature_path, feature_sha=sha256(feature_path.read_bytes()).hexdigest(),
        inputs=inputs, targets=targets, fold=fold, horizon=60)
    report = json.loads(gzip.decompress((failed_run / "E60_F1.json.gz").read_bytes()))
    assert len(primary_phase.records) == 4 and all(r.matched for r in primary_phase.records)
    assert failed_primary.is_file() and sha256(failed_primary.read_bytes()).hexdigest() == failed_primary_sha
    assert report["comparator"] is None and report["comparator_status"]["status"] == "FIT_FAILED"
    assert len(report["shadow_scores"]) == 4
    failed_primary.write_bytes(b"corrupt")
    with pytest.raises(DevelopmentInputError, match="seal mismatch"):
        runner._prepare_primary_stage(
            run_dir=failed_run, env=env, runner_sha="1" * 64, feature_path=feature_path,
            feature_sha=sha256(feature_path.read_bytes()).hexdigest(), inputs=inputs,
            targets=targets, fold=fold, horizon=60)


def _comparator_stage_fixture(tmp_path, monkeypatch):
    run_root = tmp_path / "runs"
    run_dir = run_root / "20261019T100000000000Z_13d242c0"
    run_dir.mkdir(parents=True)
    monkeypatch.setattr(runner, "RUN_ROOT", run_root)
    monkeypatch.setattr(runner, "REPO", tmp_path)
    job = runner.ComparatorJob(
        str(tmp_path), str(run_dir), "a" * 64, str(run_dir / "features.jsonl.gz"),
        "b" * 64, 60, "F1", "c" * 64, "d" * 64, "e" * 64, "f" * 64, ())
    output = {"horizon": 60, "fit_id": "F1", "parents": runner._comparator_parents(job),
              "primary_bundle_sha256": "1" * 64, "comparator": None,
              "comparator_scores": [], "fit_error": "ValueError: synthetic",
              "completed_at": "2026-10-19T10:00:00.000000Z"}
    return job, output


def test_comparator_stage_publish_isolated_immutable_and_corruption_detected(tmp_path, monkeypatch):
    job, output = _comparator_stage_fixture(tmp_path, monkeypatch)
    temporary = runner._write_comparator_temp(job, output)
    persisted, artifact_sha = runner._publish_comparator_stage(temporary, job=job)
    final = runner._comparator_stage_dir(Path(job.run_dir), 60, "F1")
    assert persisted == output and len(artifact_sha) == 64 and final.is_dir()
    with pytest.raises(DevelopmentInputError, match="already exists"):
        runner._publish_comparator_stage(runner._write_comparator_temp(job, output), job=job)
    (final / "artifact.json.gz").write_bytes(b"corrupt")
    with pytest.raises(DevelopmentInputError, match="seal mismatch"):
        runner._read_comparator_stage(final, job=job)


def test_comparator_publish_rejects_worker_path_escape_and_lock_collision(tmp_path, monkeypatch):
    job, output = _comparator_stage_fixture(tmp_path, monkeypatch)
    # Deliberately keep the malicious worker path outside the authenticated run directory.
    outside = tmp_path / (".E60_F1.comparator-incomplete-" + "a" * 32)
    outside.mkdir()
    with pytest.raises(DevelopmentInputError, match="temporary path"):
        runner._publish_comparator_stage(outside, job=job)
    temporary = runner._write_comparator_temp(job, output)
    with runner._comparator_publish_lock(job):
        with pytest.raises(DevelopmentInputError, match="publish collision"):
            runner._publish_comparator_stage(temporary, job=job)


def test_comparator_publish_rejects_redirected_lock_without_writing(tmp_path, monkeypatch):
    job, _ = _comparator_stage_fixture(tmp_path, monkeypatch)
    lock = Path(job.run_dir) / ".E60_F1.comparator-publish.lock"
    lock.write_bytes(b"")
    original_is_symlink = Path.is_symlink
    monkeypatch.setattr(Path, "is_symlink", lambda path:
                        path == lock or original_is_symlink(path))
    with pytest.raises(DevelopmentInputError, match="redirected evidence path"):
        with runner._comparator_publish_lock(job):
            pass
    assert lock.read_bytes() == b""


def test_interrupted_comparator_temp_never_counts_as_complete(tmp_path, monkeypatch):
    job, output = _comparator_stage_fixture(tmp_path, monkeypatch)
    temporary = runner._write_comparator_temp(job, output)
    final = runner._comparator_stage_dir(Path(job.run_dir), 60, "F1")
    assert temporary.is_dir() and not final.exists()
    with pytest.raises(DevelopmentInputError, match="missing or invalid"):
        runner._read_comparator_stage(final, job=job)


def test_worker_rechecks_committed_runner_and_environment_identity(tmp_path, monkeypatch):
    job, _ = _comparator_stage_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(runner, "_committed_runner", lambda: "0" * 64)
    with pytest.raises(DevelopmentInputError, match="runner identity mismatch"):
        runner._verify_worker_identity(job)
    monkeypatch.setattr(runner, "_committed_runner", lambda: job.runner_sha)
    verified = []
    environment = SimpleNamespace(identity_sha256="0" * 64,
                                  verify=lambda: verified.append(True))
    monkeypatch.setattr(runner, "build_development_environment", lambda **_kwargs: environment)
    with pytest.raises(DevelopmentInputError, match="environment identity mismatch"):
        runner._verify_worker_identity(job)
    assert verified == [True]
    environment.identity_sha256 = job.environment_sha
    runner._verify_worker_identity(job)


def test_e120_preparation_failure_preserves_independent_e60_work():
    events = []
    def prepare(horizon):
        events.append(horizon)
        if horizon == 120:
            raise DevelopmentInputError("synthetic E120 failure")
        return "inputs60", "registration60", {"F1": "a" * 64}, ("E60-job",)
    contexts, jobs, deferred = runner._prepare_independent_horizons(prepare)
    assert events == [60, 120]
    assert contexts == {60: ("inputs60", "registration60", {"F1": "a" * 64})}
    assert jobs == ("E60-job",)
    assert isinstance(deferred, DevelopmentInputError)
    with pytest.raises(DevelopmentInputError, match="synthetic E60 failure"):
        runner._prepare_independent_horizons(
            lambda horizon: (_ for _ in ()).throw(
                DevelopmentInputError("synthetic E60 failure")))


@pytest.mark.parametrize("workers", [0, -1, 5, True, 1.5])
def test_invalid_comparator_worker_counts_fail_closed(workers):
    with pytest.raises(DevelopmentInputError, match="integer in \\[1,4\\]"):
        runner._validate_worker_count(workers)
    assert runner._validate_worker_count(1) == 1


def test_comparator_scheduler_returns_canonical_caller_order_on_reuse(tmp_path, monkeypatch):
    base_job, output = _comparator_stage_fixture(tmp_path, monkeypatch)
    jobs = []
    for horizon, fit_id in ((60, "F1"), (60, "F2"), (120, "F1")):
        job = replace(base_job, horizon=horizon, fit_id=fit_id,
                      canonical_label_sha=("f" if horizon == 60 else "9") * 64)
        runner._publish_comparator_stage(runner._write_comparator_temp(job, {
            **output, "horizon": horizon, "fit_id": fit_id,
            "parents": runner._comparator_parents(job)}), job=job)
        jobs.append(job)
    result, failures = runner._schedule_comparator_jobs(tuple(jobs), workers=4)
    assert tuple(result) == tuple(job.key for job in jobs)
    assert failures == {}


def test_e120_worker_failure_is_collected_without_discarding_e60_result(tmp_path, monkeypatch):
    base_job, output = _comparator_stage_fixture(tmp_path, monkeypatch)
    e60 = base_job
    e120 = replace(base_job, horizon=120, fit_id="F1", canonical_label_sha="9" * 64)
    def worker(job):
        if job.horizon == 120:
            raise DevelopmentInputError("synthetic E120 worker failure")
        return str(runner._write_comparator_temp(job, output))
    monkeypatch.setattr(runner, "_comparator_worker", worker)
    results, failures = runner._schedule_comparator_jobs((e60, e120), workers=1)
    assert tuple(results) == (e60.key,)
    assert tuple(failures) == (e120.key,)
    assert isinstance(failures[e120.key], DevelopmentInputError)
    assert runner._comparator_stage_dir(Path(e60.run_dir), 60, "F1").is_dir()
    assert not runner._comparator_stage_dir(Path(e120.run_dir), 120, "F1").exists()


def test_corrupt_existing_e120_stage_does_not_discard_valid_e60_result(tmp_path, monkeypatch):
    e60, output = _comparator_stage_fixture(tmp_path, monkeypatch)
    e120 = replace(e60, horizon=120, fit_id="F1", canonical_label_sha="9" * 64)
    runner._publish_comparator_stage(runner._write_comparator_temp(e60, output), job=e60)
    e120_output = {**output, "horizon": 120, "parents": runner._comparator_parents(e120)}
    runner._publish_comparator_stage(runner._write_comparator_temp(e120, e120_output), job=e120)
    e120_artifact = runner._comparator_stage_dir(Path(e120.run_dir), 120, "F1") / "artifact.json.gz"
    e120_artifact.write_bytes(b"corrupt")
    results, failures = runner._schedule_comparator_jobs((e60, e120), workers=1)
    assert tuple(results) == (e60.key,)
    assert tuple(failures) == (e120.key,)
    assert isinstance(failures[e120.key], DevelopmentInputError)

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
import gzip
from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

from tools.audit.research_v2_checkpoint_driver import parse_args, run_research_v2_checkpoint_driver
from tools.research_v2.run_7d_screen import EXPECTED_DATASET_ID, load_ordered_jobs


def test_research_v2_checkpoint_driver_cli_parsing() -> None:
    args = parse_args(
        [
            "runtime/audit/research_v2_7d_test",
            "--dataset",
            "runtime/data/research-v2/7d_20260819_20260826/dataset_manifest.json",
            "--jobs",
            "J0,J3",
            "--limit",
            "1",
            "--resume",
            "--population",
            "runtime/audit/source/research_v2_set_population.json",
            "--replay-only",
            "--finalize-existing",
        ]
    )

    assert str(args.output_dir) == "runtime\\audit\\research_v2_7d_test" or str(args.output_dir) == "runtime/audit/research_v2_7d_test"
    assert args.jobs == "J0,J3"
    assert args.limit == 1
    assert args.resume is True
    assert str(args.population).replace("\\", "/") == "runtime/audit/source/research_v2_set_population.json"
    assert args.replay_only is True
    assert args.finalize_existing is True


def test_research_v2_checkpoint_driver_loads_j0_j7() -> None:
    assert [job.job_id for job in load_ordered_jobs()] == [f"J{idx}" for idx in range(8)]


def test_research_v2_checkpoint_driver_passes_replay_only_population(monkeypatch: pytest.MonkeyPatch) -> None:
    tmp_path = _workspace_tmp("replay_only_passthrough")
    output = tmp_path / "out"
    dataset = tmp_path / "dataset_manifest.json"
    dataset.write_text("{}", encoding="utf-8")
    population = tmp_path / "research_v2_set_population.json"
    population.write_text("{}", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_run_screen(**kwargs):
        captured.update(kwargs)
        kwargs["output_dir"].mkdir(parents=True)
        return 3, 3

    import tools.research_v2.run_7d_screen as run_7d_screen

    monkeypatch.setattr(run_7d_screen, "run_screen", fake_run_screen)
    summary = run_research_v2_checkpoint_driver(
        output_dir=output,
        dataset=dataset,
        jobs="J3,J4",
        population=population,
        replay_only=True,
    )

    assert summary["completed"] == 3
    assert captured["population_path"] == population
    assert captured["replay_only"] is True


def test_research_v2_checkpoint_driver_finalize_existing_does_not_call_replay(monkeypatch: pytest.MonkeyPatch) -> None:
    tmp_path = _workspace_tmp("finalize_existing_passthrough")
    output = tmp_path / "out"
    dataset = tmp_path / "dataset_manifest.json"
    dataset.write_text("{}", encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_finalize(**kwargs):
        captured.update(kwargs)
        kwargs["output_dir"].mkdir(parents=True)
        return {
            "status": "COMPLETE",
            "mode": "EVIDENCE_ONLY_FINALIZATION",
            "contexts": 7,
            "economic_event_fingerprint_changed": False,
        }

    def fail_run_screen(**_kwargs):
        raise AssertionError("run_screen must not be called for evidence-only finalization")

    import tools.research_v2.run_7d_screen as run_7d_screen

    monkeypatch.setattr(run_7d_screen, "finalize_research_v2_existing_run", fake_finalize)
    monkeypatch.setattr(run_7d_screen, "run_screen", fail_run_screen)
    summary = run_research_v2_checkpoint_driver(
        output_dir=output,
        dataset=dataset,
        jobs="J3",
        finalize_existing=True,
    )

    assert summary["mode"] == "EVIDENCE_ONLY_FINALIZATION"
    assert summary["completed"] == 7
    assert summary["total"] == 7
    assert captured["output_dir"] == output.resolve()
    assert captured["dataset_path"] == dataset.resolve()
    assert captured["jobs_arg"] == "J3"


def test_research_v2_checkpoint_driver_checkpoint_resume_and_summary() -> None:
    tmp_path = _workspace_tmp("checkpoint_resume")
    dataset = _dataset_manifest(tmp_path)
    output = tmp_path / "out"
    calls: list[str] = []

    def executor(job, _manifest, _output):
        calls.append(job.job_id)
        return _result(job.job_id, job.config_fingerprint)

    first = run_research_v2_checkpoint_driver(
        output_dir=output,
        dataset=dataset,
        jobs="J0,J1",
        executor=executor,
    )

    assert first["completed"] == 2
    assert first["total"] == 2
    assert first["errors"] == 0
    assert calls == ["J0", "J1"]
    assert (output / "job_results.jsonl").exists()
    assert (output / "job_errors.jsonl").exists() is False
    assert (output / "screen_summary.json").exists()
    assert (output / "jobs" / "J0" / "job_result.json").exists()
    assert (output / "jobs" / "J1" / "job_result.json").exists()

    calls.clear()
    resumed = run_research_v2_checkpoint_driver(
        output_dir=output,
        dataset=dataset,
        jobs="J0,J1",
        resume=True,
        executor=executor,
    )

    assert resumed["completed"] == 2
    assert calls == []
    assert len((output / "job_results.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_research_v2_checkpoint_driver_limit_smoke_and_isolated_job_outputs() -> None:
    tmp_path = _workspace_tmp("limit_smoke")
    dataset = _dataset_manifest(tmp_path)
    output = tmp_path / "out"
    seen: list[tuple[str, Path]] = []

    def executor(job, _manifest, out):
        seen.append((job.job_id, out))
        return _result(job.job_id, job.config_fingerprint)

    summary = run_research_v2_checkpoint_driver(
        output_dir=output,
        dataset=dataset,
        jobs="ALL",
        limit=1,
        executor=executor,
    )

    assert summary["completed"] == 1
    assert seen == [("J0", output.resolve())]
    assert (output / "jobs" / "J0" / "job_config.json").exists()
    assert not (output / "jobs" / "J1").exists()


def test_research_v2_checkpoint_driver_invokes_default_executor_without_placeholder() -> None:
    tmp_path = _workspace_tmp("default_executor")
    dataset = _dataset_manifest_with_candles(tmp_path)
    output = tmp_path / "out"

    summary = run_research_v2_checkpoint_driver(
        output_dir=output,
        dataset=dataset,
        jobs="J3",
    )

    result = json.loads((output / "jobs" / "J3" / "job_result.json").read_text(encoding="utf-8"))
    assert summary["completed"] == 1
    assert summary["errors"] == 0
    assert result["matched"] >= 1
    assert (output / "research_v2_set_population.json").exists()
    assert (output / "progress.json").exists()
    assert "RAW_TRADES_INDEXED_MINUTE_BARS" in (output / "lifecycle_results.jsonl").read_text(encoding="utf-8")
    assert "RESEARCH_V2_JOB_EXECUTOR_NOT_WIRED" not in (output / "job_results.jsonl").read_text(encoding="utf-8")


def _dataset_manifest(tmp_path: Path) -> Path:
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    data_file = dataset / "data.json"
    data_file.write_text('{"ok":true}', encoding="utf-8")
    digest = sha256(data_file.read_bytes()).hexdigest()
    manifest = {
        "dataset_id": EXPECTED_DATASET_ID,
        "status": "DATA_READY",
        "validation": {"status": "PASS"},
        "coverage": {
            "job_readiness": [
                {
                    "job_id": f"J{idx}",
                    "candles_ready": True,
                    "raw_trades_ready": True,
                    "funding_ready": True,
                    "mark_ready": True,
                    "instrument_ready": True,
                    "warmup_ready": True,
                    "overall_status": "READY",
                }
                for idx in range(8)
            ]
        },
        "files": [
            {
                "type": "fixture",
                "local_path": str(data_file),
                "sha256": digest,
            }
        ],
    }
    path = dataset / "dataset_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _dataset_manifest_with_candles(tmp_path: Path) -> Path:
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    files = []
    for symbol in ("AVAXUSDT", "SUIUSDT", "1000PEPEUSDT"):
        candle_file = dataset / f"{symbol}__linear__1m__fixture.json"
        candle_file.write_text(json.dumps(_fixture_candles(symbol=symbol, triggering=symbol == "AVAXUSDT")), encoding="utf-8")
        files.append(
            {
                "type": "candles_1m",
                "symbol": "PEPEUSDT" if symbol == "1000PEPEUSDT" else symbol,
                "physical_symbol": symbol,
                "local_path": str(candle_file),
                "sha256": sha256(candle_file.read_bytes()).hexdigest(),
            }
        )
        raw_file = dataset / f"{symbol}_2026-08-19_raw_trades.csv.gz"
        _write_raw_fixture(raw_file, symbol=symbol)
        files.append(
            {
                "type": "raw_trades_archive",
                "symbol": "PEPEUSDT" if symbol == "1000PEPEUSDT" else symbol,
                "physical_symbol": symbol,
                "local_path": str(raw_file),
                "sha256": sha256(raw_file.read_bytes()).hexdigest(),
            }
        )
    manifest = {
        "dataset_id": EXPECTED_DATASET_ID,
        "status": "DATA_READY",
        "validation": {"status": "PASS"},
        "coverage": {
            "job_readiness": [
                {
                    "job_id": f"J{idx}",
                    "candles_ready": True,
                    "raw_trades_ready": True,
                    "funding_ready": True,
                    "mark_ready": True,
                    "instrument_ready": True,
                    "warmup_ready": True,
                    "overall_status": "READY",
                }
                for idx in range(8)
            ]
        },
        "files": files,
    }
    path = dataset / "dataset_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _fixture_candles(*, symbol: str, triggering: bool) -> list[dict[str, object]]:
    start = datetime(2026, 8, 19, 0, 0, tzinfo=UTC)
    rows: list[dict[str, object]] = []
    for index in range(270):
        open_time = start + timedelta(minutes=index)
        close_time = open_time + timedelta(minutes=1)
        close = Decimal("100")
        if triggering and index == 175:
            low = Decimal("99.4")
            high = Decimal("100.4")
        elif index < 240 or not triggering:
            low = Decimal("99.6")
            high = Decimal("100.4")
        else:
            close = Decimal("100.60")
            low = Decimal("100.15")
            high = Decimal("100.95")
        rows.append(
            {
                "symbol": symbol,
                "category": "linear",
                "timeframe": "1m",
                "open_time": open_time.isoformat().replace("+00:00", "Z"),
                "close_time": close_time.isoformat().replace("+00:00", "Z"),
                "open": str(close),
                "high": str(high),
                "low": str(low),
                "close": str(close),
                "volume": "100",
                "turnover": "10000",
                "completed": True,
            }
        )
    return rows


def _write_raw_fixture(path: Path, *, symbol: str) -> None:
    start = datetime(2026, 8, 19, 4, 0, tzinfo=UTC)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        handle.write("timestamp,symbol,side,size,price,tickDirection,trdMatchID,grossValue,homeNotional,foreignNotional\n")
        for index in range(30):
            ts = start + timedelta(minutes=index, seconds=5)
            price = Decimal("100.25") + Decimal(index) * Decimal("0.01")
            handle.write(f"{ts.isoformat().replace('+00:00', 'Z')},{symbol},Buy,1,{price},PlusTick,{index},0,0,0\n")


def _workspace_tmp(name: str) -> Path:
    path = Path("runtime/tmp/research_v2_checkpoint_driver") / name
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)
    return path


def _result(job_id: str, fingerprint: str) -> dict[str, object]:
    return {
        "job_id": job_id,
        "config_fingerprint": fingerprint,
        "status": "COMPLETE",
        "evaluation_start": "2026-08-19T00:00:00Z",
        "evaluation_end": "2026-08-26T00:00:00Z",
        "unique_signal_episodes": 1,
        "matched": 1,
        "approved": 1,
        "accepted": 1,
        "filled": 1,
        "closed": 1,
        "account_net": Decimal("1"),
        "actual_notional_turnover": Decimal("10"),
        "mean_net_notional_expectancy": Decimal("0.1"),
        "fees": Decimal("0"),
        "funding": Decimal("0"),
        "stress_net": Decimal("1"),
        "leave_best_event_out_net": Decimal("1"),
    }

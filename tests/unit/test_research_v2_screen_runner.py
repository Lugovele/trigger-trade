from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
import gzip
from hashlib import sha256
import json
from pathlib import Path
import shutil

import pytest

import tools.research_v2.run_7d_screen as screen_runner
from tools.research_v2.run_7d_screen import (
    EXPECTED_DATASET_ID,
    ResearchV2RunnerError,
    _dedupe_set_scan_jobs,
    _evaluate_job_signal_from_timeline,
    _execution_contexts_from_population,
    _load_dataset_candles,
    _parse_raw_trade_time,
    _replay_one_context,
    build_research_v2_feature_timeline,
    load_research_v2_set_population,
    load_ordered_jobs,
    materialize_research_v2_set_population,
    parse_args,
    replay_research_v2_materialized_population,
    run_screen,
    select_jobs,
    validate_dataset,
)
from triggertrade.research_v2_execution import V2PortfolioExposureState
from triggertrade.research_v2 import atr15, return_pct_points
from triggertrade.services.research_backtest_execution import ResearchV1BacktestLifecycleResult
from triggertrade.set_engine import q18_export_text


def test_research_v2_screen_runner_cli_parsing() -> None:
    args = parse_args(
        [
            "--dataset",
            "runtime/data/research-v2/7d_20260819_20260826/dataset_manifest.json",
            "--output",
            "runtime/audit/research_v2_7d_test",
            "--jobs",
            "ALL",
            "--resume",
            "--max-jobs",
            "2",
        ]
    )

    assert args.jobs == "ALL"
    assert args.resume is True
    assert args.max_jobs == 2


def test_research_v2_screen_runner_job_selection() -> None:
    jobs = load_ordered_jobs()

    assert [job.job_id for job in select_jobs("ALL", jobs)] == [f"J{idx}" for idx in range(8)]
    assert [job.job_id for job in select_jobs("J3,J7", jobs)] == ["J3", "J7"]

    with pytest.raises(ResearchV2RunnerError):
        select_jobs("J8", jobs)


def test_research_v2_screen_runner_validates_dataset_before_execution() -> None:
    case_dir = _case_dir("invalid_dataset")
    manifest = _dataset_manifest(case_dir, status="BLOCKED_DATA_INCOMPLETE")
    called = False

    def executor(*_args, **_kwargs):
        nonlocal called
        called = True
        return {}

    with pytest.raises(ResearchV2RunnerError):
        run_screen(dataset_path=manifest, output_dir=case_dir / "out", jobs_arg="J0", executor=executor)

    assert called is False


def test_research_v2_screen_runner_checkpoint_resume_and_summary() -> None:
    case_dir = _case_dir("checkpoint_resume")
    manifest = _dataset_manifest(case_dir)
    output = case_dir / "out"
    calls: list[str] = []

    def executor(job, _manifest, _output):
        calls.append(job.job_id)
        return _result(job.job_id, job.config_fingerprint, account_net=Decimal("50") if job.job_id == "J0" else Decimal("-1"))

    completed, total = run_screen(dataset_path=manifest, output_dir=output, jobs_arg="J0,J1", executor=executor)

    assert (completed, total) == (2, 2)
    assert calls == ["J0", "J1"]
    assert len((output / "job_results.jsonl").read_text(encoding="utf-8").splitlines()) == 2
    assert (output / "jobs" / "J0" / "job_result.json").exists()
    assert (output / "jobs" / "J1" / "job_config.json").exists()

    summary = json.loads((output / "screen_summary.json").read_text(encoding="utf-8"))
    assert [row["job_id"] for row in summary] == ["J0", "J1"]
    assert summary[0]["economic_gate"] == "ECONOMIC_PASS"
    assert summary[1]["economic_gate"] == "FAIL"

    calls.clear()
    completed, total = run_screen(dataset_path=manifest, output_dir=output, jobs_arg="J0,J1", resume=True, executor=executor)

    assert (completed, total) == (2, 2)
    assert calls == []
    assert len((output / "job_results.jsonl").read_text(encoding="utf-8").splitlines()) == 2


def test_research_v2_screen_runner_default_executor_reaches_canonical_v2_path() -> None:
    case_dir = _case_dir("default_executor_smoke")
    manifest = _dataset_manifest_with_candles(case_dir)
    output = case_dir / "out"

    completed, total = run_screen(dataset_path=manifest, output_dir=output, jobs_arg="J3")

    assert (completed, total) == (1, 1)
    result = json.loads((output / "jobs" / "J3" / "job_result.json").read_text(encoding="utf-8"))
    assert result["job_id"] == "J3"
    assert result["status"] in {"COMPLETE", "DATA_INVALID"}
    assert result["matched"] >= 1
    assert (output / "research_v2_set_population.json").exists()
    assert (output / "progress.json").exists()
    lifecycle_rows = (output / "lifecycle_results.jsonl").read_text(encoding="utf-8").splitlines()
    assert lifecycle_rows
    assert "RAW_TRADES_INDEXED_MINUTE_BARS" in lifecycle_rows[0]
    assert "RESEARCH_V2_JOB_EXECUTOR_NOT_WIRED" not in (output / "job_results.jsonl").read_text(encoding="utf-8")


def test_research_v2_replay_only_skips_materialization_and_uses_population(monkeypatch: pytest.MonkeyPatch) -> None:
    case_dir = _case_dir("replay_only")
    manifest = _dataset_manifest_with_candles(case_dir)
    source = case_dir / "source"
    population = _single_population(manifest, jobs_arg="J3", output_dir=source)
    population_path = source / "research_v2_set_population.json"
    output = case_dir / "out"

    def fail_materialize(*_args, **_kwargs):
        raise AssertionError("materialization must be skipped in replay-only mode")

    monkeypatch.setattr(screen_runner, "materialize_research_v2_set_population", fail_materialize)
    completed, total = run_screen(
        dataset_path=manifest,
        output_dir=output,
        jobs_arg="J3",
        population_path=population_path,
        replay_only=True,
    )

    assert population["summary"]["matched_episodes"] >= 1
    assert (completed, total) == (1, 1)
    assert not (output / "research_v2_set_population.json").exists()
    assert (output / "lifecycle_results.jsonl").exists()
    assert (output / "progress.json").exists()


def test_research_v2_replay_only_requires_population() -> None:
    case_dir = _case_dir("replay_only_missing_population")
    manifest = _dataset_manifest_with_candles(case_dir)

    with pytest.raises(ResearchV2RunnerError, match="requires --population"):
        run_screen(dataset_path=manifest, output_dir=case_dir / "out", jobs_arg="J3", replay_only=True)


def test_research_v2_replay_only_blocks_dataset_mismatch() -> None:
    case_dir = _case_dir("replay_only_dataset_mismatch")
    manifest = _dataset_manifest_with_candles(case_dir)
    source = case_dir / "source"
    _single_population(manifest, jobs_arg="J3", output_dir=source)
    population_path = source / "research_v2_set_population.json"
    population = json.loads(population_path.read_text(encoding="utf-8"))
    population["dataset_id"] = "other-dataset"
    population_path.write_text(json.dumps(population), encoding="utf-8")

    with pytest.raises(ResearchV2RunnerError, match="dataset_id mismatch"):
        load_research_v2_set_population(
            population_path,
            dataset_manifest=json.loads(manifest.read_text(encoding="utf-8")),
            selected_jobs=select_jobs("J3", load_ordered_jobs()),
        )


def test_research_v2_replay_only_requires_fresh_output_and_no_old_checkpoint_reuse() -> None:
    case_dir = _case_dir("replay_only_fresh_output")
    manifest = _dataset_manifest_with_candles(case_dir)
    source = case_dir / "source"
    _single_population(manifest, jobs_arg="J3", output_dir=source)
    population_path = source / "research_v2_set_population.json"
    (source / "job_results.jsonl").write_text('{"old":true}\n', encoding="utf-8")

    with pytest.raises(ResearchV2RunnerError, match="population source directory"):
        run_screen(
            dataset_path=manifest,
            output_dir=source,
            jobs_arg="J3",
            population_path=population_path,
            replay_only=True,
        )

    stale_output = case_dir / "stale_out"
    stale_output.mkdir()
    (stale_output / "lifecycle_results.jsonl").write_text('{"stale":true}\n', encoding="utf-8")
    with pytest.raises(ResearchV2RunnerError, match="fresh output directory"):
        run_screen(
            dataset_path=manifest,
            output_dir=stale_output,
            jobs_arg="J3",
            population_path=population_path,
            replay_only=True,
        )

    fresh_output = case_dir / "fresh_out"
    completed, total = run_screen(
        dataset_path=manifest,
        output_dir=fresh_output,
        jobs_arg="J3",
        population_path=population_path,
        replay_only=True,
    )
    assert (completed, total) == (1, 1)
    replay_rows = [json.loads(line) for line in (fresh_output / "lifecycle_results.jsonl").read_text(encoding="utf-8").splitlines()]
    assert all("old" not in row for row in replay_rows)


def test_research_v2_replay_only_blocks_incompatible_jobs() -> None:
    case_dir = _case_dir("replay_only_incompatible")
    manifest = _dataset_manifest_with_candles(case_dir)
    source = case_dir / "source"
    _single_population(manifest, jobs_arg="J3", output_dir=source)

    with pytest.raises(ResearchV2RunnerError, match="selected jobs"):
        run_screen(
            dataset_path=manifest,
            output_dir=case_dir / "out",
            jobs_arg="J4",
            population_path=source / "research_v2_set_population.json",
            replay_only=True,
        )


def test_research_v2_portfolio_book_isolates_coin_slots_and_job_accounts() -> None:
    book = screen_runner.V2ReplayPortfolioBook(account_capital=Decimal("1000"), active=[])
    book.commit(
        symbol="SUIUSDT",
        economics={
            "actual_committed_margin": "250",
            "actual_order_notional": "250",
            "actual_stop_risk": "5",
        },
        release_at=None,
        context_id="sui-open",
        lifecycle_status="FILLED_OPEN_AT_ENDPOINT",
    )

    sui = book.state_for_symbol("SUIUSDT")
    avax = book.state_for_symbol("AVAXUSDT")
    pepe = book.state_for_symbol("PEPEUSDT")
    assert sui.open_pending_count == 1
    assert sui.coin_open_pending_count == 1
    assert avax.open_pending_count == 1
    assert avax.coin_open_pending_count == 0
    assert pepe.open_pending_count == 1
    assert pepe.coin_open_pending_count == 0

    state: dict[str, object] = {}
    j4 = {"job_id": "J4", "execution_profile_fingerprint": "same"}
    j7 = {"job_id": "J7", "execution_profile_fingerprint": "same"}
    screen_runner._portfolio_book(state, screen_runner._portfolio_book_key(j4))
    screen_runner._portfolio_book(state, screen_runner._portfolio_book_key(j7))
    assert sorted(state) == ["J4:same", "J7:same"]


def test_research_v2_g0_protective_swing_selection_skips_wrong_side_and_old_refs() -> None:
    cutoff = datetime(2026, 8, 19, 4, 0, tzinfo=UTC)
    timeline = screen_runner.FeatureTimeline(
        symbol="AVAXUSDT",
        physical_symbol="AVAXUSDT",
        candles=(),
        close_times=(),
        by_close={},
        return5={},
        return15={},
        atr15={},
        ema20={},
        ema50={},
        rvol5={},
        turnover_acceleration={},
        compression_atr_median96={},
        prior_12_range={},
        swing_long={},
        swing_short={},
        swing_low_refs=(
            screen_runner.V2TimelineSwingReference(Decimal("99.0"), cutoff - timedelta(minutes=90), cutoff - timedelta(minutes=80), cutoff - timedelta(minutes=80), "LOW"),
            screen_runner.V2TimelineSwingReference(Decimal("99.0"), cutoff - timedelta(minutes=30), cutoff - timedelta(minutes=20), cutoff - timedelta(minutes=20), "LOW"),
            screen_runner.V2TimelineSwingReference(Decimal("99.5"), cutoff - timedelta(minutes=20), cutoff - timedelta(minutes=10), cutoff - timedelta(minutes=10), "LOW"),
            screen_runner.V2TimelineSwingReference(Decimal("100.2"), cutoff - timedelta(minutes=10), cutoff - timedelta(minutes=5), cutoff - timedelta(minutes=5), "LOW"),
        ),
        swing_high_refs=(
            screen_runner.V2TimelineSwingReference(Decimal("101.0"), cutoff - timedelta(minutes=30), cutoff - timedelta(minutes=20), cutoff - timedelta(minutes=20), "HIGH"),
            screen_runner.V2TimelineSwingReference(Decimal("100.4"), cutoff - timedelta(minutes=20), cutoff - timedelta(minutes=10), cutoff - timedelta(minutes=10), "HIGH"),
            screen_runner.V2TimelineSwingReference(Decimal("99.8"), cutoff - timedelta(minutes=10), cutoff - timedelta(minutes=5), cutoff - timedelta(minutes=5), "HIGH"),
        ),
    )

    long_ref = screen_runner._latest_protective_swing_from_timeline(
        timeline=timeline,
        cutoff=cutoff,
        direction=screen_runner.V2Direction.LONG,
        entry=Decimal("100"),
    )
    short_ref = screen_runner._latest_protective_swing_from_timeline(
        timeline=timeline,
        cutoff=cutoff,
        direction=screen_runner.V2Direction.SHORT,
        entry=Decimal("100"),
    )
    no_ref = screen_runner._latest_protective_swing_from_timeline(
        timeline=timeline,
        cutoff=cutoff,
        direction=screen_runner.V2Direction.LONG,
        entry=Decimal("98"),
    )

    assert long_ref.price == Decimal("99.5")
    assert short_ref.price == Decimal("100.4")
    assert no_ref is None


def test_research_v2_replay_rolls_back_g0_reject_before_commit() -> None:
    case_dir = _case_dir("g0_reject_rollback")
    reject_manifest_path = _dataset_manifest_with_candles(case_dir / "reject", swing_low=Decimal("98.8"))
    pass_manifest_path = _dataset_manifest_with_candles(case_dir / "pass")
    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")

    reject_context = _single_materialized_context(reject_manifest_path, job=job, output_dir=case_dir / "reject_out")
    pass_context = _single_materialized_context(pass_manifest_path, job=job, output_dir=case_dir / "pass_out")
    reject_manifest = json.loads(reject_manifest_path.read_text(encoding="utf-8"))
    pass_manifest = json.loads(pass_manifest_path.read_text(encoding="utf-8"))
    state: dict[str, object] = {}

    rejected = _replay_one_context(
        context=reject_context,
        dataset_manifest=reject_manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )

    assert rejected["status"] == "CONSTRUCTION_REJECTED"
    assert rejected["reason_code"] == "G0_STRUCTURAL_STOP_BEYOND_MAXIMUM"
    assert rejected["state_committed"] is False
    rejected_state = _book_state(state, reject_context, "AVAXUSDT")
    assert rejected_state.open_pending_count == 0
    assert rejected_state.coin_open_pending_count == 0
    assert rejected_state.committed_margin == Decimal("0")
    assert rejected_state.coin_committed_margin == Decimal("0")
    assert rejected_state.gross_notional == Decimal("0")
    assert rejected_state.stop_risk == Decimal("0")

    allowed = _replay_one_context(
        context=pass_context,
        dataset_manifest=pass_manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )

    assert allowed.get("reason_code") != "MAX_COIN_OPEN_PENDING_REACHED"
    assert allowed["status"] == "COMPLETE"


def test_research_v2_raw_timestamp_parsing_supports_epoch_fraction_and_iso() -> None:
    integer = _parse_raw_trade_time("1787097601")
    fractional = _parse_raw_trade_time("1787097601.2805")
    later_fractional = _parse_raw_trade_time("1787097601.2806")
    iso = _parse_raw_trade_time("2026-08-19T00:00:01.280500Z")

    assert integer.tzinfo == UTC
    assert fractional.tzinfo == UTC
    assert fractional.microsecond == 280500
    assert later_fractional > fractional
    assert iso == datetime(2026, 8, 19, 0, 0, 1, 280500, tzinfo=UTC)
    with pytest.raises(ValueError):
        _parse_raw_trade_time("1787097601.bad")


def test_research_v2_replay_rolls_back_raw_parse_failure_before_commit() -> None:
    case_dir = _case_dir("raw_parse_rollback")
    invalid_manifest_path = _dataset_manifest_with_candles(case_dir / "invalid", raw_timestamp_mode="invalid")
    fractional_manifest_path = _dataset_manifest_with_candles(case_dir / "fractional", raw_timestamp_mode="fractional_epoch")
    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")
    invalid_context = _single_materialized_context(invalid_manifest_path, job=job, output_dir=case_dir / "invalid_out")
    fractional_context = _single_materialized_context(fractional_manifest_path, job=job, output_dir=case_dir / "fractional_out")
    invalid_manifest = json.loads(invalid_manifest_path.read_text(encoding="utf-8"))
    fractional_manifest = json.loads(fractional_manifest_path.read_text(encoding="utf-8"))
    state: dict[str, object] = {}

    with pytest.raises(ValueError):
        _replay_one_context(
            context=invalid_context,
            dataset_manifest=invalid_manifest,
            raw_indexes={},
            candles_cache={},
            venue_cache={},
            funding_cache={},
            portfolio_state=state,
        )

    invalid_state = _book_state(state, invalid_context, "AVAXUSDT")
    assert invalid_state.open_pending_count == 0
    assert invalid_state.coin_open_pending_count == 0
    assert invalid_state.committed_margin == Decimal("0")
    assert invalid_state.coin_committed_margin == Decimal("0")
    assert invalid_state.gross_notional == Decimal("0")
    assert invalid_state.stop_risk == Decimal("0")

    result = _replay_one_context(
        context=fractional_context,
        dataset_manifest=fractional_manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )

    assert result["status"] == "COMPLETE"


def test_research_v2_ttl_expiry_unfilled_releases_committed_reservation(monkeypatch: pytest.MonkeyPatch) -> None:
    case_dir = _case_dir("ttl_expiry_release")
    manifest_path = _dataset_manifest_with_candles(case_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")
    context = _single_materialized_context(manifest_path, job=job, output_dir=case_dir / "source")
    state: dict[str, object] = {}

    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_expired_unfilled)
    result = _replay_one_context(
        context=context,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )

    assert result["backtest_lifecycle"]["status"] == "ACCEPTED_NOT_FILLED"
    assert result["backtest_lifecycle"]["reason_code"] == "ENTRY_ORDER_EXPIRED_UNFILLED"
    assert result["reservation_committed"] is True
    assert result["reservation_released"] is True
    assert result["state_committed"] is False
    pending_state = _book_state(state, context, "AVAXUSDT")
    assert pending_state.open_pending_count == 1
    assert pending_state.coin_open_pending_count == 1

    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_filled_open)
    later_context = _clone_context_with_set_id(context, "set-result-after-expiry")
    _set_context_observed_at(later_context, "2026-08-19T04:20:00Z")
    later = _replay_one_context(
        context=later_context,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )

    assert later.get("reason_code") != "MAX_COIN_OPEN_PENDING_REACHED"
    assert later["state_committed"] is True
    later_state = _book_state(state, later_context, "AVAXUSDT")
    assert later_state.open_pending_count == 1
    assert later_state.coin_open_pending_count == 1


def test_research_v2_acceptance_cooldown_survives_close_and_exports_accepted_at(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case_dir = _case_dir("cooldown_survives_close")
    manifest_path = _dataset_manifest_with_candles(case_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")
    context = _single_materialized_context(manifest_path, job=job, output_dir=case_dir / "source")
    state: dict[str, object] = {}

    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_closed)
    first = _replay_one_context(
        context=context,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )
    assert first["cooldown_evidence"]["accepted_at"] == "2026-08-19T04:01:00Z"

    early = _clone_context_with_set_id(context, "set-result-cooldown-early")
    _set_context_observed_at(early, "2026-08-19T04:10:00Z")
    blocked = _replay_one_context(
        context=early,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )
    assert blocked["status"] == "PORTFOLIO_BLOCKED"
    assert blocked["reason_code"] == "COOLDOWN_ACTIVE"
    assert blocked["cooldown_evidence"]["previous_same_symbol_accepted_at"] == "2026-08-19T04:01:00Z"
    assert blocked["cooldown_evidence"]["cooldown_until"] == "2026-08-19T04:16:00Z"
    assert blocked["cooldown_evidence"]["accepted_at"] is None

    boundary = _clone_context_with_set_id(context, "set-result-cooldown-boundary")
    _set_context_observed_at(boundary, "2026-08-19T04:16:00Z")
    allowed = _replay_one_context(
        context=boundary,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )
    assert allowed["status"] != "PORTFOLIO_BLOCKED"
    assert allowed["cooldown_evidence"]["cooldown_decision"] == "PASS"


def test_research_v2_acceptance_cooldown_survives_unfilled_expiry_per_symbol_and_job(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case_dir = _case_dir("cooldown_expiry_symbol_job")
    manifest_path = _dataset_manifest_with_candles(case_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    j3 = next(job for job in load_ordered_jobs() if job.job_id == "J3")
    j4 = next(job for job in load_ordered_jobs() if job.job_id == "J4")
    avax = _single_materialized_context(manifest_path, job=j3, output_dir=case_dir / "j3")
    state: dict[str, object] = {}

    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_expired_unfilled)
    _replay_one_context(
        context=avax,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )

    early_same_symbol = _clone_context_with_set_id(avax, "set-result-expired-cooldown")
    _set_context_observed_at(early_same_symbol, "2026-08-19T04:10:00Z")
    blocked = _replay_one_context(
        context=early_same_symbol,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )
    assert blocked["reason_code"] == "COOLDOWN_ACTIVE"

    sui = _clone_context_with_set_id(avax, "set-result-sui-no-cooldown")
    _set_context_symbol(sui, "SUIUSDT")
    _set_context_observed_at(sui, "2026-08-19T04:10:00Z")
    allowed_symbol = _replay_one_context(
        context=sui,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )
    assert allowed_symbol.get("reason_code") != "COOLDOWN_ACTIVE"

    j4_context = _clone_context_with_set_id(avax, "set-result-j4-no-cooldown")
    _set_context_job(j4_context, j4)
    _set_context_observed_at(j4_context, "2026-08-19T04:10:00Z")
    allowed_job = _replay_one_context(
        context=j4_context,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )
    assert allowed_job.get("reason_code") != "COOLDOWN_ACTIVE"


def test_research_v2_terminal_censored_filled_releases_but_marks_account_invalid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case_dir = _case_dir("terminal_censored_release")
    manifest_path = _dataset_manifest_with_candles(case_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")
    context = _single_materialized_context(manifest_path, job=job, output_dir=case_dir / "source")
    state: dict[str, object] = {}

    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_censored_intrabar)
    censored = _replay_one_context(
        context=context,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )

    assert censored["backtest_lifecycle"]["status"] == "CENSORED"
    assert censored["reservation_released"] is True
    assert censored["state_committed"] is False
    assert _book_state(state, context, "AVAXUSDT").open_pending_count == 1

    later_context = _clone_context_with_set_id(context, "set-result-after-censor")
    _set_context_observed_at(later_context, "2026-08-19T04:20:00Z")
    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_filled_open)
    later = _replay_one_context(
        context=later_context,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=state,
    )
    assert later.get("reason_code") != "MAX_OPEN_PENDING_REACHED"


def test_research_v2_g0_evidence_exports_complete_ranked_candidate_witness() -> None:
    case_dir = _case_dir("g0_candidate_witness")
    manifest_path = _dataset_manifest_with_candles(case_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")
    context = _single_materialized_context(manifest_path, job=job, output_dir=case_dir / "source")

    result = _replay_one_context(
        context=context,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state={},
        mark_cache={},
    )
    base = {
        "context_id": str(context["context_id"]),
        "job_id": str(context["job_id"]),
        "set_result_id": str(context["record"]["set_result_id"]),
        "observed_at": str(context["observed_at"]),
        "logical_symbol": str(context["record"]["symbol"]),
        "physical_symbol": str(context["record"]["physical_symbol"]),
    }

    evidence = screen_runner._g0_reference_evidence(
        base=base,
        record=context["record"],
        result=result,
        dataset_manifest=manifest,
    )

    assert evidence is not None
    assert evidence["candidate_witness_complete"] is True
    assert evidence["selected_is_rank_1"] is True
    assert evidence["selected_rank"] == 1
    assert evidence["total_eligible_candidates"] >= 1
    assert evidence["ordered_eligible_candidate_list"][0]["price"] == evidence["selected_swing_price"]


def test_research_v2_daily_equity_guard_uses_frozen_marks_and_inclusive_threshold() -> None:
    case_dir = _case_dir("daily_equity_guard")
    manifest_path = _dataset_manifest_with_mark(case_dir, mark_price=Decimal("977.51"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    as_of = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)
    book = screen_runner.V2ReplayPortfolioBook(
        account_capital=Decimal("1000"),
        active=[
            screen_runner.V2ReplayExposure(
                symbol="AVAXUSDT",
                physical_symbol="AVAXUSDT",
                margin=Decimal("100"),
                gross_notional=Decimal("100"),
                stop_risk=Decimal("1"),
                release_at=None,
                context_id="ctx-open",
                lifecycle_status="FILLED_OPEN",
                direction="LONG",
                entry_price=Decimal("1000"),
                quantity=Decimal("0.1"),
                entry_fee=Decimal("0"),
                funding=Decimal("0"),
                opened_at=datetime(2026, 8, 19, 11, 0, tzinfo=UTC),
            )
        ],
    )

    evidence = screen_runner._daily_equity_guard_evidence(
        book=book,
        job_id="J3",
        as_of=as_of,
        dataset_manifest=manifest,
        mark_cache={},
        daily_loss_fraction=Decimal("0.0225"),
    )
    assert evidence["loss_guard_decision"] == "PASS"
    assert evidence["open_positions"][0]["mark_price"] == "977.51"
    assert evidence["daily_equity_delta_usdt"] == "-2.249"

    exact_path = _dataset_manifest_with_mark(case_dir / "exact", mark_price=Decimal("775"))
    exact_manifest = json.loads(exact_path.read_text(encoding="utf-8"))
    exact = screen_runner._daily_equity_guard_evidence(
        book=book,
        job_id="J3",
        as_of=as_of,
        dataset_manifest=exact_manifest,
        mark_cache={},
        daily_loss_fraction=Decimal("0.0225"),
    )
    assert exact["daily_equity_delta_usdt"] == "-22.5"
    assert exact["loss_guard_decision"] == "REJECT"
    assert exact["threshold_operator"] == "<="


def test_research_v2_daily_equity_is_causal_for_close_fill_and_funding_timing() -> None:
    case_dir = _case_dir("daily_equity_causal_timing")
    manifest_path = _dataset_manifest_with_mark(case_dir, mark_price=Decimal("1005.3143836"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    book = screen_runner.V2ReplayPortfolioBook(
        account_capital=Decimal("1000"),
        active=[
            screen_runner.V2ReplayExposure(
                symbol="AVAXUSDT",
                physical_symbol="AVAXUSDT",
                margin=Decimal("100"),
                gross_notional=Decimal("100"),
                stop_risk=Decimal("1"),
                release_at=datetime(2026, 8, 19, 0, 48, 59, 999999, tzinfo=UTC),
                context_id="ctx-closed-later",
                lifecycle_status="CLOSED",
                direction="LONG",
                entry_price=Decimal("1000"),
                quantity=Decimal("0.1"),
                entry_fee=Decimal("0"),
                opened_at=datetime(2026, 8, 19, 0, 6, 59, 999999, tzinfo=UTC),
                funding_events=(
                    {
                        "funding_timestamp": "2026-08-19T08:00:00Z",
                        "calculated_funding_cashflow": "-99",
                    },
                ),
            ),
            screen_runner.V2ReplayExposure(
                symbol="SUIUSDT",
                physical_symbol="SUIUSDT",
                margin=Decimal("100"),
                gross_notional=Decimal("100"),
                stop_risk=Decimal("1"),
                release_at=None,
                context_id="ctx-prefill",
                lifecycle_status="FILLED_OPEN",
                direction="LONG",
                entry_price=Decimal("1"),
                quantity=Decimal("100"),
                entry_fee=Decimal("0"),
                opened_at=datetime(2026, 8, 19, 5, 26, 59, 999999, tzinfo=UTC),
            ),
        ],
        account_events=[
            screen_runner.V2ReplayAccountEvent(
                timestamp=datetime(2026, 8, 19, 0, 48, 59, 999999, tzinfo=UTC),
                sequence=70,
                event_type="FINAL_CLOSE",
                context_id="ctx-closed-later",
                symbol="AVAXUSDT",
                physical_symbol="AVAXUSDT",
                realized_gross_pnl=Decimal("-1.3507956900"),
            ),
            screen_runner.V2ReplayAccountEvent(
                timestamp=datetime(2026, 8, 19, 8, 0, tzinfo=UTC),
                sequence=40,
                event_type="FUNDING_BOUNDARY",
                context_id="ctx-closed-later",
                symbol="AVAXUSDT",
                physical_symbol="AVAXUSDT",
                funding_amount=Decimal("-99"),
                cashflow_amount=Decimal("-99"),
            ),
        ],
    )

    at_0012 = screen_runner._daily_equity_guard_evidence(
        book=book,
        job_id="J3",
        as_of=datetime(2026, 8, 19, 0, 12, tzinfo=UTC),
        dataset_manifest=manifest,
        mark_cache={},
        daily_loss_fraction=Decimal("0.0225"),
    )
    assert at_0012["realized_gross_pnl_to_date"] == "0"
    assert at_0012["current_factual_equity"] == "1000.53143836"

    at_0519 = screen_runner._daily_equity_guard_evidence(
        book=book,
        job_id="J3",
        as_of=datetime(2026, 8, 19, 5, 19, tzinfo=UTC),
        dataset_manifest=manifest,
        mark_cache={},
        daily_loss_fraction=Decimal("0.0225"),
    )
    assert all(position["context_id"] != "ctx-prefill" for position in at_0519["open_positions"])

    at_0718 = screen_runner._daily_equity_guard_evidence(
        book=book,
        job_id="J3",
        as_of=datetime(2026, 8, 19, 7, 18, tzinfo=UTC),
        dataset_manifest=manifest,
        mark_cache={},
        daily_loss_fraction=Decimal("0.0225"),
    )
    assert at_0718["realized_funding_to_date"] == "0"


def test_research_v2_funding_events_use_boundary_mark_and_physical_symbol() -> None:
    order = {
        "order_spec_id": "order-avx",
        "symbol": "AVAXUSDT",
        "physical_symbol": "AVAXUSDT",
        "direction": "LONG",
        "entry": {"price": "7.601", "quantity": "32.8"},
    }
    events = screen_runner._funding_events_for_position(
        funding_facts=[
            {
                "symbol": "AVAXUSDT",
                "funding_time": "2026-08-21T16:00:00Z",
                "funding_rate": "0.0001",
                "mark_price": "7.617",
            }
        ],
        dataset_manifest=None,
        mark_cache=None,
        order=order,
        context_id="ctx-funding",
        opened_at=datetime(2026, 8, 21, 15, 0, tzinfo=UTC),
        closed_at=datetime(2026, 8, 21, 17, 0, tzinfo=UTC),
    )
    assert events[0]["physical_symbol"] == "AVAXUSDT"
    assert events[0]["factual_boundary_mark"] == "7.617"
    assert events[0]["calculated_funding_cashflow"] == "-0.02498376"

    pepe = dict(order)
    pepe.update({"order_spec_id": "order-pepe", "symbol": "PEPEUSDT", "physical_symbol": "1000PEPEUSDT", "entry": {"price": "0.003704", "quantity": "67400"}})
    pepe_events = screen_runner._funding_events_for_position(
        funding_facts=[
            {
                "symbol": "1000PEPEUSDT",
                "funding_time": "2026-08-21T16:00:00Z",
                "funding_rate": "0.0001",
                "mark_price": "0.003694",
            }
        ],
        dataset_manifest=None,
        mark_cache=None,
        order=pepe,
        context_id="ctx-pepe-funding",
        opened_at=datetime(2026, 8, 21, 15, 0, tzinfo=UTC),
        closed_at=datetime(2026, 8, 21, 17, 0, tzinfo=UTC),
    )
    assert pepe_events[0]["physical_symbol"] == "1000PEPEUSDT"
    assert pepe_events[0]["calculated_funding_cashflow"] == "-0.02489756"

    sui = dict(order)
    sui.update({"order_spec_id": "order-sui", "symbol": "SUIUSDT", "physical_symbol": "SUIUSDT", "entry": {"price": "0.738", "quantity": "130"}})
    sui_events = screen_runner._funding_events_for_position(
        funding_facts=[
            {
                "symbol": "SUIUSDT",
                "funding_time": "2026-08-20T16:00:00Z",
                "funding_rate": "0.0001",
                "mark_price": "0.73945",
            }
        ],
        dataset_manifest=None,
        mark_cache=None,
        order=sui,
        context_id="ctx-sui-funding",
        opened_at=datetime(2026, 8, 20, 15, 0, tzinfo=UTC),
        closed_at=datetime(2026, 8, 20, 17, 0, tzinfo=UTC),
    )
    assert sui_events[0]["calculated_funding_cashflow"] == "-0.00961285"


def test_research_v2_lifecycle_consumes_canonical_mark_backed_funding_facts() -> None:
    case_dir = _case_dir("lifecycle_mark_backed_funding")
    manifest_path = _dataset_manifest_with_mark(case_dir, mark_price=Decimal("7.617"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    mark_path = Path(manifest["files"][0]["local_path"])
    rows = json.loads(mark_path.read_text(encoding="utf-8"))
    rows[0]["open_time"] = "2026-08-19T15:59:00Z"
    rows[0]["close_time"] = "2026-08-19T16:00:00Z"
    mark_path.write_text(json.dumps(rows), encoding="utf-8")
    manifest["files"][0]["sha256"] = sha256(mark_path.read_bytes()).hexdigest()
    raw_facts = (
        {
            "symbol": "AVAXUSDT",
            "funding_time": "2026-08-19T16:00:00Z",
            "funding_rate": "0.0001",
        },
    )
    canonical_facts = screen_runner._canonical_lifecycle_funding_facts(
        raw_facts,
        dataset_manifest=manifest,
        mark_cache={},
        physical_symbol="AVAXUSDT",
    )
    order = {
        "order_spec": {
            "order_spec_id": "order-lifecycle-funding",
            "decision_cycle_id": "decision-lifecycle-funding",
            "set_result_id": "set-lifecycle-funding",
            "position_decision_id": "position-lifecycle-funding",
            "capital_grant_id": "grant-lifecycle-funding",
            "symbol": "AVAXUSDT",
            "physical_symbol": "AVAXUSDT",
            "direction": "LONG",
            "entry": {"price": "7.5", "quantity": "32.8"},
            "stop_loss": {"price": "7.4"},
            "take_profit": {"price": "7.7"},
            "economics": {"maker_fee_rate": "0.0002", "taker_fee_rate": "0.00055"},
        }
    }
    lifecycle = screen_runner._closed_lifecycle_result(
        spec=order["order_spec"],
        direction="LONG",
        entry=Decimal("7.5"),
        quantity=Decimal("32.8"),
        exit_price=Decimal("7.7"),
        leverage=Decimal("1"),
        maker_fee_rate=Decimal("0.0002"),
        taker_fee_rate=Decimal("0.00055"),
        submitted=datetime(2026, 8, 19, 0, 0, tzinfo=UTC),
        proxy=Decimal("7.5"),
        entry_filled_at="2026-08-19T15:59:00Z",
        exit_reason="TAKE_PROFIT",
        exit_at="2026-08-19T16:01:00Z",
        tp=Decimal("7.7"),
        sl=Decimal("7.4"),
        funding=screen_runner._research_v1_backtest_funding_amount(
            funding_facts=canonical_facts,
            spec=order["order_spec"],
            direction="LONG",
            quantity=Decimal("32.8"),
            entry=Decimal("7.5"),
            opened_at=datetime(2026, 8, 19, 15, 59, tzinfo=UTC),
            closed_at=datetime(2026, 8, 19, 16, 1, tzinfo=UTC),
        ),
    )

    assert lifecycle.status == "CLOSED"
    assert lifecycle.closed_result["funding"] == "-0.02498376"


def test_research_v2_endpoint_open_funding_excludes_replay_right_boundary() -> None:
    order = {
        "order_spec_id": "order-endpoint",
        "symbol": "AVAXUSDT",
        "physical_symbol": "AVAXUSDT",
        "direction": "SHORT",
        "entry": {"price": "7.323", "quantity": "14.6"},
        "economics": {"maker_fee_rate": "0.0002"},
    }
    events = screen_runner._funding_events_for_position(
        funding_facts=(
            {"symbol": "AVAXUSDT", "funding_time": "2026-08-25T16:00:00Z", "funding_rate": "0.0001", "mark_price": "7.4"},
            {"symbol": "AVAXUSDT", "funding_time": "2026-08-26T00:00:00Z", "funding_rate": "0.0001", "mark_price": "7.323"},
        ),
        dataset_manifest=None,
        mark_cache=None,
        order=order,
        context_id="endpoint",
        opened_at=datetime(2026, 8, 25, 15, 59, tzinfo=UTC),
        closed_at=datetime(2026, 8, 26, 0, 0, tzinfo=UTC),
        include_right_boundary=False,
    )

    assert [event["funding_timestamp"] for event in events] == ["2026-08-25T16:00:00Z"]


def test_research_v2_account_event_ledger_sorted_per_job() -> None:
    output = _case_dir("account_event_ledger_sorted") / "out"
    output.mkdir()
    screen_runner.append_jsonl(
        output / "account_event_ledger.jsonl",
        {"job_id": "J3", "timestamp": "2026-08-19T00:10:00Z", "sequence": 70, "context_id": "b", "event_type": "FINAL_CLOSE"},
    )
    screen_runner.append_jsonl(
        output / "account_event_ledger.jsonl",
        {"job_id": "J3", "timestamp": "2026-08-19T00:05:00Z", "sequence": 20, "context_id": "a", "event_type": "ENTRY_FILLED"},
    )
    screen_runner._rewrite_account_event_ledger_sorted(output)

    rows = screen_runner.read_jsonl(output / "account_event_ledger.jsonl")
    assert [row["event_type"] for row in rows] == ["ENTRY_FILLED", "FINAL_CLOSE"]


def test_research_v2_funding_missing_boundary_mark_fails_closed_without_entry_fallback() -> None:
    order = {
        "order_spec_id": "order-no-mark",
        "symbol": "AVAXUSDT",
        "physical_symbol": "AVAXUSDT",
        "direction": "LONG",
        "entry": {"price": "7.601", "quantity": "32.8"},
    }
    with pytest.raises(ResearchV2RunnerError, match="RATE_OR_MARK_MISSING"):
        screen_runner._funding_events_for_position(
            funding_facts=[
                {
                    "symbol": "AVAXUSDT",
                    "funding_time": "2026-08-21T16:00:00Z",
                    "funding_rate": "0.0001",
                }
            ],
            dataset_manifest=None,
            mark_cache=None,
            order=order,
            context_id="ctx-no-mark",
            opened_at=datetime(2026, 8, 21, 15, 0, tzinfo=UTC),
            closed_at=datetime(2026, 8, 21, 17, 0, tzinfo=UTC),
        )


def test_research_v2_daily_guard_timing_witness_decisions() -> None:
    case_dir = _case_dir("daily_guard_timing_decisions")
    manifest = json.loads(_dataset_manifest_with_mark(case_dir, mark_price=Decimal("100")).read_text(encoding="utf-8"))
    as_of = datetime(2026, 8, 19, 12, 0, tzinfo=UTC)

    def decision(delta: Decimal) -> str:
        book = screen_runner.V2ReplayPortfolioBook(
            account_capital=Decimal("1000"),
            active=[],
            account_events=[
                screen_runner.V2ReplayAccountEvent(
                    timestamp=as_of,
                    sequence=70,
                    event_type="FINAL_CLOSE",
                    context_id="ctx-delta",
                    symbol="AVAXUSDT",
                    physical_symbol="AVAXUSDT",
                    realized_gross_pnl=delta,
                )
            ],
        )
        evidence = screen_runner._daily_equity_guard_evidence(
            book=book,
            job_id="J3",
            as_of=as_of,
            dataset_manifest=manifest,
            mark_cache={},
            daily_loss_fraction=Decimal("0.0225"),
        )
        return evidence["loss_guard_decision"]

    assert decision(Decimal("-19.6983794")) == "PASS"
    assert decision(Decimal("-23.8624474")) == "REJECT"
    assert decision(Decimal("-23.1493282")) == "REJECT"


def test_research_v2_day_opening_equity_is_frozen_and_uses_boundary_mtm() -> None:
    case_dir = _case_dir("immutable_day_opening")
    manifest = json.loads(
        _dataset_manifest_with_mark_rows(
            case_dir,
            [
                ("2026-08-21T20:59:00Z", "2026-08-21T21:00:00Z", Decimal("105")),
                ("2026-08-21T21:59:00Z", "2026-08-21T22:00:00Z", Decimal("107")),
                ("2026-08-21T23:29:00Z", "2026-08-21T23:30:00Z", Decimal("109")),
            ],
        ).read_text(encoding="utf-8")
    )
    book = screen_runner.V2ReplayPortfolioBook(
        account_capital=Decimal("1000"),
        active=[],
        account_events=[
            screen_runner.V2ReplayAccountEvent(
                timestamp=datetime(2026, 8, 21, 20, 0, tzinfo=UTC),
                sequence=screen_runner._EVENT_ORDER["ENTRY_FILLED"],
                event_type="ENTRY_FILLED",
                context_id="overnight",
                symbol="AVAXUSDT",
                physical_symbol="AVAXUSDT",
                order_spec_id="order-overnight",
                quantity=Decimal("1"),
                source_provenance={"entry_price": "100", "direction": "LONG"},
            ),
            screen_runner.V2ReplayAccountEvent(
                timestamp=datetime(2026, 8, 21, 23, 0, tzinfo=UTC),
                sequence=screen_runner._EVENT_ORDER["FINAL_CLOSE"],
                event_type="FINAL_CLOSE",
                context_id="overnight",
                symbol="AVAXUSDT",
                physical_symbol="AVAXUSDT",
                order_spec_id="order-overnight",
                quantity=Decimal("1"),
                realized_gross_pnl=Decimal("6"),
            ),
        ],
    )

    before_close = screen_runner._daily_equity_guard_evidence(
        book=book,
        job_id="J3",
        as_of=datetime(2026, 8, 21, 22, 0, tzinfo=UTC),
        dataset_manifest=manifest,
        mark_cache={},
        daily_loss_fraction=Decimal("0.0225"),
    )
    after_close = screen_runner._daily_equity_guard_evidence(
        book=book,
        job_id="J3",
        as_of=datetime(2026, 8, 21, 23, 30, tzinfo=UTC),
        dataset_manifest=manifest,
        mark_cache={},
        daily_loss_fraction=Decimal("0.0225"),
    )

    assert before_close["day_opening_equity"] == "1005"
    assert after_close["day_opening_equity"] == "1005"
    assert before_close["current_factual_equity"] == "1007"
    assert after_close["current_factual_equity"] == "1006"


def test_research_v2_daily_guard_cancels_pending_without_touching_open_position() -> None:
    pending = screen_runner.V2ReplayExposure(
        symbol="AVAXUSDT",
        physical_symbol="AVAXUSDT",
        margin=Decimal("100"),
        gross_notional=Decimal("100"),
        stop_risk=Decimal("1"),
        release_at=datetime(2026, 8, 19, 12, 15, tzinfo=UTC),
        context_id="pending",
        lifecycle_status="ACCEPTED_NOT_FILLED",
        opened_at=None,
    )
    filled = screen_runner.V2ReplayExposure(
        symbol="SUIUSDT",
        physical_symbol="SUIUSDT",
        margin=Decimal("100"),
        gross_notional=Decimal("100"),
        stop_risk=Decimal("1"),
        release_at=None,
        context_id="filled",
        lifecycle_status="FILLED_OPEN_AT_ENDPOINT",
        opened_at=datetime(2026, 8, 19, 11, 0, tzinfo=UTC),
        direction="LONG",
        entry_price=Decimal("1"),
        quantity=Decimal("100"),
    )
    book = screen_runner.V2ReplayPortfolioBook(account_capital=Decimal("1000"), active=[pending, filled])

    events = book.cancel_pending_for_daily_guard(as_of=datetime(2026, 8, 19, 12, 1, tzinfo=UTC))

    assert [event.event_type for event in events] == ["ORDER_CANCEL_REQUEST", "ENTRY_CANCELLED_UNFILLED", "RESERVATION_RELEASE"]
    assert {event.context_id for event in events} == {"pending"}
    assert [exposure.context_id for exposure in book.active] == ["filled"]


def test_research_v2_daily_guard_cancel_override_removes_future_fill_artifacts() -> None:
    output = _case_dir("daily_guard_cancel_override") / "out"
    output.mkdir()
    accepted = {
        "job_id": "J3",
        "context_id": "ctx",
        "timestamp": "2026-08-19T12:00:00Z",
        "event_type": "ORDER_ACCEPTED",
        "sequence": 60,
        "order_spec_id": "order",
    }
    future_fill = {
        "job_id": "J3",
        "context_id": "ctx",
        "timestamp": "2026-08-19T12:04:00Z",
        "event_type": "ENTRY_FILLED",
        "sequence": 70,
        "order_spec_id": "order",
    }
    cancel_request = {
        "job_id": "J3",
        "context_id": "ctx",
        "timestamp": "2026-08-19T12:01:00Z",
        "event_type": "ORDER_CANCEL_REQUEST",
        "sequence": 45,
        "order_spec_id": "order",
    }
    terminal_cancel = {
        "job_id": "J3",
        "context_id": "ctx",
        "timestamp": "2026-08-19T12:01:00Z",
        "event_type": "ENTRY_CANCELLED_UNFILLED",
        "sequence": 46,
        "order_spec_id": "order",
    }
    release = {
        "job_id": "J3",
        "context_id": "ctx",
        "timestamp": "2026-08-19T12:01:00Z",
        "event_type": "RESERVATION_RELEASE",
        "sequence": 50,
        "order_spec_id": "order",
    }
    for row in (accepted, future_fill, cancel_request, terminal_cancel, release):
        screen_runner.append_jsonl(output / "account_event_ledger.jsonl", row)
    screen_runner.append_jsonl(
        output / "lifecycle_results.jsonl",
        {
            "index": 1,
            "context": {"context_id": "ctx", "job_id": "J3"},
            "result": {
                "order_spec": {"order_spec": {"order_spec_id": "order"}},
                "backtest_lifecycle": {"accepted": True, "filled": True, "status": "CLOSED", "evidence": {"entry_filled_at": "2026-08-19T12:04:00Z"}},
                "account_event_ledger": [accepted, future_fill],
            },
        },
    )
    screen_runner.append_jsonl(output / "funding_boundary_evidence.jsonl", {"context_id": "ctx", "funding_boundary_crossed": True})
    screen_runner.append_jsonl(output / "intrabar_sequence_evidence.jsonl", {"context_id": "ctx"})

    screen_runner._apply_daily_guard_cancellation_overrides(output)

    ledger = screen_runner.read_jsonl(output / "account_event_ledger.jsonl")
    assert [row["event_type"] for row in ledger] == ["ORDER_ACCEPTED", "ORDER_CANCEL_REQUEST", "ENTRY_CANCELLED_UNFILLED", "RESERVATION_RELEASE"]
    result = screen_runner.read_jsonl(output / "lifecycle_results.jsonl")[0]["result"]
    assert result["backtest_lifecycle"]["status"] == "ENTRY_CANCELLED_UNFILLED"
    assert result["backtest_lifecycle"]["filled"] is False
    assert result["reservation_released"] is True
    assert screen_runner.read_jsonl(output / "funding_boundary_evidence.jsonl") == []
    assert screen_runner.read_jsonl(output / "intrabar_sequence_evidence.jsonl") == []


def test_research_v2_factual_timeline_guard_cancels_pending_at_first_minute_breach() -> None:
    case_dir = _case_dir("factual_timeline_guard_first_breach")
    manifest = json.loads(
        _dataset_manifest_with_mark_rows(
            case_dir,
            [
                ("2026-08-19T00:00:00Z", "2026-08-19T00:01:00Z", Decimal("977.40")),
                ("2026-08-19T00:01:00Z", "2026-08-19T00:02:00Z", Decimal("981.00")),
            ],
        ).read_text(encoding="utf-8")
    )
    open_position = screen_runner.V2ReplayExposure(
        symbol="AVAXUSDT",
        physical_symbol="AVAXUSDT",
        margin=Decimal("100"),
        gross_notional=Decimal("100"),
        stop_risk=Decimal("1"),
        release_at=None,
        context_id="open",
        lifecycle_status="FILLED_OPEN_AT_ENDPOINT",
        order_spec_id="open-order",
        direction="LONG",
        entry_price=Decimal("1000"),
        quantity=Decimal("1"),
        opened_at=datetime(2026, 8, 19, 0, 0, tzinfo=UTC),
    )
    pending = screen_runner.V2ReplayExposure(
        symbol="SUIUSDT",
        physical_symbol="SUIUSDT",
        margin=Decimal("100"),
        gross_notional=Decimal("100"),
        stop_risk=Decimal("1"),
        release_at=datetime(2026, 8, 19, 0, 15, tzinfo=UTC),
        context_id="pending",
        lifecycle_status="ACCEPTED_NOT_FILLED",
        order_spec_id="pending-order",
        opened_at=datetime(2026, 8, 19, 0, 3, tzinfo=UTC),
    )
    book = screen_runner.V2ReplayPortfolioBook(account_capital=Decimal("1000"), active=[open_position, pending])

    evidence, events = screen_runner._factual_timeline_daily_guard_enforcement(
        book=book,
        job_id="J3",
        start_at=datetime(2026, 8, 19, 0, 0, tzinfo=UTC),
        window_end=datetime(2026, 8, 19, 0, 10, tzinfo=UTC),
        dataset_manifest=manifest,
        mark_cache={},
        daily_loss_fraction=Decimal("0.0225"),
        trigger_context_id="pending",
    )

    assert evidence[0]["evaluated_at"] == "2026-08-19T00:01:00Z"
    assert evidence[0]["breached"] is True
    assert evidence[0]["pending_order_context_ids"] == ["pending"]
    assert evidence[0]["protected_open_position_context_ids"] == ["open"]
    assert [event.event_type for event in events] == ["ORDER_CANCEL_REQUEST", "ENTRY_CANCELLED_UNFILLED", "RESERVATION_RELEASE"]
    assert all(event.timestamp == datetime(2026, 8, 19, 0, 1, tzinfo=UTC) for event in events)
    assert [exposure.context_id for exposure in book.active] == ["open", "pending"]
    assert not book.pending_entry_exposures(datetime(2026, 8, 19, 0, 1, tzinfo=UTC))


def test_research_v2_factual_timeline_guard_cancels_all_pending_and_keeps_open_protection() -> None:
    case_dir = _case_dir("factual_timeline_guard_multiple_pending")
    manifest = json.loads(
        _dataset_manifest_with_mark_rows(
            case_dir,
            [("2026-08-19T00:00:00Z", "2026-08-19T00:01:00Z", Decimal("977.40"))],
        ).read_text(encoding="utf-8")
    )
    open_position = screen_runner.V2ReplayExposure(
        symbol="AVAXUSDT",
        physical_symbol="AVAXUSDT",
        margin=Decimal("100"),
        gross_notional=Decimal("100"),
        stop_risk=Decimal("1"),
        release_at=None,
        context_id="open",
        lifecycle_status="FILLED_OPEN_AT_ENDPOINT",
        order_spec_id="open-order",
        direction="LONG",
        entry_price=Decimal("1000"),
        quantity=Decimal("1"),
        opened_at=datetime(2026, 8, 19, 0, 0, tzinfo=UTC),
    )
    pending_a = screen_runner.V2ReplayExposure(
        symbol="SUIUSDT",
        physical_symbol="SUIUSDT",
        margin=Decimal("100"),
        gross_notional=Decimal("100"),
        stop_risk=Decimal("1"),
        release_at=datetime(2026, 8, 19, 0, 15, tzinfo=UTC),
        context_id="pending-a",
        lifecycle_status="ACCEPTED_NOT_FILLED",
        order_spec_id="pending-a-order",
        opened_at=datetime(2026, 8, 19, 0, 3, tzinfo=UTC),
    )
    pending_b = screen_runner.V2ReplayExposure(
        symbol="PEPEUSDT",
        physical_symbol="1000PEPEUSDT",
        margin=Decimal("100"),
        gross_notional=Decimal("100"),
        stop_risk=Decimal("1"),
        release_at=datetime(2026, 8, 19, 0, 15, tzinfo=UTC),
        context_id="pending-b",
        lifecycle_status="ACCEPTED_NOT_FILLED",
        order_spec_id="pending-b-order",
        opened_at=datetime(2026, 8, 19, 0, 4, tzinfo=UTC),
    )
    book = screen_runner.V2ReplayPortfolioBook(account_capital=Decimal("1000"), active=[open_position, pending_a, pending_b])

    evidence, events = screen_runner._factual_timeline_daily_guard_enforcement(
        book=book,
        job_id="J3",
        start_at=datetime(2026, 8, 19, 0, 0, tzinfo=UTC),
        window_end=datetime(2026, 8, 19, 0, 10, tzinfo=UTC),
        dataset_manifest=manifest,
        mark_cache={},
        daily_loss_fraction=Decimal("0.0225"),
        trigger_context_id="pending-a",
    )

    assert set(evidence[0]["pending_order_context_ids"]) == {"pending-a", "pending-b"}
    assert [event.event_type for event in events].count("ENTRY_CANCELLED_UNFILLED") == 2
    assert [event.event_type for event in events].count("RESERVATION_RELEASE") == 2
    assert [exposure.context_id for exposure in book.active] == ["open", "pending-a", "pending-b"]
    assert not book.pending_entry_exposures(datetime(2026, 8, 19, 0, 1, tzinfo=UTC))


def test_research_v2_factual_timeline_guard_continues_after_earliest_pending_fill() -> None:
    case_dir = _case_dir("factual_timeline_guard_staggered_pending")
    manifest = json.loads(
        _dataset_manifest_with_mark_rows(
            case_dir,
            [
                ("2026-08-19T00:00:00Z", "2026-08-19T00:01:00Z", Decimal("1000")),
                ("2026-08-19T00:01:00Z", "2026-08-19T00:02:00Z", Decimal("1000")),
                ("2026-08-19T00:02:00Z", "2026-08-19T00:03:00Z", Decimal("977.40")),
            ],
        ).read_text(encoding="utf-8")
    )
    open_position = screen_runner.V2ReplayExposure(
        symbol="AVAXUSDT",
        physical_symbol="AVAXUSDT",
        margin=Decimal("100"),
        gross_notional=Decimal("100"),
        stop_risk=Decimal("1"),
        release_at=None,
        context_id="open",
        lifecycle_status="FILLED_OPEN_AT_ENDPOINT",
        order_spec_id="open-order",
        direction="LONG",
        entry_price=Decimal("1000"),
        quantity=Decimal("1"),
        opened_at=datetime(2026, 8, 19, 0, 0, tzinfo=UTC),
    )
    fills_first = screen_runner.V2ReplayExposure(
        symbol="SUIUSDT",
        physical_symbol="SUIUSDT",
        margin=Decimal("100"),
        gross_notional=Decimal("100"),
        stop_risk=Decimal("1"),
        release_at=datetime(2026, 8, 19, 0, 15, tzinfo=UTC),
        context_id="fills-first",
        lifecycle_status="FILLED_OPEN_AT_ENDPOINT",
        order_spec_id="fills-first-order",
        opened_at=datetime(2026, 8, 19, 0, 1, tzinfo=UTC),
    )
    remains_pending = screen_runner.V2ReplayExposure(
        symbol="PEPEUSDT",
        physical_symbol="1000PEPEUSDT",
        margin=Decimal("100"),
        gross_notional=Decimal("100"),
        stop_risk=Decimal("1"),
        release_at=datetime(2026, 8, 19, 0, 15, tzinfo=UTC),
        context_id="remains-pending",
        lifecycle_status="ACCEPTED_NOT_FILLED",
        order_spec_id="remains-pending-order",
        opened_at=datetime(2026, 8, 19, 0, 4, tzinfo=UTC),
    )
    book = screen_runner.V2ReplayPortfolioBook(account_capital=Decimal("1000"), active=[open_position, fills_first, remains_pending])

    evidence, events = screen_runner._factual_timeline_daily_guard_enforcement(
        book=book,
        job_id="J3",
        start_at=datetime(2026, 8, 19, 0, 0, tzinfo=UTC),
        window_end=datetime(2026, 8, 19, 0, 10, tzinfo=UTC),
        dataset_manifest=manifest,
        mark_cache={},
        daily_loss_fraction=Decimal("0.0225"),
        trigger_context_id="fills-first",
    )

    assert [row["evaluated_at"] for row in evidence] == [
        "2026-08-19T00:01:00Z",
        "2026-08-19T00:02:00Z",
        "2026-08-19T00:03:00Z",
    ]
    assert evidence[0]["breached"] is False
    assert evidence[0]["pending_order_context_ids"] == ["remains-pending"]
    assert evidence[1]["breached"] is False
    assert evidence[1]["pending_order_context_ids"] == ["remains-pending"]
    assert evidence[2]["breached"] is True
    assert evidence[2]["pending_order_context_ids"] == ["remains-pending"]
    assert [event.context_id for event in events if event.event_type == "ENTRY_CANCELLED_UNFILLED"] == ["remains-pending"]
    assert {exposure.context_id for exposure in book.active} == {"open", "fills-first", "remains-pending"}
    assert not book.pending_entry_exposures(datetime(2026, 8, 19, 0, 3, tzinfo=UTC))


def test_research_v2_factual_guard_publish_rewrites_from_completed_ledger_state() -> None:
    case_dir = _case_dir("factual_guard_rewrite_completed_ledger")
    manifest = json.loads(
        _dataset_manifest_with_mark_rows(
            case_dir,
            [("2026-08-19T16:16:00Z", "2026-08-19T16:17:00Z", Decimal("0.0027093"))],
        ).read_text(encoding="utf-8")
    )
    output = case_dir / "out"
    output.mkdir()
    ledger_rows = [
        {
            "job_id": "J3",
            "timestamp": "2026-08-19T16:15:00Z",
            "sequence": screen_runner._EVENT_ORDER["FINAL_CLOSE"],
            "event_type": "FINAL_CLOSE",
            "context_id": "ctx-before",
            "symbol": "AVAXUSDT",
            "physical_symbol": "AVAXUSDT",
            "order_spec_id": "order-before",
            "quantity": "1",
            "realized_gross_pnl": "-0.394626528374",
            "fee_amount": "0",
            "funding_amount": "0",
            "causal_sequence": 1,
        },
        {
            "job_id": "J3",
            "timestamp": "2026-08-19T16:16:59.999999Z",
            "sequence": screen_runner._EVENT_ORDER["ENTRY_FILLED"],
            "event_type": "ENTRY_FILLED",
            "context_id": "ctx-113",
            "symbol": "AVAXUSDT",
            "physical_symbol": "AVAXUSDT",
            "order_spec_id": "order-113",
            "quantity": "92300",
            "source_provenance": {"entry_price": "0.002707", "direction": "LONG"},
            "causal_sequence": 2,
        },
        {
            "job_id": "J3",
            "timestamp": "2026-08-19T16:16:59.999999Z",
            "sequence": screen_runner._EVENT_ORDER["ENTRY_FEE"],
            "event_type": "ENTRY_FEE",
            "context_id": "ctx-113",
            "symbol": "AVAXUSDT",
            "physical_symbol": "AVAXUSDT",
            "order_spec_id": "order-113",
            "quantity": "92300",
            "fee_amount": "0.04997122",
            "causal_sequence": 3,
        },
    ]
    screen_runner._write_jsonl(output / "account_event_ledger.jsonl", ledger_rows)
    stale = {
        "job_id": "J3",
        "context_id": "ctx-112",
        "lifecycle_index": 112,
        "evaluated_at": "2026-08-19T16:17:00Z",
        "configured_loss_threshold_fraction": "0.0225",
        "current_factual_equity": "999.605373471626",
        "daily_equity_delta_fraction": "-0.000394626528374",
        "open_positions": [],
        "protected_open_position_context_ids": [],
        "protected_open_position_order_spec_ids": [],
        "breached": False,
    }
    screen_runner._write_jsonl(output / "factual_timeline_daily_guard_evidence.jsonl", [stale])
    screen_runner._write_jsonl(
        output / "lifecycle_results.jsonl",
        [
            {
                "context": {"job_id": "J3", "context_id": "ctx-112"},
                "result": {
                    "factual_timeline_guard_evidence": [
                        {
                            **stale,
                            "current_factual_equity": "999.605373471626",
                            "open_positions": [],
                            "protected_open_position_context_ids": [],
                        }
                    ],
                    "backtest_lifecycle": {},
                },
            }
        ],
    )
    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")

    screen_runner._rewrite_factual_timeline_guard_evidence_from_event_ledger(
        output,
        selected_jobs=[job],
        dataset_manifest=manifest,
    )

    [rewritten] = screen_runner.read_jsonl(output / "factual_timeline_daily_guard_evidence.jsonl")
    assert rewritten["open_positions"][0]["context_id"] == "ctx-113"
    assert rewritten["current_factual_equity"] == "999.767692251626"
    assert rewritten["daily_equity_delta_fraction"] == "-0.000232307748374"
    assert rewritten["loss_guard_decision"] == "PASS"
    assert rewritten["protected_open_position_context_ids"] == ["ctx-113"]
    assert rewritten["protected_open_position_order_spec_ids"] == ["order-113"]

    [lifecycle_row] = screen_runner.read_jsonl(output / "lifecycle_results.jsonl")
    [embedded] = lifecycle_row["result"]["factual_timeline_guard_evidence"]
    assert embedded["open_positions"] == rewritten["open_positions"]
    assert embedded["current_factual_equity"] == "999.767692251626"
    assert embedded["daily_equity_delta_fraction"] == "-0.000232307748374"
    assert embedded["loss_guard_decision"] == "PASS"
    assert embedded["protected_open_position_context_ids"] == ["ctx-113"]
    assert embedded["protected_open_position_order_spec_ids"] == ["order-113"]


def test_research_v2_finalize_existing_run_is_evidence_only_and_reconciles_progress() -> None:
    case_dir = _case_dir("evidence_only_finalize")
    manifest_path = _dataset_manifest(case_dir)
    output = case_dir / "out"
    output.mkdir()
    screen_runner._write_jsonl(
        output / "account_event_ledger.jsonl",
        [
            {
                "job_id": "J3",
                "timestamp": "2026-08-19T00:10:00Z",
                "sequence": screen_runner._EVENT_ORDER["FINAL_CLOSE"],
                "event_type": "FINAL_CLOSE",
                "context_id": "ctx-closed",
                "symbol": "AVAXUSDT",
                "physical_symbol": "AVAXUSDT",
                "order_spec_id": "order-closed",
                "quantity": "1",
                "realized_gross_pnl": "1",
                "fee_amount": "0",
                "funding_amount": "0",
                "causal_sequence": 1,
            }
        ],
    )
    closed_result = {
        "gross_pnl": "1",
        "entry_fee": "0",
        "exit_fee": "0",
        "other_fees": "0",
        "funding": "0",
        "net_pnl": "1",
        "exit_vwap": "101",
        "quantity": "1",
    }
    screen_runner._write_jsonl(
        output / "lifecycle_results.jsonl",
        [
            {
                "context": {"job_id": "J3", "context_id": "ctx-closed"},
                "result": {
                    "order_spec": None,
                    "backtest_lifecycle": {
                        "accepted": True,
                        "filled": True,
                        "status": "CLOSED",
                        "closed_result": closed_result,
                    },
                },
            }
        ],
    )
    screen_runner._write_jsonl(
        output / "job_results.jsonl",
        [
            {
                "job_id": "J3",
                "status": "COMPLETE",
                "accepted": 1,
                "filled": 1,
                "closed": 1,
                "account_net": "1",
                "net_closed_pnl": "1",
                "gross_pnl": "1",
                "fees": "0",
                "funding": "0",
                "end_mtm_contribution": "0",
            }
        ],
    )
    (output / "progress.json").write_text(
        json.dumps({"status": "COMPLETE", "execution_contexts_done": 1, "execution_contexts_total": 1, "orders_created": 99, "fills": 99, "closed": 99}),
        encoding="utf-8",
    )
    before = screen_runner._economic_event_fingerprint(output)["digest"]

    summary = screen_runner.finalize_research_v2_existing_run(
        output_dir=output,
        dataset_path=manifest_path,
        jobs_arg="J3",
    )

    after = screen_runner._economic_event_fingerprint(output)["digest"]
    progress = json.loads((output / "progress.json").read_text(encoding="utf-8"))
    assert summary["mode"] == "EVIDENCE_ONLY_FINALIZATION"
    assert summary["economic_event_fingerprint_changed"] is False
    assert after == before
    assert progress["execution_contexts_done"] == 1
    assert progress["execution_contexts_total"] == 1
    assert progress["orders_created"] == 0
    assert progress["fills"] == 1
    assert progress["closed"] == 1


def test_research_v2_finalize_existing_run_does_not_apply_lifecycle_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    case_dir = _case_dir("evidence_only_no_lifecycle_overrides")
    manifest_path = _dataset_manifest(case_dir)
    output = case_dir / "out"
    output.mkdir()
    screen_runner._write_jsonl(output / "account_event_ledger.jsonl", [])
    screen_runner._write_jsonl(output / "lifecycle_results.jsonl", [])
    (output / "progress.json").write_text(json.dumps({"status": "COMPLETE"}), encoding="utf-8")
    captured: dict[str, object] = {}

    def fake_write_phase_b_job_results(*args, **kwargs) -> None:
        captured.update(kwargs)

    monkeypatch.setattr(screen_runner, "_write_phase_b_job_results", fake_write_phase_b_job_results)

    summary = screen_runner.finalize_research_v2_existing_run(
        output_dir=output,
        dataset_path=manifest_path,
        jobs_arg="J3",
    )

    assert summary["mode"] == "EVIDENCE_ONLY_FINALIZATION"
    assert captured["apply_daily_cancel_overrides"] is False


def test_research_v2_future_daily_cancel_remains_reserved_until_release_for_grant() -> None:
    book = screen_runner.V2ReplayPortfolioBook(
        account_capital=Decimal("1000"),
        active=[
            screen_runner.V2ReplayExposure(
                symbol="SUIUSDT",
                physical_symbol="SUIUSDT",
                margin=Decimal("242.353"),
                gross_notional=Decimal("242.353"),
                stop_risk=Decimal("2.3645295"),
                release_at=None,
                context_id="ctx-1739",
                lifecycle_status="FILLED_OPEN",
                opened_at=datetime(2026, 8, 22, 17, 0, tzinfo=UTC),
            ),
            screen_runner.V2ReplayExposure(
                symbol="AVAXUSDT",
                physical_symbol="AVAXUSDT",
                margin=Decimal("249.382"),
                gross_notional=Decimal("249.382"),
                stop_risk=Decimal("2.479673"),
                release_at=None,
                context_id="ctx-1740",
                lifecycle_status="FILLED_OPEN",
                opened_at=datetime(2026, 8, 22, 17, 1, tzinfo=UTC),
            ),
            screen_runner.V2ReplayExposure(
                symbol="PEPEUSDT",
                physical_symbol="1000PEPEUSDT",
                margin=Decimal("108.0405"),
                gross_notional=Decimal("108.0405"),
                stop_risk=Decimal("1.24856075"),
                release_at=datetime(2026, 8, 22, 17, 59, tzinfo=UTC),
                context_id="ctx-1757",
                lifecycle_status="ACCEPTED_NOT_FILLED",
                opened_at=datetime(2026, 8, 22, 17, 59, tzinfo=UTC),
            ),
        ],
    )
    cancel_events = book.cancel_pending_for_daily_guard(
        as_of=datetime(2026, 8, 22, 17, 46, tzinfo=UTC),
        retain_until_release=True,
    )

    assert [event.event_type for event in cancel_events] == ["ORDER_CANCEL_REQUEST", "ENTRY_CANCELLED_UNFILLED", "RESERVATION_RELEASE"]
    book.apply_due(datetime(2026, 8, 22, 17, 44, tzinfo=UTC))
    state = book.state_for_symbol("SUIUSDT")
    profile = screen_runner.build_research_v2_canonical_execution_profile(next(job for job in load_ordered_jobs() if job.job_id == "J3"))
    grant = screen_runner.evaluate_research_v2_portfolio_grant(profile=profile, state=state).to_payload()["v2_portfolio_grant"]

    assert state.committed_margin == Decimal("599.7755")
    assert state.gross_notional == Decimal("599.7755")
    assert state.stop_risk == Decimal("6.09276325")
    assert state.open_pending_count == 3
    assert grant["free_margin"] == "0.2245"
    assert grant["remaining_gross_notional"] == "1200.2245"
    assert grant["remaining_stop_risk"] == "8.90723675"
    assert grant["remaining_global_slots"] == 0
    assert grant["status"] == "BLOCK"


def test_research_v2_final_progress_reconciles_from_authoritative_lifecycle_rows() -> None:
    output = _case_dir("final_progress_reconcile") / "out"
    output.mkdir()
    stale = {
        "status": "COMPLETE",
        "position_evaluations": 3,
        "orders_created": 3,
        "fills": 3,
        "closed": 3,
        "execution_contexts_done": 2,
        "execution_contexts_total": 3,
    }
    (output / "progress.json").write_text(json.dumps(stale), encoding="utf-8")
    rows = [
        {"result": {"order_spec": {"order_spec": {}}, "backtest_lifecycle": {"filled": True, "status": "CLOSED"}}},
        {"result": {"order_spec": {"order_spec": {}}, "backtest_lifecycle": {"filled": True, "status": "FILLED_OPEN_AT_ENDPOINT"}}},
        {"result": {"order_spec": None, "backtest_lifecycle": {}}},
    ]

    screen_runner._reconcile_final_progress_counts(output, rows)

    progress = json.loads((output / "progress.json").read_text(encoding="utf-8"))
    assert progress["position_evaluations"] == 3
    assert progress["orders_created"] == 2
    assert progress["fills"] == 2
    assert progress["closed"] == 1
    assert progress["execution_contexts_done"] == 3
    assert progress["execution_contexts_total"] == 3
    assert progress["progress_pct"] == 100.0


def test_research_v2_intrabar_evidence_exports_full_raw_minute_with_source_identity() -> None:
    rows = tuple(
        screen_runner.RawTradePoint(
            datetime(2026, 8, 19, 22, 0, idx, tzinfo=UTC),
            Decimal(price),
            Decimal("1"),
            idx,
            "AVAXUSDT2026-08-19.csv.gz",
        )
        for idx, price in enumerate(("6.833", "6.850", "6.861"))
    )
    spec = {
        "physical_symbol": "AVAXUSDT",
        "symbol": "AVAXUSDT",
        "spec_created_at": "2026-08-19T21:59:00Z",
        "entry": {"price": "6.833"},
        "stop_loss": {"price": "6.861"},
        "take_profit": {"price": "6.777"},
    }

    evidence = screen_runner._intrabar_sequence_evidence(
        rows=rows,
        spec=spec,
        entry_time=rows[0].occurred_at,
        resolution="RESOLVED_STOP_LOSS",
        exit_event=rows[-1],
        source_identity={"source_file": "AVAXUSDT2026-08-19.csv.gz", "source_hash": "abc", "physical_symbol": "AVAXUSDT"},
        evidence_start=datetime(2026, 8, 19, 21, 59, tzinfo=UTC),
        evidence_end=datetime(2026, 8, 19, 22, 1, tzinfo=UTC),
    )

    assert evidence["raw_trade_witness_coverage"] == "FULL_RAW_MINUTE"
    assert evidence["raw_trade_witness_count"] == 3
    assert evidence["source_file"] == "AVAXUSDT2026-08-19.csv.gz"
    assert evidence["evidence_coverage_start"] == "2026-08-19T21:59:00Z"
    assert evidence["acceptance_prefix_unverified"] is False
    assert any(row["price"] == "6.861" and row["timestamp"] == "2026-08-19T22:00:02Z" for row in evidence["raw_trade_witness"])


def test_research_v2_account_event_ledger_uses_parsed_time_and_release_before_acceptance() -> None:
    output = _case_dir("account_event_ledger_parsed_priority") / "out"
    output.mkdir()
    rows = [
        {"job_id": "J3", "timestamp": "2026-08-23T22:01:00.522700Z", "sequence": 80, "context_id": "b", "event_type": "ENTRY_FEE"},
        {"job_id": "J3", "timestamp": "2026-08-23T22:01:00Z", "sequence": 60, "context_id": "a", "event_type": "ORDER_ACCEPTED"},
        {"job_id": "J3", "timestamp": "2026-08-23T22:05:00Z", "sequence": 60, "context_id": "new", "event_type": "ORDER_ACCEPTED"},
        {"job_id": "J3", "timestamp": "2026-08-23T22:05:00Z", "sequence": 50, "context_id": "old", "event_type": "RESERVATION_RELEASE"},
        {"job_id": "J3", "timestamp": "2026-08-23T22:06:00Z", "sequence": 60, "causal_sequence": 9, "context_id": "second", "event_type": "ORDER_ACCEPTED"},
        {"job_id": "J3", "timestamp": "2026-08-23T22:06:00Z", "sequence": 60, "causal_sequence": 8, "context_id": "first", "event_type": "ORDER_ACCEPTED"},
    ]
    for row in rows:
        screen_runner.append_jsonl(output / "account_event_ledger.jsonl", row)

    screen_runner._rewrite_account_event_ledger_sorted(output)

    ordered = screen_runner.read_jsonl(output / "account_event_ledger.jsonl")
    assert [row["event_type"] for row in ordered[:2]] == ["ORDER_ACCEPTED", "ENTRY_FEE"]
    same_time = [row for row in ordered if row["timestamp"] == "2026-08-23T22:05:00Z"]
    assert [row["event_type"] for row in same_time] == ["RESERVATION_RELEASE", "ORDER_ACCEPTED"]
    same_time_admissions = [row for row in ordered if row["timestamp"] == "2026-08-23T22:06:00Z"]
    assert [row["context_id"] for row in same_time_admissions] == ["first", "second"]


def test_research_v2_funding_provenance_distinguishes_rate_and_mark_sources() -> None:
    case_dir = _case_dir("funding_provenance")
    manifest = json.loads(_dataset_manifest_with_mark_rows(case_dir, [("2026-08-19T15:59:00Z", "2026-08-19T16:00:00Z", Decimal("7.617"))]).read_text(encoding="utf-8"))
    funding_file = case_dir / "dataset" / "AVAXUSDT__funding_fixture.json"
    funding_file.write_text(json.dumps([{"symbol": "AVAXUSDT", "funding_time": "2026-08-19T16:00:00Z", "funding_rate": "0.0001"}]), encoding="utf-8")
    manifest["files"].append(
        {
            "type": "funding_facts",
            "symbol": "AVAXUSDT",
            "physical_symbol": "AVAXUSDT",
            "local_path": str(funding_file),
            "sha256": sha256(funding_file.read_bytes()).hexdigest(),
        }
    )
    facts = screen_runner._canonical_lifecycle_funding_facts(
        json.loads(funding_file.read_text(encoding="utf-8")),
        dataset_manifest=manifest,
        mark_cache={},
        physical_symbol="AVAXUSDT",
    )
    event = screen_runner._funding_events_for_position(
        funding_facts=facts,
        dataset_manifest=manifest,
        mark_cache={},
        order={"order_spec_id": "order", "symbol": "AVAXUSDT", "physical_symbol": "AVAXUSDT", "direction": "LONG", "entry": {"price": "7.5", "quantity": "32.8"}},
        context_id="ctx",
        opened_at=datetime(2026, 8, 19, 15, 0, tzinfo=UTC),
        closed_at=datetime(2026, 8, 19, 17, 0, tzinfo=UTC),
    )[0]

    assert event["funding_source_hash"] == manifest["files"][1]["sha256"]
    assert event["mark_source_hash"] == manifest["files"][0]["sha256"]
    assert event["mark_source_provenance"] == manifest["files"][0]["local_path"]
    assert event["calculated_funding_cashflow"] == "-0.02498376"


def test_research_v2_mtm_series_includes_one_minute_marks_while_position_open() -> None:
    case_dir = _case_dir("mtm_one_minute_cadence")
    output = case_dir / "out"
    output.mkdir(parents=True)
    manifest = json.loads(
        _dataset_manifest_with_mark_rows(
            case_dir,
            [
                ("2026-08-19T00:00:00Z", "2026-08-19T00:01:00Z", Decimal("101")),
                ("2026-08-19T00:01:00Z", "2026-08-19T00:02:00Z", Decimal("102")),
                ("2026-08-19T00:02:00Z", "2026-08-19T00:03:00Z", Decimal("103")),
            ],
        ).read_text(encoding="utf-8")
    )
    for row in (
        {"job_id": "J3", "timestamp": "2026-08-19T00:00:30Z", "sequence": 70, "event_type": "ENTRY_FILLED", "context_id": "ctx", "order_spec_id": "order", "symbol": "AVAXUSDT", "physical_symbol": "AVAXUSDT", "quantity": "1", "source_provenance": {"entry_price": "100", "direction": "LONG"}},
        {"job_id": "J3", "timestamp": "2026-08-19T00:03:30Z", "sequence": 40, "event_type": "FINAL_CLOSE", "context_id": "ctx", "order_spec_id": "order", "symbol": "AVAXUSDT", "physical_symbol": "AVAXUSDT", "quantity": "1", "realized_gross_pnl": "4"},
    ):
        screen_runner.append_jsonl(output / "account_event_ledger.jsonl", row)

    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")
    screen_runner._write_factual_mtm_series_from_event_ledger(output, selected_jobs=[job], dataset_manifest=manifest)

    rows = screen_runner.read_jsonl(output / "factual_mtm_equity_series.jsonl")
    timestamps = {row["timestamp"] for row in rows}
    assert "2026-08-19T00:01:00Z" in timestamps
    assert "2026-08-19T00:02:00Z" in timestamps
    assert any("ONE_MINUTE_WHILE_OPEN" in row["series_cadence"] for row in rows)


def test_research_v2_filled_open_keeps_ownership_closed_releases_and_no_double_release(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case_dir = _case_dir("filled_and_closed_ownership")
    manifest_path = _dataset_manifest_with_candles(case_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")
    context = _single_materialized_context(manifest_path, job=job, output_dir=case_dir / "source")
    key = str(context["execution_profile_fingerprint"])

    filled_state: dict[str, object] = {}
    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_filled_open)
    filled = _replay_one_context(
        context=context,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=filled_state,
    )
    assert filled["backtest_lifecycle"]["filled"] is True
    assert filled["reservation_released"] is False
    assert filled["state_committed"] is True
    assert _book_state(filled_state, context, "AVAXUSDT").open_pending_count == 1
    assert _book_state(filled_state, context, "AVAXUSDT").coin_open_pending_count == 1

    closed_state: dict[str, object] = {}
    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_closed)
    closed = _replay_one_context(
        context=context,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=closed_state,
    )
    assert closed["backtest_lifecycle"]["filled"] is True
    assert closed["backtest_lifecycle"]["status"] == "CLOSED"
    assert closed["reservation_released"] is True
    assert closed["state_committed"] is False
    assert _book_state(closed_state, context, "AVAXUSDT").open_pending_count == 1
    after_close = _clone_context_with_set_id(context, "set-result-after-close")
    _set_context_observed_at(after_close, "2026-08-19T04:20:00Z")
    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_filled_open)
    _replay_one_context(
        context=after_close,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=closed_state,
    )
    assert _book_state(closed_state, after_close, "AVAXUSDT").open_pending_count == 1

    expired_state: dict[str, object] = {}
    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_expired_unfilled)
    first = _replay_one_context(
        context=context,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=expired_state,
    )
    after_expiry = _clone_context_with_set_id(context, "set-result-after-expiry-double-release")
    _set_context_observed_at(after_expiry, "2026-08-19T04:20:00Z")
    second = _replay_one_context(
        context=after_expiry,
        dataset_manifest=manifest,
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=expired_state,
    )
    assert first["reservation_released"] is True
    assert second["reservation_released"] is True
    expired_book_state = _book_state(expired_state, after_expiry, "AVAXUSDT")
    assert expired_book_state.open_pending_count == 1
    assert expired_book_state.coin_open_pending_count == 1


def test_research_v2_checkpoint_resume_does_not_restore_expired_unfilled_reservation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    case_dir = _case_dir("ttl_resume_release")
    manifest_path = _dataset_manifest_with_candles(case_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")
    first = _single_materialized_context(manifest_path, job=job, output_dir=case_dir / "source")
    later = _clone_context_with_set_id(first, "set-result-resume-later")
    output = case_dir / "out"
    output.mkdir()

    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_expired_unfilled)
    completed, total = replay_research_v2_materialized_population(
        contexts=[first],
        dataset_manifest=manifest,
        output_dir=output,
        resume=False,
        progress=None,
        phase_a_units_done=0,
    )
    assert (completed, total) == (1, 1)

    monkeypatch.setattr(screen_runner, "_simulate_research_v1_backtest_lifecycle", _lifecycle_filled_open)
    completed, total = replay_research_v2_materialized_population(
        contexts=[first, later],
        dataset_manifest=manifest,
        output_dir=output,
        resume=True,
        progress=None,
        phase_a_units_done=0,
    )

    assert (completed, total) == (2, 2)
    rows = [json.loads(line) for line in (output / "lifecycle_results.jsonl").read_text(encoding="utf-8").splitlines()]
    later_rows = [row for row in rows if row["context"]["set_result_id"] == "set-result-resume-later"]
    assert len(later_rows) == 1
    assert later_rows[0]["result"].get("reason_code") != "MAX_COIN_OPEN_PENDING_REACHED"
    assert later_rows[0]["result"]["state_committed"] is True


def test_research_v2_summary_uses_fills_not_matched_for_unique_filled_episodes() -> None:
    case_dir = _case_dir("summary_unique_filled")
    manifest = _dataset_manifest_with_candles(case_dir)
    output = case_dir / "out"

    run_screen(dataset_path=manifest, output_dir=output, jobs_arg="J3")

    result = json.loads((output / "jobs" / "J3" / "job_result.json").read_text(encoding="utf-8"))
    summary = json.loads((output / "screen_summary.json").read_text(encoding="utf-8"))
    assert summary[0]["unique_filled_episodes"] == result["filled"]
    assert summary[0]["unique_filled_episodes"] <= summary[0]["fills"]


def test_research_v2_feature_timeline_matches_existing_definitions() -> None:
    case_dir = _case_dir("feature_equivalence")
    manifest_path = _dataset_manifest_with_candles(case_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    candles = _load_dataset_candles(manifest, physical_symbol="AVAXUSDT")
    timeline = build_research_v2_feature_timeline(symbol="AVAXUSDT", physical_symbol="AVAXUSDT", candles=candles)
    job = next(job for job in load_ordered_jobs() if job.job_id == "J3")
    cutoff = datetime(2026, 8, 19, 4, 1, tzinfo=UTC)

    signal, evidence = _evaluate_job_signal_from_timeline(job, timeline=timeline, cutoff=cutoff)

    assert signal.status.value == "PASS"
    assert evidence["return5_pct_points"] == str(return_pct_points(candles, cutoff=cutoff, window_minutes=5).value)
    assert evidence["return15_pct_points"] == str(return_pct_points(candles, cutoff=cutoff, window_minutes=15).value)
    assert evidence["atr15"] == q18_export_text(str(atr15(candles, cutoff=cutoff).value))


def test_research_v2_materializer_shares_j4_j7_set_scan() -> None:
    case_dir = _case_dir("j4_j7_shared")
    manifest_path = _dataset_manifest_with_candles(case_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    jobs = select_jobs("J4,J7", load_ordered_jobs())

    assert [job.job_id for job in _dedupe_set_scan_jobs(jobs)] == ["J4"]
    population = materialize_research_v2_set_population(jobs=jobs, dataset_manifest=manifest, output_dir=case_dir / "out")

    assert population["summary"]["unique_set_configurations_scanned"] == 1
    assert population["summary"]["j4_j7_shared_population"] is True
    assert (case_dir / "out" / "research_v2_set_population.json").exists()


def test_research_v2_screen_runner_rejects_hash_mismatch() -> None:
    case_dir = _case_dir("hash_mismatch")
    manifest_path = _dataset_manifest(case_dir)
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"][0]["sha256"] = "0" * 64
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    with pytest.raises(ResearchV2RunnerError, match="hash mismatch"):
        validate_dataset(manifest_path)


def _case_dir(name: str) -> Path:
    root = Path("runtime") / "tmp" / "research_v2_screen_runner" / name
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    return root


def _dataset_manifest(tmp_path: Path, *, status: str = "DATA_READY") -> Path:
    dataset = tmp_path / "dataset"
    dataset.mkdir()
    data_file = dataset / "data.json"
    data_file.write_text('{"ok":true}', encoding="utf-8")
    digest = sha256(data_file.read_bytes()).hexdigest()
    manifest = {
        "dataset_id": EXPECTED_DATASET_ID,
        "status": status,
        "validation": {"status": "PASS" if status == "DATA_READY" else "FAIL"},
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


def _dataset_manifest_with_candles(
    tmp_path: Path,
    *,
    swing_low: Decimal = Decimal("99.4"),
    raw_timestamp_mode: str = "iso",
) -> Path:
    dataset = tmp_path / "dataset"
    dataset.mkdir(parents=True)
    files = []
    for symbol in ("AVAXUSDT", "SUIUSDT", "1000PEPEUSDT"):
        candle_file = dataset / f"{symbol}__linear__1m__fixture.json"
        rows = _fixture_candles(symbol=symbol, triggering=symbol == "AVAXUSDT", swing_low=swing_low)
        candle_file.write_text(json.dumps(rows), encoding="utf-8")
        digest = sha256(candle_file.read_bytes()).hexdigest()
        files.append(
            {
                "type": "candles_1m",
                "symbol": "PEPEUSDT" if symbol == "1000PEPEUSDT" else symbol,
                "physical_symbol": symbol,
                "local_path": str(candle_file),
                "sha256": digest,
            }
        )
        raw_file = dataset / f"{symbol}_2026-08-19_raw_trades.csv.gz"
        _write_raw_fixture(raw_file, symbol=symbol, timestamp_mode=raw_timestamp_mode)
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


def _dataset_manifest_with_mark(tmp_path: Path, *, mark_price: Decimal) -> Path:
    dataset = tmp_path / "dataset"
    dataset.mkdir(parents=True)
    mark_file = dataset / "AVAXUSDT__linear__mark_1m__fixture.json"
    row = {
        "symbol": "AVAXUSDT",
        "category": "linear",
        "timeframe": "1m",
        "open_time": "2026-08-19T00:11:00Z",
        "close_time": "2026-08-19T00:12:00Z",
        "open": str(mark_price),
        "high": str(mark_price),
        "low": str(mark_price),
        "close": str(mark_price),
        "volume": "0",
        "turnover": "0",
        "completed": True,
    }
    mark_file.write_text(json.dumps([row]), encoding="utf-8")
    manifest = {
        "dataset_id": EXPECTED_DATASET_ID,
        "status": "DATA_READY",
        "validation": {"status": "PASS"},
        "files": [
            {
                "type": "mark_price_1m",
                "symbol": "AVAXUSDT",
                "physical_symbol": "AVAXUSDT",
                "local_path": str(mark_file),
                "sha256": sha256(mark_file.read_bytes()).hexdigest(),
            }
        ],
    }
    path = dataset / "dataset_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _dataset_manifest_with_mark_rows(tmp_path: Path, rows: list[tuple[str, str, Decimal]]) -> Path:
    dataset = tmp_path / "dataset"
    dataset.mkdir(parents=True)
    mark_file = dataset / "AVAXUSDT__linear__mark_1m__fixture.json"
    payload = [
        {
            "symbol": "AVAXUSDT",
            "category": "linear",
            "timeframe": "1m",
            "open_time": open_time,
            "close_time": close_time,
            "open": str(price),
            "high": str(price),
            "low": str(price),
            "close": str(price),
            "volume": "0",
            "turnover": "0",
            "completed": True,
        }
        for open_time, close_time, price in rows
    ]
    mark_file.write_text(json.dumps(payload), encoding="utf-8")
    manifest = {
        "dataset_id": EXPECTED_DATASET_ID,
        "status": "DATA_READY",
        "validation": {"status": "PASS"},
        "files": [
            {
                "type": "mark_price_1m",
                "symbol": "AVAXUSDT",
                "physical_symbol": "AVAXUSDT",
                "local_path": str(mark_file),
                "sha256": sha256(mark_file.read_bytes()).hexdigest(),
            }
        ],
    }
    path = dataset / "dataset_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    return path


def _fixture_candles(*, symbol: str, triggering: bool, swing_low: Decimal = Decimal("99.4")) -> list[dict[str, object]]:
    start = datetime(2026, 8, 19, 0, 0, tzinfo=UTC)
    rows: list[dict[str, object]] = []
    for index in range(270):
        open_time = start + timedelta(minutes=index)
        close_time = open_time + timedelta(minutes=1)
        close = Decimal("100")
        if triggering and index == 175:
            low = swing_low
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


def _write_raw_fixture(path: Path, *, symbol: str, timestamp_mode: str = "iso") -> None:
    start = datetime(2026, 8, 19, 4, 0, tzinfo=UTC)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as handle:
        handle.write("timestamp,symbol,side,size,price,tickDirection,trdMatchID,grossValue,homeNotional,foreignNotional\n")
        for index in range(30):
            ts = start + timedelta(minutes=index, seconds=5)
            ts_value = ts.isoformat().replace("+00:00", "Z")
            if timestamp_mode == "fractional_epoch":
                ts_value = str(Decimal(str(ts.timestamp())).quantize(Decimal("0.0001")))
            elif timestamp_mode == "invalid":
                ts_value = "1787097601.bad"
            price = Decimal("100.25") + Decimal(index) * Decimal("0.01")
            handle.write(f"{ts_value},{symbol},Buy,1,{price},PlusTick,{index},0,0,0\n")


def _single_materialized_context(manifest_path: Path, *, job, output_dir: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    population = materialize_research_v2_set_population(jobs=[job], dataset_manifest=manifest, output_dir=output_dir)
    contexts = _execution_contexts_from_population(population, [job])
    assert contexts
    return contexts[0]


def _single_population(manifest_path: Path, *, jobs_arg: str, output_dir: Path) -> dict[str, object]:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    jobs = select_jobs(jobs_arg, load_ordered_jobs())
    population = materialize_research_v2_set_population(jobs=jobs, dataset_manifest=manifest, output_dir=output_dir)
    assert population["records"]
    return population


def _clone_context_with_set_id(context: dict[str, object], set_result_id: str) -> dict[str, object]:
    cloned = dict(context)
    record = dict(cloned["record"])
    record["set_result_id"] = set_result_id
    resolution = json.loads(json.dumps(record["resolution"]))
    resolution["research_v2_set_resolution"]["set_result_id"] = set_result_id
    record["resolution"] = resolution
    cloned["record"] = record
    cloned["context_id"] = f"context-{set_result_id}"
    return cloned


def _set_context_observed_at(context: dict[str, object], observed_at: str) -> None:
    context["observed_at"] = observed_at
    record = dict(context["record"])
    record["observed_at"] = observed_at
    context["record"] = record


def _set_context_symbol(context: dict[str, object], symbol: str) -> None:
    context["symbol"] = symbol
    record = dict(context["record"])
    record["symbol"] = symbol
    record["physical_symbol"] = symbol
    resolution = json.loads(json.dumps(record["resolution"]))
    resolution["research_v2_set_resolution"]["symbol"] = symbol
    resolution["research_v2_set_resolution"]["physical_symbol"] = symbol
    record["resolution"] = resolution
    context["record"] = record


def _set_context_job(context: dict[str, object], job) -> None:
    profile = screen_runner.build_research_v2_canonical_execution_profile(job)
    context["job"] = job
    context["job_id"] = job.job_id
    context["execution_profile_fingerprint"] = profile.config_fingerprint
    context["context_id"] = f"{context['context_id']}-{job.job_id}"


def _book_state(portfolio_state: dict[str, object], context: dict[str, object], symbol: str):
    key = f"{context['job_id']}:{context['execution_profile_fingerprint']}"
    book = portfolio_state[key]
    return book.state_for_symbol(symbol)


def _lifecycle_expired_unfilled(**_kwargs) -> ResearchV1BacktestLifecycleResult:
    return ResearchV1BacktestLifecycleResult(
        status="ACCEPTED_NOT_FILLED",
        reason_code="ENTRY_ORDER_EXPIRED_UNFILLED",
        accepted=True,
        filled=False,
        completed=True,
        censored=False,
        evidence={"status": "ACCEPTED_NOT_FILLED", "reason_code": "ENTRY_ORDER_EXPIRED_UNFILLED"},
    )


def _lifecycle_filled_open(**_kwargs) -> ResearchV1BacktestLifecycleResult:
    return ResearchV1BacktestLifecycleResult(
        status="FILLED_OPEN_AT_ENDPOINT",
        reason_code="NO_PROTECTIVE_EXIT_TOUCHED",
        accepted=True,
        filled=True,
        completed=False,
        censored=True,
        evidence={"status": "FILLED_OPEN_AT_ENDPOINT", "reason_code": "NO_PROTECTIVE_EXIT_TOUCHED"},
    )


def _lifecycle_censored_intrabar(**_kwargs) -> ResearchV1BacktestLifecycleResult:
    return ResearchV1BacktestLifecycleResult(
        status="CENSORED",
        reason_code="ENTRY_PROTECTION_INTRABAR_SEQUENCE_UNRESOLVED",
        accepted=True,
        filled=True,
        completed=False,
        censored=True,
        evidence={
            "status": "CENSORED",
            "reason_code": "ENTRY_PROTECTION_INTRABAR_SEQUENCE_UNRESOLVED",
            "entry_filled_at": "2026-08-19T04:05:00Z",
        },
    )


def _lifecycle_closed(**_kwargs) -> ResearchV1BacktestLifecycleResult:
    return ResearchV1BacktestLifecycleResult(
        status="CLOSED",
        reason_code="TAKE_PROFIT_FILLED",
        accepted=True,
        filled=True,
        completed=True,
        censored=False,
        closed_result={"net_pnl": "1", "gross_pnl": "2", "fees": "-1", "funding": "0"},
        evidence={
            "status": "CLOSED",
            "reason_code": "TAKE_PROFIT_FILLED",
            "exit_at": "2026-08-19T04:20:00Z",
        },
    )


def _result(job_id: str, fingerprint: str, *, account_net: Decimal) -> dict[str, object]:
    return {
        "job_id": job_id,
        "config_fingerprint": fingerprint,
        "status": "COMPLETE",
        "evaluation_start": "2026-08-19T00:00:00Z",
        "evaluation_end": "2026-08-26T00:00:00Z",
        "unique_signal_episodes": 3,
        "filled": 2,
        "closed": 2,
        "account_net": account_net,
        "actual_notional_turnover": Decimal("1000"),
        "mean_net_notional_expectancy": Decimal("0.01"),
        "fees": Decimal("-1"),
        "funding": Decimal("0"),
        "stress_net": Decimal("1"),
        "leave_best_event_out_net": Decimal("1"),
    }

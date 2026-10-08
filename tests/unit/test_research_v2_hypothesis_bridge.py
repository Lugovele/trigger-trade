from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path
from typing import Mapping

import pytest

import tools.research_v2.run_7d_screen as screen_runner
import tools.research_v2.run_hypothesis_batch as hypothesis_batch_cli
from tools.research_v2.run_7d_screen import (
    FeatureTimeline,
    _apply_direction_mode,
    _compression_ratio_bucket,
    _directional_efficiency5_from_timeline,
    _evaluate_job_signal_from_timeline,
    _execution_contexts_from_population,
    _portfolio_book_key,
    _replay_one_context,
    _research_identity_payload,
    _set_scan_key,
    _trend_only_signal,
    build_research_v2_canonical_execution_profile,
    build_research_v2_feature_timeline,
    materialize_research_v2_set_population,
)
from triggertrade.backtest.models import HistoricalCandle
from triggertrade.research_v2 import (
    V2DecisionStatus,
    V2Direction,
    V2SignalResult,
    compression_breakout_signal,
    load_common_profile,
    load_research_v2_jobs,
)
from triggertrade.research_v2_execution import VenueConstraints
from triggertrade.research_v2_hypotheses import ResearchV2HypothesisSpec, load_rv2_hb001_hypothesis_jobs
from triggertrade.research_v2_hypotheses import (
    _runtime_profile_for_hypothesis,
    ResearchV2HypothesisJob,
    build_resolved_research_spec,
)
from tests.unit.test_research_v2_screen_runner import (
    _case_dir,
    _dataset_manifest_with_candles,
    _set_context_job,
    _single_materialized_context,
)


def test_h001_h002_suppress_short_before_admission_and_h002_uses_g1() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()
    short = V2SignalResult(V2DecisionStatus.PASS, V2Direction.SHORT, "test")

    assert _apply_direction_mode(jobs["H001"], short).reason == "DIRECTION_MODE_SHORT_SUPPRESSED"
    h002_signal = _apply_direction_mode(jobs["H002"], short)
    assert h002_signal.status is V2DecisionStatus.NONE
    assert h002_signal.reason == "DIRECTION_MODE_SHORT_SUPPRESSED"
    assert build_research_v2_canonical_execution_profile(jobs["H002"]).stop_profile["type"] == "ATR_ONLY"


def test_h003_h004_factor_decomposition_is_literal() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()
    h003_signal = jobs["H003"].runtime_profile["signal"]
    h004_signal = jobs["H004"].runtime_profile["signal"]
    base_long = V2SignalResult(V2DecisionStatus.PASS, V2Direction.LONG, "base")
    base_short = V2SignalResult(V2DecisionStatus.PASS, V2Direction.SHORT, "base")

    assert h003_signal["trend_gate"] == "J4_ONLY"
    assert h003_signal["rvol_gate"] == "DISABLED"
    assert _trend_only_signal(job=jobs["H003"], base=base_long, ema20=Decimal("101"), ema50=Decimal("100"), return15_pct_points=Decimal("0.5")).direction is V2Direction.LONG
    assert _trend_only_signal(job=jobs["H003"], base=base_short, ema20=Decimal("99"), ema50=Decimal("100"), return15_pct_points=Decimal("-0.5")).direction is V2Direction.SHORT

    assert h004_signal["trend_gate"] == "DISABLED"
    assert h004_signal["rvol5_min"] == "1.2"
    assert "trend_gate" not in {key: value for key, value in h004_signal.items() if key != "trend_gate" and value == "J4_ONLY"}


def test_h005_h010_preserve_signal_family_and_switch_only_to_stock_g1() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()

    assert jobs["H005"].runtime_profile["signal"]["family"] == "COMPRESSION_BREAKOUT"
    assert jobs["H010"].runtime_profile["signal"]["family"] == "EXHAUSTION_REVERSAL"
    assert build_research_v2_canonical_execution_profile(jobs["H005"]).stop_profile["type"] == "ATR_ONLY"
    assert build_research_v2_canonical_execution_profile(jobs["H010"]).stop_profile["type"] == "ATR_ONLY"


def test_h006_applies_de_only_to_short_and_uses_exactly_nine_completed_5m_closes() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()
    start = datetime(2026, 8, 19, tzinfo=UTC)
    timeline = build_research_v2_feature_timeline(
        symbol="AVAXUSDT",
        physical_symbol="AVAXUSDT",
        candles=_minute_candles(start, 45, close_start=Decimal("100"), step=Decimal("-0.1"), turnover=Decimal("100")),
    )
    de = _directional_efficiency5_from_timeline(timeline=timeline, cutoff=start + timedelta(minutes=45))

    assert de["value"] == "1"
    assert len(de["source_closes"]) == 9
    assert len(de["source_close_times"]) == 9
    assert _directional_efficiency5_from_timeline(timeline=timeline, cutoff=start + timedelta(minutes=44))["value"] is None

    long_timeline = _manual_timeline(
        cutoff=start + timedelta(minutes=1),
        close=Decimal("100"),
        return5=Decimal("0.31"),
        return15=Decimal("0.6"),
        atr=Decimal("1"),
        ema20=Decimal("101"),
        ema50=Decimal("100"),
        rvol=Decimal("1.2"),
    )
    signal, evidence = _evaluate_job_signal_from_timeline(
        jobs["H006"],
        timeline=long_timeline,
        cutoff=start + timedelta(minutes=1),
        venue=VenueConstraints(Decimal("0.1"), Decimal("0.001"), Decimal("0.001"), Decimal("5")),
    )
    assert signal.direction is V2Direction.LONG
    assert signal.status is V2DecisionStatus.PASS
    assert evidence["directional_efficiency_5m"] is None


def test_h007_g0_eligibility_only_rejects_before_account_side_effects_and_pass_uses_g1() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()
    case_dir = _case_dir("hypothesis_h007_g0_eligibility")
    manifest_path = _dataset_manifest_with_candles(case_dir)
    j3 = load_research_v2_jobs()["J3"]
    context = _single_materialized_context(manifest_path, job=j3, output_dir=case_dir / "source")
    _set_context_job(context, jobs["H007"])
    profile = build_research_v2_canonical_execution_profile(jobs["H007"])
    context["execution_profile_fingerprint"] = profile.config_fingerprint
    context["research_identity"] = _research_identity_payload(jobs["H007"], execution_profile_fingerprint=profile.config_fingerprint)
    record = dict(context["record"])
    evidence = dict(record["factual_feature_evidence"])
    evidence["structural_reference_price"] = None
    record["factual_feature_evidence"] = evidence
    context["record"] = record
    portfolio_state = {}

    result = _replay_one_context(
        context=context,
        dataset_manifest=json.loads(manifest_path.read_text(encoding="utf-8")),
        raw_indexes={},
        candles_cache={},
        venue_cache={},
        funding_cache={},
        portfolio_state=portfolio_state,
        mark_cache={},
    )

    assert result["status"] == "HYPOTHESIS_REJECTED"
    assert result["order_spec"] is None
    assert result["portfolio_grant"] is None
    assert result["cooldown_evidence"] is None
    assert portfolio_state == {}
    assert result["g0_eligibility_evidence"]["account_state_mutated"] is False
    assert profile.stop_profile["type"] == "ATR_ONLY"


def test_h008_turnover_acceleration_gate_is_causal_and_applies_to_passed_continuation() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()
    cutoff = datetime(2026, 8, 19, 0, 1, tzinfo=UTC)
    low_accel = _manual_timeline(cutoff=cutoff, close=Decimal("100"), return5=Decimal("0.31"), return15=Decimal("0.6"), atr=Decimal("1"), ema20=Decimal("101"), ema50=Decimal("100"), rvol=Decimal("1.2"), accel=Decimal("1.19"))
    pass_accel = replace(low_accel, turnover_acceleration={cutoff: Decimal("1.2")})

    signal, evidence = _evaluate_job_signal_from_timeline(jobs["H008"], timeline=low_accel, cutoff=cutoff, venue=None)
    assert signal.reason == "TURNOVER_ACCELERATION_BELOW_THRESHOLD"
    assert evidence["turnover_acceleration"] == "1.19"

    signal, evidence = _evaluate_job_signal_from_timeline(jobs["H008"], timeline=pass_accel, cutoff=cutoff, venue=None)
    assert signal.status is V2DecisionStatus.PASS
    assert evidence["turnover_acceleration"] == "1.2"


def test_h009_parameterizes_only_compression_threshold_and_preserves_default() -> None:
    default_signal = compression_breakout_signal(
        atr15_value=Decimal("0.9"),
        preceding_atr15_values=(Decimal("1"),) * 96,
        close=Decimal("100.1"),
        prior_range_high=Decimal("100"),
        prior_range_low=Decimal("95"),
        rvol5_value=Decimal("1.5"),
        turnover_acceleration_value=Decimal("1.2"),
    )
    h009_signal = compression_breakout_signal(
        atr15_value=Decimal("0.9"),
        preceding_atr15_values=(Decimal("1"),) * 96,
        close=Decimal("100.1"),
        prior_range_high=Decimal("100"),
        prior_range_low=Decimal("95"),
        rvol5_value=Decimal("1.5"),
        turnover_acceleration_value=Decimal("1.2"),
        compression_ratio_max=Decimal("1.00"),
    )

    assert default_signal.reason == "COMPRESSION_FILTER_FAILED"
    assert h009_signal.status is V2DecisionStatus.PASS
    assert _compression_ratio_bucket(atr_value=Decimal("0.9"), median=Decimal("1")) == "GT_0_80_LTE_1_00"
    assert load_rv2_hb001_hypothesis_jobs()["H005"].runtime_profile["signal"]["compression_ratio_max"] == "0.80"
    assert load_rv2_hb001_hypothesis_jobs()["H009"].runtime_profile["signal"]["compression_ratio_max"] == "1.00"


def test_hypotheses_have_isolated_population_account_keys_and_material_parameter_fingerprints() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()
    h001 = jobs["H001"]
    h008 = jobs["H008"]
    profile_h001 = build_research_v2_canonical_execution_profile(h001)
    profile_h008 = build_research_v2_canonical_execution_profile(h008)
    ctx1 = {"job_id": h001.job_id, "execution_profile_fingerprint": profile_h001.config_fingerprint, "research_identity": _research_identity_payload(h001)}
    ctx2 = {"job_id": h008.job_id, "execution_profile_fingerprint": profile_h008.config_fingerprint, "research_identity": _research_identity_payload(h008)}

    assert _set_scan_key(h001) != _set_scan_key(h008)
    assert _portfolio_book_key(ctx1) != _portfolio_book_key(ctx2)

    changed = ResearchV2HypothesisSpec.from_payload(
        {
            **h008.spec.to_payload(),
            "parameters": {"turnover_acceleration_min": "1.3"},
        }
    )
    assert changed.fingerprint != h008.spec.fingerprint


def test_baseline_j3_j7_profiles_remain_semantically_equivalent_under_default_configuration() -> None:
    jobs = load_research_v2_jobs()

    assert jobs["J4"].normalized_config()["runtime_profile"]["signal"] == jobs["J7"].normalized_config()["runtime_profile"]["signal"]
    assert build_research_v2_canonical_execution_profile(jobs["J4"]).stop_profile["type"] == "HYBRID_STRUCTURAL"
    assert build_research_v2_canonical_execution_profile(jobs["J7"]).stop_profile["type"] == "ATR_ONLY"
    assert compression_breakout_signal(
        atr15_value=Decimal("0.9"),
        preceding_atr15_values=(Decimal("1"),) * 96,
        close=Decimal("100.1"),
        prior_range_high=Decimal("100"),
        prior_range_low=Decimal("95"),
        rvol5_value=Decimal("1.5"),
        turnover_acceleration_value=Decimal("1.2"),
    ).reason == "COMPRESSION_FILTER_FAILED"


def test_two_hypotheses_from_same_parent_materialize_separate_contexts_and_books() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()
    selected = [jobs["H003"], jobs["H004"]]
    population = {
        "records": [
            {
                "set_result_id": "set-result-shared-parent",
                "decision_cycle_id": "decision-cycle-shared-parent",
                "set_scan_key": "scan-key",
                "applicable_jobs": ["H003", "H004"],
                "symbol": "AVAXUSDT",
                "physical_symbol": "AVAXUSDT",
                "observed_at": "2026-08-19T04:00:00Z",
            }
        ]
    }
    contexts = _execution_contexts_from_population(population, selected)

    assert {context["job_id"] for context in contexts} == {"H003", "H004"}
    assert len({_portfolio_book_key(context) for context in contexts}) == 2


def test_h001_resolved_passport_shows_long_only_j4_g0_and_unchanged_portfolio() -> None:
    passport = build_resolved_research_spec(load_rv2_hb001_hypothesis_jobs()["H001"])

    assert set(passport) >= {"schema", "research", "set", "triggers", "position_rules", "portfolio_rules"}
    assert passport["position_rules"]["direction_mode"]["value"] == "LONG_ONLY"
    assert passport["position_rules"]["direction_mode"]["runtime_application_stage"] == "PRE_ADMISSION_SIGNAL_FILTER"
    assert passport["position_rules"]["stop"]["family"]["value"] == "G0"
    assert passport["position_rules"]["stop"]["type"]["value"] == "HYBRID_STRUCTURAL"
    assert passport["portfolio_rules"]["capital_usdt"]["value"] == "1000"
    assert _trigger_names(passport) >= {"RET_OR_LONG", "RET_OR_SHORT", "J4_LONG_TREND", "J4_SHORT_TREND", "RVOL5_MIN"}


def test_h003_and_h004_factor_passports_have_literal_trigger_membership() -> None:
    passports = {key: build_resolved_research_spec(load_rv2_hb001_hypothesis_jobs()[key]) for key in ("H003", "H004")}

    assert {"RET_OR_LONG", "RET_OR_SHORT", "J4_LONG_TREND", "J4_SHORT_TREND"} <= _trigger_names(passports["H003"])
    assert "RVOL5_MIN" not in _trigger_names(passports["H003"])

    assert {"RET_OR_LONG", "RET_OR_SHORT", "RVOL5_MIN"} <= _trigger_names(passports["H004"])
    assert "J4_LONG_TREND" not in _trigger_names(passports["H004"])
    assert _trigger_by_name(passports["H004"], "RVOL5_MIN")["value"] == "1.2"


def test_h005_h009_h010_passports_keep_stop_changes_out_of_triggers() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()
    h005 = build_resolved_research_spec(jobs["H005"])
    h009 = build_resolved_research_spec(jobs["H009"])
    h010 = build_resolved_research_spec(jobs["H010"])

    assert h005["position_rules"]["stop"]["family"]["value"] == "G1"
    assert h005["position_rules"]["stop"]["type"]["value"] == "ATR_ONLY"
    assert "G1" not in json.dumps(h005["triggers"], sort_keys=True)
    assert _trigger_by_name(h005, "COMPRESSION_ATR15_MEDIAN96")["value"] == "0.80"

    assert _trigger_by_name(h009, "COMPRESSION_ATR15_MEDIAN96")["value"] == "1.00"
    unchanged_names = _trigger_names(h005) - {"COMPRESSION_ATR15_MEDIAN96"}
    assert unchanged_names == _trigger_names(h009) - {"COMPRESSION_ATR15_MEDIAN96"}

    assert h010["set"]["signal_family"] == "EXHAUSTION_REVERSAL"
    assert h010["position_rules"]["stop"]["family"]["value"] == "G1"
    assert {"EXHAUSTION_REVERSAL_LONG", "EXHAUSTION_REVERSAL_SHORT"} <= _trigger_names(h010)


def test_h006_h007_h008_resolved_passports_capture_special_gates() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()
    h006 = build_resolved_research_spec(jobs["H006"])
    h007 = build_resolved_research_spec(jobs["H007"])
    h008 = build_resolved_research_spec(jobs["H008"])

    de = _trigger_by_name(h006, "SHORT_DIRECTIONAL_EFFICIENCY")
    assert de["direction_scope"] == "SHORT"
    assert de["value"] == "0.30"
    assert de["timeframe"] == "5m"
    assert de["completed_close_count"] == 9

    g0 = _trigger_by_name(h007, "G0_STRUCTURAL_ELIGIBILITY")
    assert g0["role"] == "ENTRY_ELIGIBILITY_ONLY"
    assert h007["position_rules"]["stop"]["family"]["value"] == "G1"
    assert h007["position_rules"]["stop"]["type"]["value"] == "ATR_ONLY"
    assert h007["position_rules"]["stop"]["parameters"]["type"] == "ATR_ONLY"

    turnover = _trigger_by_name(h008, "TURNOVER_ACCELERATION")
    assert turnover["metric"] == "turnover_acceleration"
    assert turnover["operator"] == "GTE"
    assert turnover["value"] == "1.2"


def test_resolved_passport_has_coins_only_under_portfolio_rules_and_no_universe_or_metrics() -> None:
    passport = build_resolved_research_spec(load_rv2_hb001_hypothesis_jobs()["H007"])

    assert "universe" not in passport
    assert "metrics" not in passport
    assert "coins" not in passport["research"]
    assert "coins" not in passport["set"]
    assert passport["portfolio_rules"]["coins"] == [
        {"logical_symbol": "AVAXUSDT", "enabled": True, "allocation_or_cap": None, "physical_symbol": "AVAXUSDT", "source": "ResearchV2JobConfig.symbols + common_profile.physical_binding"},
        {"logical_symbol": "SUIUSDT", "enabled": True, "allocation_or_cap": None, "physical_symbol": "SUIUSDT", "source": "ResearchV2JobConfig.symbols + common_profile.physical_binding"},
        {"logical_symbol": "PEPEUSDT", "enabled": True, "allocation_or_cap": None, "physical_symbol": "1000PEPEUSDT", "source": "ResearchV2JobConfig.symbols + common_profile.physical_binding"},
    ]


def test_resolved_passport_is_deterministic_and_material_parameter_changes_content() -> None:
    jobs = load_rv2_hb001_hypothesis_jobs()
    first = build_resolved_research_spec(jobs["H008"])
    second = build_resolved_research_spec(jobs["H008"])
    assert first == second

    changed_spec = ResearchV2HypothesisSpec.from_payload(
        {
            **jobs["H008"].spec.to_payload(),
            "parameters": {"turnover_acceleration_min": "1.3"},
        }
    )
    changed_job = ResearchV2HypothesisJob(
        spec=changed_spec,
        parent_job=jobs["H008"].parent_job,
        runtime_profile=_runtime_profile_for_hypothesis(changed_spec, jobs["H008"].parent_job, load_common_profile()),
        code_commit=jobs["H008"].code_commit,
    )
    changed = build_resolved_research_spec(changed_job)

    assert changed["research"]["hypothesis_fingerprint"] != first["research"]["hypothesis_fingerprint"]
    assert changed["research"]["strategy_fingerprint"] != first["research"]["strategy_fingerprint"]
    assert _trigger_by_name(changed, "TURNOVER_ACCELERATION")["value"] == "1.3"


def test_resolve_only_runner_writes_passports_without_dataset_or_replay(monkeypatch) -> None:
    writes: dict[str, Mapping[str, object]] = {}

    monkeypatch.setattr(Path, "mkdir", lambda self, parents=False, exist_ok=False: None)
    monkeypatch.setattr(hypothesis_batch_cli, "write_json", lambda path, payload: writes.setdefault(str(path), payload))

    assert hypothesis_batch_cli.main(["--hypotheses", "H001,H005", "--output", "resolved", "--resolve-only"]) == 0

    h001 = writes["resolved\\H001\\resolved_research_spec.json"]
    h005 = writes["resolved\\H005\\resolved_research_spec.json"]
    assert h001["research"]["dataset_fingerprint"] is None  # type: ignore[index]
    assert h001["research"]["population_fingerprint_status"] == "AVAILABLE_AFTER_POPULATION_MATERIALIZATION"  # type: ignore[index]
    assert h005["position_rules"]["stop"]["family"]["value"] == "G1"  # type: ignore[index]


def test_finalize_existing_resolves_hypotheses_from_manifest_without_baseline_lookup(monkeypatch) -> None:
    writes: dict[str, Mapping[str, object]] = {}
    captured: dict[str, object] = {}

    def fake_finalize(**kwargs):
        captured.update(kwargs)
        return {
            "dataset_fingerprint": "dataset-fingerprint",
            "population_fingerprint": "population-fingerprint",
        }

    monkeypatch.setattr(Path, "mkdir", lambda self, parents=False, exist_ok=False: None)
    monkeypatch.setattr(hypothesis_batch_cli, "write_json", lambda path, payload: writes.setdefault(str(path), payload))
    monkeypatch.setattr(hypothesis_batch_cli, "finalize_research_v2_existing_run", fake_finalize)

    assert hypothesis_batch_cli.main(
        [
            "--dataset",
            "dataset.json",
            "--manifest",
            "docs/research-v2/hypotheses/RV2_HB001.json",
            "--hypotheses",
            "H001,H002,H003,H004,H005",
            "--existing-run",
            "existing-run",
            "--finalize-existing",
        ]
    ) == 0

    selected_jobs = captured["selected_jobs"]
    assert [job.job_id for job in selected_jobs] == ["H001", "H002", "H003", "H004", "H005"]  # type: ignore[union-attr]
    assert captured["jobs_arg"] == "H001,H002,H003,H004,H005"
    assert "existing-run\\H001\\resolved_research_spec.json" in writes
    assert writes["existing-run\\resolved_hypothesis_identity.json"]["hypotheses"][0]["hypothesis_id"] == "H001"  # type: ignore[index]


def test_finalize_existing_unknown_hypothesis_fails_before_finalizer(monkeypatch) -> None:
    def forbidden_finalize(**kwargs):
        raise AssertionError("finalizer should not run for an unknown hypothesis")

    monkeypatch.setattr(hypothesis_batch_cli, "finalize_research_v2_existing_run", forbidden_finalize)

    with pytest.raises(screen_runner.ResearchV2RunnerError, match="unknown hypothesis IDs: H999"):
        hypothesis_batch_cli.main(
            [
                "--dataset",
                "dataset.json",
                "--hypotheses",
                "H999",
                "--existing-run",
                "existing-run",
                "--finalize-existing",
            ]
        )


def test_finalize_existing_baseline_job_selection_stays_on_baseline_path(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_finalize(**kwargs):
        captured.update(kwargs)
        return {"dataset_fingerprint": "dataset-fingerprint", "population_fingerprint": "population-fingerprint"}

    monkeypatch.setattr(hypothesis_batch_cli, "finalize_research_v2_existing_run", fake_finalize)

    assert hypothesis_batch_cli.main(
        [
            "--dataset",
            "dataset.json",
            "--hypotheses",
            "J3",
            "--existing-run",
            "existing-run",
            "--finalize-existing",
        ]
    ) == 0

    assert captured["jobs_arg"] == "J3"
    assert "selected_jobs" not in captured


def test_finalize_existing_selection_path_does_not_call_replay_or_materialization(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def fake_finalize(**kwargs):
        captured.update(kwargs)
        return {"dataset_fingerprint": "dataset-fingerprint", "population_fingerprint": "population-fingerprint"}

    monkeypatch.setattr(Path, "mkdir", lambda self, parents=False, exist_ok=False: None)
    monkeypatch.setattr(hypothesis_batch_cli, "write_json", lambda path, payload: None)
    monkeypatch.setattr(hypothesis_batch_cli, "finalize_research_v2_existing_run", fake_finalize)
    monkeypatch.setattr(hypothesis_batch_cli, "run_screen_two_phase", lambda **kwargs: (_ for _ in ()).throw(AssertionError("replay must not run")))
    monkeypatch.setattr(screen_runner, "materialize_research_v2_set_population", lambda **kwargs: (_ for _ in ()).throw(AssertionError("materialization must not run")))

    assert hypothesis_batch_cli.main(
        [
            "--dataset",
            "dataset.json",
            "--hypotheses",
            "H001",
            "--existing-run",
            "existing-run",
            "--finalize-existing",
        ]
    ) == 0

    assert [job.job_id for job in captured["selected_jobs"]] == ["H001"]  # type: ignore[union-attr]


def _minute_candles(
    start: datetime,
    count: int,
    *,
    close_start: Decimal,
    step: Decimal,
    turnover: Decimal,
) -> tuple[HistoricalCandle, ...]:
    rows = []
    for index in range(count):
        close = close_start + (Decimal(index + 1) * step)
        rows.append(
            HistoricalCandle(
                symbol="AVAXUSDT",
                category="linear",
                timeframe="1m",
                open_time=start + timedelta(minutes=index),
                close_time=start + timedelta(minutes=index + 1),
                open=close,
                high=close + Decimal("0.1"),
                low=close - Decimal("0.1"),
                close=close,
                volume=Decimal("100"),
                turnover=turnover,
                completed=True,
            )
        )
    return tuple(rows)


def _manual_timeline(
    *,
    cutoff: datetime,
    close: Decimal,
    return5: Decimal,
    return15: Decimal,
    atr: Decimal,
    ema20: Decimal,
    ema50: Decimal,
    rvol: Decimal,
    accel: Decimal = Decimal("1.2"),
) -> FeatureTimeline:
    candle = HistoricalCandle(
        symbol="AVAXUSDT",
        category="linear",
        timeframe="1m",
        open_time=cutoff - timedelta(minutes=1),
        close_time=cutoff,
        open=close,
        high=close + Decimal("0.1"),
        low=close - Decimal("0.1"),
        close=close,
        volume=Decimal("100"),
        turnover=Decimal("10000"),
        completed=True,
    )
    return FeatureTimeline(
        symbol="AVAXUSDT",
        physical_symbol="AVAXUSDT",
        candles=(candle,),
        close_times=(cutoff,),
        by_close={cutoff: candle},
        return5={cutoff: return5},
        return15={cutoff: return15},
        atr15={cutoff: atr},
        ema20={cutoff: ema20},
        ema50={cutoff: ema50},
        rvol5={cutoff: rvol},
        turnover_acceleration={cutoff: accel},
        compression_atr_median96={},
        prior_12_range={},
        swing_long={},
        swing_short={},
        swing_low_refs=(),
        swing_high_refs=(),
    )


def _trigger_names(passport: Mapping[str, object]) -> set[str]:
    return {str(trigger["name"]) for trigger in passport["triggers"]}  # type: ignore[index]


def _trigger_by_name(passport: Mapping[str, object], name: str) -> Mapping[str, object]:
    for trigger in passport["triggers"]:  # type: ignore[index]
        if trigger["name"] == name:
            return trigger
    raise AssertionError(f"missing trigger {name}")

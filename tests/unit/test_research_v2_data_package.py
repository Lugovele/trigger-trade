from __future__ import annotations

from pathlib import Path
import shutil

import pytest

import tools.research_v2.prepare_7d_data as prepare_7d_data
from tools.research_v2.prepare_7d_data import build_job_readiness
from tools.research_v2.run_7d_screen import validate_dataset
from triggertrade.market_data.raw_trades import instrument_symbol_for_logical_symbol


def _ready_summary() -> dict[str, dict[str, str]]:
    return {"AVAXUSDT": {"status": "READY"}, "SUIUSDT": {"status": "READY"}, "PEPEUSDT": {"status": "READY"}}


def test_research_v2_data_readiness_requires_dataset_status_not_exchange_status() -> None:
    instrument_summary = {
        "AVAXUSDT": {"status": "READY", "trading_status": "Trading"},
        "SUIUSDT": {"status": "READY", "trading_status": "Trading"},
        "1000PEPEUSDT": {"status": "READY", "trading_status": "Trading"},
        "BTCUSDT": {"status": "READY", "trading_status": "Trading"},
    }

    rows = build_job_readiness(
        candle_summary={**_ready_summary(), "BTCUSDT": {"status": "READY"}},
        raw_summary=_ready_summary(),
        funding_summary=_ready_summary(),
        mark_summary=_ready_summary(),
        instrument_summary=instrument_summary,
        feature_summary=_ready_summary(),
    )

    assert {row["job_id"] for row in rows} == {"J0", "J1", "J2", "J3", "J4", "J5", "J6", "J7"}
    assert all(row["instrument_ready"] for row in rows)
    assert all(row["overall_status"] == "READY" for row in rows)


def test_research_v2_data_package_preserves_pepe_physical_binding() -> None:
    assert instrument_symbol_for_logical_symbol("PEPEUSDT") == "1000PEPEUSDT"
    assert instrument_symbol_for_logical_symbol("AVAXUSDT") == "AVAXUSDT"
    assert instrument_symbol_for_logical_symbol("SUIUSDT") == "SUIUSDT"


def test_research_v2_data_window_configuration_derives_holdout_identity() -> None:
    original = {
        "DATASET_ID": prepare_7d_data.DATASET_ID,
        "SCREEN_START": prepare_7d_data.SCREEN_START,
        "SCREEN_END": prepare_7d_data.SCREEN_END,
        "WARMUP_START": prepare_7d_data.WARMUP_START,
        "DATASET_ROOT": prepare_7d_data.DATASET_ROOT,
    }
    try:
        prepare_7d_data.configure_dataset_window(
            start="2026-05-24T00:00:00Z",
            end="2026-05-31T00:00:00Z",
            output_root=Path("runtime/test-artifacts/holdout-a"),
        )

        assert prepare_7d_data.DATASET_ID == "research-v2-7d-20260524-20260531-v1"
        assert prepare_7d_data.iso(prepare_7d_data.WARMUP_START) == "2026-05-09T00:00:00Z"
        assert prepare_7d_data.DATASET_ROOT == Path("runtime/test-artifacts/holdout-a")
        assert prepare_7d_data.stamp(prepare_7d_data.WARMUP_START) == "20260509T000000Z"
    finally:
        for name, value in original.items():
            setattr(prepare_7d_data, name, value)


def test_research_v2_data_window_must_be_exactly_seven_days() -> None:
    with pytest.raises(ValueError, match="exactly 7 days"):
        prepare_7d_data.configure_dataset_window(
            start="2026-05-24T00:00:00Z",
            end="2026-05-30T00:00:00Z",
        )


def test_research_v2_data_package_rejects_all_zero_candle_volume_turnover() -> None:
    zero_rows = [
        {"volume": "0", "turnover": "0"},
        {"volume": "0", "turnover": "0"},
    ]
    mixed_rows = [
        {"volume": "0", "turnover": "0"},
        {"volume": "1", "turnover": "10"},
    ]

    assert not prepare_7d_data._candle_volume_turnover_ready(zero_rows)
    assert prepare_7d_data._candle_volume_turnover_ready(mixed_rows)


def test_research_v2_dataset_validator_accepts_holdout_dataset_ids() -> None:
    root = Path("runtime/test-artifacts/holdout-validator")
    manifest_path = root / "dataset_manifest.json"
    try:
        root.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            prepare_7d_data.json.dumps(
                {
                    "dataset_id": "research-v2-7d-20260524-20260531-v1",
                    "status": "DATA_READY",
                    "validation": {"status": "PASS"},
                    "files": [],
                    "coverage": {
                        "job_readiness": [
                            {"job_id": f"J{index}", "overall_status": "READY"}
                            for index in range(8)
                        ]
                    },
                }
            ),
            encoding="utf-8",
        )

        assert validate_dataset(manifest_path)["dataset_id"] == "research-v2-7d-20260524-20260531-v1"
    finally:
        shutil.rmtree(root, ignore_errors=True)

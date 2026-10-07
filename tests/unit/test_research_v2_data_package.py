from __future__ import annotations

from tools.research_v2.prepare_7d_data import build_job_readiness
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

"""Backtest set-vs-set comparison helpers."""

from __future__ import annotations

from hashlib import sha256
import json

from triggertrade.analytics import compare_baseline
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore

from .engine import _trade_facts
from .store import BacktestStore


def compare_backtest_runs(*, db_path, baseline_run_id: str, candidate_run_id: str) -> dict[str, object]:
    store = BacktestStore(db_path)
    baseline = store.get_run(baseline_run_id)
    candidate = store.get_run(candidate_run_id)
    if baseline is None or candidate is None:
        raise ValueError("both backtest runs must exist")
    baseline_payload = json.loads(baseline["payload"])
    candidate_payload = json.loads(candidate["payload"])
    for field in ("period_start", "period_end", "data_cache_hash", "simulation_model_version", "cost_model_version", "accounting_version"):
        if baseline_payload[field] != candidate_payload[field]:
            raise ValueError("backtest comparison requires matching period/source/simulation/cost/accounting")
    if _comparable_assumptions(baseline_payload) != _comparable_assumptions(candidate_payload):
        raise ValueError("backtest comparison requires matching replay assumptions")
    accounting = FuturesAccountingStore(db_path)
    baseline_ids = store.list_trade_ids(baseline_run_id)
    candidate_ids = store.list_trade_ids(candidate_run_id)
    comparison = compare_baseline(baseline_set=f"{baseline_payload['trigger_set_id']}@{baseline_payload['trigger_set_version']}", candidate_set=f"{candidate_payload['trigger_set_id']}@{candidate_payload['trigger_set_version']}", baseline_trades=_trade_facts(accounting, baseline_ids), candidate_trades=_trade_facts(accounting, candidate_ids))
    payload = comparison.__dict__
    comparison_id = "btc-" + sha256(f"{baseline_run_id}|{candidate_run_id}".encode("utf-8")).hexdigest()[:24]
    store.save_comparison(comparison_id=comparison_id, baseline_run_id=baseline_run_id, candidate_run_id=candidate_run_id, payload=payload)
    return payload | {"comparison_id": comparison_id}


def _comparable_assumptions(payload: dict[str, object]) -> dict[str, object]:
    assumptions = dict(payload.get("assumptions") or {})
    assumptions.pop("trigger_set_config_snapshot", None)
    return assumptions

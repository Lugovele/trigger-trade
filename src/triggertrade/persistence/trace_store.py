"""Minimal traceability persistence for the first e2e slice."""

from __future__ import annotations

from pathlib import Path
import json
import sqlite3
from typing import Any

from triggertrade.execution import RiskDecision, TradeIntent
from triggertrade.triggers import Signal


class TraceStore:
    def __init__(self, path: str | Path = "runtime/triggertrade.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def save_trigger_evaluation(self, signal: Signal) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO trigger_evaluations (
                    signal_id, trigger_rule_id, trigger_rule_version, symbol,
                    observed_at, window, input_snapshot, condition_result, signal_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.signal_id,
                    signal.trigger_rule_id,
                    signal.trigger_rule_version,
                    signal.symbol,
                    signal.observed_at,
                    signal.window,
                    json.dumps(dict(signal.input_snapshot), sort_keys=True),
                    int(signal.condition_result),
                    signal.signal_type.value,
                ),
            )

    def save_strategy_decision(self, intent: TradeIntent) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO strategy_decisions (
                    intent_id, strategy_rule_id, strategy_rule_version, symbol,
                    side, signal_ids, trigger_ids, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    intent.intent_id,
                    intent.strategy_rule_id,
                    intent.strategy_rule_version,
                    intent.symbol,
                    intent.side.value,
                    json.dumps(intent.reason_signal_ids),
                    json.dumps(intent.reason_trigger_ids),
                    intent.created_at,
                ),
            )

    def save_risk_decision(self, decision: RiskDecision) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO risk_decisions (
                    risk_decision_id, intent_id, approved, checked_rule_ids,
                    blocking_rule_ids, approved_notional, approved_quantity,
                    rejection_reason, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.risk_decision_id,
                    decision.intent_id,
                    int(decision.approved),
                    json.dumps(decision.checked_rule_ids),
                    json.dumps(decision.blocking_rule_ids),
                    None if decision.approved_notional is None else str(decision.approved_notional),
                    None if decision.approved_quantity is None else str(decision.approved_quantity),
                    decision.rejection_reason,
                    decision.created_at,
                ),
            )

    def trace_for_intent(self, intent_id: str) -> dict[str, Any]:
        with self._connect() as conn:
            strategy = conn.execute(
                "SELECT * FROM strategy_decisions WHERE intent_id = ?",
                (intent_id,),
            ).fetchone()
            risk = conn.execute(
                "SELECT * FROM risk_decisions WHERE intent_id = ?",
                (intent_id,),
            ).fetchone()
            signals = []
            if strategy is not None:
                for signal_id in json.loads(strategy["signal_ids"]):
                    signal = conn.execute(
                        "SELECT * FROM trigger_evaluations WHERE signal_id = ?",
                        (signal_id,),
                    ).fetchone()
                    if signal is not None:
                        signals.append(dict(signal))
        return {
            "strategy": None if strategy is None else dict(strategy),
            "risk": None if risk is None else dict(risk),
            "signals": signals,
        }

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS trigger_evaluations (
                    signal_id TEXT PRIMARY KEY,
                    trigger_rule_id TEXT NOT NULL,
                    trigger_rule_version TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    window TEXT NOT NULL,
                    input_snapshot TEXT NOT NULL,
                    condition_result INTEGER NOT NULL,
                    signal_type TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS strategy_decisions (
                    intent_id TEXT PRIMARY KEY,
                    strategy_rule_id TEXT NOT NULL,
                    strategy_rule_version TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    side TEXT NOT NULL,
                    signal_ids TEXT NOT NULL,
                    trigger_ids TEXT NOT NULL,
                    created_at TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS risk_decisions (
                    risk_decision_id TEXT PRIMARY KEY,
                    intent_id TEXT NOT NULL,
                    approved INTEGER NOT NULL,
                    checked_rule_ids TEXT NOT NULL,
                    blocking_rule_ids TEXT NOT NULL,
                    approved_notional TEXT,
                    approved_quantity TEXT,
                    rejection_reason TEXT,
                    created_at TEXT
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

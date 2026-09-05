"""SQLite persistence for immutable historical replay runs."""

from __future__ import annotations

from dataclasses import asdict
import json
from pathlib import Path
import sqlite3

from .models import BacktestResult, BacktestRun, BacktestStatus


class BacktestStoreError(RuntimeError):
    pass


class BacktestStore:
    def __init__(self, path: str | Path = "runtime/triggertrade_paper.sqlite3") -> None:
        self.path = Path(path)
        if self.path.parent != Path("."):
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def create_run(self, run: BacktestRun) -> bool:
        payload = _run_payload(run)
        with self._connect() as conn:
            existing = conn.execute("SELECT payload FROM backtest_runs WHERE backtest_run_id = ?", (run.backtest_run_id,)).fetchone()
            if existing is not None:
                if existing["payload"] != payload:
                    raise BacktestStoreError("immutable backtest run conflict")
                return False
            conn.execute(
                """
                INSERT INTO backtest_runs (
                    backtest_run_id, status, created_at, trigger_set_id,
                    trigger_set_version, period_start, period_end, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (run.backtest_run_id, run.status.value, run.created_at, run.trigger_set_id, run.trigger_set_version, run.period_start, run.period_end, payload),
            )
        return True

    def update_status(self, run_id: str, status: BacktestStatus) -> None:
        with self._connect() as conn:
            row = conn.execute("SELECT status FROM backtest_runs WHERE backtest_run_id = ?", (run_id,)).fetchone()
            if row is None:
                raise BacktestStoreError("backtest run not found")
            if row["status"] in {BacktestStatus.COMPLETED.value, BacktestStatus.CANCELLED.value} and row["status"] != status.value:
                raise BacktestStoreError("completed backtest runs are immutable")
            conn.execute("UPDATE backtest_runs SET status = ? WHERE backtest_run_id = ?", (status.value, run_id))

    def save_result(self, result: BacktestResult) -> bool:
        payload = _result_payload(result)
        with self._connect() as conn:
            existing = conn.execute("SELECT payload FROM backtest_results WHERE backtest_run_id = ?", (result.backtest_run_id,)).fetchone()
            if existing is not None:
                if existing["payload"] != payload:
                    raise BacktestStoreError("immutable backtest result conflict")
                return False
            conn.execute(
                """
                INSERT INTO backtest_results (
                    backtest_run_id, status, closed_trades, net_pnl,
                    expectancy, profit_factor, payload
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.backtest_run_id,
                    result.status.value,
                    result.closed_trades,
                    str(result.net_pnl),
                    None if result.expectancy is None else str(result.expectancy),
                    None if result.profit_factor is None else str(result.profit_factor),
                    payload,
                ),
            )
        return True

    def save_run_trades(self, *, run_id: str, trade_ids: tuple[str, ...]) -> bool:
        expected = tuple(sorted(trade_ids))
        with self._connect() as conn:
            existing = tuple(
                row["trade_id"]
                for row in conn.execute(
                    "SELECT trade_id FROM backtest_run_trades WHERE backtest_run_id = ? ORDER BY trade_id",
                    (run_id,),
                ).fetchall()
            )
            if existing:
                if existing != expected:
                    raise BacktestStoreError("immutable backtest run trade mapping conflict")
                return False
            conn.executemany(
                "INSERT INTO backtest_run_trades (backtest_run_id, trade_id) VALUES (?, ?)",
                [(run_id, trade_id) for trade_id in expected],
            )
        return True

    def list_trade_ids(self, run_id: str) -> tuple[str, ...]:
        with self._connect() as conn:
            return tuple(
                row["trade_id"]
                for row in conn.execute(
                    "SELECT trade_id FROM backtest_run_trades WHERE backtest_run_id = ? ORDER BY trade_id",
                    (run_id,),
                ).fetchall()
            )

    def save_comparison(self, *, comparison_id: str, baseline_run_id: str, candidate_run_id: str, payload: dict[str, object]) -> bool:
        serialized = json.dumps(_jsonable(payload), sort_keys=True)
        with self._connect() as conn:
            existing = conn.execute("SELECT payload FROM backtest_comparisons WHERE comparison_id = ?", (comparison_id,)).fetchone()
            if existing is not None:
                if existing["payload"] != serialized:
                    raise BacktestStoreError("immutable backtest comparison conflict")
                return False
            conn.execute(
                "INSERT INTO backtest_comparisons (comparison_id, baseline_run_id, candidate_run_id, payload) VALUES (?, ?, ?, ?)",
                (comparison_id, baseline_run_id, candidate_run_id, serialized),
            )
        return True

    def list_runs(self, limit: int = 20) -> tuple[sqlite3.Row, ...]:
        with self._connect() as conn:
            return tuple(
                conn.execute(
                    """
                    SELECT r.backtest_run_id, r.status, r.created_at, r.trigger_set_id,
                           r.trigger_set_version, r.period_start, r.period_end,
                           r.payload, b.payload AS result_payload
                    FROM backtest_runs r
                    LEFT JOIN backtest_results b ON b.backtest_run_id = r.backtest_run_id
                    ORDER BY r.created_at DESC, r.backtest_run_id
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()
            )

    def get_run(self, run_id: str) -> sqlite3.Row | None:
        with self._connect() as conn:
            return conn.execute(
                """
                SELECT r.backtest_run_id, r.status, r.created_at, r.payload,
                       b.payload AS result_payload
                FROM backtest_runs r
                LEFT JOIN backtest_results b ON b.backtest_run_id = r.backtest_run_id
                WHERE r.backtest_run_id = ?
                """,
                (run_id,),
            ).fetchone()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS backtest_runs (
                    backtest_run_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    trigger_set_id TEXT NOT NULL,
                    trigger_set_version TEXT NOT NULL,
                    period_start TEXT NOT NULL,
                    period_end TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS backtest_results (
                    backtest_run_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    closed_trades INTEGER NOT NULL,
                    net_pnl TEXT NOT NULL,
                    expectancy TEXT,
                    profit_factor TEXT,
                    payload TEXT NOT NULL,
                    FOREIGN KEY (backtest_run_id) REFERENCES backtest_runs(backtest_run_id)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS backtest_comparisons (
                    comparison_id TEXT PRIMARY KEY,
                    baseline_run_id TEXT NOT NULL,
                    candidate_run_id TEXT NOT NULL,
                    payload TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS backtest_run_trades (
                    backtest_run_id TEXT NOT NULL,
                    trade_id TEXT NOT NULL,
                    PRIMARY KEY (backtest_run_id, trade_id),
                    FOREIGN KEY (backtest_run_id) REFERENCES backtest_runs(backtest_run_id)
                )
                """
            )

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn


def _run_payload(run: BacktestRun) -> str:
    data = asdict(run)
    data["status"] = run.status.value
    for key in ("spread_bps", "slippage_bps", "maker_fee_rate", "taker_fee_rate"):
        data[key] = str(data[key])
    return json.dumps(_jsonable(data), sort_keys=True)


def _result_payload(result: BacktestResult) -> str:
    data = asdict(result)
    data["status"] = result.status.value
    for key in ("net_pnl", "expectancy", "profit_factor", "max_drawdown", "fees", "funding"):
        value = data[key]
        data[key] = None if value is None else str(value)
    return json.dumps(data, sort_keys=True)


def _jsonable(value):
    if hasattr(value, "value"):
        return value.value
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(item) for item in value]
    if value.__class__.__name__ == "Decimal":
        return str(value)
    return value

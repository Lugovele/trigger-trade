"""Research orchestration service for backend-owned product state."""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
import sqlite3
from typing import Any, Callable

from triggertrade.analytics import TradePerformanceFact, compute_futures_performance
from triggertrade.backtest import BacktestPlan, BacktestResult, HistoricalCandle, run_backtest
from triggertrade.config import AppConfig
from triggertrade.market_data import FuturesInstrumentMetadata
from triggertrade.persistence import MessageStore, TraceStore, TradingRulesStore, TriggerSetStore
from triggertrade.persistence.research_store import (
    ResearchBacktestRunRecord,
    ResearchBacktestStatus,
    ResearchDecision,
    ResearchDemoRunRecord,
    ResearchDemoStatus,
    ResearchRecord,
    ResearchStatus,
    ResearchStore,
    ResearchStoreError,
)
from triggertrade.rules.trading import TRADING_RULES_SCOPE_LIVE, draft_from_json
from triggertrade.rules import DirectionMode, TakeProfitMode, TradingRulesVersion
from triggertrade.trigger_sets import TriggerSetStatus, TriggerSetVersion


class ResearchServiceError(ValueError):
    pass


@dataclass(frozen=True)
class ResearchDemoIsolation:
    available: bool = False
    reason: str = "research_demo_exchange_isolation_unavailable"
    execution_scope_id: str | None = None
    account_scope: str | None = None


@dataclass(frozen=True)
class ResearchCompareResult:
    available: bool
    reason: str | None
    overlap_period: str | None = None
    research_demo: dict[str, Any] | None = None
    active_benchmark: dict[str, Any] | None = None
    difference: dict[str, Any] | None = None


BacktestRunner = Callable[..., BacktestResult]


class ResearchService:
    def __init__(
        self,
        *,
        store: ResearchStore,
        trigger_set_store: TriggerSetStore,
        trading_rules_store: TradingRulesStore,
        message_store: MessageStore | None = None,
        config: AppConfig | None = None,
        instrument: FuturesInstrumentMetadata | None = None,
        demo_isolation: ResearchDemoIsolation | None = None,
        backtest_runner: BacktestRunner | None = None,
    ) -> None:
        self._store = store
        self._trigger_set_store = trigger_set_store
        self._trading_rules_store = trading_rules_store
        self._message_store = message_store
        self._trace_store = TraceStore(store.path)
        self._config = config
        self._instrument = instrument
        self._demo_isolation = demo_isolation or ResearchDemoIsolation()
        self._backtest_runner = backtest_runner or run_backtest

    def create_research(
        self,
        *,
        set_id: str,
        set_version: str,
        rules_version_id: str,
        created_source: str = "service",
        created_at: str | None = None,
    ) -> ResearchRecord:
        trigger_set = self._trigger_set_store.get_set(set_id, set_version)
        if trigger_set is None:
            raise ResearchServiceError("exact trigger set version not found")
        rules = self._exact_rules_version(rules_version_id)
        record, _created = self._store.create_research(
            set_id=trigger_set.set_id,
            set_version=trigger_set.version,
            rules_version_id=rules.rules_version_id,
            rules_display_version=rules.version,
            created_source=created_source,
            created_at=created_at,
        )
        self._audit_research_event(
            "RESEARCH_CREATED",
            record,
            result="CREATED",
            source_id=created_source,
            created_at=record.created_at,
            metadata={"rules_display_version": record.rules_display_version},
        )
        return record

    def run_backtest(
        self,
        *,
        research_id: str,
        plan: BacktestPlan,
        candles: tuple[HistoricalCandle, ...] = (),
        created_at: datetime | None = None,
    ) -> ResearchBacktestRunRecord:
        research = self._required_research(research_id)
        if self._config is None or self._instrument is None or not candles:
            return self._blocked_backtest(
                research,
                plan=plan,
                reason="backend_historical_replay_inputs_unavailable",
                created_at=(created_at or datetime.now(UTC)).isoformat(),
            )
        rules = self._exact_rules_version(research.rules_version_id)
        block_reason = _backtest_block_reason(rules, self._config, plan)
        if block_reason is not None:
            return self._blocked_backtest(
                research,
                plan=plan,
                reason=block_reason,
                created_at=(created_at or datetime.now(UTC)).isoformat(),
            )
        try:
            result = self._backtest_runner(
                config=_config_for_rules(self._config, rules),
                db_path=self._store.path,
                trigger_set_id=research.set_id,
                trigger_set_version=research.set_version,
                plan=plan,
                candles=candles,
                instrument=self._instrument,
            )
        except Exception as exc:  # noqa: BLE001 - persisted failed evidence must stay bounded and public-safe.
            record = self._store.add_backtest_run(
                research_id=research.research_id,
                period_start=plan.research_start.astimezone(UTC).isoformat(),
                period_end=plan.research_end.astimezone(UTC).isoformat(),
                timeframe=plan.timeframe,
                status=ResearchBacktestStatus.FAILED,
                metrics={},
                unavailable_reason=_public_reason(str(exc)),
                created_at=(created_at or datetime.now(UTC)).isoformat(),
            )
            self._message(
                severity="ERROR",
                title="Research backtest failed",
                body="A Research backtest did not complete.",
                entity_type="research",
                entity_id=research.research_id,
                dedupe_key=f"research:{research.research_id}:backtest_failed:{_public_reason(str(exc))}",
            )
            self._audit_research_run_event(
                "BACKTEST_RUN_FAILED",
                research,
                run_id=record.run_id,
                result=record.status.value,
                reason=record.unavailable_reason,
                created_at=record.created_at,
                metadata={"period_start": record.period_start, "period_end": record.period_end, "timeframe": record.timeframe},
            )
            return record
        status = ResearchBacktestStatus.COMPLETED if result.closed_trades > 0 else ResearchBacktestStatus.COMPLETED_NO_TRADES
        record = self._store.add_backtest_run(
            research_id=research.research_id,
            period_start=plan.research_start.astimezone(UTC).isoformat(),
            period_end=plan.research_end.astimezone(UTC).isoformat(),
            timeframe=plan.timeframe,
            status=status,
            engine_run_id=result.backtest_run_id,
            metrics=_backtest_metrics(result),
            created_at=(created_at or datetime.now(UTC)).isoformat(),
        )
        self._audit_research_run_event(
            "BACKTEST_RUN_COMPLETED",
            research,
            run_id=record.run_id,
            result=record.status.value,
            created_at=record.created_at,
            metadata={
                "period_start": record.period_start,
                "period_end": record.period_end,
                "timeframe": record.timeframe,
                "metrics": record.metrics,
            },
        )
        return record

    def select_backtest_run(self, research_id: str, run_id: str) -> ResearchRecord:
        record = self._store.select_backtest_run(research_id, run_id)
        self._audit_research_event("BACKTEST_SELECTED_FOR_USE", record, result="SELECTED", run_id=run_id)
        return record

    def start_demo_run(self, research_id: str, *, created_at: str | None = None) -> ResearchDemoRunRecord:
        research = self._required_research(research_id)
        rules = self._exact_rules_version(research.rules_version_id)
        block_reason = self._demo_block_reason(rules)
        if block_reason is not None:
            return self._blocked_demo(research, reason=block_reason, created_at=created_at)
        now = created_at or datetime.now(UTC).isoformat()
        scope = self._demo_isolation.execution_scope_id or f"research:{research.research_id}"
        record = self._store.add_demo_run(
            research_id=research.research_id,
            status=ResearchDemoStatus.RUNNING,
            started_at=now,
            execution_scope_id=scope,
            account_scope=self._demo_isolation.account_scope or scope,
            created_at=now,
        )
        self._audit_research_run_event(
            "DEMO_RUN_STARTED",
            research,
            run_id=record.run_id,
            result=record.status.value,
            created_at=record.created_at,
            metadata={"execution_scope_id": record.execution_scope_id, "account_scope": record.account_scope},
        )
        return record

    def stop_demo_run(self, research_id: str, run_id: str, *, stopped_at: str | None = None) -> ResearchDemoRunRecord:
        record = self._store.stop_demo_run(research_id, run_id, stopped_at=stopped_at)
        research = self._required_research(research_id)
        self._audit_research_run_event(
            "DEMO_RUN_STOPPED",
            research,
            run_id=record.run_id,
            result=record.status.value,
            created_at=record.stopped_at or record.created_at,
            metadata={"started_at": record.started_at, "stopped_at": record.stopped_at},
        )
        return record

    def select_demo_run(self, research_id: str, run_id: str) -> ResearchRecord:
        record = self._store.select_demo_run(research_id, run_id)
        self._audit_research_event("DEMO_SELECTED_FOR_USE", record, result="SELECTED", run_id=run_id)
        self._message(
            severity="ATTENTION",
            title="Research decision needed",
            body="A Research Demo run was selected for comparison and decision.",
            entity_type="research",
            entity_id=record.research_id,
            dedupe_key=f"research:{record.research_id}:decision_needed",
        )
        return record

    def archive_research(self, research_id: str) -> ResearchRecord:
        record = self._store.archive_research(research_id)
        self._audit_research_event("RESEARCH_ARCHIVED", record, result="ARCHIVED", created_at=record.updated_at)
        return record

    def request_make_active(self, research_id: str) -> ResearchRecord:
        return self.make_active(research_id)

    def make_active(
        self,
        research_id: str,
        *,
        decided_at: str | None = None,
        _fault_after: str | None = None,
    ) -> ResearchRecord:
        decided_at = decided_at or datetime.now(UTC).isoformat()
        research = self._required_research(research_id)
        self._exact_trigger_set(research.set_id, research.set_version)
        self._exact_rules_version(research.rules_version_id)
        blocked_reason = None

        with sqlite3.connect(self._store.path) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("BEGIN IMMEDIATE")
            current_research = conn.execute("SELECT * FROM research_entities WHERE research_id = ?", (research.research_id,)).fetchone()
            if current_research is None:
                raise ResearchServiceError("research id not found")
            if current_research["status"] == ResearchStatus.ARCHIVED.value:
                raise ResearchStoreError("archived research is immutable")
            current_set = conn.execute(
                """
                SELECT set_id, version, status, symbol, timeframe
                FROM trigger_set_versions
                WHERE set_id = ? AND version = ?
                """,
                (research.set_id, research.set_version),
            ).fetchone()
            current_rules = conn.execute(
                "SELECT rules_version_id, version, payload FROM trading_rules_versions WHERE rules_version_id = ?",
                (research.rules_version_id,),
            ).fetchone()
            if current_set is None:
                raise ResearchServiceError("exact trigger set version not found")
            if current_rules is None:
                raise ResearchServiceError("exact trading rules version not found")
            active_set = conn.execute(
                """
                SELECT set_id, version, status
                FROM trigger_set_versions
                WHERE symbol = ? AND timeframe = ? AND status = ?
                """,
                (current_set["symbol"], current_set["timeframe"], TriggerSetStatus.ACTIVE.value),
            ).fetchone()
            previous_rules = conn.execute(
                "SELECT rules_version_id FROM trading_rules_current WHERE scope = ?",
                (TRADING_RULES_SCOPE_LIVE,),
            ).fetchone()
            previous_set_id = None if active_set is None else active_set["set_id"]
            previous_set_version = None if active_set is None else active_set["version"]
            previous_rules_id = None if previous_rules is None else previous_rules["rules_version_id"]
            blocked_reason = _locked_promotion_block_reason(
                research_status=current_research["status"],
                set_status=current_set["status"],
                set_symbol=current_set["symbol"],
                rules_payload=current_rules["payload"],
                conn=conn,
                research_id=research.research_id,
            )
            if blocked_reason is not None:
                conn.execute(
                    """
                    UPDATE research_entities
                    SET decision = ?, decision_at = ?, updated_at = ?
                    WHERE research_id = ?
                    """,
                    (ResearchDecision.MAKE_ACTIVE_BLOCKED.value, decided_at, decided_at, research.research_id),
                )
                conn.execute(
                    """
                    INSERT INTO research_decision_events(research_id, event_at, decision, reason)
                    VALUES (?, ?, ?, ?)
                    """,
                    (research.research_id, decided_at, ResearchDecision.MAKE_ACTIVE_BLOCKED.value, blocked_reason),
                )
                conn.execute("COMMIT")
                already_active = False
            else:
                already_active = (
                    previous_set_id == research.set_id
                    and previous_set_version == research.set_version
                    and previous_rules_id == research.rules_version_id
                    and current_research["decision"] == ResearchDecision.MADE_ACTIVE.value
                )
                if not already_active:
                    if active_set is not None and (active_set["set_id"], active_set["version"]) != (research.set_id, research.set_version):
                        conn.execute(
                            "UPDATE trigger_set_versions SET status = ? WHERE set_id = ? AND version = ?",
                            (TriggerSetStatus.ARCHIVE.value, active_set["set_id"], active_set["version"]),
                        )
                        conn.execute(
                            """
                            INSERT INTO trigger_set_transitions (
                                set_id, set_version, from_status, to_status, changed_at, reason
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                active_set["set_id"],
                                active_set["version"],
                                active_set["status"],
                                TriggerSetStatus.ARCHIVE.value,
                                decided_at,
                                "archived by Research Make Active promotion",
                            ),
                        )
                    if _fault_after == "set":
                        raise ResearchServiceError("injected promotion failure after set update")
                    if current_set["status"] != TriggerSetStatus.ACTIVE.value:
                        conn.execute(
                            "UPDATE trigger_set_versions SET status = ? WHERE set_id = ? AND version = ?",
                            (TriggerSetStatus.ACTIVE.value, research.set_id, research.set_version),
                        )
                        conn.execute(
                            """
                            INSERT INTO trigger_set_transitions (
                                set_id, set_version, from_status, to_status, changed_at, reason
                            ) VALUES (?, ?, ?, ?, ?, ?)
                            """,
                            (
                                research.set_id,
                                research.set_version,
                                current_set["status"],
                                TriggerSetStatus.ACTIVE.value,
                                decided_at,
                                "Research Make Active promoted exact tested Set Version",
                            ),
                        )
                    conn.execute(
                        """
                        INSERT INTO trading_rules_current(scope, rules_version_id, updated_at)
                        VALUES (?, ?, ?)
                        ON CONFLICT(scope) DO UPDATE SET rules_version_id = excluded.rules_version_id, updated_at = excluded.updated_at
                        """,
                        (TRADING_RULES_SCOPE_LIVE, research.rules_version_id, decided_at),
                    )
                    if _fault_after == "rules":
                        raise ResearchServiceError("injected promotion failure after rules update")
                    metadata = {
                        "result": "promoted",
                        "promoted_set": f"{research.set_id}@{research.set_version}",
                        "promoted_rules_version_id": research.rules_version_id,
                        "previous_set": None if previous_set_id is None else f"{previous_set_id}@{previous_set_version}",
                        "previous_rules_version_id": previous_rules_id,
                    }
                    conn.execute(
                        """
                        UPDATE research_entities
                        SET status = ?, decision = ?, decision_at = COALESCE(decision_at, ?),
                            made_active_at = COALESCE(made_active_at, ?), updated_at = ?,
                            promoted_set_id = ?, promoted_set_version = ?,
                            promoted_rules_version_id = ?, previous_active_set_id = ?,
                            previous_active_set_version = ?, previous_rules_version_id = ?,
                            promotion_result_metadata = ?
                        WHERE research_id = ?
                        """,
                        (
                            ResearchStatus.DECISION_NEEDED.value,
                            ResearchDecision.MADE_ACTIVE.value,
                            decided_at,
                            decided_at,
                            decided_at,
                            research.set_id,
                            research.set_version,
                            research.rules_version_id,
                            previous_set_id,
                            previous_set_version,
                            previous_rules_id,
                            json.dumps(metadata, sort_keys=True),
                            research.research_id,
                        ),
                    )
                    conn.execute(
                        """
                        INSERT INTO research_decision_events(research_id, event_at, decision, reason)
                        VALUES (?, ?, ?, ?)
                        """,
                        (research.research_id, decided_at, ResearchDecision.MADE_ACTIVE.value, json.dumps(metadata, sort_keys=True)),
                    )
                else:
                    conn.execute(
                        "UPDATE research_entities SET updated_at = ? WHERE research_id = ?",
                        (decided_at, research.research_id),
                    )
                conn.execute("COMMIT")
        record = self._store.get_research(research.research_id)
        if record is None:
            raise ResearchServiceError("research id not found after promotion")
        if blocked_reason is not None:
            self._audit_research_event(
                "RESEARCH_MAKE_ACTIVE_BLOCKED",
                record,
                result="BLOCKED",
                reason=blocked_reason,
                created_at=record.decision_at or decided_at,
                metadata={"decision": record.decision.value},
            )
            self._message(
                severity="WARNING",
                title="Research promotion blocked",
                body="Research Make Active did not change the active configuration.",
                entity_type="research",
                entity_id=record.research_id,
                dedupe_key=f"research:{record.research_id}:make_active_blocked:{blocked_reason}",
                metadata={"reason": blocked_reason},
            )
        elif not already_active:
            self._audit_research_event(
                "RESEARCH_MADE_ACTIVE",
                record,
                result="MADE_ACTIVE",
                created_at=record.made_active_at or decided_at,
                metadata={
                    "promoted_set_id": record.promoted_set_id,
                    "promoted_set_version": record.promoted_set_version,
                    "promoted_rules_version_id": record.promoted_rules_version_id,
                    "previous_active_set_id": record.previous_active_set_id,
                    "previous_active_set_version": record.previous_active_set_version,
                    "previous_rules_version_id": record.previous_rules_version_id,
                    "promotion_result_metadata": record.promotion_result_metadata,
                },
                event_id=f"audit-research-made-active-{record.research_id}",
            )
            self._message(
                severity="ATTENTION",
                title="Research promoted",
                body=f"Research {record.research_id} promoted. Active configuration is now {record.set_id} {record.set_version} + Rules {record.rules_display_version}.",
                entity_type="research",
                entity_id=record.research_id,
                dedupe_key=f"research:{record.research_id}:made_active",
                metadata={
                    "set_id": record.set_id,
                    "set_version": record.set_version,
                    "rules_version_id": record.rules_version_id,
                },
            )
        return record

    def compare(self, research_id: str) -> ResearchCompareResult:
        research = self._required_research(research_id)
        if not research.selected_demo_run_id:
            return ResearchCompareResult(False, "selected Research Demo run unavailable")
        demo = self._store.get_demo_run(research.research_id, research.selected_demo_run_id)
        if demo is None or demo.status is not ResearchDemoStatus.STOPPED:
            return ResearchCompareResult(False, "selected Research Demo run is not stopped")
        demo_facts = _facts_from_demo_metrics(research, demo)
        if not demo_facts:
            return ResearchCompareResult(False, "selected Research Demo metrics unavailable")
        active_facts = _active_trade_facts(self._store.path, symbol=demo_facts[0].symbol)
        if not active_facts:
            return ResearchCompareResult(False, "active overlapping benchmark unavailable")
        overlap = _overlap_samples(active_facts, demo_facts)
        if overlap is None:
            return ResearchCompareResult(False, "closed-trade periods do not overlap")
        active_sample, demo_sample, overlap_period = overlap
        active_label = _active_set_label(active_sample)
        active_set_id, active_set_version = active_label.split("@", 1)
        active = compute_futures_performance(set_id=active_set_id, version=active_set_version, status="ACTIVE", trades=active_sample, include_direction_breakdown=False)
        demo_metrics = compute_futures_performance(set_id=research.set_id, version=research.set_version, status="RESEARCH_DEMO", trades=demo_sample, include_direction_breakdown=False)
        research_metrics = _metrics_summary(
            closed_trades=demo_metrics.closed_trades,
            net_pnl=demo_metrics.net_pnl,
            expectancy=demo_metrics.expectancy_per_trade,
            fees=demo_metrics.fees,
        )
        active_metrics = _metrics_summary(
            closed_trades=active.closed_trades,
            net_pnl=active.net_pnl,
            expectancy=active.expectancy_per_trade,
            fees=active.fees,
        )
        return ResearchCompareResult(
            True,
            None,
            overlap_period=overlap_period,
            research_demo=research_metrics,
            active_benchmark=active_metrics,
            difference=_difference(research_metrics, active_metrics),
        )

    def _blocked_backtest(
        self,
        research: ResearchRecord,
        *,
        plan: BacktestPlan,
        reason: str,
        created_at: str,
    ) -> ResearchBacktestRunRecord:
        record = self._store.add_backtest_run(
            research_id=research.research_id,
            period_start=plan.research_start.astimezone(UTC).isoformat(),
            period_end=plan.research_end.astimezone(UTC).isoformat(),
            timeframe=plan.timeframe,
            status=ResearchBacktestStatus.FAILED,
            unavailable_reason=reason,
            created_at=created_at,
        )
        self._audit_research_run_event(
            "BACKTEST_RUN_BLOCKED",
            research,
            run_id=record.run_id,
            result=record.status.value,
            reason=reason,
            created_at=record.created_at,
            metadata={"period_start": record.period_start, "period_end": record.period_end, "timeframe": record.timeframe},
        )
        self._message(
            severity="WARNING",
            title="Research backtest unavailable",
            body="A Research backtest could not start because required runtime inputs were unavailable.",
            entity_type="research",
            entity_id=research.research_id,
            dedupe_key=f"research:{research.research_id}:backtest_unavailable:{reason}",
        )
        return record

    def _blocked_demo(
        self,
        research: ResearchRecord,
        *,
        reason: str,
        created_at: str | None,
    ) -> ResearchDemoRunRecord:
        record = self._store.add_demo_run(
            research_id=research.research_id,
            status=ResearchDemoStatus.BLOCKED,
            blocked_reason=reason,
            created_at=created_at,
        )
        self._audit_research_run_event(
            "DEMO_RUN_BLOCKED",
            research,
            run_id=record.run_id,
            result=record.status.value,
            reason=reason,
            created_at=record.created_at,
            metadata={"blocked_reason": reason},
        )
        self._message(
            severity="WARNING",
            title="Research Demo blocked",
            body="Research Demo did not start because isolated Research execution is not available.",
            entity_type="research",
            entity_id=research.research_id,
            dedupe_key=f"research:{research.research_id}:demo_blocked:{reason}",
            metadata={"reason": reason},
        )
        return record

    def _demo_block_reason(self, rules: TradingRulesVersion) -> str | None:
        draft = rules.draft
        if draft.take_profit_mode is TakeProfitMode.DYNAMIC:
            return "dynamic_take_profit_requires_unimplemented_research_demo_runtime"
        if draft.daily_loss_limit_enabled:
            return "research_daily_loss_accounting_isolation_unavailable"
        if not self._demo_isolation.available:
            return self._demo_isolation.reason
        if not self._demo_isolation.execution_scope_id or not self._demo_isolation.account_scope:
            return "research_demo_isolation_scope_unattributed"
        return None

    def _required_research(self, research_id: str) -> ResearchRecord:
        try:
            record = self._store.get_research(research_id)
        except ResearchStoreError as exc:
            raise ResearchServiceError(str(exc)) from exc
        if record is None:
            raise ResearchServiceError("research id not found")
        return record

    def _exact_trigger_set(self, set_id: str, set_version: str) -> TriggerSetVersion:
        trigger_set = self._trigger_set_store.get_set(set_id, set_version)
        if trigger_set is None:
            raise ResearchServiceError("exact trigger set version not found")
        for rule_id, version in trigger_set.rule_versions:
            self._trigger_set_store.get_exact_rule(rule_id, version)
        return trigger_set

    def _exact_rules_version(self, rules_version_id: str) -> TradingRulesVersion:
        rules = self._trading_rules_store.get_version(rules_version_id)
        if rules is None or rules.rules_version_id != rules_version_id:
            raise ResearchServiceError("exact trading rules version not found")
        return rules

    def _message(self, **kwargs: Any) -> None:
        if self._message_store is None:
            return
        try:
            self._message_store.create_message(source="research_service", **kwargs)
        except Exception:
            return

    def _audit_research_event(
        self,
        event_type: str,
        record: ResearchRecord,
        *,
        result: str,
        source_id: str = "research_service",
        reason: str | None = None,
        run_id: str | None = None,
        created_at: str | None = None,
        metadata: dict[str, Any] | None = None,
        event_id: str | None = None,
    ) -> None:
        try:
            self._trace_store.record_audit_event(
                event_type=event_type,
                source_type="RESEARCH",
                source_id=source_id,
                scope="RESEARCH",
                entity_type="research",
                entity_id=record.research_id,
                set_id=record.set_id,
                set_version=record.set_version,
                rules_version_id=record.rules_version_id,
                research_id=record.research_id,
                run_id=run_id,
                result=result,
                reason_code=reason,
                safe_metadata=metadata or {},
                created_at=created_at or record.updated_at,
                event_id=event_id,
            )
        except Exception:
            return

    def _audit_research_run_event(
        self,
        event_type: str,
        research: ResearchRecord,
        *,
        run_id: str,
        result: str,
        reason: str | None = None,
        created_at: str,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        try:
            self._trace_store.record_audit_event(
                event_type=event_type,
                source_type="RESEARCH",
                source_id="research_service",
                scope="RESEARCH",
                entity_type="research_run",
                entity_id=run_id,
                related_entity_type="research",
                related_entity_id=research.research_id,
                set_id=research.set_id,
                set_version=research.set_version,
                rules_version_id=research.rules_version_id,
                research_id=research.research_id,
                run_id=run_id,
                result=result,
                reason_code=reason,
                safe_metadata=metadata or {},
                created_at=created_at,
            )
        except Exception:
            return


def _locked_promotion_block_reason(
    *,
    research_status: str,
    set_status: str,
    set_symbol: str,
    rules_payload: str,
    conn: sqlite3.Connection,
    research_id: str,
) -> str | None:
    if research_status == ResearchStatus.ARCHIVED.value:
        return "archived_research_cannot_be_promoted"
    if set_status not in {TriggerSetStatus.TESTING.value, TriggerSetStatus.ACTIVE.value}:
        return "trigger_set_version_not_promotion_eligible"
    draft = draft_from_json(rules_payload)
    if not any(coin.enabled and coin.symbol == set_symbol for coin in draft.coins):
        return "rules_version_does_not_enable_research_set_symbol"
    if draft.take_profit_mode is TakeProfitMode.DYNAMIC:
        return "dynamic_take_profit_is_not_supported_for_active_promotion"
    running_demo = conn.execute(
        """
        SELECT 1
        FROM research_demo_runs
        WHERE research_id = ? AND status = ?
        LIMIT 1
        """,
        (research_id, ResearchDemoStatus.RUNNING.value),
    ).fetchone()
    if running_demo is not None:
        return "research_demo_must_be_stopped_before_promotion"
    return None


def _backtest_metrics(result: BacktestResult) -> dict[str, Any]:
    data = asdict(result)
    data["status"] = result.status.value
    for key in ("net_pnl", "expectancy", "profit_factor", "max_drawdown", "fees", "funding"):
        data[key] = None if data[key] is None else str(data[key])
    return data


def _config_for_rules(config: AppConfig, rules: TradingRulesVersion) -> AppConfig:
    draft = rules.draft
    minimum_net_edge = draft.minimum_net_edge_pct if draft.minimum_net_edge_enabled and draft.minimum_net_edge_pct is not None else Decimal("0")
    max_open_positions = draft.max_open_positions if draft.max_open_positions_enabled and draft.max_open_positions is not None else config.futures_runtime.max_open_positions
    runtime = replace(
        config.futures_runtime,
        version=rules.rules_version_id,
        leverage=draft.leverage,
        position_size_pct_of_available_capital=draft.position_size_pct,
        max_open_positions=max_open_positions,
        take_profit_pct=draft.fixed_take_profit_pct or draft.minimum_take_profit_pct or config.futures_runtime.take_profit_pct,
        stop_loss_pct=draft.stop_loss_pct,
        minimum_risk_reward=draft.minimum_risk_reward,
        minimum_net_edge=minimum_net_edge,
        maker_fee_rate=draft.maker_fee_rate,
        taker_fee_rate=draft.taker_fee_rate,
        spread_cost=draft.spread_cost,
        slippage_cost=draft.slippage_cost,
        funding_cost=draft.funding_cost,
    )
    return replace(config, futures_runtime=runtime)


def _backtest_block_reason(rules: TradingRulesVersion, config: AppConfig, plan: BacktestPlan) -> str | None:
    draft = rules.draft
    if draft.take_profit_mode is TakeProfitMode.DYNAMIC:
        return "dynamic_take_profit_requires_unimplemented_research_backtest_runtime"
    if draft.daily_loss_limit_enabled:
        return "research_daily_loss_accounting_isolation_unavailable"
    if draft.direction_mode is not DirectionMode.LONG_SHORT:
        return "research_backtest_direction_filters_unimplemented"
    enabled = tuple(coin for coin in draft.coins if coin.enabled)
    if not any(coin.symbol == plan.symbol for coin in enabled):
        return "research_backtest_symbol_not_enabled_by_pinned_rules"
    if any(coin.max_allocation_pct is not None for coin in enabled):
        return "research_backtest_coin_allocation_rules_unimplemented"
    if not draft.max_positions_per_coin_enabled or draft.max_positions_per_coin != 1:
        return "research_backtest_position_per_coin_rules_unimplemented"
    if not draft.max_open_positions_enabled or draft.max_open_positions is None or draft.max_open_positions < 1:
        return "research_backtest_max_open_positions_rules_unimplemented"
    configured_cap = config.futures_runtime.max_total_position_notional / Decimal("100")
    if draft.max_capital_in_positions_pct != configured_cap:
        return "research_backtest_aggregate_capital_rules_unimplemented"
    return None


def _facts_from_demo_metrics(research: ResearchRecord, demo: ResearchDemoRunRecord) -> tuple[TradePerformanceFact, ...]:
    rows = demo.metrics.get("closed_trades")
    if not isinstance(rows, list):
        return ()
    facts: list[TradePerformanceFact] = []
    for row in rows[:250]:
        if not isinstance(row, dict):
            continue
        try:
            facts.append(
                TradePerformanceFact(
                    trade_id=str(row["trade_id"]),
                    trigger_set_id=research.set_id,
                    trigger_set_version=research.set_version,
                    symbol=str(row.get("symbol") or "BTCUSDT"),
                    direction=str(row.get("direction") or "LONG"),
                    closed_at=str(row["closed_at"]),
                    net_pnl=Decimal(str(row["net_pnl"])),
                    gross_pnl=Decimal(str(row.get("gross_pnl", row["net_pnl"]))),
                    entry_fee=Decimal(str(row.get("entry_fee", "0"))),
                    exit_fee=Decimal(str(row.get("exit_fee", "0"))),
                    other_fees=Decimal(str(row.get("other_fees", "0"))),
                    funding=Decimal(str(row.get("funding", "0"))),
                    duration_seconds=int(row.get("duration_seconds", 0)),
                    regime_label=row.get("regime_label"),
                    evidence_source="RESEARCH_DEMO",
                )
            )
        except (KeyError, ValueError, ArithmeticError):
            continue
    return tuple(facts)


def _active_trade_facts(db_path, *, symbol: str) -> tuple[TradePerformanceFact, ...]:
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                """
                SELECT trade_id, trigger_set_id, trigger_set_version, symbol, direction,
                       closed_at, net_pnl, gross_pnl, entry_fee, exit_fee, other_fees,
                       funding, duration_seconds, regime_label,
                       COALESCE(evidence_source, 'exchange') AS evidence_source
                FROM futures_closed_trades
                WHERE symbol = ?
                  AND UPPER(COALESCE(evidence_source, 'exchange')) IN ('ACTIVE', 'EXCHANGE')
                ORDER BY closed_at, trade_id
                LIMIT 250
                """,
                (symbol,),
            ).fetchall()
    except sqlite3.Error:
        return ()
    return tuple(
        TradePerformanceFact(
            trade_id=row["trade_id"],
            trigger_set_id=row["trigger_set_id"],
            trigger_set_version=row["trigger_set_version"],
            symbol=row["symbol"],
            direction=row["direction"],
            closed_at=row["closed_at"],
            net_pnl=Decimal(row["net_pnl"]),
            gross_pnl=Decimal(row["gross_pnl"]),
            entry_fee=Decimal(row["entry_fee"]),
            exit_fee=Decimal(row["exit_fee"]),
            other_fees=Decimal(row["other_fees"]),
            funding=Decimal(row["funding"]),
            duration_seconds=int(row["duration_seconds"]),
            regime_label=row["regime_label"],
            evidence_source=row["evidence_source"],
        )
        for row in rows
        if row["trigger_set_id"] and row["trigger_set_version"]
    )


def _overlap_samples(
    active_facts: tuple[TradePerformanceFact, ...],
    demo_facts: tuple[TradePerformanceFact, ...],
) -> tuple[tuple[TradePerformanceFact, ...], tuple[TradePerformanceFact, ...], str] | None:
    active_label = _active_set_label(active_facts)
    active_sample_source = tuple(fact for fact in active_facts if f"{fact.trigger_set_id}@{fact.trigger_set_version}" == active_label)
    if not active_sample_source or not demo_facts:
        return None
    overlap_start = max(min(fact.closed_at for fact in active_sample_source), min(fact.closed_at for fact in demo_facts))
    overlap_end = min(max(fact.closed_at for fact in active_sample_source), max(fact.closed_at for fact in demo_facts))
    if overlap_start > overlap_end:
        return None
    active_sample = tuple(fact for fact in active_sample_source if overlap_start <= fact.closed_at <= overlap_end)
    demo_sample = tuple(fact for fact in demo_facts if overlap_start <= fact.closed_at <= overlap_end)
    if not active_sample or not demo_sample:
        return None
    return active_sample, demo_sample, f"{overlap_start} -> {overlap_end}"


def _active_set_label(facts: tuple[TradePerformanceFact, ...]) -> str:
    if not facts:
        return "unavailable@unavailable"
    first = facts[0]
    return f"{first.trigger_set_id}@{first.trigger_set_version}"


def _metrics_summary(
    *,
    closed_trades: int,
    net_pnl: Decimal | None,
    expectancy: Decimal | None,
    fees: Decimal | None,
) -> dict[str, Any]:
    return {
        "closed_trades": closed_trades,
        "net_pnl": None if net_pnl is None else str(net_pnl),
        "expectancy": None if expectancy is None else str(expectancy),
        "fees": None if fees is None else str(fees),
    }


def _difference(candidate: dict[str, Any], baseline: dict[str, Any]) -> dict[str, Any]:
    return {
        "closed_trades": int(candidate["closed_trades"]) - int(baseline["closed_trades"]),
        "net_pnl": _decimal_diff(candidate.get("net_pnl"), baseline.get("net_pnl")),
        "expectancy": _decimal_diff(candidate.get("expectancy"), baseline.get("expectancy")),
        "fees": _decimal_diff(candidate.get("fees"), baseline.get("fees")),
    }


def _decimal_diff(left: Any, right: Any) -> str | None:
    if left is None or right is None:
        return None
    return str(Decimal(str(left)) - Decimal(str(right)))


def _public_reason(value: str) -> str:
    lowered = value.lower()
    if any(token in lowered for token in ("secret", "api_key", "authorization", "cookie", "token", ".env")):
        return "sanitized_error"
    return " ".join(value.replace("\x00", "").split())[:180] or "unavailable"

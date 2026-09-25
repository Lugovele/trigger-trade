"""Dashboard write command boundary.

The dashboard HTTP layer parses requests and authorizes operator principals;
this module owns the write-side calls into existing backend services/stores.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol

from triggertrade.backtest import BacktestPlan
from triggertrade.backtest.data import HistoricalDataError
from triggertrade.backtest.models import HistoricalCandle
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.market_data import FuturesInstrumentMetadata
from triggertrade.persistence import MessageStore, OperatorStateStore
from triggertrade.rules import TradingRulesService
from triggertrade.services.runtime import interval_delta
from triggertrade.services.instrument_catalog import InstrumentCatalogService
from triggertrade.services.operator_auth import AuthorizedOperatorCommand
from triggertrade.services.research import ResearchPromotionCommand, ResearchService
from triggertrade.services.system_history import SystemHistoryExporter


class HistoricalReplaySource(Protocol):
    def load(self, *, symbol: str, category: str, timeframe: str, start: datetime, end: datetime, use_cache: bool = True): ...


class BacktestInstrumentProvider(Protocol):
    def __call__(self, symbol: str) -> FuturesInstrumentMetadata: ...


class DashboardCommandBoundary:
    """Idempotent/audited command ingress for dashboard writes."""

    def __init__(
        self,
        *,
        read_model: DashboardReadModel,
        operator_store: OperatorStateStore,
        message_store: MessageStore,
        trading_rules_service: TradingRulesService,
        instrument_catalog_service: InstrumentCatalogService,
        research_service: ResearchService,
        historical_replay_source: HistoricalReplaySource | None = None,
        backtest_instrument_provider: BacktestInstrumentProvider | None = None,
        operator_actions=None,
    ) -> None:
        self.read_model = read_model
        self.operator_store = operator_store
        self.message_store = message_store
        self.trading_rules_service = trading_rules_service
        self.instrument_catalog_service = instrument_catalog_service
        self.research_service = research_service
        self.historical_replay_source = historical_replay_source
        self.backtest_instrument_provider = backtest_instrument_provider
        self.operator_actions = operator_actions

    def create_research(
        self,
        command: AuthorizedOperatorCommand,
        *,
        set_id: str,
        set_version: str,
        rules_version_id: str,
    ):
        return self.research_service.create_research(
            set_id=set_id,
            set_version=set_version,
            rules_version_id=rules_version_id,
            created_source=command.audit_source,
            created_at=datetime.now(UTC).isoformat(),
        )

    def run_backtest(self, command: AuthorizedOperatorCommand, *, research_id: str, plan: BacktestPlan):
        candles: tuple[HistoricalCandle, ...] = ()
        unavailable_reason: str | None = None
        instrument: FuturesInstrumentMetadata | None = None
        source = self.historical_replay_source
        if source is None:
            unavailable_reason = "historical_provider_unavailable"
        else:
            try:
                record = source.load(
                    symbol=plan.symbol,
                    category=plan.category,
                    timeframe=plan.timeframe,
                    start=_historical_replay_load_start(plan),
                    end=plan.research_end,
                    use_cache=True,
                )
                candles = tuple(record.candles)
            except Exception as exc:  # noqa: BLE001 - persisted failure reason must be safe and bounded.
                unavailable_reason = _historical_unavailable_reason(exc)
        if unavailable_reason is None:
            if self.backtest_instrument_provider is None:
                unavailable_reason = "historical_provider_unavailable"
            else:
                try:
                    instrument = self.backtest_instrument_provider(plan.symbol)
                except Exception:  # noqa: BLE001 - public instrument metadata is part of replay inputs.
                    unavailable_reason = "historical_provider_unavailable"
        return self.research_service.run_backtest(
            research_id=research_id,
            plan=plan,
            candles=candles,
            created_at=datetime.now(UTC),
            historical_unavailable_reason=unavailable_reason,
            instrument=instrument,
        )

    def select_backtest_run(self, command: AuthorizedOperatorCommand, *, research_id: str, run_id: str):
        return self.research_service.select_backtest_run(research_id, run_id)

    def start_demo_run(self, command: AuthorizedOperatorCommand, *, research_id: str):
        return self.research_service.start_demo_run(research_id, created_at=datetime.now(UTC).isoformat())

    def stop_demo_run(self, command: AuthorizedOperatorCommand, *, research_id: str, run_id: str):
        return self.research_service.stop_demo_run(research_id, run_id, stopped_at=datetime.now(UTC).isoformat())

    def select_demo_run(self, command: AuthorizedOperatorCommand, *, research_id: str, run_id: str):
        return self.research_service.select_demo_run(research_id, run_id)

    def archive_research(self, command: AuthorizedOperatorCommand, *, research_id: str):
        return self.research_service.archive_research(research_id)

    def request_make_active(self, command: AuthorizedOperatorCommand, *, research_id: str, idempotency_key: str):
        return self.research_service.request_make_active(
            research_id,
            command=ResearchPromotionCommand(
                operator_principal=command.principal.principal_id,
                authorization_source=command.principal.auth_source,
                idempotency_key=idempotency_key,
            ),
        )

    def create_rules_version(
        self,
        command: AuthorizedOperatorCommand,
        *,
        changes: dict[str, object],
        expected_current_rules_version_id: str,
        expected_current_display_version: str,
    ):
        return self.trading_rules_service.create_rules_version_from_current(
            changes=changes,
            created_source=command.audit_source,
            created_at=datetime.now(UTC).isoformat(),
            expected_current_rules_version_id=expected_current_rules_version_id,
            expected_current_display_version=expected_current_display_version,
        )

    def refresh_instrument_catalog(self, command: AuthorizedOperatorCommand):
        return self.instrument_catalog_service.refresh_instrument_catalog()

    def record_instrument_catalog_refresh_failure(self, result) -> None:
        _record_message(
            self.message_store,
            severity="WARNING",
            title="Instrument catalog refresh failed",
            body="Instrument catalog refresh did not complete successfully.",
            source="local_dashboard",
            dedupe_key=f"instrument_refresh:{result.status}",
            metadata={"status": result.status, "error": result.error},
        )

    def mark_messages_read(self, command: AuthorizedOperatorCommand, message_ids: list[str]) -> int:
        return self.message_store.mark_read(message_ids)

    def export_system_history(self, command: AuthorizedOperatorCommand) -> str:
        text = SystemHistoryExporter(
            read_model=self.read_model,
            operator_store=self.operator_store,
            message_store=self.message_store,
        ).build_export()
        self.operator_store.record_operator_action(
            action="SYSTEM_HISTORY_EXPORTED",
            target="CLIPBOARD",
            result="SUCCESS",
            source=command.audit_source,
        )
        return text

    def record_system_history_export_failure(self, command: AuthorizedOperatorCommand, error: str) -> None:
        self.operator_store.record_operator_action(
            action="SYSTEM_HISTORY_EXPORTED",
            target="CLIPBOARD",
            result="FAILED",
            source=command.audit_source,
            error=error,
        )

    def pause_entries(self, command: AuthorizedOperatorCommand) -> None:
        self.operator_store.pause(source=command.audit_source, reason="confirmed dashboard Pause Entries")
        self.operator_store.record_operator_action(
            action="PAUSE_ENTRIES",
            target="ACTIVE",
            result="SUCCESS",
            source=command.audit_source,
        )
        _record_message(
            self.message_store,
            severity="ATTENTION",
            title="New entries paused",
            body="New entries were paused from the dashboard. Existing positions remain active.",
            source="local_dashboard",
            dedupe_key="operator:PAUSE_ENTRIES:ACTIVE",
        )

    def resume_entries(self, command: AuthorizedOperatorCommand) -> None:
        self.operator_store.resume(source=command.audit_source, reason="confirmed dashboard Resume")
        self.operator_store.record_operator_action(
            action="RESUME_ENTRIES",
            target="ACTIVE",
            result="SUCCESS",
            source=command.audit_source,
        )
        _record_message(
            self.message_store,
            severity="INFO",
            title="New entries resumed",
            body="New entries were resumed from the dashboard.",
            source="local_dashboard",
            dedupe_key="operator:RESUME_ENTRIES:ACTIVE",
        )

    def close_one(self, command: AuthorizedOperatorCommand, *, position_id: str, symbol: str) -> None:
        action = self.operator_actions
        if action is None:
            error = "close-one execution bridge is not attached to this dashboard process"
            self.operator_store.record_operator_action(
                action="CLOSE_ONE",
                target=position_id,
                result="FAILED",
                source=command.audit_source,
                error=error,
            )
            _record_message(
                self.message_store,
                severity="ERROR",
                title="Close One failed",
                body="Close One could not run because no execution bridge is attached.",
                source="local_dashboard",
                entity_type="position",
                entity_id=position_id,
                dedupe_key=f"operator:CLOSE_ONE:FAILED:{position_id}",
            )
            raise DashboardCommandError(error)
        _require_canonical_execution_bridge(action, command_name="close-one")
        try:
            _close_single_position(action, command=command, position_id=position_id, symbol=symbol)
        except Exception as exc:  # noqa: BLE001 - operator failures are recorded, then surfaced.
            error = str(exc)[:500]
            public_error = _safe_public_error(exc)
            self.operator_store.record_operator_action(
                action="CLOSE_ONE",
                target=position_id,
                result="FAILED",
                source=command.audit_source,
                error=error,
            )
            _record_message(
                self.message_store,
                severity="ERROR",
                title="Close One failed",
                body="Close One failed from the dashboard.",
                source="local_dashboard",
                entity_type="position",
                entity_id=position_id,
                dedupe_key=f"operator:CLOSE_ONE:FAILED:{position_id}:{error[:80]}",
            )
            raise DashboardCommandError(public_error) from exc
        self.operator_store.record_operator_action(
            action="CLOSE_ONE",
            target=position_id,
            result="ACCEPTED",
            source=command.audit_source,
        )

    def close_all(self, command: AuthorizedOperatorCommand) -> None:
        action = self.operator_actions
        if action is None:
            error = "close-all execution bridge is not attached to this dashboard process"
            self.operator_store.record_operator_action(
                action="CLOSE_ALL",
                target="ACTIVE",
                result="FAILED",
                source=command.audit_source,
                error=error,
            )
            _record_message(
                self.message_store,
                severity="ERROR",
                title="Close All failed",
                body="Close All could not run because no execution bridge is attached.",
                source="local_dashboard",
                dedupe_key="operator:CLOSE_ALL:FAILED:no_bridge",
            )
            raise DashboardCommandError(error)
        _require_canonical_execution_bridge(action, command_name="close-all")
        try:
            _close_all_positions(action, command=command)
        except Exception as exc:  # noqa: BLE001 - operator failures are recorded, then surfaced.
            error = str(exc)[:500]
            public_error = _safe_public_error(exc)
            self.operator_store.record_operator_action(
                action="CLOSE_ALL",
                target="ACTIVE",
                result="FAILED",
                source=command.audit_source,
                error=error,
            )
            _record_message(
                self.message_store,
                severity="ERROR",
                title="Close All failed",
                body="Close All failed from the dashboard.",
                source="local_dashboard",
                dedupe_key=f"operator:CLOSE_ALL:FAILED:{error[:80]}",
            )
            raise DashboardCommandError(public_error) from exc
        self.operator_store.record_operator_action(
            action="CLOSE_ALL",
            target="ACTIVE",
            result="ACCEPTED",
            source=command.audit_source,
        )


class DashboardCommandError(RuntimeError):
    pass


def _close_single_position(operator_actions, *, command: AuthorizedOperatorCommand, position_id: str, symbol: str):
    return operator_actions.close_position(
        position_id=position_id,
        symbol=symbol,
        close_reason="MANUAL",
        requested_by=command.principal.principal_id,
        authorization_source=command.principal.auth_source,
        idempotency_key=command.idempotency_key,
    )


def _close_all_positions(operator_actions, *, command: AuthorizedOperatorCommand):
    return operator_actions.close_all_positions(
        scope="ACTIVE",
        requested_by=command.principal.principal_id,
        authorization_source=command.principal.auth_source,
        idempotency_key=command.idempotency_key,
    )


def _require_canonical_execution_bridge(operator_actions, *, command_name: str) -> None:
    if not getattr(operator_actions, "canonical_execution_bridge", False):
        raise DashboardCommandError(f"{command_name} execution bridge is not canonical")


def _record_message(store: MessageStore, **kwargs: Any) -> None:
    try:
        store.create_message(**kwargs)
    except Exception:  # noqa: BLE001 - message persistence must not change command results.
        return


def _historical_replay_load_start(plan: BacktestPlan) -> datetime:
    # The engine counts warmup candles whose close_time is strictly before
    # research_start, so include one extra interval as the CLI replay path does.
    return plan.research_start.astimezone(UTC) - interval_delta(plan.timeframe) * (plan.warmup_candles + 1)


def _historical_unavailable_reason(exc: Exception) -> str:
    text = str(exc).lower()
    if isinstance(exc, HistoricalDataError):
        if "empty" in text:
            return "historical_candles_empty"
        if any(token in text for token in ("gap", "boundary", "requested", "start", "end", "warmup")):
            return "historical_window_incomplete"
        return "historical_source_error"
    return "historical_source_error"


def _safe_public_error(exc: Exception) -> str:
    text = str(exc)
    lower = text.lower()
    if any(token in lower for token in ("secret", "api_key", "authorization", "x-bapi", "password", "token")):
        return exc.__class__.__name__
    return text[:240]

"""Dashboard write command boundary.

The dashboard HTTP layer parses requests and authorizes operator principals;
this module owns the write-side calls into existing backend services/stores.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from triggertrade.backtest import BacktestPlan
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.persistence import MessageStore, OperatorStateStore
from triggertrade.rules import TradingRulesService
from triggertrade.services.instrument_catalog import InstrumentCatalogService
from triggertrade.services.operator_auth import AuthorizedOperatorCommand
from triggertrade.services.research import ResearchPromotionCommand, ResearchService
from triggertrade.services.system_history import SystemHistoryExporter


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
        operator_actions=None,
    ) -> None:
        self.read_model = read_model
        self.operator_store = operator_store
        self.message_store = message_store
        self.trading_rules_service = trading_rules_service
        self.instrument_catalog_service = instrument_catalog_service
        self.research_service = research_service
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
        return self.research_service.run_backtest(
            research_id=research_id,
            plan=plan,
            created_at=datetime.now(UTC),
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
        try:
            _close_single_position(action, position_id=position_id, symbol=symbol)
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
            result="SUCCESS",
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
        try:
            _close_all_positions(action)
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
            result="SUCCESS",
            source=command.audit_source,
        )


class DashboardCommandError(RuntimeError):
    pass


def _close_single_position(operator_actions, *, position_id: str, symbol: str):
    try:
        return operator_actions.close_position(position_id=position_id, symbol=symbol, close_reason="MANUAL")
    except TypeError:
        return operator_actions.close_position(position_id=position_id, close_reason="MANUAL")


def _close_all_positions(operator_actions):
    try:
        return operator_actions.close_all_positions(scope="ACTIVE")
    except TypeError:
        return operator_actions.close_all_positions()


def _record_message(store: MessageStore, **kwargs: Any) -> None:
    try:
        store.create_message(**kwargs)
    except Exception:  # noqa: BLE001 - message persistence must not change command results.
        return


def _safe_public_error(exc: Exception) -> str:
    text = str(exc)
    lower = text.lower()
    if any(token in lower for token in ("secret", "api_key", "authorization", "x-bapi", "password", "token")):
        return exc.__class__.__name__
    return text[:240]

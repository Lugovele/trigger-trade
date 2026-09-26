"""Canonical owner-message dispatch for payload-complete B12 routes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from hashlib import sha256
from typing import Any

from triggertrade.persistence import (
    DurableMessageStore,
    LifecycleStartGateStore,
    OrderSpecStore,
    PortfolioFinalReceiptStore,
    SubmitAuthorizationStore,
)
from triggertrade.persistence.durable_messages import OutboxMessageRecord
from triggertrade.persistence.postgres import PostgresPersistenceError
from triggertrade.services.operator_execution_bridge import (
    OPERATOR_EXECUTION_CONSUMER,
    OPERATOR_EXECUTION_MESSAGE_TYPE,
    OPERATOR_EXECUTION_MESSAGE_VERSION,
    OPERATOR_EXECUTION_PRODUCER,
    OperatorExecutionCommandStore,
    OperatorExecutionDispatcher,
    OperatorExecutionExecutor,
)
from triggertrade.services.research_backtest_execution import (
    RESEARCH_BACKTEST_CONSUMER,
    RESEARCH_BACKTEST_MESSAGE_TYPE,
    RESEARCH_BACKTEST_MESSAGE_VERSION,
    RESEARCH_BACKTEST_PRODUCER,
    ResearchBacktestExecutionDispatcher,
    ResearchBacktestExecutionExecutor,
)
from triggertrade.services.research_demo_execution import (
    RESEARCH_DEMO_CONSUMER,
    RESEARCH_DEMO_MESSAGE_TYPE,
    RESEARCH_DEMO_MESSAGE_VERSION,
    RESEARCH_DEMO_PRODUCER,
    ResearchDemoExecutionDispatcher,
    ResearchDemoExecutionExecutor,
    ResearchDemoExecutionStore,
)


class OwnerDispatchBlocked(PostgresPersistenceError):
    """Raised when a canonical owner route must remain fail-closed."""


@dataclass(frozen=True)
class OwnerDispatchResult:
    processed: bool
    detail: str


class CanonicalOwnerDispatcher:
    """Dispatch only routes whose downstream owner effect is source-complete."""

    def __init__(
        self,
        connection,
        *,
        operator_executor: OperatorExecutionExecutor | None = None,
        research_backtest_executor: ResearchBacktestExecutionExecutor | None = None,
        research_demo_executor: ResearchDemoExecutionExecutor | None = None,
    ) -> None:
        self._connection = connection
        self._messages = DurableMessageStore(connection)
        self._operator_executor = operator_executor
        self._research_backtest_executor = research_backtest_executor
        self._research_demo_executor = research_demo_executor

    def dispatch(self, message: OutboxMessageRecord) -> OwnerDispatchResult:
        inbox, _ = self._messages.record_inbox(
            consumer=message.consumer,
            message_id=message.message_id,
            producer=message.producer,
            message_type=message.message_type,
            message_version=message.message_version,
            payload=message.payload,
        )
        if inbox.status == "PROCESSED":
            self._messages.mark_outbox_consumed(message_id=message.message_id)
            return OwnerDispatchResult(processed=False, detail="inbox_replay_already_processed")

        detail = self._dispatch_payload_complete_route(message)
        self._messages.mark_inbox_processed(consumer=message.consumer, message_id=message.message_id)
        self._messages.mark_outbox_consumed(message_id=message.message_id)
        return OwnerDispatchResult(processed=True, detail=detail)

    def _dispatch_payload_complete_route(self, message: OutboxMessageRecord) -> str:
        route = (message.producer, message.consumer, message.message_type, message.message_version)
        if route == ("Position", "Lifecycle", "ORDER_SPEC", "5"):
            return self._try_lifecycle_start_from_order_spec(message.payload)
        if route == ("Portfolio", "Lifecycle", "SUBMIT_AUTHORIZED", "5"):
            return self._try_lifecycle_start_from_authorization(message.payload)
        if route == ("Lifecycle", "Portfolio", "ORDER_EVENT", "7"):
            return self._accept_portfolio_final_receipt(message)
        if route == (
            OPERATOR_EXECUTION_PRODUCER,
            OPERATOR_EXECUTION_CONSUMER,
            OPERATOR_EXECUTION_MESSAGE_TYPE,
            OPERATOR_EXECUTION_MESSAGE_VERSION,
        ):
            return self._execute_operator_command(message.payload)
        if route == (
            RESEARCH_BACKTEST_PRODUCER,
            RESEARCH_BACKTEST_CONSUMER,
            RESEARCH_BACKTEST_MESSAGE_TYPE,
            RESEARCH_BACKTEST_MESSAGE_VERSION,
        ):
            return self._execute_research_backtest(message.payload)
        if route == (
            RESEARCH_DEMO_PRODUCER,
            RESEARCH_DEMO_CONSUMER,
            RESEARCH_DEMO_MESSAGE_TYPE,
            RESEARCH_DEMO_MESSAGE_VERSION,
        ):
            return self._execute_research_demo(message.payload)
        raise OwnerDispatchBlocked(
            f"handler_not_certified:{message.consumer}:{message.message_type}:{message.message_version}"
        )

    def _execute_operator_command(self, payload: dict[str, Any]) -> str:
        command_id = _body_text(payload, "operator_command", "command_id")
        try:
            return OperatorExecutionDispatcher(
                store=OperatorExecutionCommandStore(self._connection),
                executor=self._operator_executor,
            ).dispatch(command_id)
        except PostgresPersistenceError as exc:
            raise OwnerDispatchBlocked(str(exc)) from exc

    def _execute_research_demo(self, payload: dict[str, Any]) -> str:
        demo_run_id = _body_text(payload, "research_demo", "demo_run_id")
        try:
            return ResearchDemoExecutionDispatcher(
                store=ResearchDemoExecutionStore(self._connection),
                executor=self._research_demo_executor,
            ).dispatch(demo_run_id)
        except PostgresPersistenceError as exc:
            raise OwnerDispatchBlocked(str(exc)) from exc

    def _execute_research_backtest(self, payload: dict[str, Any]) -> str:
        research_id = _body_text(payload, "research_backtest", "research_id")
        run_id = _body_text(payload, "research_backtest", "run_id")
        try:
            from triggertrade.persistence.postgres_research_registry import PostgresResearchRunStore

            return ResearchBacktestExecutionDispatcher(
                store=PostgresResearchRunStore(self._connection),
                executor=self._research_backtest_executor,
            ).dispatch(research_id=research_id, run_id=run_id)
        except PostgresPersistenceError as exc:
            raise OwnerDispatchBlocked(str(exc)) from exc

    def _try_lifecycle_start_from_order_spec(self, order_spec_payload: dict[str, Any]) -> str:
        order_spec_id = _body_text(order_spec_payload, "order_spec", "order_spec_id")
        authorization = SubmitAuthorizationStore(self._connection).get_by_order_spec_id(order_spec_id=order_spec_id)
        if authorization is None:
            raise OwnerDispatchBlocked("dependency_unavailable:Lifecycle:SUBMIT_AUTHORIZED")
        LifecycleStartGateStore(self._connection).accept(
            start_gate_id=_start_gate_id(order_spec_id, authorization.authorization_id),
            order_spec=order_spec_payload,
            submit_authorized=authorization.payload,
        )
        return "processed:Lifecycle:ORDER_SPEC:start_gate"

    def _try_lifecycle_start_from_authorization(self, authorization_payload: dict[str, Any]) -> str:
        order_spec_id = _body_text(authorization_payload, "submit_authorized", "order_spec_id")
        spec = OrderSpecStore(self._connection).get_by_order_spec_id(order_spec_id=order_spec_id)
        if spec is None:
            raise OwnerDispatchBlocked("dependency_unavailable:Lifecycle:ORDER_SPEC")
        authorization_id = _body_text(authorization_payload, "submit_authorized", "authorization_id")
        LifecycleStartGateStore(self._connection).accept(
            start_gate_id=_start_gate_id(order_spec_id, authorization_id),
            order_spec=spec.payload,
            submit_authorized=authorization_payload,
        )
        return "processed:Lifecycle:SUBMIT_AUTHORIZED:start_gate"

    def _accept_portfolio_final_receipt(self, message: OutboxMessageRecord) -> str:
        PortfolioFinalReceiptStore(self._connection).accept_order_event(
            order_event_payload=message.payload,
            delivered_at=_timestamp_text(message.created_at),
        )
        return "processed:Portfolio:ORDER_EVENT:final_receipt"


def _body_text(payload: dict[str, Any], root: str, field: str) -> str:
    body = payload.get(root)
    if not isinstance(body, dict):
        raise OwnerDispatchBlocked(f"invalid_payload:{root}")
    value = body.get(field)
    if not isinstance(value, str) or not value or "\x00" in value:
        raise OwnerDispatchBlocked(f"invalid_payload:{root}.{field}")
    return value


def _start_gate_id(order_spec_id: str, authorization_id: str) -> str:
    source = f"{order_spec_id}\x1f{authorization_id}"
    return f"start-gate-{sha256(source.encode('utf-8')).hexdigest()[:32]}"


def _timestamp_text(value: datetime) -> str:
    resolved = value.astimezone(UTC) if value.tzinfo is not None else value.replace(tzinfo=UTC)
    return resolved.isoformat().replace("+00:00", "Z")

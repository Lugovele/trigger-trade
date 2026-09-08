"""Accounting-backed daily loss enforcement for new entries."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from triggertrade.market_data import FuturesAccountState
from triggertrade.persistence import MessageSeverity, MessageStore
from triggertrade.persistence.daily_loss_store import DailyLossRecord, DailyLossStore
from triggertrade.persistence.futures_accounting_store import FuturesAccountingStore
from triggertrade.rules import TradingRulesVersion


DAILY_LOSS_BLOCKING_RULE = "daily_loss_limit_reached"
DAILY_LOSS_BASELINE_UNAVAILABLE = "daily_loss_baseline_unavailable"
DAILY_LOSS_ACCOUNTING_UNAVAILABLE = "daily_loss_accounting_unavailable"


@dataclass(frozen=True)
class DailyLossEvaluation:
    trading_day: str
    enabled: bool
    status: str
    blocked: bool
    rules_version_id: str
    limit_pct: Decimal | None
    baseline_equity: Decimal | None
    baseline_source: str | None
    baseline_observed_at: str | None
    realized_net_pnl: Decimal | None
    limit_amount: Decimal | None
    loss_used_amount: Decimal | None
    loss_used_pct: Decimal | None
    latched: bool
    latched_at: str | None
    latched_rules_version_id: str | None
    evaluated_at: str
    reason: str | None = None

    def evidence(self) -> dict[str, str | None]:
        payload = asdict(self)
        return {key: None if value is None else str(value) for key, value in payload.items()}


class DailyLossEvaluator:
    def __init__(
        self,
        *,
        accounting_store: FuturesAccountingStore,
        daily_loss_store: DailyLossStore,
        message_store: MessageStore | None = None,
    ) -> None:
        self._accounting_store = accounting_store
        self._daily_loss_store = daily_loss_store
        self._message_store = message_store

    def evaluate(
        self,
        *,
        rules_version: TradingRulesVersion,
        now: datetime,
        account: FuturesAccountState | None = None,
        notify: bool = False,
        persist: bool = True,
    ) -> DailyLossEvaluation:
        evaluated_at = _utc(now).isoformat()
        trading_day = _utc(now).date().isoformat()
        rules = rules_version.draft
        if not rules.daily_loss_limit_enabled:
            return DailyLossEvaluation(
                trading_day=trading_day,
                enabled=False,
                status="DISABLED",
                blocked=False,
                rules_version_id=rules_version.rules_version_id,
                limit_pct=None,
                baseline_equity=None,
                baseline_source=None,
                baseline_observed_at=None,
                realized_net_pnl=None,
                limit_amount=None,
                loss_used_amount=None,
                loss_used_pct=None,
                latched=False,
                latched_at=None,
                latched_rules_version_id=None,
                evaluated_at=evaluated_at,
            )

        limit_pct = rules.daily_loss_limit_pct
        if limit_pct is None or limit_pct <= 0:
            return _blocked_uncertain(
                trading_day=trading_day,
                evaluated_at=evaluated_at,
                rules_version_id=rules_version.rules_version_id,
                limit_pct=limit_pct,
                status="CONFIG_UNAVAILABLE",
                reason=DAILY_LOSS_BASELINE_UNAVAILABLE,
            )

        try:
            record = self._record_for_day(trading_day=trading_day, evaluated_at=evaluated_at, account=account, persist=persist)
            realized = self._accounting_store.realized_net_pnl_for_utc_day(trading_day)
        except Exception as exc:  # noqa: BLE001 - uncertain accounting must fail closed for new entries.
            return _blocked_uncertain(
                trading_day=trading_day,
                evaluated_at=evaluated_at,
                rules_version_id=rules_version.rules_version_id,
                limit_pct=limit_pct,
                status="ACCOUNTING_UNAVAILABLE",
                reason=f"{DAILY_LOSS_ACCOUNTING_UNAVAILABLE}:{exc.__class__.__name__}",
            )

        limit_amount = record.baseline_equity * limit_pct
        loss_used = max(-realized, Decimal("0"))
        loss_used_pct = Decimal("0") if record.baseline_equity <= 0 else loss_used / record.baseline_equity
        threshold_reached = realized <= -limit_amount
        if threshold_reached and not record.latched and persist:
            record = self._daily_loss_store.latch(
                trading_day=trading_day,
                latched_at=evaluated_at,
                rules_version_id=rules_version.rules_version_id,
                reason=DAILY_LOSS_BLOCKING_RULE,
            )
            if notify:
                self._notify_first_latch(record=record, evaluation_at=evaluated_at, limit_amount=limit_amount, realized_net_pnl=realized)

        blocked = record.latched or threshold_reached
        status = "LATCHED" if record.latched else "LIMIT_REACHED" if threshold_reached else "OK"
        reason = DAILY_LOSS_BLOCKING_RULE if blocked else None
        return DailyLossEvaluation(
            trading_day=trading_day,
            enabled=True,
            status=status,
            blocked=blocked,
            rules_version_id=rules_version.rules_version_id,
            limit_pct=limit_pct,
            baseline_equity=record.baseline_equity,
            baseline_source=record.baseline_source,
            baseline_observed_at=record.baseline_observed_at,
            realized_net_pnl=realized,
            limit_amount=limit_amount,
            loss_used_amount=loss_used,
            loss_used_pct=loss_used_pct,
            latched=record.latched,
            latched_at=record.latched_at,
            latched_rules_version_id=record.latched_rules_version_id,
            evaluated_at=evaluated_at,
            reason=reason,
        )

    def _record_for_day(self, *, trading_day: str, evaluated_at: str, account: FuturesAccountState | None, persist: bool) -> DailyLossRecord:
        existing = self._daily_loss_store.get_record(trading_day)
        if existing is not None:
            return existing
        snapshot = self._accounting_store.first_equity_snapshot_for_utc_day(trading_day)
        if snapshot is not None:
            if not persist:
                return DailyLossRecord(
                    trading_day=trading_day,
                    baseline_equity=Decimal(str(snapshot["equity"])),
                    baseline_source=str(snapshot["source"]),
                    baseline_observed_at=str(snapshot["observed_at"]),
                    latched=False,
                    latched_at=None,
                    latched_rules_version_id=None,
                    latched_reason=None,
                    notified_at=None,
                    updated_at=evaluated_at,
                )
            return self._daily_loss_store.ensure_baseline(
                trading_day=trading_day,
                baseline_equity=Decimal(str(snapshot["equity"])),
                baseline_source=str(snapshot["source"]),
                baseline_observed_at=str(snapshot["observed_at"]),
                updated_at=evaluated_at,
            )
        if not persist or account is None or account.equity is None or account.equity <= 0:
            raise RuntimeError(DAILY_LOSS_BASELINE_UNAVAILABLE)
        return self._daily_loss_store.ensure_baseline(
            trading_day=trading_day,
            baseline_equity=account.equity,
            baseline_source="active_account_first_evaluation",
            baseline_observed_at=evaluated_at,
            updated_at=evaluated_at,
        )

    def _notify_first_latch(
        self,
        *,
        record: DailyLossRecord,
        evaluation_at: str,
        limit_amount: Decimal,
        realized_net_pnl: Decimal,
    ) -> None:
        if self._message_store is None or record.notified_at is not None:
            return
        self._message_store.create_message(
            severity=MessageSeverity.WARNING,
            title="Daily loss limit reached",
            body="Daily loss limit reached. New entries are blocked for the rest of the UTC trading day; existing positions continue to be managed.",
            source="daily_loss_enforcement",
            entity_type="trading_day",
            entity_id=record.trading_day,
            dedupe_key=f"daily_loss:{record.trading_day}:latched",
            metadata={
                "trading_day": record.trading_day,
                "limit_amount": str(limit_amount),
                "realized_net_pnl": str(realized_net_pnl),
            },
            created_at=evaluation_at,
        )
        self._daily_loss_store.mark_notified(trading_day=record.trading_day, notified_at=evaluation_at)


def read_only_daily_loss_state(
    *,
    accounting_store: FuturesAccountingStore,
    daily_loss_store: DailyLossStore,
    rules_version: TradingRulesVersion,
    now: datetime | None = None,
) -> dict[str, Any]:
    evaluation = DailyLossEvaluator(accounting_store=accounting_store, daily_loss_store=daily_loss_store).evaluate(
        rules_version=rules_version,
        now=now or datetime.now(UTC),
        account=None,
        notify=False,
        persist=False,
    )
    return evaluation.evidence()


def _blocked_uncertain(
    *,
    trading_day: str,
    evaluated_at: str,
    rules_version_id: str,
    limit_pct: Decimal | None,
    status: str,
    reason: str,
) -> DailyLossEvaluation:
    return DailyLossEvaluation(
        trading_day=trading_day,
        enabled=True,
        status=status,
        blocked=True,
        rules_version_id=rules_version_id,
        limit_pct=limit_pct,
        baseline_equity=None,
        baseline_source=None,
        baseline_observed_at=None,
        realized_net_pnl=None,
        limit_amount=None,
        loss_used_amount=None,
        loss_used_pct=None,
        latched=False,
        latched_at=None,
        latched_rules_version_id=None,
        evaluated_at=evaluated_at,
        reason=reason,
    )


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)

"""Portfolio-owned ACCOUNTING_DAY_V1 base, live metrics and capacity gates."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime, time
from enum import StrEnum
from fractions import Fraction
from typing import Any
from zoneinfo import ZoneInfo

from triggertrade.numeric_policy import NumericPolicyError, canonical_decimal_text, compare_exact, parse_decimal_text
from triggertrade.portfolio_state import CommitmentBuckets


ACCOUNTING_DAY_POLICY_VERSION = "ACCOUNTING_DAY_V1"
ACCOUNTING_TIMEZONE = "Asia/Jerusalem"


class PortfolioAccountingDayError(ValueError):
    """Raised when Portfolio accounting-day state cannot be represented safely."""


class RolloverState(StrEnum):
    PROVEN = "PROVEN"
    RECONCILING = "RECONCILING"


class PortfolioGateStatus(StrEnum):
    PASS = "PASS"
    BLOCKED = "BLOCKED"
    UNAVAILABLE = "UNAVAILABLE"


@dataclass(frozen=True)
class AccountingDayWindow:
    accounting_day_id: str
    boundary_start_at: str
    boundary_end_at: str
    timezone: str = ACCOUNTING_TIMEZONE
    policy_version: str = ACCOUNTING_DAY_POLICY_VERSION


@dataclass(frozen=True)
class AccountingDayEvidence:
    source: str
    evidence_id: str
    basis: dict[str, Any]

    def __post_init__(self) -> None:
        _text(self.source, field="source")
        _text(self.evidence_id, field="evidence_id")

    def to_payload(self) -> dict[str, Any]:
        return {"source": self.source, "evidence_id": self.evidence_id, "basis": dict(self.basis)}

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "AccountingDayEvidence":
        return cls(source=str(payload["source"]), evidence_id=str(payload["evidence_id"]), basis=dict(payload["basis"]))


@dataclass(frozen=True)
class PortfolioAccountingDay:
    portfolio_id: str
    accounting_day_id: str
    boundary_start_at: str
    boundary_end_at: str
    rollover_state: RolloverState
    daily_portfolio_base: str | None
    base_evidence: AccountingDayEvidence | None
    current_portfolio_equity: str | None = None
    daily_realized_pnl: str = "0"
    unrealized_pnl: str | None = None
    total_pnl: str | None = None
    external_capital_flow_amount: str = "0"
    daily_loss_latched: bool = False
    daily_loss_latched_at: str | None = None
    daily_loss_reason: str | None = None

    def __post_init__(self) -> None:
        _text(self.portfolio_id, field="portfolio_id")
        _text(self.accounting_day_id, field="accounting_day_id")
        _parse_rfc3339(self.boundary_start_at, field="boundary_start_at")
        _parse_rfc3339(self.boundary_end_at, field="boundary_end_at")
        object.__setattr__(self, "rollover_state", RolloverState(self.rollover_state))
        if self.rollover_state is RolloverState.PROVEN:
            if self.daily_portfolio_base is None:
                raise PortfolioAccountingDayError("PROVEN accounting day requires daily_portfolio_base")
            if self.base_evidence is None:
                raise PortfolioAccountingDayError("PROVEN accounting day requires base_evidence")
        if self.daily_portfolio_base is not None:
            object.__setattr__(self, "daily_portfolio_base", _decimal_text(self.daily_portfolio_base, field="daily_portfolio_base", allow_negative=False))
        for field in ("current_portfolio_equity", "unrealized_pnl", "total_pnl"):
            value = getattr(self, field)
            if value is not None:
                object.__setattr__(self, field, _decimal_text(value, field=field, allow_negative=True))
        object.__setattr__(self, "daily_realized_pnl", _decimal_text(self.daily_realized_pnl, field="daily_realized_pnl", allow_negative=True))
        object.__setattr__(
            self,
            "external_capital_flow_amount",
            _decimal_text(self.external_capital_flow_amount, field="external_capital_flow_amount", allow_negative=True),
        )
        if not isinstance(self.daily_loss_latched, bool):
            raise PortfolioAccountingDayError("daily_loss_latched must be a boolean")
        if self.daily_loss_latched_at is not None:
            _parse_rfc3339(self.daily_loss_latched_at, field="daily_loss_latched_at")
        if self.daily_loss_reason is not None:
            _text(self.daily_loss_reason, field="daily_loss_reason")

    @property
    def is_exposure_blocked_by_rollover(self) -> bool:
        return self.rollover_state is RolloverState.RECONCILING

    def to_payload(self) -> dict[str, Any]:
        return {
            "portfolio_accounting_day": {
                "policy_version": ACCOUNTING_DAY_POLICY_VERSION,
                "timezone": ACCOUNTING_TIMEZONE,
                "portfolio_id": self.portfolio_id,
                "accounting_day_id": self.accounting_day_id,
                "boundary_start_at": self.boundary_start_at,
                "boundary_end_at": self.boundary_end_at,
                "rollover_state": self.rollover_state.value,
                "daily_portfolio_base": self.daily_portfolio_base,
                "base_evidence": None if self.base_evidence is None else self.base_evidence.to_payload(),
                "current_portfolio_equity": self.current_portfolio_equity,
                "daily_realized_pnl": self.daily_realized_pnl,
                "unrealized_pnl": self.unrealized_pnl,
                "total_pnl": self.total_pnl,
                "external_capital_flow_amount": self.external_capital_flow_amount,
                "daily_loss_latched": self.daily_loss_latched,
                "daily_loss_latched_at": self.daily_loss_latched_at,
                "daily_loss_reason": self.daily_loss_reason,
            }
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PortfolioAccountingDay":
        body = payload["portfolio_accounting_day"]
        evidence = body.get("base_evidence")
        return cls(
            portfolio_id=str(body["portfolio_id"]),
            accounting_day_id=str(body["accounting_day_id"]),
            boundary_start_at=str(body["boundary_start_at"]),
            boundary_end_at=str(body["boundary_end_at"]),
            rollover_state=RolloverState(body["rollover_state"]),
            daily_portfolio_base=body["daily_portfolio_base"],
            base_evidence=None if evidence is None else AccountingDayEvidence.from_payload(evidence),
            current_portfolio_equity=body["current_portfolio_equity"],
            daily_realized_pnl=str(body["daily_realized_pnl"]),
            unrealized_pnl=body["unrealized_pnl"],
            total_pnl=body["total_pnl"],
            external_capital_flow_amount=str(body["external_capital_flow_amount"]),
            daily_loss_latched=bool(body["daily_loss_latched"]),
            daily_loss_latched_at=body["daily_loss_latched_at"],
            daily_loss_reason=body["daily_loss_reason"],
        )


@dataclass(frozen=True)
class DailyLossGateResult:
    status: PortfolioGateStatus
    blocked: bool
    limit_amount: str | None
    reason_code: str | None
    latched: bool


@dataclass(frozen=True)
class PortfolioLimitConfiguration:
    max_capital_in_positions_pct: str
    coin_allocation_pct: dict[str, str]
    max_open_positions: int
    max_positions_per_coin: int

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "max_capital_in_positions_pct",
            _percentage_text(self.max_capital_in_positions_pct, field="max_capital_in_positions_pct"),
        )
        if not self.coin_allocation_pct:
            raise PortfolioAccountingDayError("coin_allocation_pct is required")
        normalized: dict[str, str] = {}
        for symbol, pct in self.coin_allocation_pct.items():
            symbol_key = _text(symbol, field="symbol").upper()
            if symbol_key in normalized:
                raise PortfolioAccountingDayError("coin allocations must be unique by symbol")
            normalized[symbol_key] = _percentage_text(pct, field="allocation_pct")
        object.__setattr__(self, "coin_allocation_pct", normalized)
        for field in ("max_open_positions", "max_positions_per_coin"):
            value = getattr(self, field)
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                raise PortfolioAccountingDayError(f"{field} must be a nonnegative integer")

    def global_capital_cap(self, daily_portfolio_base: str) -> str:
        return _format_decimal(_decimal(daily_portfolio_base, field="daily_portfolio_base") * _decimal(self.max_capital_in_positions_pct, field="max_capital_in_positions_pct") / 100)

    def coin_capital_cap(self, *, symbol: str, daily_portfolio_base: str) -> str:
        symbol = _text(symbol, field="symbol").upper()
        if symbol not in self.coin_allocation_pct:
            raise PortfolioAccountingDayError("symbol is not configured for allocation")
        return _format_decimal(_decimal(daily_portfolio_base, field="daily_portfolio_base") * _decimal(self.coin_allocation_pct[symbol], field="allocation_pct") / 100)


@dataclass(frozen=True)
class CapacityGateResult:
    status: PortfolioGateStatus
    remaining_global_capital: str
    remaining_coin_capital: str
    remaining_global_slots: int
    remaining_coin_slots: int
    reason_code: str | None


def accounting_day_window(instant: str | datetime, *, timezone: str = ACCOUNTING_TIMEZONE) -> AccountingDayWindow:
    zone = ZoneInfo(timezone)
    resolved = _coerce_datetime(instant).astimezone(zone)
    local_date = resolved.date()
    start_local = datetime.combine(local_date, time.min, tzinfo=zone)
    next_local = datetime.combine(local_date.fromordinal(local_date.toordinal() + 1), time.min, tzinfo=zone)
    return AccountingDayWindow(
        accounting_day_id=local_date.isoformat(),
        boundary_start_at=_format_time(start_local.astimezone(UTC)),
        boundary_end_at=_format_time(next_local.astimezone(UTC)),
        timezone=timezone,
    )


def establish_day_from_boundary_snapshot(
    *,
    portfolio_id: str,
    boundary_instant: str | datetime,
    strategy_wallet_capital_excluding_unrealized_pnl: str,
    evidence_id: str,
    evidence: dict[str, Any] | None = None,
) -> PortfolioAccountingDay:
    window = accounting_day_window(boundary_instant)
    base = _decimal_text(strategy_wallet_capital_excluding_unrealized_pnl, field="daily_portfolio_base", allow_negative=False)
    return PortfolioAccountingDay(
        portfolio_id=portfolio_id,
        accounting_day_id=window.accounting_day_id,
        boundary_start_at=window.boundary_start_at,
        boundary_end_at=window.boundary_end_at,
        rollover_state=RolloverState.PROVEN,
        daily_portfolio_base=base,
        base_evidence=AccountingDayEvidence(
            source="VERIFIED_BOUNDARY_SNAPSHOT",
            evidence_id=evidence_id,
            basis={"strategy_wallet_capital_excluding_unrealized_pnl": base, **(evidence or {})},
        ),
    )


def establish_day_from_reconstruction(
    *,
    portfolio_id: str,
    boundary_instant: str | datetime,
    reconstructed_wallet_capital: str | None,
    evidence_id: str,
    complete_authoritative_cashflow_history: bool,
    reconstruction_basis: dict[str, Any] | None = None,
) -> PortfolioAccountingDay:
    window = accounting_day_window(boundary_instant)
    if not complete_authoritative_cashflow_history or reconstructed_wallet_capital is None:
        return PortfolioAccountingDay(
            portfolio_id=portfolio_id,
            accounting_day_id=window.accounting_day_id,
            boundary_start_at=window.boundary_start_at,
            boundary_end_at=window.boundary_end_at,
            rollover_state=RolloverState.RECONCILING,
            daily_portfolio_base=None,
            base_evidence=AccountingDayEvidence(
                source="UNPROVEN_BOUNDARY",
                evidence_id=evidence_id,
                basis=reconstruction_basis or {},
            ),
        )
    base = _decimal_text(reconstructed_wallet_capital, field="daily_portfolio_base", allow_negative=False)
    return PortfolioAccountingDay(
        portfolio_id=portfolio_id,
        accounting_day_id=window.accounting_day_id,
        boundary_start_at=window.boundary_start_at,
        boundary_end_at=window.boundary_end_at,
        rollover_state=RolloverState.PROVEN,
        daily_portfolio_base=base,
        base_evidence=AccountingDayEvidence(
            source="COMPLETE_DETERMINISTIC_RECONSTRUCTION",
            evidence_id=evidence_id,
            basis={"reconstructed_wallet_capital": base, **(reconstruction_basis or {})},
        ),
    )


def record_live_metrics(
    day: PortfolioAccountingDay,
    *,
    current_portfolio_equity: str,
    unrealized_pnl: str,
    external_capital_flow_amount: str | None = None,
) -> PortfolioAccountingDay:
    realized = _decimal(day.daily_realized_pnl, field="daily_realized_pnl")
    unrealized = _decimal(unrealized_pnl, field="unrealized_pnl")
    return replace(
        day,
        current_portfolio_equity=_decimal_text(current_portfolio_equity, field="current_portfolio_equity", allow_negative=True),
        unrealized_pnl=_format_decimal(unrealized),
        total_pnl=_format_decimal(realized + unrealized),
        external_capital_flow_amount=(
            day.external_capital_flow_amount
            if external_capital_flow_amount is None
            else _decimal_text(external_capital_flow_amount, field="external_capital_flow_amount", allow_negative=True)
        ),
    )


def apply_final_result_to_day(
    day: PortfolioAccountingDay,
    *,
    realized_pnl: str,
    result_id: str,
    tranche_id: str,
) -> PortfolioAccountingDay:
    _text(result_id, field="result_id")
    _text(tranche_id, field="tranche_id")
    realized = _decimal(day.daily_realized_pnl, field="daily_realized_pnl") + _decimal(realized_pnl, field="realized_pnl")
    unrealized = Fraction(0) if day.unrealized_pnl is None else _decimal(day.unrealized_pnl, field="unrealized_pnl")
    return replace(day, daily_realized_pnl=_format_decimal(realized), total_pnl=_format_decimal(realized + unrealized))


def evaluate_daily_loss_gate(
    day: PortfolioAccountingDay,
    *,
    enabled: bool,
    daily_loss_limit_pct: str | None,
    evaluated_at: str,
) -> DailyLossGateResult:
    if not enabled:
        return DailyLossGateResult(
            status=PortfolioGateStatus.PASS,
            blocked=False,
            limit_amount=None,
            reason_code=None,
            latched=day.daily_loss_latched,
        )
    if day.daily_loss_latched:
        return DailyLossGateResult(
            status=PortfolioGateStatus.BLOCKED,
            blocked=True,
            limit_amount=None,
            reason_code=day.daily_loss_reason or "DAILY_LOSS_LIMIT_REACHED",
            latched=True,
        )
    if day.rollover_state is RolloverState.RECONCILING or day.daily_portfolio_base is None:
        return DailyLossGateResult(
            status=PortfolioGateStatus.UNAVAILABLE,
            blocked=True,
            limit_amount=None,
            reason_code="ACCOUNTING_DAY_BASE_UNPROVEN",
            latched=day.daily_loss_latched,
        )
    pct = _decimal(_percentage_text(daily_loss_limit_pct or "", field="daily_loss_limit_pct"), field="daily_loss_limit_pct")
    base = _decimal(day.daily_portfolio_base, field="daily_portfolio_base")
    limit_amount = base * pct / 100
    realized = _decimal(day.daily_realized_pnl, field="daily_realized_pnl")
    threshold_reached = compare_exact(100 * realized, -(base * pct)) <= 0
    return DailyLossGateResult(
        status=PortfolioGateStatus.BLOCKED if threshold_reached else PortfolioGateStatus.PASS,
        blocked=threshold_reached,
        limit_amount=_format_decimal(limit_amount),
        reason_code="DAILY_LOSS_LIMIT_REACHED" if threshold_reached else None,
        latched=threshold_reached,
    )


def latch_daily_loss(day: PortfolioAccountingDay, *, latched_at: str, reason_code: str = "DAILY_LOSS_LIMIT_REACHED") -> PortfolioAccountingDay:
    _parse_rfc3339(latched_at, field="latched_at")
    _text(reason_code, field="reason_code")
    if day.daily_loss_latched:
        return day
    return replace(day, daily_loss_latched=True, daily_loss_latched_at=latched_at, daily_loss_reason=reason_code)


def evaluate_capacity_gate(
    *,
    config: PortfolioLimitConfiguration,
    symbol: str,
    daily_portfolio_base: str,
    global_buckets: CommitmentBuckets,
    coin_buckets: CommitmentBuckets,
    requested_committed_capital: str,
) -> CapacityGateResult:
    symbol = _text(symbol, field="symbol").upper()
    requested = _nonnegative_decimal(requested_committed_capital, field="requested_committed_capital")
    global_cap = _decimal(config.global_capital_cap(daily_portfolio_base), field="global_capital_cap")
    coin_cap = _decimal(config.coin_capital_cap(symbol=symbol, daily_portfolio_base=daily_portfolio_base), field="coin_capital_cap")
    global_committed = _bucket_total(global_buckets)
    coin_committed = _bucket_total(coin_buckets)
    remaining_global = global_cap - global_committed
    remaining_coin = coin_cap - coin_committed
    remaining_global_slots = config.max_open_positions - global_buckets.committed_tranches
    remaining_coin_slots = config.max_positions_per_coin - coin_buckets.committed_tranches
    if remaining_global < requested:
        reason = "GLOBAL_CAPACITY_EXCEEDED"
        status = PortfolioGateStatus.BLOCKED
    elif remaining_coin < requested:
        reason = "COIN_CAPACITY_EXCEEDED"
        status = PortfolioGateStatus.BLOCKED
    elif remaining_global_slots <= 0:
        reason = "GLOBAL_SLOT_UNAVAILABLE"
        status = PortfolioGateStatus.BLOCKED
    elif remaining_coin_slots <= 0:
        reason = "COIN_SLOT_UNAVAILABLE"
        status = PortfolioGateStatus.BLOCKED
    else:
        reason = None
        status = PortfolioGateStatus.PASS
    return CapacityGateResult(
        status=status,
        remaining_global_capital=_format_decimal(remaining_global),
        remaining_coin_capital=_format_decimal(remaining_coin),
        remaining_global_slots=max(remaining_global_slots, 0),
        remaining_coin_slots=max(remaining_coin_slots, 0),
        reason_code=reason,
    )


def _bucket_total(buckets: CommitmentBuckets) -> Fraction:
    return (
        _decimal(buckets.held_committed_capital, field="held_committed_capital")
        + _decimal(buckets.reserved_committed_capital, field="reserved_committed_capital")
        + _decimal(buckets.filled_committed_capital, field="filled_committed_capital")
        + _decimal(buckets.closing_retained_committed_capital, field="closing_retained_committed_capital")
    )


def _coerce_datetime(value: str | datetime) -> datetime:
    if isinstance(value, datetime):
        resolved = value
    else:
        resolved = _parse_rfc3339(value, field="instant")
    return resolved if resolved.tzinfo is not None else resolved.replace(tzinfo=UTC)


def _parse_rfc3339(value: str, *, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise PortfolioAccountingDayError(f"{field} is required")
    try:
        resolved = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise PortfolioAccountingDayError(f"{field} must be an RFC3339 datetime") from exc
    if resolved.tzinfo is None:
        raise PortfolioAccountingDayError(f"{field} must include timezone")
    return resolved


def _format_time(value: datetime) -> str:
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _decimal_text(value: str, *, field: str, allow_negative: bool) -> str:
    resolved = _decimal(value, field=field)
    if not allow_negative and resolved < 0:
        raise PortfolioAccountingDayError(f"{field} must be nonnegative")
    return _format_decimal(resolved)


def _percentage_text(value: str, *, field: str) -> str:
    resolved = _decimal(value, field=field)
    if compare_exact(resolved, 0) < 0 or compare_exact(resolved, 100) > 0:
        raise PortfolioAccountingDayError(f"{field} must be a percentage from 0 to 100")
    return _format_decimal(resolved)


def _nonnegative_decimal(value: str, *, field: str) -> Fraction:
    resolved = _decimal(value, field=field)
    if compare_exact(resolved, 0) < 0:
        raise PortfolioAccountingDayError(f"{field} must be nonnegative")
    return resolved


def _decimal(value: str, *, field: str) -> Fraction:
    try:
        return parse_decimal_text(value)
    except NumericPolicyError as exc:
        raise PortfolioAccountingDayError(f"{field} must be an exact decimal string") from exc


def _format_decimal(value: Fraction) -> str:
    return canonical_decimal_text(value)


def _text(value: object, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise PortfolioAccountingDayError(f"{field} is required")
    return value

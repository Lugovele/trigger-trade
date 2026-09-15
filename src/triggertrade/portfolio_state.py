"""Portfolio Rules-owned state model and deterministic health transitions."""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from typing import Any


class PortfolioStateError(ValueError):
    """Raised when Portfolio state cannot be represented deterministically."""


class PortfolioHealth(StrEnum):
    LIVE = "LIVE"
    RECONCILING = "RECONCILING"
    STALE = "STALE"


@dataclass(frozen=True)
class CommitmentBuckets:
    held_committed_capital: str = "0"
    reserved_committed_capital: str = "0"
    filled_committed_capital: str = "0"
    closing_retained_committed_capital: str = "0"
    committed_tranches: int = 0

    def __post_init__(self) -> None:
        for field in (
            "held_committed_capital",
            "reserved_committed_capital",
            "filled_committed_capital",
            "closing_retained_committed_capital",
        ):
            object.__setattr__(self, field, _decimal_text(getattr(self, field), field=field))
        if not isinstance(self.committed_tranches, int) or isinstance(self.committed_tranches, bool) or self.committed_tranches < 0:
            raise PortfolioStateError("committed_tranches must be a nonnegative integer")

    def to_payload(self) -> dict[str, Any]:
        return {
            "held_committed_capital": self.held_committed_capital,
            "reserved_committed_capital": self.reserved_committed_capital,
            "filled_committed_capital": self.filled_committed_capital,
            "closing_retained_committed_capital": self.closing_retained_committed_capital,
            "committed_tranches": self.committed_tranches,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CommitmentBuckets":
        committed_tranches = payload["committed_tranches"]
        if not isinstance(committed_tranches, int) or isinstance(committed_tranches, bool):
            raise PortfolioStateError("committed_tranches must be a nonnegative integer")
        return cls(
            held_committed_capital=str(payload["held_committed_capital"]),
            reserved_committed_capital=str(payload["reserved_committed_capital"]),
            filled_committed_capital=str(payload["filled_committed_capital"]),
            closing_retained_committed_capital=str(payload["closing_retained_committed_capital"]),
            committed_tranches=committed_tranches,
        )


@dataclass(frozen=True)
class CoinPortfolioState:
    symbol: str
    buckets: CommitmentBuckets = field(default_factory=CommitmentBuckets)
    cooldown_until: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not self.symbol:
            raise PortfolioStateError("coin symbol is required")
        object.__setattr__(self, "symbol", self.symbol.upper())
        if self.cooldown_until is not None and (not isinstance(self.cooldown_until, str) or not self.cooldown_until):
            raise PortfolioStateError("cooldown_until must be a non-empty timestamp or null")

    def to_payload(self) -> dict[str, Any]:
        payload = {"symbol": self.symbol, **self.buckets.to_payload(), "cooldown_until": self.cooldown_until}
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CoinPortfolioState":
        return cls(
            symbol=str(payload["symbol"]),
            buckets=CommitmentBuckets.from_payload(payload),
            cooldown_until=payload.get("cooldown_until"),
        )


@dataclass(frozen=True)
class PortfolioState:
    portfolio_id: str
    revision: int
    health: PortfolioHealth
    as_of: str
    global_buckets: CommitmentBuckets = field(default_factory=CommitmentBuckets)
    coins: tuple[CoinPortfolioState, ...] = ()
    reason_code: str | None = None
    evidence_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.portfolio_id, str) or not self.portfolio_id:
            raise PortfolioStateError("portfolio_id is required")
        if not isinstance(self.revision, int) or isinstance(self.revision, bool) or self.revision < 1:
            raise PortfolioStateError("revision must be a positive integer")
        if not isinstance(self.as_of, str) or not self.as_of:
            raise PortfolioStateError("as_of is required")
        object.__setattr__(self, "health", PortfolioHealth(self.health))
        symbols = [coin.symbol for coin in self.coins]
        if len(set(symbols)) != len(symbols):
            raise PortfolioStateError("coin symbols must be unique")
        if self.reason_code is not None and (not isinstance(self.reason_code, str) or not self.reason_code):
            raise PortfolioStateError("reason_code must be a non-empty string or null")
        if self.evidence_id is not None and (not isinstance(self.evidence_id, str) or not self.evidence_id):
            raise PortfolioStateError("evidence_id must be a non-empty string or null")

    def to_payload(self) -> dict[str, Any]:
        return {
            "portfolio_state": {
                "portfolio_id": self.portfolio_id,
                "revision": self.revision,
                "health": self.health.value,
                "as_of": self.as_of,
                "reason_code": self.reason_code,
                "evidence_id": self.evidence_id,
                "global": self.global_buckets.to_payload(),
                "coins": [coin.to_payload() for coin in self.coins],
            }
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PortfolioState":
        body = payload["portfolio_state"]
        revision = body["revision"]
        if not isinstance(revision, int) or isinstance(revision, bool):
            raise PortfolioStateError("revision must be a positive integer")
        return cls(
            portfolio_id=str(body["portfolio_id"]),
            revision=revision,
            health=PortfolioHealth(body["health"]),
            as_of=str(body["as_of"]),
            reason_code=body.get("reason_code"),
            evidence_id=body.get("evidence_id"),
            global_buckets=CommitmentBuckets.from_payload(body["global"]),
            coins=tuple(CoinPortfolioState.from_payload(coin) for coin in body["coins"]),
        )


def initial_portfolio_state(*, portfolio_id: str, as_of: str) -> PortfolioState:
    return PortfolioState(portfolio_id=portfolio_id, revision=1, health=PortfolioHealth.STALE, as_of=as_of)


def mark_reconciling(*, state: PortfolioState, as_of: str, evidence_id: str, reason_code: str) -> PortfolioState:
    return _next_state(
        state=state,
        health=PortfolioHealth.RECONCILING,
        as_of=as_of,
        evidence_id=evidence_id,
        reason_code=reason_code,
    )


def mark_live(*, state: PortfolioState, as_of: str, evidence_id: str, reason_code: str = "PORTFOLIO_FACTS_CONFIRMED") -> PortfolioState:
    return _next_state(
        state=state,
        health=PortfolioHealth.LIVE,
        as_of=as_of,
        evidence_id=evidence_id,
        reason_code=reason_code,
    )


def mark_stale(*, state: PortfolioState, as_of: str, evidence_id: str, reason_code: str) -> PortfolioState:
    return _next_state(
        state=state,
        health=PortfolioHealth.STALE,
        as_of=as_of,
        evidence_id=evidence_id,
        reason_code=reason_code,
    )


def _next_state(
    *,
    state: PortfolioState,
    health: PortfolioHealth,
    as_of: str,
    evidence_id: str,
    reason_code: str,
) -> PortfolioState:
    return PortfolioState(
        portfolio_id=state.portfolio_id,
        revision=state.revision + 1,
        health=health,
        as_of=as_of,
        evidence_id=evidence_id,
        reason_code=reason_code,
        global_buckets=state.global_buckets,
        coins=state.coins,
    )


def _decimal_text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise PortfolioStateError(f"{field} must be an exact decimal string")
    try:
        resolved = Decimal(value)
    except InvalidOperation as exc:
        raise PortfolioStateError(f"{field} must be an exact decimal string") from exc
    if not resolved.is_finite() or resolved < 0:
        raise PortfolioStateError(f"{field} must be a finite nonnegative decimal string")
    return format(resolved.normalize(), "f") if resolved != 0 else "0"

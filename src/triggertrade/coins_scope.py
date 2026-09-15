"""Portfolio-produced Coins v2 scope revisions and Set intake rules."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from triggertrade.contracts import ContractError, TargetContract, parse_contract


class CoinsScopeError(ValueError):
    """Raised when a Coins scope revision cannot be represented safely."""


class CoinsAction(StrEnum):
    OPEN = "OPEN"
    CLOSE = "CLOSE"


@dataclass(frozen=True)
class CoinScopeDelta:
    symbol: str
    scope_revision: int
    action: CoinsAction

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        if not isinstance(self.scope_revision, int) or isinstance(self.scope_revision, bool) or self.scope_revision < 0:
            raise CoinsScopeError("scope_revision must be a nonnegative integer")
        object.__setattr__(self, "action", CoinsAction(self.action))

    def to_payload(self) -> dict[str, Any]:
        return {
            "symbol": self.symbol,
            "scope_revision": self.scope_revision,
            "action": self.action.value,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "CoinScopeDelta":
        symbol = payload["symbol"]
        if not isinstance(symbol, str):
            raise CoinsScopeError("symbol is required")
        revision = payload["scope_revision"]
        if not isinstance(revision, int) or isinstance(revision, bool):
            raise CoinsScopeError("scope_revision must be a nonnegative integer")
        return cls(symbol=symbol, scope_revision=revision, action=CoinsAction(payload["action"]))


def build_coins_contract(
    *,
    event_id: str,
    occurred_at: str,
    symbols: Sequence[CoinScopeDelta],
) -> TargetContract:
    if not symbols:
        raise CoinsScopeError("Coins contract requires at least one symbol delta")
    seen: set[tuple[str, int]] = set()
    for delta in symbols:
        key = (delta.symbol, delta.scope_revision)
        if key in seen:
            raise CoinsScopeError("Coins contract cannot repeat a symbol revision")
        seen.add(key)
    payload = {
        "coins": {
            "contract_version": 2,
            "event_id": _text(event_id, field="event_id"),
            "occurred_at": _text(occurred_at, field="occurred_at"),
            "symbols": [delta.to_payload() for delta in symbols],
        }
    }
    try:
        return parse_contract("COINS", payload)
    except ContractError as exc:
        raise CoinsScopeError(str(exc)) from exc


def apply_set_scope_delta(
    current: MappingState | None,
    delta: CoinScopeDelta,
    *,
    event_id: str,
    occurred_at: str,
    payload_digest: str,
) -> "SetScopeState | None":
    if current is not None and delta.scope_revision <= current.scope_revision:
        return None
    return SetScopeState(
        symbol=delta.symbol,
        scope_revision=delta.scope_revision,
        action=delta.action,
        event_id=event_id,
        occurred_at=occurred_at,
        payload_digest=payload_digest,
    )


@dataclass(frozen=True)
class SetScopeState:
    symbol: str
    scope_revision: int
    action: CoinsAction
    event_id: str
    occurred_at: str
    payload_digest: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        if not isinstance(self.scope_revision, int) or isinstance(self.scope_revision, bool) or self.scope_revision < 0:
            raise CoinsScopeError("scope_revision must be a nonnegative integer")
        object.__setattr__(self, "action", CoinsAction(self.action))
        _text(self.event_id, field="event_id")
        _text(self.occurred_at, field="occurred_at")
        _text(self.payload_digest, field="payload_digest")

    @property
    def is_open(self) -> bool:
        return self.action is CoinsAction.OPEN


MappingState = SetScopeState


def _symbol(value: str) -> str:
    return _text(value, field="symbol").upper()


def _text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise CoinsScopeError(f"{field} is required")
    return value

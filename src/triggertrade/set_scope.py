"""Set-owned formation epoch and configuration pin structures."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

from triggertrade.canonical_json import canonical_json_digest


class SetScopeError(ValueError):
    """Raised when Set scope epoch state cannot be represented safely."""


@dataclass(frozen=True)
class SetConfigurationBinding:
    set_config_id: str
    set_config_version: str
    set_config_digest: str
    trigger_config_id: str
    trigger_config_version: str
    trigger_config_digest: str
    core_set_config_id: str
    core_set_config_version: str
    core_set_config_digest: str
    numeric_policy_version: str = "TT_SET_NUMERIC_V1"

    def __post_init__(self) -> None:
        for field in (
            "set_config_id",
            "set_config_version",
            "set_config_digest",
            "trigger_config_id",
            "trigger_config_version",
            "trigger_config_digest",
            "core_set_config_id",
            "core_set_config_version",
            "core_set_config_digest",
            "numeric_policy_version",
        ):
            _text(getattr(self, field), field=field)
        if self.numeric_policy_version != "TT_SET_NUMERIC_V1":
            raise SetScopeError("numeric_policy_version must be TT_SET_NUMERIC_V1")

    def to_payload(self) -> dict[str, str]:
        return {
            "set_config_id": self.set_config_id,
            "set_config_version": self.set_config_version,
            "set_config_digest": self.set_config_digest,
            "trigger_config_id": self.trigger_config_id,
            "trigger_config_version": self.trigger_config_version,
            "trigger_config_digest": self.trigger_config_digest,
            "core_set_config_id": self.core_set_config_id,
            "core_set_config_version": self.core_set_config_version,
            "core_set_config_digest": self.core_set_config_digest,
            "numeric_policy_version": self.numeric_policy_version,
        }

    @property
    def digest(self) -> str:
        return canonical_json_digest(self.to_payload())

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "SetConfigurationBinding":
        expected = {
            "set_config_id",
            "set_config_version",
            "set_config_digest",
            "trigger_config_id",
            "trigger_config_version",
            "trigger_config_digest",
            "core_set_config_id",
            "core_set_config_version",
            "core_set_config_digest",
            "numeric_policy_version",
        }
        unknown = set(payload) - expected
        missing = expected - set(payload)
        if unknown:
            raise SetScopeError(f"unknown configuration binding fields: {', '.join(sorted(unknown))}")
        if missing:
            raise SetScopeError(f"missing configuration binding fields: {', '.join(sorted(missing))}")
        return cls(**{field: payload[field] for field in expected})


@dataclass(frozen=True)
class SetFormationEpoch:
    symbol: str
    formation_epoch: int
    open_event_id: str
    opened_at: str
    open_payload_digest: str
    configuration_binding: SetConfigurationBinding
    epoch_state: str = "ACTIVE"
    terminated_by_scope_revision: int | None = None
    terminated_by_event_id: str | None = None
    terminated_at: str | None = None
    terminated_by_action: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _text(self.symbol, field="symbol").upper())
        if not isinstance(self.formation_epoch, int) or isinstance(self.formation_epoch, bool) or self.formation_epoch < 0:
            raise SetScopeError("formation_epoch must be a nonnegative integer")
        for field in ("open_event_id", "opened_at", "open_payload_digest", "epoch_state"):
            _text(getattr(self, field), field=field)
        if self.epoch_state not in {"ACTIVE", "TERMINATED"}:
            raise SetScopeError("epoch_state must be ACTIVE or TERMINATED")
        if self.terminated_by_scope_revision is not None and (
            not isinstance(self.terminated_by_scope_revision, int)
            or isinstance(self.terminated_by_scope_revision, bool)
            or self.terminated_by_scope_revision < 0
        ):
            raise SetScopeError("terminated_by_scope_revision must be a nonnegative integer")
        for field in ("terminated_by_event_id", "terminated_at", "terminated_by_action"):
            value = getattr(self, field)
            if value is not None:
                _text(value, field=field)
        if self.terminated_by_action is not None and self.terminated_by_action not in {"OPEN", "CLOSE"}:
            raise SetScopeError("terminated_by_action must be OPEN or CLOSE")


def _text(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not value or "\x00" in value:
        raise SetScopeError(f"{field} is required")
    return value

"""Bounded sanitized system history export for operator analysis."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import UTC, datetime
import re
from typing import Any


EXPORT_LIMITS = {
    "open_positions": 25,
    "closed_positions": 25,
    "operator_actions": 30,
    "activity": 30,
    "rules_history": 12,
    "trigger_sets": 12,
    "triggers": 20,
    "messages": 30,
    "research": 20,
    "readiness_checks": 20,
    "heartbeats": 20,
    "runtime_recovery": 20,
}

_SECRET_RE = re.compile(
    r"(api[_-]?key|api[_-]?secret|authorization|bearer|cookie|csrf|session|token|password|credential|\.env)",
    re.I,
)


class SystemHistoryExporter:
    def __init__(self, *, read_model, operator_store=None, message_store=None) -> None:
        self.read_model = read_model
        self.operator_store = operator_store
        self.message_store = message_store

    def build_export(self, *, generated_at: str | None = None) -> str:
        generated_at = generated_at or datetime.now(UTC).isoformat()
        sections: list[str] = []
        sections.append(_section("SYSTEM", self._system_lines(generated_at)))
        sections.append(_section("PORTFOLIO", self._portfolio_lines()))
        sections.append(_section("EXECUTION", self._execution_lines()))
        sections.append(_section("SETS / TRIGGERS", self._sets_and_triggers_lines()))
        sections.append(_section("RULES", self._rules_lines()))
        sections.append(_section("INSTRUMENTS", self._instrument_lines()))
        sections.append(_section("RESEARCH", self._research_lines()))
        sections.append(_section("RISK / DECISIONS", self._risk_lines()))
        sections.append(_section("ERRORS", self._error_lines()))
        return "TriggerTrade system history export\n\n" + "\n\n".join(sections).strip() + "\n"

    def _system_lines(self, generated_at: str) -> list[str]:
        state = _call(self.read_model, "get_latest_runtime_state")
        operator = _call(self.read_model, "get_operator_trading_state")
        readiness = _call(self.read_model, "get_demo_readiness")
        active_pair = _call(self.read_model, "get_active_trading_pair_payload")
        heartbeats = _call(self.read_model, "list_runtime_heartbeats") or ()
        recovery = _call(self.read_model, "list_runtime_recovery_events", limit=EXPORT_LIMITS["runtime_recovery"]) or ()
        lines = [
            f"generated_at: {_safe(generated_at)}",
            f"runtime_state: {_one_line(state)}",
            f"operator_state: {_one_line(operator)}",
            f"active_pair: {_one_line(active_pair)}",
            f"demo_readiness: status={_safe(getattr(readiness, 'status', None))}",
        ]
        lines.extend(_row_lines("readiness_check", getattr(readiness, "checks", ()) or (), EXPORT_LIMITS["readiness_checks"]))
        lines.extend(_row_lines("runtime_heartbeat", heartbeats, EXPORT_LIMITS["heartbeats"]))
        lines.extend(_row_lines("runtime_recovery", recovery, EXPORT_LIMITS["runtime_recovery"]))
        return lines

    def _portfolio_lines(self) -> list[str]:
        snapshot = _call(self.read_model, "get_portfolio_snapshot")
        open_rows = _call(self.read_model, "list_portfolio_open_positions", limit=EXPORT_LIMITS["open_positions"]) or ()
        closed_rows = _call(self.read_model, "list_portfolio_closed_positions", limit=EXPORT_LIMITS["closed_positions"]) or ()
        lines = [f"snapshot: {_one_line(snapshot)}"]
        lines.extend(_row_lines("open_position", open_rows, EXPORT_LIMITS["open_positions"]))
        lines.extend(_row_lines("closed_position", closed_rows, EXPORT_LIMITS["closed_positions"]))
        return lines

    def _execution_lines(self) -> list[str]:
        activity = _call(self.read_model, "list_recent_activity", limit=EXPORT_LIMITS["activity"]) or ()
        actions = () if self.operator_store is None else self.operator_store.operator_action_rows(limit=EXPORT_LIMITS["operator_actions"] + 1)
        lines: list[str] = []
        lines.extend(_row_lines("activity", activity, EXPORT_LIMITS["activity"]))
        lines.extend(_row_lines("operator_action", actions, EXPORT_LIMITS["operator_actions"]))
        if not lines:
            lines.append("none_available: true")
        return lines

    def _sets_and_triggers_lines(self) -> list[str]:
        sets = _call(self.read_model, "list_set_summaries", limit=EXPORT_LIMITS["trigger_sets"] + 1) or ()
        triggers = _call(self.read_model, "list_trigger_catalog", limit=EXPORT_LIMITS["triggers"] + 1) or ()
        lines: list[str] = []
        lines.extend(_row_lines("trigger_set", sets, EXPORT_LIMITS["trigger_sets"]))
        lines.extend(_row_lines("trigger", triggers, EXPORT_LIMITS["triggers"]))
        return lines or ["none_available: true"]

    def _rules_lines(self) -> list[str]:
        current = _call(self.read_model, "get_current_rules_version_payload")
        history = _call(self.read_model, "list_rules_version_payloads", limit=EXPORT_LIMITS["rules_history"] + 1) or ()
        current_id = current.get("rules_version_id") if isinstance(current, dict) else None
        lines = [f"current_rules_version_id: {_safe(current_id or 'unavailable')}", f"current: {_one_line(current)}"]
        lines.extend(_row_lines("rules_version", history[: EXPORT_LIMITS["rules_history"]], EXPORT_LIMITS["rules_history"]))
        return lines

    def _instrument_lines(self) -> list[str]:
        catalog = _call(self.read_model, "get_rules_catalog_state")
        return [f"catalog: {_one_line(catalog)}"]

    def _research_lines(self) -> list[str]:
        research = _call(self.read_model, "list_research_summaries", limit=EXPORT_LIMITS["research"] + 1) or ()
        lines = _row_lines("research", research, EXPORT_LIMITS["research"])
        return lines or ["none_available: true"]

    def _risk_lines(self) -> list[str]:
        latest = _call(self.read_model, "get_latest_decision")
        daily_loss = _call(self.read_model, "get_daily_loss_state")
        return [f"latest_decision: {_one_line(latest)}", f"daily_loss: {_one_line(daily_loss)}"]

    def _error_lines(self) -> list[str]:
        lines: list[str] = []
        actions = () if self.operator_store is None else self.operator_store.operator_action_rows(limit=EXPORT_LIMITS["operator_actions"] + 1)
        failed_actions = [row for row in actions if str(getattr(row, "result", "")).upper() not in {"SUCCESS", "OK"}]
        lines.extend(_row_lines("operator_error", failed_actions[: EXPORT_LIMITS["operator_actions"]], EXPORT_LIMITS["operator_actions"]))
        messages = () if self.message_store is None else self.message_store.list_messages(limit=EXPORT_LIMITS["messages"])
        error_messages = [row for row in messages if str(getattr(row, "severity", "")).upper() in {"WARNING", "ERROR"}]
        lines.extend(_row_lines("message", error_messages[: EXPORT_LIMITS["messages"]], EXPORT_LIMITS["messages"]))
        return lines or ["none_available: true"]


def _section(title: str, lines: list[str]) -> str:
    return title + "\n" + "\n".join(lines)


def _row_lines(label: str, rows: Any, limit: int) -> list[str]:
    values = tuple(rows or ())
    visible = values[:limit]
    lines = [f"{label}: {_one_line(row)}" for row in visible]
    if len(values) >= limit:
        lines.append(f"{label}_truncated: true; showing latest {limit}")
    return lines


def _call(target: Any, name: str, **kwargs: Any) -> Any:
    method = getattr(target, name, None)
    if method is None:
        return None
    try:
        return method(**kwargs)
    except TypeError:
        return method()
    except Exception as exc:  # noqa: BLE001 - export should report unavailable data, not crash the dashboard.
        return {"unavailable": name, "error": _safe(str(exc))}


def _one_line(value: Any) -> str:
    return _safe(_compact(value))


def _compact(value: Any) -> str:
    if value is None:
        return "unavailable"
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, dict):
        parts = []
        for key, item in value.items():
            if key in {"input_snapshot", "metadata", "raw", "payload", "headers"}:
                continue
            parts.append(f"{key}={_compact(item)}")
        return "{" + ", ".join(parts) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_compact(item) for item in value[:6]) + (", ..." if len(value) > 6 else "") + "]"
    return str(value)


def _safe(value: str) -> str:
    text = " ".join(str(value).replace("\x00", "").split())
    if _SECRET_RE.search(text):
        return "[redacted]"
    return text[:1200]

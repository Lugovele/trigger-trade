"""PostgreSQL persistence for immutable Research Set definitions."""

from __future__ import annotations

from dataclasses import dataclass
import json
import re
from typing import Any, Iterable, Mapping

from triggertrade.canonical_json import canonical_json_digest, canonical_json_text
from triggertrade.persistence.postgres import PostgresPersistenceError
from triggertrade.persistence.postgres_trigger_registry import PostgresTriggerRegistry
from triggertrade.trigger_sets import RegistrySyncReport


RESEARCH_SET_REGISTRY_SCHEMA_VERSION = "research-set-composition@1"
_SET_ID_RE = re.compile(r"^SET-R(?:-BTC)?-\d{3}$")
_SET_VERSION_RE = re.compile(r"^SET-R(?:-BTC)?-\d{3}-V\d+$")
_BACKEND_VERSION_RE = re.compile(r"^v\d+$")


class PostgresResearchSetRegistryError(PostgresPersistenceError):
    """Raised when PostgreSQL Research Set persistence cannot safely proceed."""


@dataclass(frozen=True)
class ResearchSetTriggerMember:
    position: int
    trigger_id: str
    trigger_version: str
    role: str
    direction_applicability: str | None
    condition: str | None
    operator: str | None
    threshold: str | None
    threshold_unit: str | None
    metric_references: tuple[str, ...]
    formula_references: tuple[str, ...]
    output_states: tuple[str, ...]
    required: bool


@dataclass(frozen=True)
class ResearchSetVersion:
    set_id: str
    set_version: str
    backend_set_id: str
    backend_version: str
    display_name: str
    status: str
    source_hypothesis_ids: tuple[str, ...]
    source_candidate_ids: tuple[str, ...]
    source_position_ids: tuple[str, ...]
    source_portfolio_ids: tuple[str, ...]
    coin_applicability: tuple[str, ...]
    excluded_coins: tuple[str, ...]
    segment_applicability: str
    timeframe: str
    profile_applicability: tuple[str, ...]
    trigger_members: tuple[ResearchSetTriggerMember, ...]
    trigger_composition_logic: str
    direction_semantics: str
    edge_behavior: Mapping[str, Any]
    provenance: Mapping[str, Any]
    source_yaml_excerpt: str
    backend_mapping: Mapping[str, Any]
    created_at: str
    semantic_hash: str | None = None


class PostgresResearchSetRegistry:
    """Immutable Research Set registry backed by PostgreSQL.

    Research Sets are trigger-composition artifacts. They deliberately do not
    require strategy/risk bindings used by operational TriggerSetVersion.
    """

    def __init__(self, connection) -> None:
        self._connection = connection
        self._trigger_registry = PostgresTriggerRegistry(connection)

    def save_research_set(self, research_set: ResearchSetVersion) -> ResearchSetVersion:
        self._save_result(research_set)
        return research_set

    def register_research_sets(self, research_sets: Iterable[ResearchSetVersion]) -> RegistrySyncReport:
        return self.sync_research_sets(research_sets)

    def sync_research_sets(self, research_sets: Iterable[ResearchSetVersion]) -> RegistrySyncReport:
        unchanged: list[str] = []
        registered: list[str] = []
        conflicts: list[str] = []
        invalid: list[str] = []
        for research_set in research_sets:
            try:
                result = self._save_result(research_set)
            except PostgresResearchSetRegistryError as exc:
                message = f"{research_set.set_id}@{research_set.set_version}: {exc}"
                if _is_invalid_error(str(exc)):
                    invalid.append(message)
                else:
                    conflicts.append(message)
            else:
                (unchanged if result == "unchanged" else registered).append(
                    f"{research_set.set_id}@{research_set.set_version}"
                )
        return RegistrySyncReport(tuple(unchanged), tuple(registered), tuple(conflicts), tuple(invalid), ())

    def get_research_set(self, set_id: str, set_version: str) -> ResearchSetVersion | None:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT payload_json::text
                FROM triggertrade_research_set_versions
                WHERE set_id = %s AND set_version = %s
                """,
                (set_id, set_version),
            )
            row = cursor.fetchone()
        return None if row is None else research_set_from_payload(json.loads(str(row[0])))

    def list_research_sets(self) -> tuple[ResearchSetVersion, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT payload_json::text
                FROM triggertrade_research_set_versions
                ORDER BY set_id, set_version
                """
            )
            rows = cursor.fetchall()
        return tuple(research_set_from_payload(json.loads(str(row[0]))) for row in rows)

    def list_versions(self, set_id: str) -> tuple[ResearchSetVersion, ...]:
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT payload_json::text
                FROM triggertrade_research_set_versions
                WHERE set_id = %s
                ORDER BY set_version
                """,
                (set_id,),
            )
            rows = cursor.fetchall()
        return tuple(research_set_from_payload(json.loads(str(row[0]))) for row in rows)

    def _save_result(self, research_set: ResearchSetVersion) -> str:
        _validate_research_set(research_set)
        payload = json.loads(canonical_json_text(research_set_payload(research_set)))
        digest = research_set_digest(research_set)
        if research_set.semantic_hash is not None and research_set.semantic_hash != digest:
            raise PostgresResearchSetRegistryError("semantic_hash does not match canonical Research Set definition")
        self._validate_trigger_references(research_set)
        payload_text = canonical_json_text(payload)
        with self._connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT payload_json::text, payload_digest
                FROM triggertrade_research_set_versions
                WHERE set_id = %s AND set_version = %s
                """,
                (research_set.set_id, research_set.set_version),
            )
            existing = cursor.fetchone()
            if existing is not None:
                existing_payload = json.loads(str(existing[0]))
                if str(existing[1]) != digest or existing_payload != payload:
                    raise PostgresResearchSetRegistryError(
                        "semantic Research Set definition changed without Set Version bump"
                    )
                return "unchanged"
            cursor.execute(
                """
                INSERT INTO triggertrade_research_set_versions (
                    set_id, set_version, display_name, status, payload_json,
                    payload_digest, schema_version, created_at, provenance
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s)
                """,
                (
                    research_set.set_id,
                    research_set.set_version,
                    research_set.display_name,
                    research_set.status,
                    payload_text,
                    digest,
                    RESEARCH_SET_REGISTRY_SCHEMA_VERSION,
                    research_set.created_at,
                    research_set.provenance.get("primary_source", "unknown"),
                ),
            )
            for member in research_set.trigger_members:
                member_payload = research_set_member_payload(member)
                cursor.execute(
                    """
                    INSERT INTO triggertrade_research_set_memberships (
                        set_id, set_version, position, trigger_id, trigger_version,
                        role, direction_applicability, required, payload_json, payload_digest
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s)
                    """,
                    (
                        research_set.set_id,
                        research_set.set_version,
                        member.position,
                        member.trigger_id,
                        member.trigger_version,
                        member.role,
                        member.direction_applicability,
                        member.required,
                        canonical_json_text(member_payload),
                        canonical_json_digest(member_payload),
                    ),
                )
        return "registered"

    def _validate_trigger_references(self, research_set: ResearchSetVersion) -> None:
        for member in research_set.trigger_members:
            if self._trigger_registry.get_trigger_version(member.trigger_id, member.trigger_version) is None:
                raise PostgresResearchSetRegistryError(
                    f"unknown trigger version: {member.trigger_id}@{member.trigger_version}"
                )


def research_set_from_package_record(record: Mapping[str, Any]) -> ResearchSetVersion:
    return research_set_from_payload(record)


def research_set_from_payload(payload: Mapping[str, Any]) -> ResearchSetVersion:
    members = tuple(research_set_member_from_payload(item) for item in payload.get("trigger_members", ()))
    return ResearchSetVersion(
        set_id=_required_text(payload.get("set_id"), "set_id"),
        set_version=_required_text(payload.get("set_version"), "set_version"),
        backend_set_id=_required_text(payload.get("backend_set_id"), "backend_set_id"),
        backend_version=_required_text(payload.get("backend_version"), "backend_version"),
        display_name=_required_text(payload.get("display_name"), "display_name"),
        status=_required_text(payload.get("status"), "status"),
        source_hypothesis_ids=_string_tuple(payload.get("source_hypothesis_ids")),
        source_candidate_ids=_string_tuple(payload.get("source_candidate_ids")),
        source_position_ids=_string_tuple(payload.get("source_position_ids")),
        source_portfolio_ids=_string_tuple(payload.get("source_portfolio_ids")),
        coin_applicability=_string_tuple(payload.get("coin_applicability")),
        excluded_coins=_string_tuple(payload.get("excluded_coins")),
        segment_applicability=_required_text(payload.get("segment_applicability"), "segment_applicability"),
        timeframe=_required_text(payload.get("timeframe"), "timeframe"),
        profile_applicability=_string_tuple(payload.get("profile_applicability")),
        trigger_members=members,
        trigger_composition_logic=_required_text(payload.get("trigger_composition_logic"), "trigger_composition_logic"),
        direction_semantics=_required_text(payload.get("direction_semantics"), "direction_semantics"),
        edge_behavior=dict(payload.get("edge_behavior") or {}),
        provenance=dict(payload.get("provenance") or {}),
        source_yaml_excerpt=str(payload.get("source_yaml_excerpt") or ""),
        backend_mapping=dict(payload.get("backend_mapping") or {}),
        created_at=str(payload.get("created_at") or payload.get("package_revision") or "RESEARCH_V1_FOCUSED_CORRECTION_R3"),
        semantic_hash=None if payload.get("semantic_hash") is None else str(payload.get("semantic_hash")),
    )


def research_set_member_from_payload(payload: Mapping[str, Any]) -> ResearchSetTriggerMember:
    return ResearchSetTriggerMember(
        position=int(payload.get("position") or 0),
        trigger_id=_required_text(payload.get("trigger_id"), "trigger_id"),
        trigger_version=_required_text(payload.get("trigger_version"), "trigger_version"),
        role=_required_text(payload.get("role"), "role"),
        direction_applicability=None
        if payload.get("direction_applicability") is None
        else str(payload.get("direction_applicability")),
        condition=None if payload.get("condition") is None else str(payload.get("condition")),
        operator=None if payload.get("operator") is None else str(payload.get("operator")),
        threshold=None if payload.get("threshold") is None else str(payload.get("threshold")),
        threshold_unit=None if payload.get("threshold_unit") is None else str(payload.get("threshold_unit")),
        metric_references=_string_tuple(payload.get("metric_references")),
        formula_references=_string_tuple(payload.get("formula_references")),
        output_states=_string_tuple(payload.get("output_states")),
        required=bool(payload.get("required")),
    )


def research_set_digest(research_set: ResearchSetVersion) -> str:
    return canonical_json_digest(research_set_payload(research_set))


def research_set_payload(research_set: ResearchSetVersion) -> dict[str, Any]:
    payload = {
        "set_version_id": research_set.set_version,
        "set_id": research_set.set_id,
        "set_version": research_set.set_version,
        "backend_set_id": research_set.backend_set_id,
        "backend_version": research_set.backend_version,
        "display_name": research_set.display_name,
        "status": research_set.status,
        "source_hypothesis_ids": tuple(research_set.source_hypothesis_ids),
        "source_candidate_ids": tuple(research_set.source_candidate_ids),
        "source_position_ids": tuple(research_set.source_position_ids),
        "source_portfolio_ids": tuple(research_set.source_portfolio_ids),
        "coin_applicability": tuple(research_set.coin_applicability),
        "excluded_coins": tuple(research_set.excluded_coins),
        "segment_applicability": research_set.segment_applicability,
        "timeframe": research_set.timeframe,
        "profile_applicability": tuple(research_set.profile_applicability),
        "trigger_members": tuple(research_set_member_payload(member) for member in research_set.trigger_members),
        "trigger_composition_logic": research_set.trigger_composition_logic,
        "direction_semantics": research_set.direction_semantics,
        "edge_behavior": dict(research_set.edge_behavior),
        "provenance": dict(research_set.provenance),
        "source_yaml_excerpt": research_set.source_yaml_excerpt,
        "backend_mapping": dict(research_set.backend_mapping),
        "created_at": research_set.created_at,
    }
    return payload


def research_set_member_payload(member: ResearchSetTriggerMember) -> dict[str, Any]:
    return {
        "position": member.position,
        "trigger_id": member.trigger_id,
        "trigger_version": member.trigger_version,
        "role": member.role,
        "direction_applicability": member.direction_applicability,
        "condition": member.condition,
        "operator": member.operator,
        "threshold": member.threshold,
        "threshold_unit": member.threshold_unit,
        "metric_references": tuple(member.metric_references),
        "formula_references": tuple(member.formula_references),
        "output_states": tuple(member.output_states),
        "required": member.required,
    }


def _validate_research_set(research_set: ResearchSetVersion) -> None:
    if _SET_ID_RE.fullmatch(research_set.set_id) is None:
        raise PostgresResearchSetRegistryError("invalid Research Set ID")
    if _SET_VERSION_RE.fullmatch(research_set.set_version) is None:
        raise PostgresResearchSetRegistryError("invalid Research Set version")
    if not research_set.set_version.startswith(f"{research_set.set_id}-"):
        raise PostgresResearchSetRegistryError("Research Set version does not match set_id")
    if research_set.backend_set_id != research_set.set_id:
        raise PostgresResearchSetRegistryError("backend_set_id must preserve Research set_id")
    if _BACKEND_VERSION_RE.fullmatch(research_set.backend_version) is None:
        raise PostgresResearchSetRegistryError("backend_version must use vN naming")
    if not research_set.display_name:
        raise PostgresResearchSetRegistryError("display_name is required")
    if not research_set.status:
        raise PostgresResearchSetRegistryError("status is required")
    if not research_set.trigger_members:
        raise PostgresResearchSetRegistryError("Research Set requires at least one trigger member")
    positions = [member.position for member in research_set.trigger_members]
    if positions != list(range(1, len(research_set.trigger_members) + 1)):
        raise PostgresResearchSetRegistryError("trigger member positions must be contiguous and one-based")
    refs = [(member.trigger_id, member.trigger_version) for member in research_set.trigger_members]
    if len(set(refs)) != len(refs):
        raise PostgresResearchSetRegistryError("duplicate trigger membership is not supported")
    for member in research_set.trigger_members:
        _validate_member(member)
    if "AND" not in research_set.trigger_composition_logic and "OR" not in research_set.trigger_composition_logic:
        raise PostgresResearchSetRegistryError("unsupported composition logic")
    if not research_set.direction_semantics:
        raise PostgresResearchSetRegistryError("direction semantics are required")


def _validate_member(member: ResearchSetTriggerMember) -> None:
    if member.position < 1:
        raise PostgresResearchSetRegistryError("trigger member position must be positive")
    if not member.trigger_id or not member.trigger_version:
        raise PostgresResearchSetRegistryError("trigger member requires exact trigger ID and version")
    if not member.role:
        raise PostgresResearchSetRegistryError("trigger member role is required")


def _required_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise PostgresResearchSetRegistryError(f"{field} is required")
    return value


def _string_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise PostgresResearchSetRegistryError("expected a string list")
    return tuple(str(item) for item in value)


def _is_invalid_error(message: str) -> bool:
    invalid_terms = ("invalid", "required", "unsupported", "unknown trigger version", "duplicate")
    return any(term in message for term in invalid_terms)

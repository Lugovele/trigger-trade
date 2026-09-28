from __future__ import annotations

from dataclasses import replace
from http import HTTPStatus
import threading
import json
import os
from pathlib import Path
import uuid
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from triggertrade.dashboard.__main__ import create_server
from triggertrade.persistence import (
    PostgresConnectionFactory,
    PostgresResearchSetRegistry,
    PostgresResearchSetRegistryError,
    PostgresSettings,
    PostgresTriggerRegistry,
    PostgresUnitOfWork,
    ResearchSetVersion,
    apply_postgres_migrations,
    definition_hash,
    research_set_digest,
    research_set_from_package_record,
    research_set_payload,
)
from triggertrade.trigger_sets import RuleDefinition, RuleStatus, RuleType
from triggertrade.triggers import implementation_exists, implementation_key
from triggertrade.triggers.declarative_metric_predicate import DeclarativeMetricPredicateConfig


pytest.importorskip("psycopg")


def _settings() -> PostgresSettings:
    dsn = os.environ.get("TRIGGERTRADE_POSTGRES_DSN")
    if not dsn:
        pytest.skip("TRIGGERTRADE_POSTGRES_DSN is not configured")
    return PostgresSettings(dsn=dsn, schema=f"tt_research_sets_{uuid.uuid4().hex[:16]}")


def _drop_schema(settings: PostgresSettings) -> None:
    import psycopg

    with psycopg.connect(settings.dsn, autocommit=True) as conn:
        with conn.cursor() as cursor:
            cursor.execute(f'DROP SCHEMA IF EXISTS "{settings.schema}" CASCADE')


def _migrate(settings: PostgresSettings) -> PostgresConnectionFactory:
    applied = apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema)
    assert applied[-1].version == "0024"
    assert apply_postgres_migrations(dsn=settings.dsn, schema=settings.schema) == ()
    return PostgresConnectionFactory(dsn=settings.dsn, schema=settings.schema)


def test_research_v1_set_package_imports_idempotently_and_round_trips_exactly():
    settings = _settings()
    try:
        factory = _migrate(settings)
        trigger_rules = _research_v1_rules()
        research_sets = _research_v1_sets()
        assert len(trigger_rules) == 31
        assert len(research_sets) == 33
        assert sum(len(record.trigger_members) for record in research_sets) == 242
        assert {record.status for record in research_sets} == {"RESEARCH_ONLY"}

        with PostgresUnitOfWork(factory) as uow:
            trigger_report = PostgresTriggerRegistry(uow.connection).sync_trigger_registry(trigger_rules)
            assert len(trigger_report.new_versions_registered) == 31
            assert trigger_report.conflicts == ()
            assert trigger_report.invalid_definitions == ()

        with PostgresUnitOfWork(factory) as uow:
            store = PostgresResearchSetRegistry(uow.connection)
            first = store.sync_research_sets(research_sets)
            assert len(first.new_versions_registered) == 33
            assert first.unchanged_versions == ()
            assert first.conflicts == ()
            assert first.invalid_definitions == ()

        with PostgresUnitOfWork(factory) as uow:
            store = PostgresResearchSetRegistry(uow.connection)
            second = store.sync_research_sets(research_sets)
            assert len(second.unchanged_versions) == 33
            assert second.new_versions_registered == ()
            assert second.conflicts == ()
            assert second.invalid_definitions == ()

            persisted = store.list_research_sets()
            assert len(persisted) == 33
            persisted_by_key = {(record.set_id, record.set_version): record for record in persisted}
            for expected in research_sets:
                actual = persisted_by_key[(expected.set_id, expected.set_version)]
                assert research_set_payload(actual) == research_set_payload(expected)
                assert research_set_digest(actual) == research_set_digest(expected)
                assert actual.status == expected.status

            with uow.connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM triggertrade_research_set_memberships")
                assert cursor.fetchone()[0] == 242
    finally:
        _drop_schema(settings)


def test_research_set_registry_rejects_unresolved_trigger_references():
    settings = _settings()
    try:
        factory = _migrate(settings)
        research_set = _research_v1_sets()[0]
        missing_ref = replace(
            research_set,
            semantic_hash=None,
            trigger_members=(
                replace(research_set.trigger_members[0], trigger_version="9.9.9"),
                *research_set.trigger_members[1:],
            ),
        )

        with PostgresUnitOfWork(factory) as uow:
            PostgresTriggerRegistry(uow.connection).sync_trigger_registry(_research_v1_rules())
            store = PostgresResearchSetRegistry(uow.connection)
            report = store.sync_research_sets((missing_ref,))
            assert report.new_versions_registered == ()
            assert report.conflicts == ()
            assert len(report.invalid_definitions) == 1
            assert "unknown trigger version" in report.invalid_definitions[0]
    finally:
        _drop_schema(settings)


def test_research_set_registry_rejects_duplicate_trigger_membership():
    settings = _settings()
    try:
        factory = _migrate(settings)
        research_set = _research_v1_sets()[0]
        duplicate = replace(
            research_set,
            semantic_hash=None,
            trigger_members=(
                research_set.trigger_members[0],
                replace(research_set.trigger_members[0], position=2),
                *tuple(replace(member, position=member.position + 1) for member in research_set.trigger_members[1:]),
            ),
        )

        with PostgresUnitOfWork(factory) as uow:
            PostgresTriggerRegistry(uow.connection).sync_trigger_registry(_research_v1_rules())
            store = PostgresResearchSetRegistry(uow.connection)
            report = store.sync_research_sets((duplicate,))
            assert report.new_versions_registered == ()
            assert report.conflicts == ()
            assert len(report.invalid_definitions) == 1
            assert "duplicate trigger membership" in report.invalid_definitions[0]
    finally:
        _drop_schema(settings)


def test_research_set_registry_rejects_immutable_conflicts():
    settings = _settings()
    try:
        factory = _migrate(settings)
        research_set = _research_v1_sets()[0]
        current_refs = {(member.trigger_id, member.trigger_version) for member in research_set.trigger_members}
        replacement_ref = next(
            (rule.rule_id, rule.version)
            for rule in _research_v1_rules()
            if (rule.rule_id, rule.version) not in current_refs
        )
        variants = (
            replace(research_set, semantic_hash=None, trigger_members=research_set.trigger_members[:-1]),
            replace(
                research_set,
                semantic_hash=None,
                trigger_members=(
                    replace(
                        research_set.trigger_members[0],
                        trigger_id=replacement_ref[0],
                        trigger_version=replacement_ref[1],
                    ),
                    *research_set.trigger_members[1:],
                ),
            ),
            replace(
                research_set,
                semantic_hash=None,
                trigger_members=(
                    replace(research_set.trigger_members[0], role="CONTEXT_ONLY"),
                    *research_set.trigger_members[1:],
                ),
            ),
            replace(
                research_set,
                semantic_hash=None,
                trigger_composition_logic="OR".join(research_set.trigger_composition_logic.split("AND")),
            ),
            replace(research_set, semantic_hash=None, status="SUPERSEDED"),
            replace(research_set, semantic_hash=None, coin_applicability=("ETH",)),
            replace(research_set, semantic_hash=None, direction_semantics="changed direction semantics"),
        )

        with PostgresUnitOfWork(factory) as uow:
            PostgresTriggerRegistry(uow.connection).sync_trigger_registry(_research_v1_rules())
            store = PostgresResearchSetRegistry(uow.connection)
            store.save_research_set(research_set)
            for changed in variants:
                with pytest.raises(PostgresResearchSetRegistryError, match="changed without Set Version bump"):
                    store.save_research_set(changed)
    finally:
        _drop_schema(settings)


def test_research_set_registry_does_not_require_rules_bindings():
    record = _research_v1_sets()[0]
    assert not hasattr(record, "strategy_version")
    assert not hasattr(record, "risk_profile_version")
    assert record.backend_mapping.get("requires_strategy_version") is False
    assert record.backend_mapping.get("requires_risk_profile_version") is False


def test_dashboard_reads_research_sets_from_postgres_registry():
    settings = _settings()
    try:
        factory = _migrate(settings)
        with PostgresUnitOfWork(factory) as uow:
            PostgresTriggerRegistry(uow.connection).sync_trigger_registry(_research_v1_rules())
            PostgresResearchSetRegistry(uow.connection).sync_research_sets(_research_v1_sets())

        db_path = Path(".tt-tmp") / f"research-set-web-{uuid.uuid4().hex}" / "dashboard.sqlite3"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        server = create_server(
            port=0,
            db_path=db_path,
            trigger_registry=_TriggerRegistryClient(factory),
            research_set_registry=_ResearchSetRegistryClient(factory),
        )
        host, port = server.server_address
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            sets_payload = _json_request(host, port, "GET", "/api/research/sets")
            detail = _json_request(host, port, "GET", "/api/research/sets/SET-R-BTC-001/SET-R-BTC-001-V1")
            mutation = _json_request(
                host,
                port,
                "POST",
                "/api/research/sets",
                data=b"{}",
                expected=HTTPStatus.FORBIDDEN,
            )
        finally:
            server.shutdown()
            server.server_close()
            thread.join(timeout=2)

        affected = {
            "SET-R-BTC-001-V1",
            "SET-R-BTC-001-V2",
            "SET-R-BTC-003-V2",
            "SET-R-BTC-007-V2",
            "SET-R-BTC-008-V2",
            "SET-R-BTC-009-V2",
            "SET-R-BTC-011-V2",
            "SET-R-BTC-012-V2",
            "SET-R-BTC-015-V2",
            "SET-R-BTC-016-V2",
            "SET-R-BTC-019-V1",
            "SET-R-BTC-019-V2",
            "SET-R-BTC-020-V1",
            "SET-R-BTC-020-V2",
            "SET-R-BTC-021-V1",
            "SET-R-BTC-021-V2",
        }
        btc_trigger_ids = {"TR-R-BTC-001", "TR-R-BTC-002", "TR-R-BTC-003", "TR-R-BTC-004"}

        assert sets_payload["count"] == 33
        assert len(sets_payload["sets"]) == 33
        btc_sets = [row for row in sets_payload["sets"] if row["version"] in affected]
        assert len(btc_sets) == 16
        assert sum(
            1
            for row in btc_sets
            for member in row["trigger_members"]
            if member["trigger_id"] in btc_trigger_ids and member["version"] == "1.0.1"
        ) == 34
        assert not [
            member
            for row in btc_sets
            for member in row["trigger_members"]
            if member["trigger_id"] in btc_trigger_ids and member["version"] == "1.0.0"
        ]
        assert detail["set"]["trigger_members"][0]["position"] == 1
        assert detail["set"]["trigger_members"][0]["trigger_id"].startswith("TR-R-")
        assert mutation["error"] == "operator token required"
    finally:
        _drop_schema(settings)


def _research_v1_sets() -> tuple[ResearchSetVersion, ...]:
    package = json.loads(Path("docs/research-import/sets/RESEARCH_V1_SETS.json").read_text(encoding="utf-8"))
    return tuple(research_set_from_package_record(record) for record in package["sets"])


def _research_v1_rules() -> tuple[RuleDefinition, ...]:
    package = json.loads(Path("docs/research-import/triggers/RESEARCH_V1_TRIGGERS_WEB_IMPORT.json").read_text(encoding="utf-8"))
    rules: list[RuleDefinition] = []
    for record in package["records"]:
        data = dict(record["rule_definition"])
        data.pop("semantic_hash", None)
        data["status"] = RuleStatus(data["status"])
        data["rule_type"] = RuleType(data["rule_type"])
        rule = RuleDefinition(**data)
        assert implementation_exists(implementation_key(rule))
        DeclarativeMetricPredicateConfig.from_rule(rule)
        assert definition_hash(rule)
        rules.append(rule)
    return tuple(rules)


def _json_request(host, port, method: str, path: str, *, data: bytes | None = None, expected=HTTPStatus.OK):
    request = Request(f"http://{host}:{port}{path}", method=method, data=data)
    if data is not None:
        request.add_header("Content-Type", "application/json")
    try:
        with urlopen(request, timeout=30) as response:
            body = response.read().decode("utf-8")
            assert response.status == expected
            return json.loads(body) if body.startswith("{") else body
    except HTTPError as exc:
        body = exc.read().decode("utf-8")
        assert exc.code == expected
        return json.loads(body) if body.startswith("{") else body


class _TriggerRegistryClient:
    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def list_trigger_versions(self):
        with self._factory.connect() as connection:
            return PostgresTriggerRegistry(connection).list_trigger_versions()

    def get_rule(self, rule_id: str, version: str | None = None):
        with self._factory.connect() as connection:
            return PostgresTriggerRegistry(connection).get_rule(rule_id, version)


class _ResearchSetRegistryClient:
    def __init__(self, factory: PostgresConnectionFactory) -> None:
        self._factory = factory

    def list_research_sets(self):
        with self._factory.connect() as connection:
            return PostgresResearchSetRegistry(connection).list_research_sets()

    def get_research_set(self, set_id: str, version: str):
        with self._factory.connect() as connection:
            return PostgresResearchSetRegistry(connection).get_research_set(set_id, version)

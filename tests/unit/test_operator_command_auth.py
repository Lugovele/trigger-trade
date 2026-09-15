from __future__ import annotations

import pytest

from triggertrade.persistence import TraceStore
from triggertrade.services.operator_auth import (
    LOCAL_DEV_AUTH_SOURCE,
    MANAGED_OIDC_AUTH_SOURCE,
    OPERATOR_AUTH_EVENT_TYPE,
    OperatorAuthorizationError,
    OperatorCommandAuthorizer,
    operator_authorizer_from_env,
)


def test_managed_oidc_operator_command_is_durably_authorized_without_token(tmp_path):
    db = tmp_path / "auth.sqlite3"
    authorizer = OperatorCommandAuthorizer(db, auth_mode="managed_oidc")

    command = authorizer.authorize_http_command(
        "PAUSE_ENTRIES",
        headers={"X-MS-CLIENT-PRINCIPAL-ID": "operator-1", "X-MS-CLIENT-PRINCIPAL-ROLES": "TriggerTrade.Operator"},
        payload={},
        local_dev_token="process-secret-token",
        target="ACTIVE",
        authorized_at="2026-09-15T00:00:00+00:00",
    )

    assert command.principal.principal_id == "operator-1"
    assert command.principal.auth_source == MANAGED_OIDC_AUTH_SOURCE

    reopened = TraceStore(db)
    events = reopened.list_audit_events(event_type=OPERATOR_AUTH_EVENT_TYPE)
    assert len(events) == 1
    assert events[0].source_id == "operator-1"
    assert events[0].safe_metadata["authz_source"] == MANAGED_OIDC_AUTH_SOURCE
    assert events[0].safe_metadata["canonical_deployed_auth"] is True
    assert "process-secret-token" not in str(events[0].safe_metadata)


def test_managed_oidc_requires_app_level_authorization(tmp_path):
    authorizer = OperatorCommandAuthorizer(tmp_path / "auth.sqlite3", auth_mode="managed_oidc")

    with pytest.raises(OperatorAuthorizationError, match="not authorized"):
        authorizer.authorize_http_command(
            "PAUSE_ENTRIES",
            headers={"X-MS-CLIENT-PRINCIPAL-ID": "viewer-1", "X-MS-CLIENT-PRINCIPAL-ROLES": "Reader"},
            payload={},
            local_dev_token="process-secret-token",
        )


def test_local_dev_token_is_compatibility_only_and_audited_without_secret(tmp_path):
    authorizer = OperatorCommandAuthorizer(tmp_path / "auth.sqlite3")

    command = authorizer.authorize_http_command(
        "SYSTEM_HISTORY_EXPORT",
        headers={},
        payload={"token": "process-secret-token"},
        local_dev_token="process-secret-token",
        target="SYSTEM_HISTORY",
        authorized_at="2026-09-15T00:01:00+00:00",
    )

    assert command.principal.principal_id == "local_dashboard_operator"
    assert command.principal.auth_source == LOCAL_DEV_AUTH_SOURCE
    event = TraceStore(tmp_path / "auth.sqlite3").list_audit_events(event_type=OPERATOR_AUTH_EVENT_TYPE)[0]
    assert event.safe_metadata["authz_source"] == LOCAL_DEV_AUTH_SOURCE
    assert event.safe_metadata["canonical_deployed_auth"] is False
    assert "process-secret-token" not in str(event.safe_metadata)


def test_local_dev_token_is_rejected_in_managed_auth_mode(tmp_path):
    authorizer = OperatorCommandAuthorizer(tmp_path / "auth.sqlite3", auth_mode="managed_oidc")

    with pytest.raises(OperatorAuthorizationError, match="required"):
        authorizer.authorize_http_command(
            "PAUSE_ENTRIES",
            headers={},
            payload={"token": "process-secret-token"},
            local_dev_token="process-secret-token",
        )


def test_managed_headers_cannot_bypass_local_dev_token_mode(tmp_path):
    authorizer = OperatorCommandAuthorizer(tmp_path / "auth.sqlite3")

    with pytest.raises(OperatorAuthorizationError, match="not enabled"):
        authorizer.authorize_http_command(
            "PAUSE_ENTRIES",
            headers={"X-MS-CLIENT-PRINCIPAL-ID": "operator-1", "X-MS-CLIENT-PRINCIPAL-ROLES": "TriggerTrade.Operator"},
            payload={},
            local_dev_token="process-secret-token",
        )


def test_idempotency_key_conflict_is_rejected(tmp_path):
    db = tmp_path / "auth.sqlite3"
    authorizer = OperatorCommandAuthorizer(db)
    payload = {"token": "process-secret-token"}

    authorizer.authorize_http_command(
        "PAUSE_ENTRIES",
        headers={},
        payload=payload,
        local_dev_token="process-secret-token",
        idempotency_key="operator-command-001",
    )

    with pytest.raises(OperatorAuthorizationError, match="conflict"):
        authorizer.authorize_http_command(
            "RESUME_ENTRIES",
            headers={},
            payload=payload,
            local_dev_token="process-secret-token",
            idempotency_key="operator-command-001",
        )


def test_env_authorizer_defaults_to_managed_oidc_not_local_token(tmp_path):
    authorizer = operator_authorizer_from_env(tmp_path / "auth.sqlite3", {})

    assert authorizer.auth_mode == MANAGED_OIDC_AUTH_SOURCE
    with pytest.raises(OperatorAuthorizationError, match="required"):
        authorizer.authorize_http_command(
            "PAUSE_ENTRIES",
            headers={},
            payload={"token": "process-secret-token"},
            local_dev_token="process-secret-token",
        )


def test_env_authorizer_requires_explicit_local_dev_compat_for_process_token(tmp_path):
    authorizer = operator_authorizer_from_env(
        tmp_path / "auth.sqlite3",
        {"TRIGGERTRADE_AUTH_MODE": "local_dev_compat"},
    )

    command = authorizer.authorize_http_command(
        "PAUSE_ENTRIES",
        headers={},
        payload={"token": "process-secret-token"},
        local_dev_token="process-secret-token",
    )

    assert authorizer.auth_mode == "local_dev_compat"
    assert command.principal.auth_source == LOCAL_DEV_AUTH_SOURCE

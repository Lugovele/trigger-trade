from __future__ import annotations

import base64
import json
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
from triggertrade.dashboard.__main__ import create_server


def test_managed_oidc_operator_command_is_durably_authorized_without_token(tmp_path):
    db = tmp_path / "auth.sqlite3"
    authorizer = OperatorCommandAuthorizer(db, auth_mode="managed_oidc", allowed_principals=("operator-1",))

    command = authorizer.authorize_http_command(
        "PAUSE_ENTRIES",
        headers=_managed_principal_headers("operator-1"),
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


def test_managed_oidc_uses_azure_principal_id_when_encoded_claim_id_differs(tmp_path):
    db = tmp_path / "auth.sqlite3"
    authorizer = OperatorCommandAuthorizer(db, auth_mode="managed_oidc", allowed_principals=("azure-object-id",))

    command = authorizer.authorize_http_command(
        "RESEARCH_CREATE",
        headers=_managed_principal_headers(
            "azure-object-id",
            encoded_claims=[
                {"typ": "oid", "val": "mapped-claim-object-id"},
                {"typ": "sub", "val": "mapped-subject-id"},
                {"typ": "roles", "val": "TriggerTrade.Operator"},
            ],
        ),
        payload={},
        local_dev_token="process-secret-token",
        scope="RESEARCH",
        target="RESEARCH",
        authorized_at="2026-09-15T00:00:01+00:00",
    )

    assert command.principal.principal_id == "azure-object-id"
    assert command.principal.auth_source == MANAGED_OIDC_AUTH_SOURCE
    event = TraceStore(db).list_audit_events(event_type=OPERATOR_AUTH_EVENT_TYPE)[0]
    assert event.source_id == "azure-object-id"
    assert "mapped-claim-object-id" not in str(event.safe_metadata)


def test_managed_oidc_without_principal_id_uses_unambiguous_authoritative_claim(tmp_path):
    db = tmp_path / "auth.sqlite3"
    authorizer = OperatorCommandAuthorizer(db, auth_mode="managed_oidc", allowed_principals=("claim-object-id",))

    headers = _managed_principal_headers(
        "ignored-header-id",
        encoded_claims=[
            {"typ": "oid", "val": "claim-object-id"},
            {"typ": "http://schemas.microsoft.com/identity/claims/objectidentifier", "val": "claim-object-id"},
            {"typ": "roles", "val": "TriggerTrade.Operator"},
        ],
    )
    headers.pop("X-MS-CLIENT-PRINCIPAL-ID")

    command = authorizer.authorize_http_command(
        "PAUSE_ENTRIES",
        headers=headers,
        payload={},
        local_dev_token="process-secret-token",
    )

    assert command.principal.principal_id == "claim-object-id"


def test_managed_oidc_without_principal_id_rejects_ambiguous_identity_claims(tmp_path):
    authorizer = OperatorCommandAuthorizer(
        tmp_path / "auth.sqlite3",
        auth_mode="managed_oidc",
        allowed_principals=("claim-object-id",),
    )
    headers = _managed_principal_headers(
        "ignored-header-id",
        encoded_claims=[
            {"typ": "oid", "val": "claim-object-id"},
            {"typ": "sub", "val": "different-subject-id"},
        ],
    )
    headers.pop("X-MS-CLIENT-PRINCIPAL-ID")

    with pytest.raises(OperatorAuthorizationError, match="ambiguous principal id"):
        authorizer.authorize_http_command(
            "PAUSE_ENTRIES",
            headers=headers,
            payload={},
            local_dev_token="process-secret-token",
        )


def test_managed_oidc_requires_app_level_authorization(tmp_path):
    authorizer = OperatorCommandAuthorizer(tmp_path / "auth.sqlite3", auth_mode="managed_oidc")

    assert authorizer.browser_commands_supported is False
    with pytest.raises(OperatorAuthorizationError, match="not authorized"):
        authorizer.authorize_http_command(
            "PAUSE_ENTRIES",
            headers=_managed_principal_headers("viewer-1"),
            payload={},
            local_dev_token="process-secret-token",
        )


def test_managed_oidc_rejects_forged_loose_role_headers(tmp_path):
    authorizer = OperatorCommandAuthorizer(
        tmp_path / "auth.sqlite3",
        auth_mode="managed_oidc",
        allowed_principals=("operator-1",),
    )

    with pytest.raises(OperatorAuthorizationError, match="required"):
        authorizer.authorize_http_command(
            "PAUSE_ENTRIES",
            headers={"X-MS-CLIENT-PRINCIPAL-ID": "operator-1", "X-MS-CLIENT-PRINCIPAL-ROLES": "TriggerTrade.Operator"},
            payload={},
            local_dev_token="process-secret-token",
        )


def test_managed_oidc_rejects_malformed_principal_payload(tmp_path):
    authorizer = OperatorCommandAuthorizer(
        tmp_path / "auth.sqlite3",
        auth_mode="managed_oidc",
        allowed_principals=("operator-1",),
    )

    with pytest.raises(OperatorAuthorizationError, match="invalid managed operator principal assertion"):
        authorizer.authorize_http_command(
            "PAUSE_ENTRIES",
            headers={"X-MS-CLIENT-PRINCIPAL": "not-base64-json", "X-MS-CLIENT-PRINCIPAL-ID": "operator-1"},
            payload={},
            local_dev_token="process-secret-token",
        )


def test_managed_oidc_rejects_missing_decoded_identity_context(tmp_path):
    authorizer = OperatorCommandAuthorizer(
        tmp_path / "auth.sqlite3",
        auth_mode="managed_oidc",
        allowed_principals=("operator-1",),
    )
    empty_payload = base64.b64encode(b"{}").decode("ascii").rstrip("=")

    with pytest.raises(OperatorAuthorizationError, match="missing authenticated identity context"):
        authorizer.authorize_http_command(
            "PAUSE_ENTRIES",
            headers={"X-MS-CLIENT-PRINCIPAL": empty_payload, "X-MS-CLIENT-PRINCIPAL-ID": "operator-1"},
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
            headers=_managed_principal_headers("operator-1"),
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
    assert authorizer.browser_commands_supported is False
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
    assert authorizer.browser_commands_supported is True
    assert command.principal.auth_source == LOCAL_DEV_AUTH_SOURCE


def test_env_authorizer_rejects_local_dev_compat_for_production_web(tmp_path):
    with pytest.raises(OperatorAuthorizationError, match="production operator auth cannot use local_dev_compat"):
        operator_authorizer_from_env(
            tmp_path / "auth.sqlite3",
            {
                "TRIGGERTRADE_RUNTIME_MODE": "production",
                "TRIGGERTRADE_PROCESS_ROLE": "web",
                "TRIGGERTRADE_AUTH_MODE": "local_dev_compat",
            },
        )


def test_managed_oidc_browser_commands_require_operator_allowlist(tmp_path):
    unavailable = OperatorCommandAuthorizer(tmp_path / "unavailable.sqlite3", auth_mode="managed_oidc")
    available = OperatorCommandAuthorizer(
        tmp_path / "available.sqlite3",
        auth_mode="managed_oidc",
        allowed_principals=("operator-1",),
    )

    assert unavailable.browser_commands_supported is False
    assert available.browser_commands_supported is True


def test_dashboard_server_does_not_mint_process_local_token_for_managed_auth(tmp_path):
    db = tmp_path / "dashboard-auth.sqlite3"
    server = create_server(port=0, db_path=db)
    try:
        assert server.operator_authorizer.auth_mode == MANAGED_OIDC_AUTH_SOURCE
        assert server.operator_control_token == ""
        assert server.read_model.operator_command_submit_enabled is False
    finally:
        server.server_close()


def test_dashboard_server_mints_process_local_token_only_for_explicit_local_dev_compat(tmp_path):
    db = tmp_path / "dashboard-auth.sqlite3"
    server = create_server(
        port=0,
        db_path=db,
        operator_authorizer=OperatorCommandAuthorizer(db, auth_mode="local_dev_compat"),
    )
    try:
        assert server.operator_authorizer.auth_mode == LOCAL_DEV_AUTH_SOURCE
        assert server.operator_control_token
        assert server.read_model.operator_command_submit_enabled is True
    finally:
        server.server_close()


def _managed_principal_headers(
    principal_id: str,
    *,
    encoded_claims: list[dict[str, str]] | None = None,
) -> dict[str, str]:
    payload = {
        "auth_typ": "aad",
        "name_typ": "name",
        "role_typ": "roles",
        "userId": principal_id,
        "claims": encoded_claims or [{"typ": "roles", "val": "TriggerTrade.Operator"}],
    }
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    return {
        "X-MS-CLIENT-PRINCIPAL": encoded,
        "X-MS-CLIENT-PRINCIPAL-ID": principal_id,
        "X-MS-CLIENT-PRINCIPAL-ROLES": "TriggerTrade.Operator",
    }

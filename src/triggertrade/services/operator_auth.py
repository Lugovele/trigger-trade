"""Durable operator command authorization boundary."""

from __future__ import annotations

import base64
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import re

from triggertrade.persistence.trace_store import TraceStore, TraceStoreError


MANAGED_OIDC_AUTH_SOURCE = "managed_oidc"
LOCAL_DEV_AUTH_SOURCE = "local_dev_compat"
OPERATOR_AUTH_EVENT_TYPE = "OPERATOR_COMMAND_AUTHORIZED"

_ID_RE = re.compile(r"^[A-Za-z0-9_.:@+-]{1,160}$")
_COMMAND_RE = re.compile(r"^[A-Z0-9_:-]{3,80}$")
_SECRET_RE = re.compile(
    r"(api[_-]?key|api[_-]?secret|authorization|bearer|cookie|csrf|session|token|password|credential|signature|\.env)",
    re.I,
)
_OPERATOR_ROLES = frozenset({"operator", "admin", "triggertrade.operator", "triggertrade.admin"})


class OperatorAuthorizationError(RuntimeError):
    """Raised when an operator command lacks durable authorization."""


@dataclass(frozen=True)
class OperatorPrincipal:
    principal_id: str
    auth_source: str
    roles: tuple[str, ...]


@dataclass(frozen=True)
class AuthorizedOperatorCommand:
    command_type: str
    principal: OperatorPrincipal
    target: str
    scope: str
    idempotency_key: str | None
    authorized_at: str

    @property
    def audit_source(self) -> str:
        return f"{self.principal.auth_source}:{self.principal.principal_id}"


class OperatorCommandAuthorizer:
    """Authorize operator/admin commands and durably audit the authorization fact."""

    def __init__(
        self,
        trace_store: TraceStore | str | Path,
        *,
        allowed_principals: Sequence[str] = (),
        auth_mode: str = "local_dev_compat",
    ) -> None:
        self._trace_store = trace_store if isinstance(trace_store, TraceStore) else TraceStore(trace_store)
        self._allowed_principals = frozenset(_clean_principal(value) for value in allowed_principals if str(value).strip())
        self.auth_mode = _clean_auth_mode(auth_mode)

    @property
    def browser_commands_supported(self) -> bool:
        if self.auth_mode == MANAGED_OIDC_AUTH_SOURCE:
            return bool(self._allowed_principals)
        return self.auth_mode == LOCAL_DEV_AUTH_SOURCE

    def authorize_http_command(
        self,
        command_type: str,
        *,
        headers: Mapping[str, str],
        payload: Mapping[str, object] | None,
        local_dev_token: str,
        target: str = "ACTIVE",
        scope: str = "OPERATOR",
        idempotency_key: str | None = None,
        authorized_at: str | None = None,
    ) -> AuthorizedOperatorCommand:
        command_type = _clean_command_type(command_type)
        target = _clean_id(target, "target")
        scope = _clean_command_type(scope)
        principal = None
        if self.auth_mode == MANAGED_OIDC_AUTH_SOURCE:
            principal = self._principal_from_headers(headers)
        elif self._has_managed_principal_headers(headers):
            raise OperatorAuthorizationError("managed operator principal headers are not enabled")
        if principal is None and self.auth_mode != MANAGED_OIDC_AUTH_SOURCE:
            principal = self._local_dev_principal(payload or {}, local_dev_token)
        if principal is None:
            raise OperatorAuthorizationError("operator authorization required")
        if not self._is_app_authorized(principal):
            raise OperatorAuthorizationError("operator is not authorized for command")

        clean_key = _optional_idempotency_key(idempotency_key)
        authorized_at = authorized_at or datetime.now(UTC).isoformat()
        command = AuthorizedOperatorCommand(
            command_type=command_type,
            principal=principal,
            target=target,
            scope=scope,
            idempotency_key=clean_key,
            authorized_at=authorized_at,
        )
        self._audit_command(command)
        return command

    def _principal_from_headers(self, headers: Mapping[str, str]) -> OperatorPrincipal | None:
        encoded = _first_header(headers, "X-MS-CLIENT-PRINCIPAL")
        if encoded is None:
            return None
        principal_payload = _decode_managed_principal(encoded)
        principal_id = _managed_principal_id(principal_payload)
        roles = _managed_principal_roles(principal_payload)
        header_id = _first_header(headers, "X-MS-CLIENT-PRINCIPAL-ID")
        if header_id is not None and _clean_principal(header_id) != principal_id:
            raise OperatorAuthorizationError("managed operator principal header mismatch")
        header_roles = _split_roles(_first_header(headers, "X-MS-CLIENT-PRINCIPAL-ROLES") or "")
        if header_roles:
            roles = tuple(dict.fromkeys((*roles, *header_roles)))
        return OperatorPrincipal(
            principal_id=principal_id,
            auth_source=MANAGED_OIDC_AUTH_SOURCE,
            roles=roles,
        )

    def _has_managed_principal_headers(self, headers: Mapping[str, str]) -> bool:
        return _first_header(
            headers,
            "X-TriggerTrade-Principal",
            "X-MS-CLIENT-PRINCIPAL-ID",
            "X-MS-CLIENT-PRINCIPAL-NAME",
            "X-MS-CLIENT-PRINCIPAL",
            "X-TriggerTrade-Roles",
            "X-MS-CLIENT-PRINCIPAL-ROLES",
        ) is not None

    def _local_dev_principal(self, payload: Mapping[str, object], local_dev_token: str) -> OperatorPrincipal | None:
        token = str(payload.get("token") or "")
        if not local_dev_token or token != local_dev_token:
            return None
        return OperatorPrincipal(
            principal_id="local_dashboard_operator",
            auth_source=LOCAL_DEV_AUTH_SOURCE,
            roles=("operator",),
        )

    def _is_app_authorized(self, principal: OperatorPrincipal) -> bool:
        if principal.auth_source == LOCAL_DEV_AUTH_SOURCE:
            return self.auth_mode != MANAGED_OIDC_AUTH_SOURCE
        if principal.principal_id in self._allowed_principals:
            return True
        return False

    def _audit_command(self, command: AuthorizedOperatorCommand) -> None:
        event_id = _event_id(command)
        existing = self._trace_store.get_audit_event(event_id)
        metadata = {
            "command_type": command.command_type,
            "authz_source": command.principal.auth_source,
            "roles": list(command.principal.roles),
            "idempotency_key": command.idempotency_key,
            "canonical_deployed_auth": command.principal.auth_source == MANAGED_OIDC_AUTH_SOURCE,
        }
        if existing is not None:
            if (
                existing.event_type == OPERATOR_AUTH_EVENT_TYPE
                and existing.source_id == command.principal.principal_id
                and existing.entity_id == command.command_type
                and existing.related_entity_id == command.target
                and existing.safe_metadata == metadata
            ):
                return
            raise OperatorAuthorizationError("operator command idempotency key conflict")
        try:
            self._trace_store.record_audit_event(
                event_type=OPERATOR_AUTH_EVENT_TYPE,
                source_type="USER_OPERATOR",
                source_id=command.principal.principal_id,
                scope=command.scope,
                entity_type="operator_command",
                entity_id=command.command_type,
                related_entity_type="operator_command_target",
                related_entity_id=command.target,
                result="AUTHORIZED",
                safe_metadata=metadata,
                created_at=command.authorized_at,
                event_id=event_id,
            )
        except TraceStoreError as exc:
            if "immutable audit event conflict" in str(exc):
                raise OperatorAuthorizationError("operator command idempotency key conflict") from exc
            raise OperatorAuthorizationError("operator command authorization audit failed") from exc


def operator_authorizer_from_env(trace_store: TraceStore | str | Path, env: Mapping[str, str]) -> OperatorCommandAuthorizer:
    auth_mode = env.get("TRIGGERTRADE_AUTH_MODE", MANAGED_OIDC_AUTH_SOURCE)
    if _production_runtime(env) and _clean_auth_mode(auth_mode) == LOCAL_DEV_AUTH_SOURCE:
        raise OperatorAuthorizationError("production operator auth cannot use local_dev_compat")
    return OperatorCommandAuthorizer(
        trace_store,
        auth_mode=auth_mode,
        allowed_principals=_split_csv(env.get("TRIGGERTRADE_OPERATOR_PRINCIPALS", "")),
    )


def _production_runtime(env: Mapping[str, str]) -> bool:
    runtime_mode = str(env.get("TRIGGERTRADE_RUNTIME_MODE") or "").strip().lower()
    process_role = str(env.get("TRIGGERTRADE_PROCESS_ROLE") or env.get("TRIGGERTRADE_ROLE") or "").strip().lower().replace("_", "-")
    return runtime_mode == "production" or process_role in {"web", "api", "dashboard"}


def _event_id(command: AuthorizedOperatorCommand) -> str:
    if command.idempotency_key is not None:
        return f"audit-operator-command-{command.idempotency_key}"
    return f"audit-operator-command-{command.command_type}-{command.target}-{command.authorized_at}"


def _first_header(headers: Mapping[str, str], *names: str) -> str | None:
    for name in names:
        value = headers.get(name)
        if value is not None and str(value).strip():
            return str(value).strip()
    lower = {str(key).lower(): str(value) for key, value in headers.items()}
    for name in names:
        value = lower.get(name.lower())
        if value is not None and value.strip():
            return value.strip()
    return None


def _split_roles(raw: str) -> tuple[str, ...]:
    return tuple(_clean_role(part) for part in re.split(r"[,; ]+", raw) if part.strip())


def _split_csv(raw: str) -> tuple[str, ...]:
    return tuple(part.strip() for part in raw.split(",") if part.strip())


def _decode_managed_principal(value: str) -> dict[str, object]:
    try:
        padded = value + "=" * (-len(value) % 4)
        raw = base64.b64decode(padded.encode("ascii"), validate=True)
        payload = json.loads(raw.decode("utf-8"))
    except Exception as exc:  # noqa: BLE001 - malformed auth context must fail closed.
        raise OperatorAuthorizationError("invalid managed operator principal assertion") from exc
    if not isinstance(payload, dict):
        raise OperatorAuthorizationError("invalid managed operator principal assertion")
    return payload


def _managed_principal_id(payload: Mapping[str, object]) -> str:
    for key in ("userId", "user_id", "principal_id", "id"):
        value = payload.get(key)
        if value:
            return _clean_principal(str(value))
    for claim in _managed_claims(payload):
        claim_type = str(claim.get("typ") or claim.get("type") or "").lower()
        if claim_type.endswith("/nameidentifier") or claim_type in {"sub", "oid", "nameidentifier"}:
            return _clean_principal(str(claim.get("val") or claim.get("value") or ""))
    raise OperatorAuthorizationError("managed operator principal assertion is missing principal id")


def _managed_principal_roles(payload: Mapping[str, object]) -> tuple[str, ...]:
    roles: list[str] = []
    raw_roles = payload.get("roles")
    if isinstance(raw_roles, str):
        roles.extend(_split_roles(raw_roles))
    elif isinstance(raw_roles, Sequence):
        roles.extend(_clean_role(str(role)) for role in raw_roles if str(role).strip())
    for claim in _managed_claims(payload):
        claim_type = str(claim.get("typ") or claim.get("type") or "").lower()
        if claim_type.endswith("/role") or claim_type in {"role", "roles"}:
            value = str(claim.get("val") or claim.get("value") or "")
            roles.extend(_split_roles(value))
    return tuple(dict.fromkeys(roles))


def _managed_claims(payload: Mapping[str, object]) -> tuple[Mapping[str, object], ...]:
    claims = payload.get("claims")
    if not isinstance(claims, Sequence) or isinstance(claims, (str, bytes)):
        return ()
    return tuple(claim for claim in claims if isinstance(claim, Mapping))


def _clean_auth_mode(value: str) -> str:
    text = str(value or "local_dev_compat").strip().lower()
    if text in {"managed_oidc", "entra", "entra_oidc"}:
        return MANAGED_OIDC_AUTH_SOURCE
    if text in {"local", "local_dev", "local_dev_compat"}:
        return "local_dev_compat"
    raise OperatorAuthorizationError("unsupported operator auth mode")


def _clean_command_type(value: str) -> str:
    text = " ".join(str(value).replace("\x00", "").split()).upper()
    if _COMMAND_RE.fullmatch(text) is None:
        raise OperatorAuthorizationError("invalid operator command type")
    return text


def _clean_principal(value: str) -> str:
    text = _clean_id(value, "operator principal")
    if _SECRET_RE.search(text):
        raise OperatorAuthorizationError("operator principal contains secret-like material")
    return text


def _clean_role(value: str) -> str:
    return _clean_id(value.lower(), "operator role")


def _optional_idempotency_key(value: str | None) -> str | None:
    if value is None or not str(value).strip():
        return None
    return _clean_id(str(value), "idempotency key")


def _clean_id(value: str, field: str) -> str:
    text = " ".join(str(value).replace("\x00", "").split())[:160]
    if not text or _ID_RE.fullmatch(text) is None or "/" in text or "\\" in text:
        raise OperatorAuthorizationError(f"invalid {field}")
    return text

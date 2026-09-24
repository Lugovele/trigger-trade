from triggertrade.dashboard.commands import DashboardCommandBoundary, DashboardCommandError
from triggertrade.dashboard.read_model import DashboardReadModel
from triggertrade.persistence import MessageStore, OperatorStateStore
from triggertrade.persistence.operator_state_store import TradingState
from triggertrade.services.operator_auth import AuthorizedOperatorCommand, OperatorPrincipal
from tests.unit.test_dashboard_read_model import _empty_db


def _authorized_command(command_type: str = "PAUSE_ENTRIES") -> AuthorizedOperatorCommand:
    return AuthorizedOperatorCommand(
        command_type=command_type,
        principal=OperatorPrincipal(
            principal_id="operator-1",
            auth_source="managed_oidc",
            roles=("TriggerTrade.Operator",),
        ),
        target="ACTIVE",
        scope="OPERATOR",
        idempotency_key="cmd-1",
        authorized_at="2026-09-15T00:00:00+00:00",
    )


def _boundary(db, *, operator_actions=None) -> DashboardCommandBoundary:
    return DashboardCommandBoundary(
        read_model=DashboardReadModel(db),
        operator_store=OperatorStateStore(db),
        message_store=MessageStore(db),
        trading_rules_service=object(),
        instrument_catalog_service=object(),
        research_service=object(),
        operator_actions=operator_actions,
    )


def test_pause_entries_records_state_action_and_message_from_authorized_command(tmp_path):
    db = _empty_db(tmp_path)
    boundary = _boundary(db)

    boundary.pause_entries(_authorized_command())

    state = OperatorStateStore(db).get_trading_state()
    actions = OperatorStateStore(db).operator_action_rows()
    messages = MessageStore(db).list_messages()

    assert state.state == TradingState.TRADING_PAUSED
    assert state.source == "managed_oidc:operator-1"
    assert actions[0].action == "PAUSE_ENTRIES"
    assert actions[0].source == "managed_oidc:operator-1"
    assert messages[0].title == "New entries paused"


def test_close_one_fails_closed_and_audits_when_execution_bridge_missing(tmp_path):
    db = _empty_db(tmp_path)
    boundary = _boundary(db)

    try:
        boundary.close_one(_authorized_command("CLOSE_ONE"), position_id="pos-1", symbol="BTCUSDT")
    except DashboardCommandError as exc:
        assert "execution bridge is not attached" in str(exc)
    else:  # pragma: no cover - assertion clarity if fail-closed behavior regresses.
        raise AssertionError("close_one must fail closed without an execution bridge")

    actions = OperatorStateStore(db).operator_action_rows()
    messages = MessageStore(db).list_messages()

    assert actions[0].action == "CLOSE_ONE"
    assert actions[0].result == "FAILED"
    assert actions[0].source == "managed_oidc:operator-1"
    assert messages[0].title == "Close One failed"


def test_close_one_redacts_secret_like_execution_errors_from_public_exception(tmp_path):
    class SecretLeakingOperatorActions:
        canonical_execution_bridge = True

        def close_position(self, **kwargs):
            raise RuntimeError("authorization bearer token abc123 failed")

    db = _empty_db(tmp_path)
    boundary = _boundary(db, operator_actions=SecretLeakingOperatorActions())

    try:
        boundary.close_one(_authorized_command("CLOSE_ONE"), position_id="pos-1", symbol="BTCUSDT")
    except DashboardCommandError as exc:
        public_error = str(exc)
    else:  # pragma: no cover - assertion clarity if fail-closed behavior regresses.
        raise AssertionError("close_one must fail closed when the execution bridge fails")

    assert public_error == "RuntimeError"
    assert "token" not in public_error.lower()
    assert "authorization" not in public_error.lower()

from http import HTTPStatus
from http.client import HTTPConnection
import json
import threading

from triggertrade.dashboard.__main__ import create_server
from triggertrade.persistence import MessageStore
from tests.unit.test_dashboard_read_model import _empty_db


def test_messages_api_lists_backend_messages_and_marks_visible_rows_read(tmp_path):
    db = _empty_db(tmp_path)
    message = MessageStore(db).create_message(
        created_at="2026-09-08T10:03:00+00:00",
        severity="ATTENTION",
        title="New entries paused",
        body="New entries were paused from the dashboard.",
        source="unit",
    )
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/api/messages")
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))

        assert response.status == HTTPStatus.OK
        assert payload["unread_count"] == 1
        assert payload["messages"][0]["message_id"] == message.message_id
        assert payload["messages"][0]["severity"] == "ATTENTION"

        conn.request(
            "POST",
            "/api/messages/mark-read",
            body=json.dumps({"token": server.operator_control_token, "message_ids": [message.message_id]}),
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        marked = json.loads(response.read().decode("utf-8"))
        assert response.status == HTTPStatus.OK
        assert marked["changed"] == 1
        assert marked["unread_count"] == 0
        assert MessageStore(db).get_message(message.message_id).is_read is True
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_messages_mark_read_requires_token_and_rejects_bad_ids(tmp_path):
    db = _empty_db(tmp_path)
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request(
            "POST",
            "/api/messages/mark-read",
            body=json.dumps({"token": "wrong", "message_ids": []}),
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.FORBIDDEN

        conn.request(
            "POST",
            "/api/messages/mark-read",
            body=json.dumps({"token": server.operator_control_token, "message_ids": ["../secret"]}),
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.BAD_REQUEST
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_operator_actions_create_factual_user_messages(tmp_path):
    db = _empty_db(tmp_path)
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        token = server.operator_control_token
        conn = HTTPConnection(host, port, timeout=2)
        conn.request(
            "POST",
            "/operator/pause",
            body=f"confirm=yes&token={token}",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.SEE_OTHER

        conn.request(
            "POST",
            "/operator/resume",
            body=f"confirm=yes&token={token}",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.SEE_OTHER

        conn.request(
            "POST",
            "/operator/close-one",
            body=f"confirm=yes&token={token}&position_id=pos-1&symbol=BTCUSDT",
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.SERVICE_UNAVAILABLE
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)

    rows = MessageStore(db).list_messages()
    assert [row.title for row in rows] == ["Close One failed", "New entries resumed", "New entries paused"]
    assert rows[0].severity.value == "ERROR"


def test_system_history_export_endpoint_is_protected_and_has_no_path_parameter(tmp_path):
    db = _empty_db(tmp_path)
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request(
            "POST",
            "/api/system-history/export",
            body=json.dumps({"path": "runtime/triggertrade_paper.sqlite3"}),
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.FORBIDDEN

        conn.request(
            "POST",
            "/api/system-history/export",
            body=json.dumps({"token": server.operator_control_token, "path": "../../.env"}),
            headers={"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        payload = json.loads(response.read().decode("utf-8"))
        assert response.status == HTTPStatus.OK
        assert "SYSTEM" in payload["text"]
        assert "../../.env" not in payload["text"]
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def test_no_logs_page_route_is_created(tmp_path):
    db = _empty_db(tmp_path)
    server = create_server(port=0, db_path=db)
    host, port = server.server_address
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        conn = HTTPConnection(host, port, timeout=2)
        conn.request("GET", "/logs")
        response = conn.getresponse()
        response.read()
        assert response.status == HTTPStatus.NOT_FOUND
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)
